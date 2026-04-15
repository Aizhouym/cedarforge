#!/usr/bin/env python3
"""Pack synthesized scenarios into SFT training JSONL.

Reads every scenario that has both:
  - policy_spec.md + schema.cedarschema  (input)
  - candidate.cedar                       (ground-truth output, from synthesize.py)

Writes one record per scenario to sft_training.jsonl in OpenAI fine-tuning format.

Input format per training example:
  {"messages": [
    {"role": "system",  "content": SYNTH_SYSTEM},
    {"role": "user",    "content": "<schema>\n<spec>"},
    {"role": "assistant","content": "<cedar policy>"}
  ]}

Usage (from cedarforge/ directory):
    python sft_gen/pack_sft.py
    python sft_gen/pack_sft.py --output my_dataset.jsonl
    python sft_gen/pack_sft.py --domain github     # filter by domain
    python sft_gen/pack_sft.py --stats             # just print stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
SCENARIOS_DIR = _HERE / "scenarios"
MANIFEST_PATH = SCENARIOS_DIR / "manifest.json"
DEFAULT_OUTPUT = _HERE / "sft_training.jsonl"

# ---------------------------------------------------------------------------
# SFT system prompt — what the fine-tuned model will be trained to follow
# ---------------------------------------------------------------------------

SFT_SYSTEM = """\
You are an expert Cedar access-control policy synthesizer. Given a Cedar schema
and a natural-language policy specification, write the Cedar policies that
exactly implement the specification.

Rules:
- Output ONLY Cedar policy code — no markdown fences, no explanations.
- Cedar denies by default; write only permit and forbid rules.
- forbid always overrides permit.
- Use unless { ... } for exceptions to forbid rules.
- Optional attributes: always has-guard before reading.
- Set containment: set.contains(value), NOT value in set.
- datetime uses ISO 8601; duration uses Go-style (1h, -24h, 1h30m).
"""

# ---------------------------------------------------------------------------
# Prompt builder — mirrors synthesize.py's initial user message
# ---------------------------------------------------------------------------

def build_user_message(schema: str, spec: str) -> str:
    return (
        "## Cedar Schema\n"
        "```cedar\n"
        f"{schema.strip()}\n"
        "```\n\n"
        "## Policy Specification\n"
        f"{spec.strip()}\n\n"
        "Write the Cedar policies now. Output ONLY Cedar code, no explanation."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pack SFT scenarios into JSONL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help=f"Output JSONL file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--domain", default=None,
                        help="Only include this domain")
    parser.add_argument("--difficulty", default=None,
                        choices=["easy", "medium", "hard"],
                        help="Only include this difficulty")
    parser.add_argument("--stats", action="store_true",
                        help="Print stats only, do not write JSONL")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}")
        print("Run: python sft_gen/generate.py first")
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    entries = manifest["scenarios"]

    # Filters
    if args.domain:
        entries = [e for e in entries if e["domain"] == args.domain]
    if args.difficulty:
        entries = [e for e in entries if e["difficulty"] == args.difficulty]

    # Collect records
    records = []
    missing_candidate = []
    by_domain: dict[str, int] = {}
    by_difficulty: dict[str, int] = {}

    for entry in entries:
        sid = entry["id"]
        sdir = SCENARIOS_DIR / sid
        spec_path = sdir / "policy_spec.md"
        schema_path = sdir / "schema.cedarschema"
        candidate_path = sdir / "candidate.cedar"

        if not candidate_path.exists():
            missing_candidate.append(sid)
            continue

        schema = schema_path.read_text().strip()
        spec = spec_path.read_text().strip()
        candidate = candidate_path.read_text().strip()

        record = {
            "messages": [
                {"role": "system",    "content": SFT_SYSTEM},
                {"role": "user",      "content": build_user_message(schema, spec)},
                {"role": "assistant", "content": candidate},
            ],
            # Metadata (strip before uploading to OpenAI — kept here for filtering)
            "_meta": {
                "id": sid,
                "domain": entry["domain"],
                "difficulty": entry["difficulty"],
                "operators": entry["operators_applied"],
            },
        }
        records.append(record)

        d = entry["domain"]
        diff = entry["difficulty"]
        by_domain[d] = by_domain.get(d, 0) + 1
        by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

    # Stats
    print("=" * 60)
    print("SFT Dataset — Pack")
    print("=" * 60)
    print(f"Total records: {len(records)}")
    print(f"Missing candidate.cedar: {len(missing_candidate)}")
    if missing_candidate:
        print("  Run: python sft_gen/synthesize.py --resume")
        for sid in missing_candidate[:5]:
            print(f"    {sid}")
        if len(missing_candidate) > 5:
            print(f"    ... and {len(missing_candidate) - 5} more")
    print()
    print("By domain:")
    for d, count in sorted(by_domain.items()):
        print(f"  {d:<12} {count}")
    print()
    print("By difficulty:")
    for diff in ["easy", "medium", "hard"]:
        if diff in by_difficulty:
            print(f"  {diff:<8} {by_difficulty[diff]}")

    if args.stats or not records:
        return

    # Write JSONL — strip _meta for clean upload
    output_path = Path(args.output)
    clean_records = [
        {k: v for k, v in r.items() if k != "_meta"}
        for r in records
    ]

    output_path.write_text("\n".join(json.dumps(r) for r in clean_records) + "\n")
    print(f"\nWrote {len(clean_records)} records to: {output_path}")

    # Also write a version with metadata for inspection
    meta_path = output_path.with_suffix(".meta.jsonl")
    meta_path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    print(f"Wrote metadata version to: {meta_path}")

    # Token count estimate (rough: 4 chars per token)
    total_chars = sum(
        len(json.dumps(r["messages"])) for r in clean_records
    )
    estimated_tokens = total_chars // 4
    print(f"\nEstimated tokens: ~{estimated_tokens:,}")
    print(f"  (at ~$0.008/1K tokens fine-tune cost: ~${estimated_tokens / 1000 * 0.008:.2f})")


if __name__ == "__main__":
    main()
