"""
Layer 2 Validated Synthetic data generation pipeline.

HOW TO USE
----------
1. Implement the `generate()` function below with your API call
   (Claude or OpenAI).  The function receives a system prompt and a
   user prompt and must return the raw LLM response string.

2. Run:
       python -m src.data.layer2.run_layer2 --output-dir data/layer2_raw

Optional flags:
    --slots         Comma-separated list of slot_ids to run (default: all 200)
    --resume        Skip slots that already have output files
    --dry-run       Print prompts without calling the API

Output per slot:
    data/layer2_raw/<slot_id>.jsonl   — validated records for that slot
    data/layer2_raw/_failed/<slot_id>_failed.jsonl — failed attempts

Final merged file:
    data/layer2_raw/layer2_all.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.layer2.matrix import build_matrix, ScenarioSlot
from src.data.layer2.prompt_builder import (
    build_prompt,
    parse_response,
    validate_response_schema,
)
from src.data.layer2.validator import validate_sample


# ===========================================================================
# TODO: implement this function with your API call
# ===========================================================================

def generate(system_prompt: str, user_prompt: str) -> str:
    """
    Call your LLM API and return the raw response string.

    The response should be a JSON object as specified in prompt_builder.py.
    Implement this function before running the pipeline.

    Example using OpenAI:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.8,
        )
        return resp.choices[0].message.content

    Example using Anthropic:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text
    """
    raise NotImplementedError(
        "Implement the generate() function in run_layer2.py before running the pipeline."
    )


# ===========================================================================
# Pipeline
# ===========================================================================

MAX_RETRIES = 3          # attempts per record before giving up
RETRY_DELAY = 2.0        # seconds between retries
REQUEST_DELAY = 1.0      # seconds between successful API calls (rate limiting)


def run_slot(
    slot: ScenarioSlot,
    out_dir: Path,
    failed_dir: Path,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Generate and validate `slot.target_count` records for one scenario slot.

    Returns:
        (saved_count, failed_count)
    """
    slot_out   = out_dir   / f"{slot.slot_id}.jsonl"
    slot_failed = failed_dir / f"{slot.slot_id}_failed.jsonl"

    system_prompt, user_prompt = build_prompt(slot)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] slot: {slot.slot_id}")
        print(f"--- system prompt (first 200 chars) ---")
        print(system_prompt[:200])
        print(f"--- user prompt (first 400 chars) ---")
        print(user_prompt[:400])
        return 0, 0

    saved: list[dict] = []
    failed: list[dict] = []

    attempts = 0
    while len(saved) < slot.target_count and attempts < slot.target_count * MAX_RETRIES:
        attempts += 1
        try:
            raw = generate(system_prompt, user_prompt)
        except NotImplementedError:
            raise
        except Exception as e:
            print(f"    API error on attempt {attempts}: {e}")
            time.sleep(RETRY_DELAY)
            continue

        # Parse JSON
        parsed = parse_response(raw)
        if parsed is None:
            print(f"    [attempt {attempts}] JSON parse failed")
            failed.append({"slot_id": slot.slot_id, "attempt": attempts,
                           "error": "json_parse_failed", "raw": raw[:500]})
            continue

        # Validate response schema
        schema_ok, schema_errors = validate_response_schema(parsed)
        if not schema_ok:
            print(f"    [attempt {attempts}] Response schema invalid: {schema_errors}")
            failed.append({"slot_id": slot.slot_id, "attempt": attempts,
                           "error": "response_schema_invalid", "details": schema_errors})
            continue

        # Cedar validation
        val_result = validate_sample(parsed)

        record = _make_record(slot, parsed, val_result)

        if val_result.fully_valid:
            saved.append(record)
            print(f"    [attempt {attempts}] PASS — "
                  f"test cases {val_result.test_cases_passed}/{val_result.test_cases_total}")
            time.sleep(REQUEST_DELAY)
        else:
            print(f"    [attempt {attempts}] FAIL — "
                  f"syntax={val_result.syntax_valid} "
                  f"schema={val_result.schema_valid} "
                  f"tests={val_result.test_cases_passed}/{val_result.test_cases_total} "
                  f"errors={val_result.errors[:1]}")
            failed.append({"slot_id": slot.slot_id, "attempt": attempts,
                           "validation": val_result.to_dict(), "record": record})

    # Write output
    _append_jsonl(slot_out, saved)
    if failed:
        _append_jsonl(slot_failed, failed)

    return len(saved), len(failed)


def _make_record(slot: ScenarioSlot, parsed: dict, val_result) -> dict:
    """Assemble the final record for a validated sample."""
    return {
        "source":        "layer2_synthetic",
        "slot_id":       slot.slot_id,
        "industry":      slot.industry_id,
        "auth_model":    slot.auth_model_id,
        "complexity":    slot.complexity_id,
        "schema":        parsed.get("schema", ""),
        "nl_requirement": parsed.get("nl_requirement", ""),
        "cedar_policy":  parsed.get("cedar_policy", ""),
        "test_cases":    parsed.get("test_cases", []),
        "validation":    val_result.to_dict(),
        "needs_expansion": False,
    }


def merge_outputs(out_dir: Path) -> Path:
    """Merge all per-slot JSONL files into a single layer2_all.jsonl."""
    all_records: list[dict] = []
    for f in sorted(out_dir.glob("*.jsonl")):
        if f.name == "layer2_all.jsonl":
            continue
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))
    merged = out_dir / "layer2_all.jsonl"
    _write_jsonl(merged, all_records)
    return merged


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Layer 2 synthetic data generation")
    parser.add_argument("--output-dir", default="data/layer2_raw")
    parser.add_argument("--slots",     default=None,
                        help="Comma-separated slot_ids to run (default: all)")
    parser.add_argument("--resume",    action="store_true",
                        help="Skip slots with existing output files")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Print prompts without calling the API")
    args = parser.parse_args()

    out_dir    = Path(args.output_dir)
    failed_dir = out_dir / "_failed"
    out_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    matrix = build_matrix()
    print(f"Matrix: {len(matrix)} slots, "
          f"{sum(s.target_count for s in matrix)} target records")

    # Filter slots if --slots specified
    if args.slots:
        requested = set(args.slots.split(","))
        matrix = [s for s in matrix if s.slot_id in requested]
        print(f"Filtered to {len(matrix)} slots: {args.slots}")

    # Filter already-completed slots if --resume
    if args.resume and not args.dry_run:
        before = len(matrix)
        matrix = [
            s for s in matrix
            if not (out_dir / f"{s.slot_id}.jsonl").exists()
        ]
        print(f"Resuming: skipped {before - len(matrix)} completed slots, "
              f"{len(matrix)} remaining")

    total_saved = 0
    total_failed = 0

    for i, slot in enumerate(matrix, 1):
        print(f"\n[{i}/{len(matrix)}] {slot.slot_id} "
              f"(target={slot.target_count})")
        try:
            saved, failed = run_slot(slot, out_dir, failed_dir, dry_run=args.dry_run)
            total_saved += saved
            total_failed += failed
            print(f"  -> saved={saved}, failed={failed}")
        except NotImplementedError as e:
            print(f"\nERROR: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nInterrupted. Progress saved.")
            break

    if not args.dry_run:
        merged = merge_outputs(out_dir)
        print(f"\nDone. saved={total_saved}, failed_attempts={total_failed}")
        print(f"Merged output -> {merged}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
