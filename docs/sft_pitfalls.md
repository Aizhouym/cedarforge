# SFT Fine-Tuning Pitfalls: Qwen3.5-35B-A3B on Cedar Synthesis

Lessons learned from the first SFT run (Runs E and F, April 2026).
Read this before starting any future fine-tuning experiment on this model.

---

## The Model: What It Actually Is

`~/model/qwen35b-full` is **Qwen3.5-35B-A22B**, a multimodal (vision-language) MoE model.
- Architecture: `Qwen3_5MoeForConditionalGeneration`
- ~67 GB in BF16
- Text + vision encoder; `preprocessor_config.json` and `video_preprocessor_config.json` are part of the model directory

**Critical implication:** fine-tuning only the text LoRA layers leaves the vision encoder
untouched, but vLLM still expects all VL processor files to be present in the merged model
directory. Missing these files causes `OSError: Can't load image processor` at serve time.

**Fix:** after merging the adapter, copy all non-safetensors files from the base model:
```bash
cp ~/model/qwen35b-full/preprocessor_config.json  ~/model/cedar-qwen35b-runE/
cp ~/model/qwen35b-full/video_preprocessor_config.json ~/model/cedar-qwen35b-runE/
cp ~/model/qwen35b-full/vocab.json ~/model/cedar-qwen35b-runE/
# and verify config.json model_type == "qwen3_5_moe" (not "qwen3_5_moe_text")
```

---

## Issue 1: `config.json` model_type Mismatch After Merge

**Symptom:** vLLM fails immediately — "model type `qwen3_5_moe_text` not supported".

**Root cause:** `transformers` 5.5.x saves the LoRA-merged model with `model_type: qwen3_5_moe_text`
(the text-only sub-config class `Qwen3_5MoeTextConfig`) instead of `qwen3_5_moe`.
vLLM looks up architectures by `model_type` and cannot find a handler for `qwen3_5_moe_text`.

**Fix:**
```bash
cp ~/model/qwen35b-full/config.json ~/model/cedar-qwen35b-runE/config.json
```
The base model's `config.json` has `model_type: qwen3_5_moe` and
`architectures: ["Qwen3_5MoeForConditionalGeneration"]` — exactly what vLLM expects.

---

## Issue 2: ENOMEM / mmap Failures on HPC Nodes

**Symptom:** `OSError: [Errno 12] Cannot allocate memory` when loading the model with
`transformers.AutoModelForCausalLM.from_pretrained()` or `safetensors.safe_open()`.

**Root cause:** The HPC cluster has `vm.overcommit_memory=2`, which blocks large `mmap()` calls.
`safetensors` uses mmap by default; 67 GB of model weights exhaust the mmap budget.

**Fix:** patch `transformers.modeling_utils.safe_open` with a heap-based reader before
loading the model. See `sft_gen/finetune/merge_adapter.py` — the `_patch_safe_open_no_mmap()`
function. Apply it in any script that calls `from_pretrained()` on this node:

```python
_patch_safe_open_no_mmap()          # must be called BEFORE from_pretrained
model = AutoModelForCausalLM.from_pretrained(...)
```

---

## Issue 3: Qwen3 Chat Template Always Injects `<think>` Tokens

**Symptom:** After fine-tuning, the model outputs a long `<think>...</think>` block before
any Cedar policy, exhausting `max_new_tokens` before the actual answer appears.
Even with `enable_thinking=False` the base model strongly prefers the thinking pattern.

**Root cause:** Qwen3's `apply_chat_template()` always inserts `<think>\n` into the
generation prompt (the `[UNUSED_TOKEN_...]` / `<think>` sentinel). A LoRA adapter with
~0.43% of total parameters cannot override this deeply-ingrained prior.

**Fix:** Bypass `apply_chat_template()` entirely. Build ChatML manually without any
think tokens in **both the training data and the evaluation prompt**:

```python
# Training format (prepare_data.py / load_record)
text = (
    f"<|im_start|>system\n{SFT_SYSTEM}<|im_end|>\n"
    f"<|im_start|>user\n{user_msg}<|im_end|>\n"
    f"<|im_start|>assistant\n<cedar_policy>\n{cedar}\n</cedar_policy><|im_end|>\n"
)

# Inference prompt (evaluate.py / generate)
text = (
    f"<|im_start|>system\n{SFT_SYSTEM}<|im_end|>\n"
    f"<|im_start|>user\n{user_content}<|im_end|>\n"
    f"<|im_start|>assistant\n"          # no <think> here
)
inputs = tokenizer(text, add_special_tokens=False, return_tensors="pt")
```

The training data must also omit think tokens — if you trained with think tokens and are
now evaluating without them, the format mismatch degrades quality.

---

## Issue 4: Full-Sequence Loss Dilutes the Training Signal

**Symptom:** Validation loss looks fine but generated Cedar is malformed or ignores the spec.

**Root cause:** `SFTTrainer` with `dataset_text_field="text"` computes cross-entropy loss
over the entire sequence (system prompt + user message + assistant response). The prompt
tokens account for ~74% of the sequence but carry no useful learning signal. The effective
response-only loss is diluted ~4×.

**Fix:** Pre-tokenize the dataset and mask prompt tokens with `-100` labels.
Use `DataCollatorForSeq2Seq` instead of the default collator. See `train.py`:

```python
ASSISTANT_MARKER = "<|im_start|>assistant\n"

def format_record(example):
    full_text = example["text"]
    split_idx = full_text.rfind(ASSISTANT_MARKER)
    prompt_text = full_text[:split_idx + len(ASSISTANT_MARKER)]
    full_enc   = tokenizer(full_text, add_special_tokens=False,
                           truncation=True, max_length=args.max_seq_len)
    prompt_enc = tokenizer(prompt_text, add_special_tokens=False)
    prompt_len = min(len(prompt_enc["input_ids"]), len(full_enc["input_ids"]))
    labels = [-100] * prompt_len + full_enc["input_ids"][prompt_len:]
    return {"input_ids": full_enc["input_ids"],
            "attention_mask": full_enc["attention_mask"],
            "labels": labels}
```

Pass `dataset_text_field=None` to `SFTTrainer` when using pre-tokenized data.

---

## Issue 5: `load_best_model_at_end=True` Triggers mmap OOM During Training

**Symptom:** Training runs fine but crashes at the end when the trainer tries to reload
the best checkpoint (e.g., epoch 3 of 8).

**Root cause:** HuggingFace's `load_best_model_at_end` calls `load_adapter()` internally,
which uses the native `safe_load_file()` — NOT the patched `_patch_safe_open_no_mmap()` version.
This triggers the same ENOMEM mmap failure as Issue 2.

**Fix:** Disable automatic best-model loading and copy the best checkpoint manually:

```python
# In TrainingArguments:
load_best_model_at_end=False,
save_strategy="epoch",
evaluation_strategy="epoch",
metric_for_best_model="eval_loss",

# After training finishes:
import json, shutil
state = json.loads(Path(args.output_dir, "trainer_state.json").read_text())
best_ckpt = state["best_model_checkpoint"]
final_adapter = Path(args.output_dir) / "final_adapter"
shutil.copytree(best_ckpt, final_adapter, dirs_exist_ok=True)
```

---

## Issue 6: LoRA Cannot Target MoE Expert Layers (`nn.Parameter`)

**Symptom:** PEFT raises an error or silently skips layers when `target_modules` includes
expert weight names like `experts.*.gate` or `shared_expert.*`.

**Root cause:** Qwen3.5 MoE implements its expert layers as raw `nn.Parameter` objects, not
as `nn.Linear` modules. PEFT's LoRA implementation wraps `nn.Linear` layers only;
`nn.Parameter` tensors cannot be wrapped.

**Fix:** Target only the attention projection layers (which are standard `nn.Linear`):

```python
target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",   # standard attention
    "in_proj_qkv", "out_proj",                  # linear attention variant
    "gate_proj", "up_proj", "down_proj",        # shared MLP projections
]
```

Do not include expert parameter names. Rank=32 / alpha=64 on these layers provides
enough capacity for task-specific fine-tuning.

---

## Issue 7: `<cedar_policy>` Tag Extraction is Essential

**Symptom:** Evaluate script picks up prose, markdown fences, or think-block content
as the Cedar candidate, causing `cedar validate` to always fail.

**Fix:** Wrap the assistant's Cedar output in `<cedar_policy>...</cedar_policy>` tags
in training data. In evaluate.py, extract with:

```python
import re
m = re.search(r"<cedar_policy>\s*(.*?)\s*</cedar_policy>", text, flags=re.DOTALL)
if m:
    return m.group(1).strip()
```

This is immune to think tokens, markdown fences, and surrounding prose.
Fall back to stripping `</think>` and markdown fences only if tags are absent (zero-shot baseline).

---

## Issue 8: `merge_adapter.py` — Cannot Call `.cpu()` Before Saving

**Symptom:** `torch.cuda.OutOfMemoryError` or system hangs when attempting to move the
merged 67 GB model from GPU to CPU before saving.

**Root cause:** The node does not have 67 GB of free CPU RAM.

**Fix:** Save the model directly from GPU. `save_pretrained()` with `safe_serialization=True`
serialises shard-by-shard and never needs the full model in CPU RAM at once:

```python
model = model.merge_and_unload()
# Do NOT call model.cpu() here
model.save_pretrained(output_dir, safe_serialization=True, max_shard_size="5GB")
```

---

## Serving the Merged Model with vLLM

After resolving all issues above, the full sequence to merge and serve is:

```bash
# Step 1 — Merge
conda activate vllm
cd ~/cedar-synthesis-engine/cedarforge
python sft_gen/finetune/merge_adapter.py --run E
# => saves to ~/model/cedar-qwen35b-runE/

# Step 2 — Copy VL processor files (required even for text-only fine-tuning)
cp ~/model/qwen35b-full/preprocessor_config.json  ~/model/cedar-qwen35b-runE/
cp ~/model/qwen35b-full/video_preprocessor_config.json ~/model/cedar-qwen35b-runE/
cp ~/model/qwen35b-full/vocab.json ~/model/cedar-qwen35b-runE/
cp ~/model/qwen35b-full/config.json ~/model/cedar-qwen35b-runE/  # fixes model_type

# Step 3 — Serve
vllm serve ~/model/cedar-qwen35b-runE \
  --served-model-name cedar-qwen35b \
  --port 8002 \
  --max-model-len 20480 \
  --trust-remote-code
```

---

## Summary Table

| # | Issue | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `model_type` mismatch in vLLM | transformers saves `Qwen3_5MoeTextConfig` | copy base `config.json` |
| 2 | ENOMEM mmap on HPC | `vm.overcommit_memory=2` blocks mmap | `_patch_safe_open_no_mmap()` |
| 3 | Think tokens in output | Qwen3 template always injects `<think>` | bypass `apply_chat_template`, manual ChatML |
| 4 | Full-sequence loss | SFTTrainer includes prompt in loss | mask prompt with -100, `DataCollatorForSeq2Seq` |
| 5 | OOM at best-checkpoint reload | `load_adapter()` uses native mmap | `load_best_model_at_end=False`, manual copy |
| 6 | Cannot target expert layers | MoE experts are `nn.Parameter` not `nn.Linear` | target attention + shared MLP only |
| 7 | Prompt text returned as Cedar | No structured output format | `<cedar_policy>` tags + regex extraction |
| 8 | OOM on `.cpu()` before save | 67 GB model > CPU RAM | save directly from GPU |
| 9 | Missing VL processor files | VL model; merge_adapter only saves text weights | copy processor configs from base model |


