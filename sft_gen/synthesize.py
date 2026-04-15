#!/usr/bin/env python3
"""Batch Cedar policy synthesizer for SFT training data.

Reads every scenario produced by generate.py (policy_spec.md + schema.cedarschema),
calls an OpenAI-compatible model to synthesize a Cedar policy, validates the result
with `cedar validate`, and retries with error feedback on failure.

Saves each result as <scenario_dir>/candidate.cedar.

Usage (from cedarforge/ directory):
    # Requires OPENAI_API_KEY in environment
    python sft_gen/synthesize.py

    # Override model
    python sft_gen/synthesize.py --model o4-mini

    # Limit to one domain
    python sft_gen/synthesize.py --domain github

    # Dry-run: print prompts without calling API
    python sft_gen/synthesize.py --dry-run

    # Resume: skip scenarios that already have candidate.cedar
    python sft_gen/synthesize.py --resume

    # Parallel workers (default: 4)
    python sft_gen/synthesize.py --workers 8
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_CEDARFORGE = _HERE.parent
sys.path.insert(0, str(_CEDARFORGE))

SCENARIOS_DIR = _HERE / "scenarios"
MANIFEST_PATH = SCENARIOS_DIR / "manifest.json"

CEDAR_BINARY = os.environ.get("CEDAR", os.path.expanduser("~/.cargo/bin/cedar"))

# ---------------------------------------------------------------------------
# Models and costs (approximate, per 1M tokens)
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "o4-mini"
MAX_RETRIES = 5

# ---------------------------------------------------------------------------
# System prompt — condensed Cedar rules for policy synthesis
# ---------------------------------------------------------------------------

SYNTHESIS_SYSTEM = """\
You are an expert Cedar policy synthesizer. Your task is to write correct Cedar policies
from a natural-language specification and Cedar schema.

Cedar rules (must follow exactly):
- Output ONLY Cedar policy code — no markdown fences, no explanations.
- Cedar denies by default; write only `permit` and `forbid` rules.
- `forbid` always overrides `permit`.
- Use `unless { ... }` for exceptions to a forbid rule.
- Entity group membership: `principal in Group::"name"` (transitive).
- Attribute access: `principal.attr`, `resource.attr`, `context.field`.
- Optional attributes MUST be has-guarded: `resource has expiresAt && resource.expiresAt > ...`
- Set containment: `resource.set.contains(value)` — NOT `value in resource.set`.
- Set<EntityType>: `resource.members.contains(principal)` — NOT `principal in resource.members`.
- datetime uses ISO 8601: `datetime("2025-01-01T00:00:00Z")`.
- duration uses Go-style: `duration("1h")`, `duration("-24h")`, `duration("1h30m")`.
- Namespaced entities: `Namespace::EntityType::"id"` in policies.
- Action groups: `action in [ActionGroup::"name"]` applies to all actions in that group.
- Ternary/if-else expressions are NOT supported in Cedar.

Common patterns:
  permit (principal in Role::"admin", action, resource);
  permit (principal, action == Action::"view", resource) when { resource.isPublic };
  forbid (principal, action, resource) when { resource.isLocked };
  forbid (principal, action, resource) when { !context.mfaVerified }
    unless { principal in Role::"admin" };
"""

SYNTHESIS_USER_TEMPLATE = """\
Write a Cedar policy that satisfies the following specification.

## Cedar Schema
```cedar
{schema}
```

## Policy Specification
{spec}

Write the Cedar policies now. Output ONLY the Cedar code, no explanation, no markdown fencing.
"""

RETRY_USER_TEMPLATE = """\
Your previous Cedar policy failed validation. Fix it.

## Validation Error
{error}

## Your Previous Policy
```cedar
{candidate}
```

## Cedar Schema (for reference)
```cedar
{schema}
```

## Policy Specification (for reference)
{spec}

Output ONLY the corrected Cedar policy code. No markdown fencing, no explanation.
"""

# ---------------------------------------------------------------------------
# Cedar validation
# ---------------------------------------------------------------------------

def validate_cedar(schema_path: Path, policy_path: Path) -> tuple[bool, str]:
    """Run cedar validate. Returns (ok, error_message)."""
    try:
        result = subprocess.run(
            [CEDAR_BINARY, "validate", "--schema", str(schema_path), "--policies", str(policy_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        error = (result.stdout + result.stderr).strip()
        return False, error
    except FileNotFoundError:
        return False, f"cedar binary not found at {CEDAR_BINARY}. Set CEDAR env var."
    except subprocess.TimeoutExpired:
        return False, "cedar validate timed out"


def strip_fences(text: str) -> str:
    """Remove markdown code fences if the model adds them despite instructions."""
    text = re.sub(r'^```\w*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n?```$', '', text.strip(), flags=re.MULTILINE)
    return text.strip()

# ---------------------------------------------------------------------------
# OpenAI API call
# ---------------------------------------------------------------------------

def call_openai(
    client,
    model: str,
    messages: list[dict],
) -> str:
    """Call OpenAI chat completions API, return assistant message text."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Single scenario synthesis
# ---------------------------------------------------------------------------

def synthesize_scenario(
    scenario_id: str,
    scenario_dir: Path,
    model: str,
    client,
    dry_run: bool = False,
    resume: bool = False,
    verbose: bool = False,
) -> dict:
    """Synthesize candidate.cedar for one scenario. Returns a result dict."""
    candidate_path = scenario_dir / "candidate.cedar"

    if resume and candidate_path.exists():
        return {"id": scenario_id, "status": "skipped", "iters": 0}

    schema_path = scenario_dir / "schema.cedarschema"
    spec_path = scenario_dir / "policy_spec.md"

    schema = schema_path.read_text()
    spec = spec_path.read_text()

    # Initial prompt
    user_msg = SYNTHESIS_USER_TEMPLATE.format(schema=schema, spec=spec)
    messages = [
        {"role": "system", "content": SYNTHESIS_SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    if dry_run:
        print(f"\n[DRY RUN] {scenario_id}")
        print(f"  System: {len(SYNTHESIS_SYSTEM)} chars")
        print(f"  User:   {len(user_msg)} chars")
        return {"id": scenario_id, "status": "dry_run", "iters": 0}

    start = time.time()
    last_candidate = ""
    last_error = ""

    for iteration in range(1, MAX_RETRIES + 1):
        try:
            candidate = strip_fences(call_openai(client, model, messages))
        except Exception as e:
            return {
                "id": scenario_id,
                "status": "api_error",
                "error": str(e),
                "iters": iteration,
                "elapsed": time.time() - start,
            }

        last_candidate = candidate

        # Write to disk for validation
        candidate_path.write_text(candidate)

        ok, error = validate_cedar(schema_path, candidate_path)

        if ok:
            elapsed = time.time() - start
            if verbose:
                print(f"  [{scenario_id}] PASS iter={iteration} ({elapsed:.1f}s)")
            return {
                "id": scenario_id,
                "status": "pass",
                "iters": iteration,
                "elapsed": elapsed,
            }

        last_error = error
        if verbose:
            print(f"  [{scenario_id}] iter={iteration} FAIL: {error[:80]}")

        # Build retry message
        retry_msg = RETRY_USER_TEMPLATE.format(
            error=error,
            candidate=candidate,
            schema=schema,
            spec=spec,
        )
        messages.append({"role": "assistant", "content": candidate})
        messages.append({"role": "user", "content": retry_msg})

    # All retries exhausted — leave the last attempt on disk
    return {
        "id": scenario_id,
        "status": "fail",
        "iters": MAX_RETRIES,
        "last_error": last_error[:200],
        "elapsed": time.time() - start,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Batch Cedar policy synthesizer")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"OpenAI model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--domain", default=None,
                        help="Only process this domain")
    parser.add_argument("--scenario", default=None,
                        help="Only process this specific scenario ID")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers (default: 4)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts without calling API")
    parser.add_argument("--resume", action="store_true",
                        help="Skip scenarios that already have candidate.cedar")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output", default=None,
                        help="Path to write synthesis_results.json (default: scenarios dir)")
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
    if args.scenario:
        entries = [e for e in entries if e["id"] == args.scenario]

    print("=" * 60)
    print("SFT Cedar Policy Synthesizer")
    print("=" * 60)
    print(f"Model:    {args.model}")
    print(f"Workers:  {args.workers}")
    print(f"Scenarios: {len(entries)}")
    if args.resume:
        print(f"Mode:     resume (skip existing)")
    if args.dry_run:
        print(f"Mode:     DRY RUN")
    print()

    # Initialize OpenAI client
    client = None
    if not args.dry_run:
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("ERROR: OPENAI_API_KEY not set")
                sys.exit(1)
            client = OpenAI(api_key=api_key)
        except ImportError:
            print("ERROR: openai package not installed. Run: pip install openai")
            sys.exit(1)

    # Run synthesis
    results = []

    def _run(entry):
        sid = entry["id"]
        sdir = SCENARIOS_DIR / sid
        return synthesize_scenario(
            sid, sdir, args.model, client,
            dry_run=args.dry_run,
            resume=args.resume,
            verbose=args.verbose,
        )

    if args.workers == 1 or args.dry_run:
        for entry in entries:
            r = _run(entry)
            results.append(r)
            status = r["status"]
            iters = r.get("iters", 0)
            elapsed = r.get("elapsed", 0)
            print(f"  [{status:<8}] {r['id']:<45} iters={iters} ({elapsed:.1f}s)")
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(_run, e): e["id"] for e in entries}
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                status = r["status"]
                iters = r.get("iters", 0)
                elapsed = r.get("elapsed", 0)
                print(f"  [{status:<8}] {r['id']:<45} iters={iters} ({elapsed:.1f}s)")

    # Summary
    by_status: dict[str, int] = {}
    for r in results:
        s = r["status"]
        by_status[s] = by_status.get(s, 0) + 1

    print()
    print("=" * 60)
    print("Results:")
    for s, count in sorted(by_status.items()):
        print(f"  {s:<12} {count}")
    total_pass = by_status.get("pass", 0) + by_status.get("skipped", 0)
    print(f"\n  PASS RATE: {total_pass}/{len(results)}")

    # Write results JSON
    output_path = Path(args.output) if args.output else SCENARIOS_DIR / "synthesis_results.json"
    output_path.write_text(json.dumps({
        "model": args.model,
        "total": len(results),
        "by_status": by_status,
        "results": results,
    }, indent=2))
    print(f"\nResults written to: {output_path}")
    print("\nNext step: python sft_gen/pack_sft.py")


if __name__ == "__main__":
    main()
