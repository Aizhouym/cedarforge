# Cedar SFT Policy Synthesis — Agent Program

You are an autonomous agent. You will receive one input: a **scenario directory path**.
Execute the steps below in order. Do not skip steps. Do not ask for clarification.

---

## Step 0 — Discover environment

Given the scenario directory path (call it `SCENARIO_DIR`):

1. Derive `REPO_ROOT`: go up from `SCENARIO_DIR` until you find a directory that contains
   both `orchestrator.py` and `eval_harness.py`. That is the repo root.

2. Find the `cedar` binary:
   ```
   which cedar  →  use if found
   ~/.cargo/bin/cedar  →  try as fallback
   ```
   Store as `CEDAR`.

3. Find the `cvc5` binary:
   ```
   which cvc5  →  use if found
   ~/.local/bin/cvc5  →  try as fallback
   ```
   Store as `CVC5`.

4. Confirm both binaries exist and are executable. If either is missing, stop and report.

---

## Step 1 — Read the scenario inputs

Read these two files completely:
- `SCENARIO_DIR/policy_spec.md`
- `SCENARIO_DIR/schema.cedarschema`

From the schema, identify:
- All **entity types** and their attributes (note which attributes are optional, marked `?`)
- All **actions** and what principal/resource types they apply to
- Whether a **namespace** wraps the declarations (e.g. `namespace Taxpreparer { ... }`)
- For each attribute type: is it `UserGroup` / `Set<EntityType>` / `Set<String>` / scalar?

From the spec, identify:
- Every **permission rule** (who can do what under what condition)
- Every **forbid rule** (what is always blocked, and any exceptions via `unless`)
- Any **global forbids** that cut across multiple actions

---

## Step 2 — Skip Phase 1 if artifacts already exist

If `SCENARIO_DIR/verification_plan.py` already exists AND `SCENARIO_DIR/references/`
already exists and is non-empty, jump directly to Step 5.

---

## Step 3 — Write `verification_plan.py`

Write the file `SCENARIO_DIR/verification_plan.py`.

### 3a. Design the checks

For every action in the schema, plan:

**Ceiling check** (`type: "implies"`): encodes the MAXIMUM the candidate may permit.
- One ceiling per action, per orthogonal safety rule.
- Ask: "What is the exact condition that must hold for this action to be permitted?"
- The reference policy grants access ONLY when that condition holds.
- If a global forbid applies (e.g., archived repos block writes), encode it in the ceiling.

**Floor check** (`type: "floor"`): encodes the MINIMUM the candidate must permit.
- One floor per "this must always work" guarantee from the spec.
- Ask: "What is the simplest case that MUST be allowed?"
- CRITICAL: if a global forbid exists, include its negation in the floor's `when` clause.
  Otherwise the floor is jointly unsatisfiable with the forbid and Phase 2 will never converge.
  Example: spec says "admins can add_reader unless isArchived AND ssoVerified required"
  → floor must say: `when { principal in resource.admins && !resource.isArchived && context.ssoVerified }`

**Liveness check** (`type: "always-denies-liveness"`): ensures the policy is not trivially deny-all.
- One per action.
- No reference file needed.

### 3b. Write the file

```python
"""Verification plan for <scenario_name>."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "ceiling_<action>_<property>",
            "description": "<what this ceiling enforces>",
            "type": "implies",
            "principal_type": "<EntityType>",
            "action": "Action::\"<action_name>\"",
            "resource_type": "<EntityType>",
            "reference_path": os.path.join(REFS, "ceiling_<action>_<property>.cedar"),
        },
        {
            "name": "floor_<role>_<action>",
            "description": "<what must always be allowed>",
            "type": "floor",
            "principal_type": "<EntityType>",
            "action": "Action::\"<action_name>\"",
            "resource_type": "<EntityType>",
            "floor_path": os.path.join(REFS, "floor_<role>_<action>.cedar"),
        },
        {
            "name": "liveness_<action>",
            "description": "<action> is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "<EntityType>",
            "action": "Action::\"<action_name>\"",
            "resource_type": "<EntityType>",
        },
    ]
```

Fill in one dict per check based on the design from 3a.
If the schema uses a namespace, use the fully qualified type: `Taxpreparer::Document`.

---

## Step 4 — Write reference Cedar files

Create directory `SCENARIO_DIR/references/`.
Write one `.cedar` file for each `implies` check and each `floor` check.

### Reference file format

```cedar
permit (
    principal is <PrincipalType>,
    action == Action::"<name>",
    resource is <ResourceType>
)
when { <condition> };
```

### How to write conditions — decision rules

**Deciding the condition for a CEILING** (`ceiling_*.cedar`):
The condition is the MAXIMUM allowed: "access is permitted ONLY IF this holds."
It describes the precise guard from the spec, including global forbids.

```cedar
// Example: ceiling for "push requires writer AND not archived"
when { principal in resource.writers && !resource.isArchived };

// Example: ceiling for "add_reader requires admin AND not archived AND SSO verified"
when { principal in resource.admins && !resource.isArchived && context.ssoVerified };

// Example: ceiling for "viewDocument requires org-match"
when { principal.assigned_orgs.contains({
    organization: resource.owner.organization,
    serviceline: resource.serviceline,
    location: resource.location,
}) };
```

**Deciding the condition for a FLOOR** (`floor_*.cedar`):
The condition is the MINIMUM required: "this specific case MUST be allowed."
Start from the spec guarantee, then subtract every global forbid condition.

```cedar
// Example: floor "writers must be able to push to non-archived repos"
when { principal in resource.writers && !resource.isArchived };
//     ^from spec guarantee              ^global forbid negated

// Example: floor "assigned professionals must be able to viewDocument (with valid consent)"
when { principal.assigned_orgs.contains({
    organization: resource.owner.organization,
    serviceline: resource.serviceline,
    location: resource.location,
}) && context.consent.client == resource.owner
  && context.consent.team_region_list.contains(principal.location) };
//   ^consent is a global forbid in the tax domain — must include it
```

### Attribute type lookup — critical for correct syntax

Look at the schema attribute type to choose the right Cedar expression:

| Schema type | Cedar expression |
|---|---|
| `UserGroup` | `principal in resource.writers` (entity hierarchy `in`) |
| `Set<EntityType>` | `resource.members.contains(principal)` (set containment) |
| `Set<String>` | `resource.allowedRegions.contains(context.userRegion)` |
| `Bool` | `resource.isArchived`, `!resource.isArchived`, `context.mfaVerified` |
| `Long` | `resource.accessCount >= resource.maxAccess` |
| `String` | `resource.environment == "production"` |
| `datetime` | `context.now > resource.expiresAt` |
| Optional (`?`) | **must has-guard**: `resource has expiresAt && context.now > resource.expiresAt` |

**NEVER** write `principal in resource.setAttr` when `setAttr` is `Set<EntityType>`.
**ALWAYS** write `resource.setAttr.contains(principal)` instead.

### Safety rules for references

**Rule 1 — No role-keyed negations.**
Never write `when { !(principal in Role::"X") }` in a reference.
This blocks multi-role users. Encode role restrictions by limiting what role X's permit covers,
not by forbidding role X by name.

**Rule 2 — Optional attribute has-guard.**
If any attribute is declared with `?` in the schema, guard it before reading:
```cedar
// WRONG
when { context.now > resource.expiresAt }
// RIGHT
when { resource has expiresAt && context.now > resource.expiresAt }
```
Cedar also rejects `!(context has x) || context.x == v`. Instead write:
```cedar
when { (!(context has x)) || (context has x && context.x == v) }
```

**Rule 3 — Namespace prefix.**
If the schema has `namespace Foo { entity Bar = { ... }; }`, then in Cedar policies
and references, write `principal is Foo::Bar`, not `principal is Bar`.

**Rule 4 — datetime vs duration syntax.**
```
datetime("2025-01-01T00:00:00Z")   ← ISO 8601
duration("1h")                      ← Go-style  (NOT "PT1H")
duration("-24h")                    ← Go-style  (NOT "-PT24H")
duration("1h30m")                   ← Go-style  (NOT "PT1H30M")
```

**Rule 5 — No ternary/if-else.**
Cedar has no `if/then/else`. Use `&&`, `||`, `!`, `has` only.

---

## Step 4b — Validate every reference file

For each file written in Step 4, run:
```
CEDAR validate --schema SCENARIO_DIR/schema.cedarschema \
               --policies SCENARIO_DIR/references/<filename>.cedar
```

If validation fails, read the error and fix the file. Re-run until it passes.
Do not proceed to Step 5 until ALL reference files pass validation.

A malformed reference file will cause Phase 2 to loop forever on unfixable errors.

---

## Step 5 — Write initial `candidate.cedar`

Write `SCENARIO_DIR/candidate.cedar`.

Start from the policy spec. Write one `permit` rule per role or access path described.
Add `forbid` rules for every deny rule in the spec.

Template patterns:
```cedar
// Role-based permit (UserGroup)
permit (principal is User, action == Action::"pull", resource is Repository)
when { principal in resource.readers };

// Set-based permit (Set<EntityType>)
permit (principal is User, action == Action::"view", resource is Document)
when { resource.viewers.contains(principal) };

// Forbid with global condition
forbid (principal is User, action, resource is Repository)
when { resource.isArchived }
unless { action in [Action::"pull", Action::"fork"] };

// Forbid with context
forbid (principal is User, action in [Action::"add_reader", Action::"add_writer"], resource)
when { !context.ssoVerified };

// Cross-entity traversal (Issue → Repository)
permit (principal is User, action == Action::"edit_issue", resource is Issue)
when { principal in resource.repo.writers };

// Namespaced
permit (principal is Taxpreparer::Professional,
        action == Action::"viewDocument",
        resource is Taxpreparer::Document)
when { principal.assigned_orgs.contains({
    organization: resource.owner.organization,
    serviceline:  resource.serviceline,
    location:     resource.location,
}) };
```

---

## Step 6 — CEGIS loop

Run from `REPO_ROOT`:
```
cd REPO_ROOT
CVC5=<cvc5_path> python orchestrator.py --workspace SCENARIO_DIR
```

Read the output. For each check:
- `✓ PASS` — this check is satisfied
- `✗ FAIL  type=implies` — your policy is MORE PERMISSIVE than the ceiling
- `✗ FAIL  type=floor` — your policy is MORE RESTRICTIVE than the floor
- `✗ FAIL  type=always-denies-liveness` — your policy denies ALL requests for this action

`loss: N` = number of failed checks. Goal: loss == 0.

### How to fix failures

**`implies` ceiling FAIL — policy too permissive:**
The counterexample shows a request your policy allows but shouldn't.
→ Find which `permit` rule matches that request.
→ Add the missing condition to its `when` clause, OR add a `forbid` for that case.

**`floor` FAIL — policy too restrictive:**
The counterexample shows a request your policy blocks but must allow.
→ Find which condition in your `permit` blocks it (extra `&&` clause?).
→ Find which `forbid` fires for it.
→ Remove the extra condition, or narrow the `forbid`'s scope.

**`always-denies-liveness` FAIL — trivially deny-all:**
No `permit` rule fires for this action at all.
→ Check that a permit exists for this action and its when clause can be satisfied.

**Oscillating between ceiling FAIL and floor FAIL:**
You have a role-keyed `forbid`. Example: `forbid when principal in Role::"X"`.
This blocks users who are in BOTH Role X and another role that the floor expects to work.
→ Delete the role-keyed `forbid`.
→ Instead, constrain role X's `permit` rule to exclude the resource/condition.

### Only edit `candidate.cedar`

Never modify: `schema.cedarschema`, `verification_plan.py`, `references/`, `orchestrator.py`, `solver_wrapper.py`.

---

## Step 7 — Done

When `loss == 0`, the file `SCENARIO_DIR/candidate.cedar` is formally verified.
Print: `VERIFIED: SCENARIO_DIR/candidate.cedar  loss=0`
