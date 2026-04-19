# Claude Code Guidelines for Cedarforge

## Collaboration Rules

### Confirm Before Heavy Coding
Before writing significant code (new modules, scrapers, pipelines, data processing scripts),
outline the plan and discuss it with the user first. Only proceed after explicit confirmation.

### No Chinese in Code
All code comments, variable names, string literals, prompts, and log messages must be in English.
Chinese is only acceptable in this file and in user-facing documentation outside of code.

## Data Pipeline Context

### Current Training Data Pipeline
- `data/layer1_raw/cedar_docs.jsonl` is retained as the scraped Layer 1 seed dataset.
- `src/data/layer1/scrape_docs.py` is retained as the reproducible extractor for that seed dataset.
- `sft_gen/` is the active SFT data generation pipeline.
- `sft_gen/generate.py` creates scenario directories from CedarBench base schemas and registered SFT mutations.
- `sft_gen/synthesize.py` writes `candidate.cedar` for each scenario and validates candidates with `cedar validate`.
- `sft_gen/pack_sft.py` packages scenarios into chat fine-tuning records.
- `sft_gen/finetune/prepare_data.py` creates the Qwen training and validation JSONL files.

### Legacy Data Pipeline
- The old `src/data/layer2/` pipeline has been removed.
- The removed Layer 2 pipeline was an unfinished standalone generator and is superseded by `sft_gen/`.

### What NOT to Use as Training Data
- `cedarbench/` is the target benchmark and should not be used directly as training examples.
- `cedar-integration-tests` and `cedar-examples` are used in CedarBench and should not be used as training data.
