# Fine-Tuning Plan: Qwen3.5-35B-A3B on Cedar Policy Synthesis

## Model

| Property | Value |
|---|---|
| Name | Qwen3.5-35B-A3B |
| Architecture | `Qwen3_5MoeForCausalLM` (VL-MoE backbone, text-only training) |
| Layers | 40 — every 4th is full attention, rest are linear attention (GatedDeltaNet) |
| Experts | 256 total, 8 active per token (~3B active params) |
| Total size | ~35B params, 67 GB BF16 on disk |
| Path | `~/model/qwen35b-full` |
| Context | 262,144 tokens max |

## Environment

- **Conda env:** `vllm` (transformers upgraded to 5.5.4 which adds `qwen3_5_moe` support)
- **Framework:** PyTorch 2.10 + TRL 1.1.0 + PEFT 0.19.0

## Dataset

| Split | Count | Path |
|---|---|---|
| Train | 70 | `finetune/data/train.jsonl` |
| Val | 7 (1 per domain) | `finetune/data/val.jsonl` |

Token stats: min 1,065 · mean 1,940 · max 4,261 · total ~136K

Val scenarios (never in training):
`github_deploy_env`, `doccloud_classification`, `hotel_vip_blocked`,
`sales_fiscal_window`, `streaming_release_window`, `tags_expiry`, `tax_document_type`

## Training Method: LoRA

Expert layers (`Qwen3_5MoeExperts`) store weights as fused `nn.Parameter` — not
`nn.Linear` — so standard LoRA cannot target them. LoRA is applied to all
`nn.Linear` layers across attention and shared MLP:

| Layer type | Count | LoRA targets |
|---|---|---|
| Full attention (`Qwen3_5MoeAttention`) | 10 | `q_proj, k_proj, v_proj, o_proj` |
| Linear attention (`Qwen3_5MoeGatedDeltaNet`) | 30 | `in_proj_qkv, out_proj` |
| Shared MLP (`Qwen3_5MoeMLP`) | 40 | `gate_proj, up_proj, down_proj` |
| Expert params (`Qwen3_5MoeExperts`) | 40 | — (fused `nn.Parameter`, skipped) |

LoRA rank 16 / alpha 32 → ~150M trainable params out of ~35B (~0.43%).

## Configuration-Driven Workflow

The fine-tuning entrypoint is now configuration-driven.

- `experiments.conf` is the source of truth for hyperparameters
- `run_experiments.sh` reads that config and launches `torchrun`
- `launch.sh` is now only a compatibility wrapper that forwards to
  `run_experiments.sh`

This means you no longer edit shell flags inside the launcher itself.
To create or modify experiments, change `experiments.conf`.

## Running

List the experiments currently defined in the config:

```bash
conda activate vllm
cd ~/cedar-synthesis-engine/cedarforge
bash sft_gen/finetune/run_experiments.sh --list
```

Run all experiments in `RUN_IDS`:

```bash
bash sft_gen/finetune/run_experiments.sh
```

Run one specific experiment:

```bash
bash sft_gen/finetune/run_experiments.sh --run A
bash sft_gen/finetune/run_experiments.sh --run C
```

Evaluate an existing adapter without retraining:

```bash
bash sft_gen/finetune/run_experiments.sh --run A --skip-train --eval
```

Use a different config file:

```bash
bash sft_gen/finetune/run_experiments.sh \
  --config sft_gen/finetune/my_experiments.conf
```

## Hyperparameter File

The default config file is:

- `sft_gen/finetune/experiments.conf`

Global fields:

| Field | Meaning |
|---|---|
| `BASE_MODEL` | Base model path |
| `TRAIN_FILE` | Training JSONL |
| `VAL_FILE` | Validation JSONL |
| `VAL_META_FILE` | Validation metadata used by `evaluate.py` |
| `OUTPUT_ROOT` | Root directory for run outputs |
| `PREPARE_DATA` | Whether to run `prepare_data.py` before each training run |
| `EVAL_AFTER_TRAIN` | Whether to evaluate automatically after each run |
| `MASTER_PORT_BASE` | Default fallback for `torchrun` master ports |
| `RUN_IDS` | Ordered list of experiments to run by default |

Per-run fields use the pattern `RUN_<ID>_<FIELD>`, for example:

| Field suffix | Meaning |
|---|---|
| `NAME` | Human-readable run name |
| `GPUS` | Number of GPUs for `torchrun` |
| `BATCH` | Per-device batch size |
| `ACCUM` | Gradient accumulation steps |
| `EPOCHS` | Number of epochs |
| `LR` | Learning rate |
| `RANK` | LoRA rank |
| `ALPHA` | LoRA alpha |
| `LORA_DROPOUT` | LoRA dropout |
| `MAX_SEQ_LEN` | Max sequence length |
| `USE_QLORA` | `1` to enable 4-bit QLoRA |
| `DISABLE_LAZY_NO_MMAP` | `1` to use default `mmap` loader instead of heap-read loader |
| `OUTPUT_DIR` | Output directory for that run |
| `MASTER_PORT` | Explicit `torchrun` master port |

Current example runs in `experiments.conf`:

| Run | Name | Key settings |
|---|---|---|
| `A` | `stable-baseline` | `gpus=2, batch=1, accum=8, epochs=4, lr=1e-4, rank=16` |
| `B` | `high-lr-control` | `gpus=4, batch=1, accum=8, epochs=4, lr=2e-4, rank=16` |
| `C` | `high-capacity` | `gpus=4, batch=2, accum=4, epochs=4, lr=1e-4, rank=32` |
| `D` | `longer-training` | `gpus=4, batch=2, accum=4, epochs=6, lr=1e-4, rank=16` |

To add a new run:

1. Add its id to `RUN_IDS`, for example `RUN_IDS=(A B C D E)`
2. Copy an existing block in `experiments.conf`
3. Change the values
4. Launch with `bash sft_gen/finetune/run_experiments.sh --run E`

## Known Issues and Fixes Applied

**`qwen3_5_moe` not found (transformers 4.57.6)**
→ Upgraded to `transformers==5.5.4` in the vllm env.

**FlashAttention2 not installed**
→ Changed to `attn_implementation="sdpa"` (PyTorch built-in, no extra package).

**mmap ENOMEM with 4 DDP processes**
→ Applied no-mmap patch (`_LazyHeapSafeOpen`) that reads tensors via `read()` instead
of `mmap()`, plus staggered loading with `dist.barrier()` so only one rank loads at a time.
This is enabled by default. To force the default `mmap` loader for a specific
run, set `RUN_<ID>_DISABLE_LAZY_NO_MMAP=1` in `experiments.conf`.

## Output

Each run writes to its own output directory, typically:

- `finetune/checkpoints/run_A/`
- `finetune/checkpoints/run_B/`
- `finetune/checkpoints/run_C/`
- `finetune/checkpoints/run_D/`

Within a run directory:

- epoch checkpoints are saved as `checkpoint-N/`
- the final selected adapter is saved to `final_adapter/`

The adapter is ~50 MB. The base model is never modified.

## After Training

**Evaluate one trained run:**
```bash
conda activate vllm
cd ~/cedar-synthesis-engine/cedarforge
bash sft_gen/finetune/run_experiments.sh --run A --skip-train --eval
```

Equivalent direct call:

```bash
python sft_gen/finetune/evaluate.py \
    --adapter  sft_gen/finetune/checkpoints/run_A/final_adapter \
    --base-model ~/model/qwen35b-full \
    --val-file sft_gen/finetune/data/val.meta.jsonl
```

**Merge and serve with vLLM:**
```bash
python - <<'EOF'
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch, os

base = AutoModelForCausalLM.from_pretrained(
    os.path.expanduser("~/model/qwen35b-full"),
    torch_dtype=torch.bfloat16, trust_remote_code=True)
model = PeftModel.from_pretrained(base, "sft_gen/finetune/checkpoints/run_A/final_adapter")
model.merge_and_unload().save_pretrained("~/model/cedar-qwen35b")
AutoTokenizer.from_pretrained(
    os.path.expanduser("~/model/qwen35b-full")).save_pretrained("~/model/cedar-qwen35b")
EOF

vllm serve ~/model/cedar-qwen35b --port 8002 --model cedar-qwen35b
```

## Files

```
finetune/
├── experiments.conf   ← hyperparameter source of truth
├── run_experiments.sh ← main entry point; reads experiments.conf
├── launch.sh          ← compatibility wrapper to run_experiments.sh
├── train.py           ← training loop (LoRA + SFTTrainer, heap-read loader by default)
├── prepare_data.py    ← generates data/train.jsonl + data/val.jsonl
├── evaluate.py        ← runs val set through model, checks cedar validate + symcc
├── FINETUNE_PLAN.md   ← this file
└── data/
    ├── train.jsonl
    ├── val.jsonl
    └── val.meta.jsonl
```
