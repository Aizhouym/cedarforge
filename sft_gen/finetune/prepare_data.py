#!/usr/bin/env python3
"""Prepare fine-tuning data for Qwen3.5B MoE.

Reads all 77 sft_gen scenarios and produces:
  finetune/data/train.jsonl   — 70 examples (10 per domain)
  finetune/data/val.jsonl     — 7 examples  (1 per domain, held out)

Format: ChatML — compatible with Qwen3 chat template and TRL SFTTrainer.

Usage (from cedarforge/ directory):
    python sft_gen/finetune/prepare_data.py
    python sft_gen/finetune/prepare_data.py --stats
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SFT_GEN = _HERE.parent
SCENARIOS_DIR = _SFT_GEN / "scenarios"
MANIFEST_PATH = SCENARIOS_DIR / "manifest.json"
DATA_DIR = _HERE / "data"

# Held-out scenario per domain (1 representative from each domain).
# Pick a medium-difficulty scenario so the val set tests generalisation.
VAL_IDS: set[str] = {
    "github_deploy_env",        # github   — medium
    "doccloud_classification",  # doccloud — medium
    "hotel_vip_blocked",        # hotel    — medium
    "sales_fiscal_window",      # sales    — medium
    "streaming_release_window", # streaming — medium
    "tags_expiry",              # tags     — medium
    "tax_document_type",        # tax      — medium
}

SFT_SYSTEM = """\
You are an expert Cedar access-control policy synthesizer. Given a Cedar schema \
and a natural-language policy specification, write the Cedar policies that \
exactly implement the specification.

Rules:
- Cedar denies by default; write only permit and forbid rules.
- forbid always overrides permit.
- Use unless { ... } for exceptions to forbid rules.
- Optional attributes: always has-guard before reading.
- Set containment: set.contains(value), NOT value in set.
- datetime uses ISO 8601; duration uses Go-style (1h, -24h, 1h30m).

Output Format:
Only output the final Cedar policy inside <cedar_policy> tags.

<cedar_policy>
Cedar policy here
</cedar_policy>\
"""


def build_user_message(schema: str, spec: str) -> str:
    return (
        "## Cedar Schema\n"
        "```cedar\n"
        f"{schema.strip()}\n"
        "```\n\n"
        "## Policy Specification\n"
        f"{spec.strip()}\n\n"
        "Write the Cedar policies now."
    )


def load_record(entry: dict) -> dict | None:
    sid = entry["id"]
    sdir = SCENARIOS_DIR / sid
    spec_path = sdir / "policy_spec.md"
    schema_path = sdir / "schema.cedarschema"
    candidate_path = sdir / "candidate.cedar"

    for p in (spec_path, schema_path, candidate_path):
        if not p.exists():
            print(f"  SKIP {sid}: missing {p.name}", file=sys.stderr)
            return None

    cedar = candidate_path.read_text().strip()
    user_msg = build_user_message(schema_path.read_text(), spec_path.read_text())
    # Build training text manually — no <think> tokens anywhere.
    # apply_chat_template always injects <think>\n regardless of enable_thinking,
    # so we bypass it entirely and use raw ChatML tokens directly.
    text = (
        f"<|im_start|>system\n{SFT_SYSTEM}<|im_end|>\n"
        f"<|im_start|>user\n{user_msg}<|im_end|>\n"
        f"<|im_start|>assistant\n<cedar_policy>\n{cedar}\n</cedar_policy><|im_end|>\n"
    )
    return {
        "text": text,
        "_meta": {
            "id": sid,
            "domain": entry["domain"],
            "difficulty": entry["difficulty"],
        },
    }


def print_stats(split: str, records: list[dict]) -> None:
    by_domain: dict[str, int] = {}
    by_diff: dict[str, int] = {}
    lens = []
    for r in records:
        m = r["_meta"]
        by_domain[m["domain"]] = by_domain.get(m["domain"], 0) + 1
        by_diff[m["difficulty"]] = by_diff.get(m["difficulty"], 0) + 1
        lens.append(len(r["text"]) // 4)  # rough token estimate

    print(f"\n{split}: {len(records)} examples")
    print(f"  Domains: {dict(sorted(by_domain.items()))}")
    print(f"  Difficulty: {dict(sorted(by_diff.items()))}")
    if lens:
        lens.sort()
        print(f"  Tokens — min={min(lens)}  mean={sum(lens)//len(lens)}  max={max(lens)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    if not MANIFEST_PATH.exists():
        print("ERROR: manifest.json not found. Run: python sft_gen/generate.py", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    entries = manifest["scenarios"]

    train_records: list[dict] = []
    val_records: list[dict] = []

    for entry in entries:
        rec = load_record(entry)
        if rec is None:
            continue
        if entry["id"] in VAL_IDS:
            val_records.append(rec)
        else:
            train_records.append(rec)

    print_stats("TRAIN", train_records)
    print_stats("VAL",   val_records)

    if args.stats:
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    def write_jsonl(path: Path, records: list[dict], strip_meta: bool = True) -> None:
        clean = [
            {k: v for k, v in r.items() if k != "_meta"} if strip_meta else r
            for r in records
        ]
        path.write_text("\n".join(json.dumps(r) for r in clean) + "\n")
        print(f"Wrote {len(clean)} records → {path}")

    write_jsonl(DATA_DIR / "train.jsonl", train_records)
    write_jsonl(DATA_DIR / "val.jsonl",   val_records)

    # Also write debug version with metadata
    write_jsonl(DATA_DIR / "train.meta.jsonl", train_records, strip_meta=False)
    write_jsonl(DATA_DIR / "val.meta.jsonl",   val_records,   strip_meta=False)

    total_tokens = sum(len(r["text"]) // 4 for r in train_records)
    print(f"\nTotal training tokens: ~{total_tokens:,}")


if __name__ == "__main__":
    main()
