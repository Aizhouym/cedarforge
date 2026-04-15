"""Prompt templates for LLM-based SFT scenario generation.

Two use cases:
  1. EXPAND_MUTATION_PROMPT  — given a mutation's schema + brief spec, ask GPT-5.4
     to write a detailed, unambiguous policy_spec.md.
  2. NEW_MUTATION_PROMPT     — ask GPT-5.4 to generate entirely new mutations
     (schema + spec) for a given domain, following the operator taxonomy.
  3. NEW_BASE_PROMPT         — ask GPT-5.4 to generate a brand-new domain base
     scenario (schema + NL spec) for use as a new mutation starting point.

Usage example:
    from sft_gen.llm_prompt import build_expand_prompt, build_new_mutation_prompt

    prompt = build_expand_prompt(
        domain="github",
        mutation_id="github_sso_gate",
        schema=open("sft_gen/scenarios/github_sso_gate/schema.cedarschema").read(),
        brief_spec=open("sft_gen/scenarios/github_sso_gate/policy_spec.md").read(),
    )
    # Send `prompt` to GPT-5.4 / Codex, receive detailed policy_spec.md.
"""

from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 1. EXPAND MUTATION — enrich a brief spec into a detailed policy_spec.md
# ─────────────────────────────────────────────────────────────────────────────

EXPAND_SYSTEM_PROMPT = """\
You are a security engineer and Cedar policy expert. You write precise, unambiguous
access-control policy specifications for Cedar (the AWS policy language).

Cedar rules:
- Entity hierarchy: `User in [Group]`. Transitive `in` is used for membership checks.
- Forbid overrides permit. `forbid ... unless { condition }` creates a forbid with exception.
- Cedar extension types: datetime("ISO8601"), duration("Go-style: 1h, -24h, 1h30m").
- Optional attributes MUST be has-guarded before reading.
- Set containment: `resource.setAttr.contains(value)` — NOT `value in resource.setAttr`.
- `Set<User>` uses `.contains(principal)`, NOT `principal in resource.setAttr`.

Your output must be a complete policy_spec.md with:
1. YAML frontmatter (pattern, difficulty, features list, domain, source)
2. A Context section describing all entity types, attributes, and actions
3. Numbered Requirements sections — one per policy rule or forbid/permit
4. A Notes section with Cedar-specific implementation hints
"""

EXPAND_USER_TEMPLATE = """\
Given the following Cedar schema and brief policy specification, write a complete,
detailed, and unambiguous policy_spec.md suitable for training a language model
to generate Cedar policies.

The specification must:
- Cover every attribute in the schema and explain its role
- State precisely which principal can perform which action under what condition
- Call out all forbid rules with their exact trigger conditions
- Note any `has` guards needed for optional attributes
- Note `unless` clauses for forbid exceptions
- Note cross-entity traversal paths (e.g., `resource.repo.writers`)
- Be unambiguous enough that a model can write the Cedar policy from spec alone

Cedar schema:
```cedar
{schema}
```

Brief mutation spec:
```markdown
{brief_spec}
```

Mutation metadata:
- ID: {mutation_id}
- Domain: {domain}
- Operators applied: {operators}
- Features tested: {features}

Write the full policy_spec.md now. Do not add any commentary outside the markdown.
"""


def build_expand_prompt(
    domain: str,
    mutation_id: str,
    schema: str,
    brief_spec: str,
    operators: list[str] | None = None,
    features: list[str] | None = None,
) -> dict[str, str]:
    """Build a system+user prompt pair for expanding a brief spec into full policy_spec.md."""
    user = EXPAND_USER_TEMPLATE.format(
        schema=schema,
        brief_spec=brief_spec,
        mutation_id=mutation_id,
        domain=domain,
        operators=", ".join(operators or []),
        features=", ".join(features or []),
    )
    return {"system": EXPAND_SYSTEM_PROMPT, "user": user}


# ─────────────────────────────────────────────────────────────────────────────
# 2. NEW MUTATION — generate new (schema + spec) from operator description
# ─────────────────────────────────────────────────────────────────────────────

NEW_MUTATION_SYSTEM_PROMPT = """\
You are a Cedar policy expert designing mutation-based benchmark scenarios for
evaluating LLM-based Cedar policy synthesis.

Mutation taxonomy:
  Schema operators:
    S1=add Bool attr  S2=add Long attr  S3=add String attr  S4=add datetime attr
    S5=add Set<EntityType> attr  S6=add new entity  S7=add new action
    S8=add context field  S9=add UserGroup attr (new role)
    S10=remove attr  S11=remove entity  S12=remove action  S13=add typedef
    S14=modify entity parents (hierarchy change)
  Policy operators:
    P1=new forbid rule (boolean guard)  P2=new permit rule  P3=remove permit
    P4=unless exception on forbid  P5=dual-path permit  P6=numeric forbid
    P7=string-enum condition  P8=role redistribution  P9=cross-entity traversal
    P10=self-exclusion forbid (principal == resource.author)

Cedar rules:
- Optional attributes: declared with `?`, MUST be has-guarded before reading.
- datetime uses ISO 8601: datetime("2025-01-01T00:00:00Z").
- duration uses Go-style: duration("1h"), duration("-24h"), duration("1h30m").
- Set containment: set.contains(value) — NOT value in set.
- Forbid overrides permit. unless{} creates exceptions.
"""

NEW_MUTATION_USER_TEMPLATE = """\
Design a new Cedar policy mutation for the **{domain}** domain.

Base scenario schema:
```cedar
{base_schema}
```

Operator combination to use: {operators}

Requirements for the new mutation:
1. The mutation ID must be `{mutation_id}` (not already in CedarBench).
2. Apply exactly the operators listed above to the base schema.
3. The resulting scenario must be clearly different from these existing mutations:
{existing_mutations}
4. The scenario must be Cedar-valid (syntactically correct schema, valid attribute types).
5. Difficulty level: {difficulty}

Output two code blocks:
- A ```cedar block with the MODIFIED schema (apply schema operators to base)
- A ```markdown block with the complete policy_spec.md (YAML frontmatter + full spec)

The policy_spec.md must precisely describe what changed, all new rules, and
Cedar implementation hints (has guards, unless clauses, set containment vs in-operator).
"""


def build_new_mutation_prompt(
    domain: str,
    mutation_id: str,
    base_schema: str,
    operators: list[str],
    difficulty: str,
    existing_mutations: list[str],
) -> dict[str, str]:
    """Build a prompt for GPT-5.4 to generate a brand-new mutation."""
    existing_str = "\n".join(f"  - {m}" for m in existing_mutations)
    user = NEW_MUTATION_USER_TEMPLATE.format(
        domain=domain,
        mutation_id=mutation_id,
        base_schema=base_schema,
        operators=" + ".join(operators),
        difficulty=difficulty,
        existing_mutations=existing_str,
    )
    return {"system": NEW_MUTATION_SYSTEM_PROMPT, "user": user}


# ─────────────────────────────────────────────────────────────────────────────
# 3. NEW BASE — generate a brand-new domain base scenario
# ─────────────────────────────────────────────────────────────────────────────

NEW_BASE_SYSTEM_PROMPT = """\
You are a Cedar policy expert creating base scenarios for a benchmark dataset.
Each base scenario defines a real-world access-control system in Cedar schema format.

Cedar schema rules:
- Entity declaration: `entity Name [in [Parent]] [= { attr: Type, ... }];`
- Attribute types: Bool, Long, String, datetime, Set<EntityType>, Set<String>
- Optional attributes: `attr?: Type` (MUST be has-guarded in policy)
- Action declaration: `action name appliesTo { principal: [Type], resource: [Type], context?: {...} };`
- Named types: `type Name = { ... };` declared before entities
- Namespaces: `namespace Ns { ... }` wraps all declarations

Requirements for a valid base scenario:
1. 2-4 entity types (principal + 1-3 resource types)
2. 4-10 actions covering the core operations (view/edit/delete/manage pattern)
3. At least 2 different principal types OR 2 distinct resource types
4. At least one role-based or attribute-based access pattern
5. Cedar-valid: all referenced types must be declared
6. At least one optional attribute (declared with ?) for has-guard practice
"""

NEW_BASE_USER_TEMPLATE = """\
Design a new Cedar base scenario for the following domain:

Domain: **{domain_name}**
Description: {domain_description}
Access pattern: {access_pattern}

Requirements:
- The scenario must be DIFFERENT from these existing CedarBench domains:
  github (repo permissions), doccloud (document sharing), hotel (hotel chains),
  sales (sales CRM), streaming (video streaming), tags (workspace tags), tax (tax preparer)
- Include at least one interesting access-control challenge:
  {challenge}
- Difficulty: base (easy — clear rules, no compound mutations)

Output TWO code blocks:
1. ```cedar — complete Cedar schema (entities + actions, Cedar-valid)
2. ```markdown — complete policy_spec.md with:
   - YAML frontmatter: pattern, difficulty, features list, domain, source: "new base"
   - Context section: describe all entities and their attributes
   - Requirements: numbered rules for each action/role
   - Notes: Cedar implementation hints

The schema must be self-contained and Cedar-valid.
The policy_spec.md must be unambiguous enough to synthesize the Cedar policy from it.
"""

NEW_BASE_DOMAIN_IDEAS = [
    {
        "domain_name": "insurance_claims",
        "domain_description": "Insurance company claims processing system",
        "access_pattern": "Adjusters handle assigned claims; managers review any claim in their region; fraud investigators have read-only cross-region access",
        "challenge": "Claim status state machine (open/under_review/approved/denied) affects allowed operations",
    },
    {
        "domain_name": "supply_chain",
        "domain_description": "B2B supply chain platform with purchase orders and shipments",
        "access_pattern": "Suppliers see only their own POs; buyers see POs for their company; logistics staff track shipments",
        "challenge": "Multi-party ownership (supplier + buyer) and state-gated mutations (PO status)",
    },
    {
        "domain_name": "devops_infra",
        "domain_description": "Infrastructure as code platform with environment-scoped deployments",
        "access_pattern": "Developers deploy to dev/staging freely; production requires release manager approval",
        "challenge": "Environment hierarchy (dev < staging < prod) with role-gated production access",
    },
    {
        "domain_name": "legal_case_mgmt",
        "domain_description": "Law firm case management system",
        "access_pattern": "Attorneys access their own cases; partners access all cases in their practice group; clients view their own case status only",
        "challenge": "Privilege and confidentiality: client documents have attorney-client privilege blocking",
    },
    {
        "domain_name": "healthcare_billing",
        "domain_description": "Medical billing and coding platform",
        "access_pattern": "Coders process claims for their assigned providers; billers submit to insurers; patients view own EOBs",
        "challenge": "HIPAA-like separation: coders see PHI but billers submit without diagnosis codes",
    },
    {
        "domain_name": "edu_lms",
        "domain_description": "Educational learning management system",
        "access_pattern": "Students access enrolled courses; TAs grade assignments in their section; professors manage their own courses",
        "challenge": "Enrollment-based access (student must be enrolled to view course content)",
    },
    {
        "domain_name": "marketplace_seller",
        "domain_description": "E-commerce marketplace with sellers and buyers",
        "access_pattern": "Sellers manage their own product listings; buyers can view all and purchase; platform admins moderate any listing",
        "challenge": "Seller-only edit with buyer-read and transaction-state locking (sold items cannot be edited)",
    },
    {
        "domain_name": "iot_fleet_mgmt",
        "domain_description": "IoT device fleet management platform",
        "access_pattern": "Operators manage devices in their assigned fleet; readers monitor status; firmware engineers push updates to approved device models",
        "challenge": "Device model-scoped firmware updates with approval state gating",
    },
    {
        "domain_name": "content_publishing",
        "domain_description": "Digital content publishing and editorial workflow",
        "access_pattern": "Authors draft content; editors review and approve; publishers control publication; readers access published content only",
        "challenge": "Editorial state machine (draft/review/approved/published) with role-gated transitions",
    },
    {
        "domain_name": "financial_trading",
        "domain_description": "Investment bank trading desk access control",
        "access_pattern": "Traders manage their own positions; risk managers see all; compliance has read-only audit access; trading is blocked during market close",
        "challenge": "Time-gated trading (market hours) with compliance audit read-only",
    },
]


def build_new_base_prompt(domain_idea: dict) -> dict[str, str]:
    """Build a prompt for GPT-5.4 to generate a new base domain scenario."""
    user = NEW_BASE_USER_TEMPLATE.format(**domain_idea)
    return {"system": NEW_BASE_SYSTEM_PROMPT, "user": user}


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner helper
# ─────────────────────────────────────────────────────────────────────────────

def get_all_expand_prompts(scenarios_dir: Path) -> list[dict]:
    """Return a list of expand-prompt dicts for every generated scenario."""
    import json as _json
    manifest_path = scenarios_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Run generate.py first to create {manifest_path}")

    manifest = _json.loads(manifest_path.read_text())
    prompts = []
    for entry in manifest["scenarios"]:
        scenario_id = entry["id"]
        scenario_dir = scenarios_dir / scenario_id
        schema = (scenario_dir / "schema.cedarschema").read_text()
        brief_spec = (scenario_dir / "policy_spec.md").read_text()
        prompt = build_expand_prompt(
            domain=entry["domain"],
            mutation_id=scenario_id,
            schema=schema,
            brief_spec=brief_spec,
            operators=entry["operators_applied"],
            features=entry["features_tested"],
        )
        prompts.append({"id": scenario_id, **prompt})
    return prompts


def get_all_new_base_prompts() -> list[dict]:
    """Return prompts for all 10 new base domain ideas."""
    return [
        {"id": idea["domain_name"], **build_new_base_prompt(idea)}
        for idea in NEW_BASE_DOMAIN_IDEAS
    ]


if __name__ == "__main__":
    # Quick sanity check
    print("SFT Prompt templates loaded.")
    print(f"  New base domain ideas: {len(NEW_BASE_DOMAIN_IDEAS)}")
    print("  Use build_expand_prompt() for per-scenario spec expansion.")
    print("  Use build_new_mutation_prompt() for generating additional mutations.")
    print("  Use build_new_base_prompt(idea) for new domain base generation.")
