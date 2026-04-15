#!/usr/bin/env python3
"""SFT dataset generator.

Applies all registered SFT mutations to their base scenarios and writes
scenario directories (schema.cedarschema + policy_spec.md) into sft_gen/scenarios/.

Usage (run from cedarforge/ directory):
    python sft_gen/generate.py
    python sft_gen/generate.py --domain github
    python sft_gen/generate.py --difficulty easy
    python sft_gen/generate.py --list
    python sft_gen/generate.py --output /custom/path
"""

import argparse
import shutil
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure cedarforge/ is importable
_HERE = Path(__file__).resolve().parent
_CEDARFORGE = _HERE.parent
sys.path.insert(0, str(_CEDARFORGE))

from cedarbench.mutation import get_all_mutations, MutationMeta

# Import all SFT domain mutation modules to trigger registration
from sft_gen.mutations import (  # noqa: F401
    github, doccloud, hotel, sales, streaming, tags, tax,
)

DEFAULT_OUTPUT = _HERE / "scenarios"

# Base schemas are loaded from the pre-generated cedarforge cedarbench scenarios.
_SCENARIO_BASE = _CEDARFORGE / "cedarbench" / "scenarios"

BASE_SCHEMA_PATHS: dict[str, Path] = {
    "github":    _SCENARIO_BASE / "github_base"    / "schema.cedarschema",
    "doccloud":  _SCENARIO_BASE / "doccloud_base"  / "schema.cedarschema",
    "hotel":     _SCENARIO_BASE / "hotel_base"     / "schema.cedarschema",
    "sales":     _SCENARIO_BASE / "sales_base"     / "schema.cedarschema",
    "streaming": _SCENARIO_BASE / "streaming_base" / "schema.cedarschema",
    "tags":      _SCENARIO_BASE / "tags_base"      / "schema.cedarschema",
    "tax":       _SCENARIO_BASE / "tax_base"       / "schema.cedarschema",
}

SFT_BASE_DOMAINS = ["github", "doccloud", "hotel", "sales", "streaming", "tags", "tax"]

# SFT mutation IDs — only include mutations registered by sft_gen modules.
# Determined by prefix after filtering (all new IDs don't overlap with cedarbench).
_CEDARBENCH_IDS: set[str] = {
    # github
    "github_base", "github_add_private", "github_add_close_issue", "github_remove_triager",
    "github_add_locked_issue", "github_no_archive", "github_add_pullrequest",
    "github_add_contributor", "github_private_and_locked", "github_add_visibility",
    "github_add_security_admin", "github_pr_review_workflow", "github_full_expansion",
    "github_numeric_constraints",
    # doccloud
    "doccloud_base", "doccloud_add_admin_group", "doccloud_add_comment_acl",
    "doccloud_add_expiry", "doccloud_add_version_lock", "doccloud_graduated_sharing",
    "doccloud_org_isolation", "doccloud_remove_blocking", "doccloud_remove_public",
    "doccloud_temporal_sharing",
    # hotel
    "hotel_base", "hotel_add_franchise", "hotel_add_guest", "hotel_add_loyalty_tier",
    "hotel_add_renovation_lock", "hotel_add_cancel", "hotel_franchise_loyalty",
    "hotel_remove_hierarchy", "hotel_temporal_rates",
    # sales
    "sales_base", "sales_add_approval", "sales_add_archive", "sales_add_delete",
    "sales_add_regional_manager", "sales_add_team", "sales_full_expansion",
    "sales_remove_customer_restriction", "sales_temporal_campaign",
    # streaming
    "streaming_base", "streaming_add_age_rating", "streaming_add_download",
    "streaming_add_geo_restriction", "streaming_add_trial_tier", "streaming_full_expansion",
    "streaming_multidevice", "streaming_parental_controls", "streaming_remove_bedtime",
    "streaming_remove_oscars",
    # tags
    "tags_base", "tags_add_approval", "tags_add_fourth_dimension", "tags_add_owner_bypass",
    "tags_add_role_c", "tags_add_sensitivity", "tags_remove_all_wildcard",
    "tags_sensitivity_and_owner",
    # tax
    "tax_base", "tax_add_auditor", "tax_add_client_profile", "tax_add_edit",
    "tax_add_sensitivity", "tax_add_supervisor", "tax_full_expansion", "tax_remove_consent",
}


def load_base_schema(domain: str) -> str:
    path = BASE_SCHEMA_PATHS.get(domain)
    if not path or not path.exists():
        raise FileNotFoundError(
            f"Base schema for domain '{domain}' not found at {path}. "
            "Run cedarforge/cedarbench/generate.py first to populate base scenarios."
        )
    return path.read_text()


def load_base_policy_spec(domain: str) -> str:
    path = _SCENARIO_BASE / f"{domain}_base" / "policy_spec.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Base policy spec for domain '{domain}' not found at {path}. "
            "Run cedarforge/cedarbench/generate.py first to populate base scenarios."
        )
    return path.read_text()


def copy_base_verification_assets(domain: str, scenario_dir: Path) -> None:
    base_dir = _SCENARIO_BASE / f"{domain}_base"

    verification_plan = base_dir / "verification_plan.py"
    if verification_plan.exists():
        shutil.copy2(verification_plan, scenario_dir / "verification_plan.py")

    references_dir = base_dir / "references"
    if references_dir.exists():
        dst_references = scenario_dir / "references"
        dst_references.mkdir(parents=True, exist_ok=True)
        for ref in references_dir.glob("*.cedar"):
            shutil.copy2(ref, dst_references / ref.name)


def generate_base_scenarios(
    output_dir: Path,
    domain_filter: str | None = None,
) -> list[dict]:
    entries = []
    for domain in SFT_BASE_DOMAINS:
        if domain_filter and domain != domain_filter:
            continue

        scenario_id = f"{domain}_base"
        scenario_dir = output_dir / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / "schema.cedarschema").write_text(load_base_schema(domain))
        (scenario_dir / "policy_spec.md").write_text(load_base_policy_spec(domain))
        copy_base_verification_assets(domain, scenario_dir)

        entries.append({
            "id": scenario_id,
            "domain": domain,
            "base_scenario": None,
            "difficulty": "base",
            "mutation_description": f"Unmodified base scenario for the {domain} domain",
            "operators_applied": [],
            "features_tested": [],
            "path": f"sft_gen/scenarios/{scenario_id}/",
        })

    return entries


def generate_sft_scenarios(
    output_dir: Path,
    domain_filter: str | None = None,
    difficulty_filter: str | None = None,
) -> list[dict]:
    all_mutations = get_all_mutations()
    entries = generate_base_scenarios(output_dir, domain_filter)
    errors = []

    for mutation_id, mutation in sorted(all_mutations.items()):
        # Skip cedarbench mutations — only process SFT-new ones
        if mutation_id in _CEDARBENCH_IDS:
            continue

        meta = mutation.meta()

        if domain_filter and meta.base_scenario != domain_filter:
            continue
        if difficulty_filter and meta.difficulty != difficulty_filter:
            continue

        try:
            base_schema = load_base_schema(meta.base_scenario)
            result = mutation.apply(base_schema)
        except Exception as e:
            errors.append(f"  {mutation_id}: {e}")
            continue

        scenario_dir = output_dir / mutation_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / "schema.cedarschema").write_text(result.schema)
        (scenario_dir / "policy_spec.md").write_text(result.policy_spec)

        entries.append({
            "id": mutation_id,
            "domain": meta.base_scenario,
            "base_scenario": f"{meta.base_scenario}_base",
            "difficulty": meta.difficulty,
            "mutation_description": meta.description,
            "operators_applied": meta.operators,
            "features_tested": meta.features_tested,
            "path": f"sft_gen/scenarios/{mutation_id}/",
        })

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(e)

    return entries


def write_manifest(output_dir: Path, entries: list[dict]) -> Path:
    manifest = {
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "dataset": "sft_train",
        "total_scenarios": len(entries),
        "note": "Training data only — does NOT overlap with CedarBench test set.",
        "by_difficulty": {},
        "by_domain": {},
        "by_operators": {},
        "scenarios": entries,
    }
    for e in entries:
        d = e["difficulty"]
        manifest["by_difficulty"][d] = manifest["by_difficulty"].get(d, 0) + 1
        dom = e["domain"]
        manifest["by_domain"][dom] = manifest["by_domain"].get(dom, 0) + 1
        for op in e["operators_applied"]:
            manifest["by_operators"][op] = manifest["by_operators"].get(op, 0) + 1

    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path


def list_mutations():
    all_mutations = get_all_mutations()
    by_domain: dict[str, list] = {}
    for mid, m in all_mutations.items():
        if mid in _CEDARBENCH_IDS:
            continue
        meta = m.meta()
        by_domain.setdefault(meta.base_scenario, []).append(meta)

    total = 0
    for domain in sorted(by_domain):
        muts = sorted(by_domain[domain], key=lambda m: (
            {"easy": 0, "medium": 1, "hard": 2}.get(m.difficulty, 3), m.id
        ))
        print(f"\n{domain} ({len(muts)} new mutations):")
        for m in muts:
            ops = "+".join(m.operators)
            print(f"  [{m.difficulty:<6}] {m.id}")
            print(f"           ops: {ops}")
            print(f"           {m.description}")
        total += len(muts)

    print(f"\nTotal new SFT mutations: {total}")


def main():
    parser = argparse.ArgumentParser(description="SFT dataset mutation generator")
    parser.add_argument("--output", type=str, default=None,
                        help=f"Output directory (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--domain", type=str, default=None,
                        help="Only generate for this domain")
    parser.add_argument("--difficulty", type=str, choices=["easy", "medium", "hard"],
                        help="Only generate this difficulty tier")
    parser.add_argument("--list", action="store_true",
                        help="List all new mutations without generating")
    args = parser.parse_args()

    if args.list:
        list_mutations()
        return

    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SFT DATASET — Mutation Generator")
    print("=" * 60)
    print(f"Output: {output_dir}")
    if args.domain:
        print(f"Domain: {args.domain}")
    if args.difficulty:
        print(f"Difficulty: {args.difficulty}")

    entries = generate_sft_scenarios(output_dir, args.domain, args.difficulty)
    manifest_path = write_manifest(output_dir, entries)

    by_diff: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for e in entries:
        by_diff[e["difficulty"]] = by_diff.get(e["difficulty"], 0) + 1
        by_domain[e["domain"]] = by_domain.get(e["domain"], 0) + 1

    print(f"\nTotal scenarios generated: {len(entries)}")
    print("\nBy difficulty:")
    for d in ["easy", "medium", "hard"]:
        if d in by_diff:
            print(f"  {d:<8} {by_diff[d]}")
    print("\nBy domain:")
    for dom in sorted(by_domain):
        print(f"  {dom:<12} {by_domain[dom]}")
    print(f"\nManifest: {manifest_path}")
    print("\nNext step: run eval_harness.py on each scenario to produce candidate.cedar,")
    print("then package (policy_spec.md + schema, candidate.cedar) as SFT training pairs.")


if __name__ == "__main__":
    main()
