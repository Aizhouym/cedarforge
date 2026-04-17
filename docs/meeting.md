# SFT Meeting Notes — April 17/2026

---

## 1. Training Data Design

### Dataset

- **70 training examples, 7 val examples** (1 held-out per domain)
- Sourced from Opensource Repo: cedar-examples 7 user cases.
- Format: ChatML with manual construction 

### Training Template: ChatML 

Qwen3's chat template always injects `<think>\n` into the generation prompt regardless of
`enable_thinking=False`. A LoRA adapter covering 0.43% of parameters cannot suppress this
deeply-ingrained prior. Solution: build raw ChatML directly, with no think tokens in either
training data or inference prompts.

```
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{schema + spec}<|im_end|>
<|im_start|>assistant
<cedar_policy>
{cedar policy}
</cedar_policy><|im_end|>
```

### Output format: `<cedar_policy>` tags

The assistant output is wrapped in `<cedar_policy>...</cedar_policy>` tags.


### Response-only loss

In our data, ~74% of tokens are prompt (system + user message) — only 26% are the actual Cedar response. This dilutes
the training signal ~4×.

Loss is computed only on the assistant's Cedar output.

---

## 2. Model and LoRA Configuration

- **Model:** Qwen3.5-35B-A3B (`~/model/qwen35b-full`), ~67 GB BF16
- **Architecture:** 40 layers, 256 MoE experts (8 active/token)

### LoRA target modules

Expert layers in this model are `nn.Parameter` (fused weight tensors), not `nn.Linear` —
they cannot be wrapped by standard LoRA. Targets are limited to:

| Layer type | Modules |
|---|---|
| Full attention (10 layers) | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Linear attention (30 layers) | `in_proj_qkv`, `out_proj` |
| Shared MLP (all 40 layers) | `gate_proj`, `up_proj`, `down_proj` |

Rank = 32, Alpha = 64. ~2.1B trainable parameters.

### Run E hyperparameters (2× H100, completed)

| Hyperparameter | Value | Rationale |
|---|---|---|
| Batch / GPU | 2 | H100 80GB: only ~13 GB headroom after model |
| Gradient accumulation | 16 | Effective batch = 32 |
| Epochs | 8 | Response-only loss = 26% of tokens; needs more steps to converge |
| Learning rate | 8e-5 | Conservative for 70-example dataset |
| Max seq len | 4096 | Covers all scenarios |

---

## 3. Experimental Results

| Method | Tasks | Passed | Pass rate | Avg semantic acc | Avg runtime |
|---|---:|---:|---:|---:|---:|
| `qwen35b` no repair (baseline) | 121 | 59 | 48.8% | 0.607 | 10.8s |
| `qwen35b` repair loop (baseline) | 120 | 76 | 63.3% | 0.757 | 29.8s |
| `qwen35B_runE` no repair | 121 | 51 | 42.1% | 0.625 | 6.1s |
| **`qwen35B_runE` repair loop** | **121** | **95** | **78.5%** | **0.821** | **9.3s** |

### Key finding

Fine-tuning produces a split outcome:

- **Without repair:** fine-tuned model is weaker (-6.7 points). 17 regressions, mostly on
  simpler base scenarios the baseline already solved.
- **With repair:** fine-tuned model is substantially stronger (+15.2 points, +19 tasks).
  Also 3.2× faster than the baseline repair loop (9.3s vs 29.8s).

The fine-tuned model has learned Cedar idioms and the output format well, making it highly
responsive to repair feedback. Single-shot it is less stable because 70 examples shifted
the distribution without fully stabilizing it.

### Repair benefit inside the fine-tuned model

| Outcome (no repair → repair) | Count |
|---|---:|
| Fail → Pass | 45 |
| Pass → Pass | 50 |
| Fail → Fail | 25 |
| Pass → Fail | 1 |

Only 1 task regresses when adding repair. Repair is essentially monotonically beneficial
for `qwen35B_runE`.

### Remaining failures analysis

### syntax error(8 tasks)

**1. Annotation placement** `policy_annotations` 

Cedar annotation syntax requires `@id(...)` to appear *before* the `permit`/`forbid` keyword,
not after the closing `}`. 

```cedar
// Generated (wrong):
permit ( ... ) when { ... }
@id("viewer-read-published")   ← Cedar rejects: unexpected token @

// Correct:
@id("viewer-read-published")
permit ( ... ) when { ... }
```


**2. `has` keyword misuse** `tags_add_sensitivity` 

Cedar's `has` is a binary infix operator, not a method call.
The model cycles through multiple wrong forms:

```cedar
// Wrong — method call:
resource.tags.has("production_status")   ← "has" is a reserved identifier, cannot call it

// Wrong — missing parens:
resource.tags.has production_status      ← unexpected token

// Correct:
resource.tags has "production_status"
```


**3. Markdown/tag leakage** 

The baseline model sometimes wraps its output in ` ```cedar ` fences or `<cedar_policy>`
tags that are not stripped, causing a parse failure on the very first token.
This is fixed in `qwen35B_runE` (which was trained on the tagged format), but `sales_base`
still fails runE for a different reason (optional-attribute `has` guard).


### schema error(13 tasks)

The generated *policy* fails `cedar validate --schema` because it references entities or attributes incorrectly.
Three concrete sub-types observed:

**1. Hallucinated attribute names** (`hotel_*` scenarios)


```
iter 1: resource.property.viewPermissions   ← "property" not found
iter 2: resource.viewPermissions.property   ← "viewPermissions" not found
iter 3: resource.property.viewPermissions   ← repeats
```

**2. Missing `has` guard on optional attributes** (`tags_*` and `sales_*` scenarios)

Cedar requires `context has targetUser` before accessing `context.targetUser` when `targetUser`
is optional. 

```
// Wrong — accesses context.targetUser without has-guard:
when { context.targetUser.role == "admin" }

// Correct:
when { context has targetUser && context.targetUser.role == "admin" }
```

**3. Invalid action scope** (`hotel_add_franchise`, `hotel_franchise_loyalty` in runE)

The model writes a `permit` with an action that can't apply to the principal/resource
combination defined in the schema, results error: `"unable to find an applicable action given the policy
scope constraints"`. 

## Semantic error(5 tasks)




## Open Questions

1. **More targeted training data:** create more real life scenerio examples and collect the wrong cedar files generated by model as bad examples. So the model can have a deeper understanding above the syntax and schema.

2. **Run different evaluation:** different hyperparameters may produce a model with fewer regressions. use different learning rate, batch to train the model.

3. **Stronger repair prompts:** give a detailed error feedback.

4. **GRPO RL Method:** enhance model's semantic ability.  
