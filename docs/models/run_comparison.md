# Fine-Tuned Model Comparison: Runs E / G / H / I

All four runs fine-tune Qwen3.5-35B-A22B on the same 70-example Cedar synthesis
dataset with response-only loss and no think tokens. Base model: `~/model/qwen35b-full`.

---

## Config Comparison

| Setting | Run E | Run G | Run H | Run I |
|---|---|---|---|---|
| GPUs | 2× H100 NVL | 2× H100 NVL | 2× H100 NVL | 2× H100 NVL |
| batch / GPU | 1 | 1 | **2** | 1 |
| grad accum | 16 | 16 | 8 | 16 |
| effective batch | 32 | 32 | 32 | 32 |
| epochs | 8 | 8 | 12 | 16 |
| LR | 8e-5 | 8e-5 | **5e-5** | 8e-5 |
| LoRA rank | 32 | **64** | **64** | **64** |
| LoRA alpha | 64 | 128 | 128 | 128 |
| dropout | 0.05 | 0.05 | 0.05 | 0.05 |
| QLoRA | No | No | No | No |

---

## Training Loss

| Epoch | Run E | Run G | Run H | Run I |
|---|---|---|---|---|
| 1 | 0.1189 | 0.0875 | 0.1258 | 0.1125 |
| 2 | 0.0649 | 0.0541 | 0.0653 | 0.0581 |
| 3 | 0.0499 | 0.0395 | 0.0505 | 0.0415 |
| 4 | 0.0418 | 0.0327 | 0.0413 | 0.0333 |
| 5 | 0.0372 | 0.0298 | 0.0341 | 0.0283 |
| 6 | 0.0350 | 0.0281 | 0.0302 | 0.0263 |
| 7 | **0.0330** | **0.0270** | 0.0286 | 0.0260 |
| 8 | — | — | 0.0279 | 0.0268 |
| 9 | — | — | **0.0273** | **0.0254** |
| 10 | — | — | 0.0280 | 0.0261 |
| 11 | — | — | 0.0274 | 0.0268 |
| 12 | — | — | — | 0.0263 |
| 13–15 | — | — | — | 0.0281→0.0275 |

**Best checkpoint (by eval loss):**

| Run | Best eval loss | Best epoch | Total steps |
|---|---|---|---|
| E | 0.0330 | 7 | 21 |
| G | 0.0270 | 7 | 21 |
| H | 0.0273 | 9 | 33 (best at step 27) |
| I | **0.0254** | 9 | 45 (best at step 27) |

---

## Key Differences and What Each Run Tests

### Run E — Baseline SFT
- **What it tests:** minimal working configuration. rank=32, 8 epochs, BF16.
- **Strength:** proven stable, fastest to train (21 steps).
- **Weakness:** highest eval loss (0.0330); limited LoRA capacity.
- **CedarBench result (known):** 42.1% no-repair, **78.5% repair** (3.2× faster than base model repair).

### Run G — Rank Ablation
- **What it tests:** does doubling LoRA rank (32→64) improve quality, everything else equal?
- **Strength:** lower eval loss (0.0270 vs 0.0330) with same training cost as E.
  rank=64 gives the model more capacity to learn Cedar-specific idioms.
- **Weakness:** same 8 epochs, may still underfit on complex patterns.
- **Expected advantage over E:** better hotel/tags scenarios that require
  precise attribute navigation (hallucinated attributes were the main schema failure).

### Run H — Stability Focus
- **What it tests:** batch=2 + lower LR (5e-5) + more epochs (12). Prioritises stable
  convergence over raw speed.
- **Strength:** larger batch gradient is more representative per step; lower LR reduces
  the distribution shift that caused no-repair regressions in runE.
  Best checkpoint (0.0273) is similar to G despite more conservative LR.
- **Weakness:** epochs 10–11 show slight oscillation (0.0280 → 0.0274), suggesting
  the model is near its convergence floor on this dataset.
- **Expected advantage over E:** fewer no-repair regressions on simple base scenarios
  (clinical_base, github_add_private, etc.) due to lower LR.

### Run I — Convergence Focus
- **What it tests:** 2× more epochs (16) with same memory footprint as E. Tests whether
  more training steps close the gap on complex scenarios.
- **Strength:** **best eval loss overall (0.0254)** reached at epoch 9, with best checkpoint
  at step 27. More exposure to Cedar syntax patterns (has guards, attribute navigation).
- **Weakness:** epochs 10–15 show oscillation around 0.026–0.028, meaning the model does
  not further improve after epoch 9 — extra epochs beyond 9 are wasted.
  Same potential no-repair regression risk as E (same LR).
- **Expected advantage over E:** strongest Cedar syntax internalization; most likely to
  break stuck schema and syntax loops.

---

## Which Model to Evaluate First

Based on eval loss and design intent:

| Priority | Run | Reason |
|---|---|---|
| 1 | **I** | Lowest eval loss (0.0254); most training signal |
| 2 | **G** | Clean rank ablation vs E; lower loss than E with no other changes |
| 3 | **H** | Lower LR may fix no-repair regressions; test separately |
| 4 | E | Already evaluated; baseline reference |

---

## How to Merge and Serve

```bash
# Merge adapter into base model
conda activate vllm
cd ~/cedar-synthesis-engine/cedarforge
python sft_gen/finetune/merge_adapter.py --run G   # or H, I

# Copy VL processor files (required — model is multimodal)
RUN=G
cp ~/model/qwen35b-full/preprocessor_config.json   ~/model/cedar-qwen35b-run${RUN}/
cp ~/model/qwen35b-full/video_preprocessor_config.json ~/model/cedar-qwen35b-run${RUN}/
cp ~/model/qwen35b-full/vocab.json                 ~/model/cedar-qwen35b-run${RUN}/
cp ~/model/qwen35b-full/config.json                ~/model/cedar-qwen35b-run${RUN}/

# Serve
vllm serve ~/model/cedar-qwen35b-run${RUN} \
  --served-model-name cedar-qwen35b \
  --port 8002 \
  --max-model-len 20480 \
  --trust-remote-code
```
