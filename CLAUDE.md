# Claude Code Guidelines for Cedarforge

## Collaboration Rules

### Confirm Before Heavy Coding
Before writing significant code (new modules, scrapers, pipelines, data processing scripts),
outline the plan and discuss it with the user first. Only proceed after explicit confirmation.

### No Chinese in Code
All code comments, variable names, string literals, prompts, and log messages must be in English.
Chinese is only acceptable in this file and in user-facing documentation outside of code.

## Data Pipeline Context

### Layer 1 Data Sources
- Cedar official docs (docs.cedarpolicy.com) — scraped (NL + Cedar code)
- AWS Verified Permissions docs — scraped (NL + Cedar code)
- Both policy code (permit/forbid) AND schema code (entity/action definitions) are kept
- Raw output goes to `data/layer1_raw/` inside the repo
- Each record is marked `needs_expansion: true` for later Claude/OpenAI API enrichment

### What NOT to Use as Training Data
- `/Users/chou/Cedarforge/dataset/` — this is the target benchmark (test set), not training data
- `cedar-integration-tests` and `cedar-examples` — used in CedarBench, cannot be used for training

### Output Format
JSONL, one record per line:
```json
{
  "source": "cedar_docs | aws_avp_docs",
  "page_url": "https://...",
  "page_title": "...",
  "section_heading": "...",
  "nl_description": "...",
  "cedar_code": "...",
  "code_type": "policy | schema",
  "needs_expansion": true
}
```
