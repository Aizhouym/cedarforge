# Cedar SFT Data Construction Plan

## Current Status

The active training-data path is `sft_gen/`.

Layer 1 remains in the repository as seed data:

- `data/layer1_raw/cedar_docs.jsonl` contains the scraped Cedar documentation
  examples.
- `src/data/layer1/scrape_docs.py` is the extractor used to reproduce that
  dataset.

The previous standalone Layer 2 pipeline under `src/data/layer2/` has been
removed. It was an unfinished LLM-generation design with a placeholder API
function. Current second-stage SFT data generation now lives in `sft_gen/` and
uses structured scenario mutation, validation, synthesis, and packing steps.

## Active Stage 2 Pipeline

The current second-stage data path is:

1. `python sft_gen/generate.py`
   - Creates scenario directories under `sft_gen/scenarios/`.
   - Uses CedarBench base schemas and SFT-only mutations.
   - Writes `schema.cedarschema`, `policy_spec.md`, copied verification assets,
     and `manifest.json`.

2. `python sft_gen/synthesize.py --resume`
   - Reads each scenario.
   - Calls a model to generate `candidate.cedar`.
   - Runs `cedar validate` and retries with validation feedback.

3. `python sft_gen/pack_sft.py`
   - Packs scenarios into chat-format SFT records.

4. `python sft_gen/finetune/prepare_data.py`
   - Creates Qwen ChatML-style training and validation files under
     `sft_gen/finetune/data/`.

## Stage 3 Direction

The next stage should build negative/error-correction examples primarily from
the current `sft_gen/scenarios/` corpus. The retained Layer 1 documentation
examples can still be used as lightweight syntax seed material, but they should
not replace the validated `sft_gen` scenario corpus.

Recommended source fields:

- `policy_spec.md` as the natural-language intent.
- `schema.cedarschema` as the grounding schema.
- `candidate.cedar` as the correct policy.
- `verification_plan.py` and `references/` where semantic checks are available.

Recommended error families:

- Syntax errors: missing semicolon, malformed scope, wrong quotes, invalid
  operator, malformed `when`/`unless`.
- Schema errors: wrong entity type, wrong action name, missing namespace,
  unguarded optional attribute, type mismatch.
- Semantic errors: over-permissive wildcard, missing forbid, inverted
  `when`/`unless`, replacing hierarchy `in` with equality, missing liveness
  permit.

Each Stage 3 record should include the broken policy, the schema and intent, the
expected corrected policy, and metadata describing the injected error type.
