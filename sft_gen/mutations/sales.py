"""Sales domain — new SFT mutations.

Already in cedarbench (excluded):
  sales_base, sales_add_approval, sales_add_archive, sales_add_delete,
  sales_add_regional_manager, sales_add_team, sales_full_expansion,
  sales_remove_customer_restriction, sales_temporal_campaign.

Base schema entities: Job, User{job,customerId} in [Market], Market,
  Presentation{owner,viewers,editors}, Template{owner,viewers,editors,viewerMarkets,editorMarkets}
Actions: viewPresentation, duplicatePresentation, editPresentation,
  grantViewAccessToPresentation, grantEditAccessToPresentation,
  viewTemplate, duplicateTemplate, editTemplate, removeSelfAccessFromTemplate,
  removeOthersAccessToTemplate, grantViewAccessToTemplate, grantEditAccessToTemplate
"""

import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
---
pattern: "base sales ACL"
difficulty: easy
features:
  - job-based access (internal/distributor/customer)
  - market-scoped sharing
  - owner/viewer/editor roles
domain: sales / CRM
source: mutation (sales domain)
---

# Sales Platform — Policy Specification

## Context

This policy governs access control for a B2B sales platform with Users, Jobs,
Markets, Presentations, and Templates.

Users have a `job` attribute (one of: internal, distributor, customer, other) and
belong to one or more `Market` groups. Presentations and Templates have `owner`,
`viewers` (Set<User>), and `editors` (Set<User>) attributes. Templates additionally
have `viewerMarkets` and `editorMarkets` (Set<Market>).

## Requirements

### 1. Presentation — Internal Users
- Any **internal** user may view, duplicate, and edit any Presentation.

### 2. Presentation — Non-Internal Users (Distributors, Customers)
- A non-internal user may **viewPresentation** and **removeSelfAccessFromPresentation**
  if they are in the Presentation's `viewers` or `editors` set.
- A non-internal user may **duplicatePresentation** and **editPresentation** only if
  they are in the Presentation's `editors` set.
- A non-internal user may **grantViewAccess** or **grantEditAccess** to a Presentation
  only if they are in the Presentation's `editors` set.
- Granting requires the context `target` to be in the `viewers`/`editors` set for
  grant-view, or in `editors` for grant-edit.

### 3. Template — Internal Users
- An **internal** user may view, duplicate, and edit any Template.

### 4. Template — Non-Internal Users
- A non-internal user may **viewTemplate** and **duplicateTemplate** if they are in
  the Template's `viewers` set OR their Market is in the Template's `viewerMarkets`.
- A non-internal user may **editTemplate** and **removeOthersAccessToTemplate** only
  if they are in the Template's `editors` set.

### 5. Customer Restriction (Deny Rule)
- Users with `job == "customer"` (customers) may NOT editPresentation or editTemplate.

## Notes
- Job type is modeled as a Cedar entity (Job) with named instances.
- Market membership is via entity hierarchy: `User in [Market]`.
- Cedar denies by default.
"""


# ── 1. VPN gate — edit actions require corporate VPN (S8 + P1) ────────────────

class SalesVpnGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_vpn_gate",
            base_scenario="sales",
            difficulty="easy",
            description="Add onVPN Bool context; editPresentation and editTemplate forbidden off-VPN",
            operators=["S8", "P1"],
            features_tested=["context_gate", "write_protection", "multi_action_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_context_field(base_schema, "editPresentation", "onVPN", "Bool")
        spec = _BASE_SPEC + """\
### 6. VPN Gate (Deny Rule)
- **editPresentation**, **editTemplate**, **removeOthersAccessToTemplate**,
  **grantEditAccessToPresentation**, and **grantEditAccessToTemplate** are **forbidden**
  when `context.onVPN == false`.
- Read and view actions (viewPresentation, viewTemplate, duplicatePresentation,
  duplicateTemplate) are not restricted by VPN status.
- This applies to all user types including internal users.
- Context carries `onVPN: Bool` set by the network authentication layer.

## Notes (VPN Gate)
- The VPN check is a blanket write protection independent of job type or ownership.
- Internal users who normally have unrestricted edit access still need to be on VPN.
- Forbid pattern: `forbid ... action in [editPresentation, editTemplate, ...]
  when { !context.onVPN }`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Presentation quota — max editors cap (S2 + P6) ────────────────────────

class SalesPresentationEditorCap(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_editor_cap",
            base_scenario="sales",
            difficulty="easy",
            description="Add editorCount + maxEditors Long to Presentation; grantEditAccess blocked when at cap",
            operators=["S2", "P6"],
            features_tested=["numeric_threshold", "cap_enforcement"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "editorCount", "Long")
        schema = schema_ops.add_attribute(schema, "Presentation", "maxEditors", "Long")
        spec = _BASE_SPEC + """\
### 6. Editor Cap (Deny Rule)
- Presentations have `editorCount: Long` (current editor count) and
  `maxEditors: Long` (configured limit).
- When `resource.editorCount >= resource.maxEditors`, **grantEditAccessToPresentation**
  is **forbidden** for all users including the owner.
- grantViewAccessToPresentation is not restricted by this cap.
- The host application updates `editorCount` when editors are added or removed.

## Notes (Editor Cap)
- Numeric comparison: `resource.editorCount >= resource.maxEditors`.
- Both attributes are on the Presentation entity (no cross-entity traversal).
- Internal users who normally have unrestricted access cannot bypass this cap.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. Account tier — enterprise requires senior internal role (S3 + P7 + P9) ──

class SalesAccountTier(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_account_tier",
            base_scenario="sales",
            difficulty="medium",
            description="Add tier String to Presentation; enterprise presentations require seniorInternal job",
            operators=["S3", "S6", "P7", "P2"],
            features_tested=["string_enum", "new_job_type", "tiered_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "tier", "String")
        # Add SeniorInternal as a new Job type instance (entity, no attrs)
        spec = _BASE_SPEC + """\
### 6. Presentation Tier Restriction
- Presentations have a `tier: String` attribute with values:
  `"standard"`, `"premium"`, `"enterprise"`.
- For **enterprise** tier presentations (`tier == "enterprise"`):
  - Only users whose job is `Job::"internal"` may **editPresentation**.
  - Distributors and customers in the `editors` set may NOT edit enterprise presentations.
  - Viewing (viewPresentation) and duplication are not affected by tier.
- For `"standard"` and `"premium"` tiers, the base access rules apply.

## Notes (Account Tier)
- The tier restriction is an additional forbid layered on top of the existing
  customer restriction: enterprise blocks distributors too.
- Implement as: `forbid editPresentation when resource.tier == "enterprise"
  unless principal.job == Job::"internal"`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Territory matching — user.market must match (S3 + P1 + P4) ─────────────

class SalesTerritory(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_territory",
            base_scenario="sales",
            difficulty="medium",
            description="Add territory String to Presentation; non-internal users can only access matching-market presentations",
            operators=["S3", "P1", "P4"],
            features_tested=["string_condition", "market_scoping", "internal_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "territory", "String")
        spec = _BASE_SPEC + """\
### 6. Territory Gate (Deny Rule with Internal Bypass)
- Presentations have a `territory: String` attribute (e.g., `"APAC"`, `"EMEA"`, `"NA"`).
- For non-internal users (distributors, customers), **viewPresentation** and
  **editPresentation** are **forbidden** if the Presentation's `territory` does not
  match a Market the user belongs to.
  - Specifically: the user must be `in` at least one Market whose name matches
    `resource.territory`. Since Market is a Cedar entity, this requires the user
    to be in a Market entity named the same as the territory string.
- **Internal** users bypass the territory restriction — they can access any presentation
  regardless of territory.
- This restriction is in addition to (not a replacement for) the viewer/editor set checks.

## Notes (Territory)
- Market membership is via entity hierarchy: `principal in Market::<territory>`.
- String equality between `resource.territory` and a market name is the check.
- Internal bypass: `unless { principal.job == Job::"internal" }`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Watcher role — Set<User> view-only on Presentation (S5 + P2) ──────────

class SalesWatcher(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_watcher",
            base_scenario="sales",
            difficulty="easy",
            description="Add watchers Set<User> to Presentation; watchers can viewPresentation only",
            operators=["S5", "P2"],
            features_tested=["set_membership_permit", "view_only_role"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "watchers", "Set<User>")
        spec = _BASE_SPEC + """\
### 6. Watcher Access (View-Only)
- Presentations have a `watchers: Set<User>` attribute for users granted view-only access
  with an explicit read-only restriction.
- A user in the `watchers` set may **viewPresentation** and **removeSelfAccessFromPresentation**.
- Watchers may NOT duplicate, edit, or grant access to the presentation.
- Watchers are separate from `viewers`: a user in `viewers` has the same view rights but
  is not explicitly marked read-only. A user in `watchers` has a forbid on edit actions
  even if they were later added to `editors`.

## Notes (Watcher)
- Dual permit for viewPresentation: `viewers` set OR `watchers` set.
- Explicit forbid for watchers on editPresentation: `forbid ... when resource.watchers.contains(principal)`.
- This tests a "read-only override" pattern where watcher membership blocks edits.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Contract entity — sign/view contract (S6 + S7 + P2 + P9) ───────────────

class SalesContract(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_contract",
            base_scenario="sales",
            difficulty="medium",
            description="Add Contract entity linked to Presentation; internal users sign, editors view",
            operators=["S6", "S7", "P2", "P9"],
            features_tested=["new_entity", "cross_traversal", "job_based_permit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Contract = {
    presentation: Presentation,
    isSigned: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Contract actions
action viewContract, signContract appliesTo {
    principal: [User],
    resource: [Contract],
};""")
        spec = _BASE_SPEC + """\
### 6. Contract Permissions
- Contracts are linked to Presentations (`Contract.presentation: Presentation`).
- Any user who can **editPresentation** on the linked presentation may **viewContract**.
  (Check via cross-entity traversal: `principal in resource.presentation.editors` OR
  `principal.job == Job::"internal"`.)
- Only **internal** users may **signContract**.
- Once a contract is signed (`isSigned == true`), **signContract** is forbidden for all users.
  A signed contract cannot be re-signed.

## Notes (Contract)
- signContract: job == internal AND !resource.isSigned.
- viewContract: same paths as editPresentation (editors set + internal).
- The isSigned check creates a state-machine-like restriction.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Fiscal window — cross-year access forbidden (S2 + S8 + P1) ─────────────

class SalesFiscalWindow(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_fiscal_window",
            base_scenario="sales",
            difficulty="medium",
            description="Add fiscalYear Long to Presentation; context currentYear; cross-year edit forbidden",
            operators=["S2", "S8", "P1"],
            features_tested=["numeric_comparison", "context_gate", "temporal_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "fiscalYear", "Long")
        schema = schema_ops.add_context_field(schema, "editPresentation", "currentYear", "Long")
        spec = _BASE_SPEC + """\
### 6. Fiscal Year Access Control (Deny Rule)
- Presentations have a `fiscalYear: Long` attribute (e.g., `2024`, `2025`).
- Context carries `currentYear: Long` — the current fiscal year from the host application.
- If `resource.fiscalYear != context.currentYear`, **editPresentation** and **editTemplate**
  are **forbidden** for non-internal users.
- Internal users may edit across fiscal years (no restriction).
- Viewing and duplicating are not restricted by fiscal year.

## Notes (Fiscal Window)
- Numeric comparison: `resource.fiscalYear != context.currentYear`.
- Internal users bypass via `unless { principal.job == Job::"internal" }`.
- This tests a "year-scoped edit" pattern common in financial sales platforms.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Remove Template — presentation-only model (S11 + P3) ───────────────────

class SalesRemoveTemplate(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_remove_template",
            base_scenario="sales",
            difficulty="easy",
            description="Remove Template entity and all template actions; presentation-only access model",
            operators=["S11", "S12", "P3"],
            features_tested=["entity_removal", "action_removal", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_entity(base_schema, "Template")
        # Remove entire template actions section via regex (handles grouped action declarations)
        schema = re.sub(
            r'\n*// Actions -- Templates\n.*',
            '',
            schema,
            flags=re.DOTALL,
        ).rstrip() + '\n'
        spec = """\
---
pattern: "remove entity"
difficulty: easy
features:
  - job-based access (internal/distributor/customer)
  - presentation-only (templates removed)
domain: sales / CRM
source: mutation (sales domain)
---

# Sales Platform — Policy Specification (Presentation-Only)

## Context

This policy governs access for a sales platform where Templates have been removed.
Only Presentations and their associated actions remain.

## Requirements

### 1. Presentation — Internal Users
- Any **internal** user may view, duplicate, and edit any Presentation.

### 2. Presentation — Non-Internal Users
- A non-internal user may **viewPresentation** and **removeSelfAccessFromPresentation**
  if they are in the Presentation's `viewers` or `editors` set.
- A non-internal user may **duplicatePresentation** and **editPresentation** only if
  they are in the Presentation's `editors` set.
- A non-internal user may grant view/edit access only if they are in the `editors` set.

### 3. Customer Restriction (Deny Rule)
- Users with `job == "customer"` may NOT editPresentation.

## Notes
- The Template entity and all template-related actions have been removed.
- Policy is simpler with no market-based template sharing logic.
- Cedar denies by default.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Self-grant forbidden — cannot grant to yourself (S8 + P10) ─────────────

class SalesSelfGrantForbid(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_self_grant_forbid",
            base_scenario="sales",
            difficulty="easy",
            description="Forbid grantViewAccess/grantEditAccess when context.target == principal (self-grant)",
            operators=["P10"],
            features_tested=["self_exclusion", "grant_control"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # No schema change needed — policy change only (P10: self-exclusion on grant)
        spec = _BASE_SPEC + """\
### 6. Self-Grant Prohibition (Deny Rule)
- A user may NOT grant view or edit access to a Presentation or Template to themselves.
- Specifically: if `context.target == principal`, **grantViewAccessToPresentation**,
  **grantEditAccessToPresentation**, **grantViewAccessToTemplate**, and
  **grantEditAccessToTemplate** are all **forbidden**.
- This prevents privilege escalation where a user in `viewers` self-upgrades to `editors`.
- Internal users are also subject to this restriction — self-grant is forbidden universally.

## Notes (Self-Grant Forbid)
- The context already carries `target: User` for grant actions.
- Self-exclusion: `forbid ... when { context.target == principal }`.
- This tests the self-exclusion pattern on context attributes (not resource attributes).
"""
        return MutationResult(schema=base_schema, policy_spec=spec)


# ── 10. Market isolation — non-internal cannot cross market (S8 + P1) ─────────

class SalesMarketIsolation(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_market_isolation",
            base_scenario="sales",
            difficulty="medium",
            description="Add ownerMarket String to Presentation; non-internal forbidden from cross-market access",
            operators=["S3", "P1", "P4"],
            features_tested=["market_isolation", "string_condition", "internal_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Presentation", "ownerMarket", "String")
        spec = _BASE_SPEC + """\
### 6. Market Isolation (Deny Rule)
- Presentations have an `ownerMarket: String` attribute identifying the market where
  the presentation was created.
- Non-internal users (distributors, customers) may only access Presentations whose
  `ownerMarket` matches a Market they are a member of.
- Formally: if `!(principal in Market::<resource.ownerMarket>)`, forbid viewPresentation,
  duplicatePresentation, editPresentation for non-internal users.
- Internal users bypass market isolation — they can access across all markets.
- Access-list membership (viewers/editors sets) does not override market isolation for
  non-internal users: both conditions must hold.

## Notes (Market Isolation)
- Note: directly referencing `Market::<string_value>` requires the entity ID to match.
  In practice, the host app ensures the ownerMarket string maps to a valid Market entity ID.
- This is a stronger isolation than the base market-based template sharing (which uses
  `viewerMarkets: Set<Market>` as an allowlist). Here, market identity is enforced on
  the owning market, not just on sharing permissions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    SalesVpnGate(),
    SalesPresentationEditorCap(),
    SalesAccountTier(),
    SalesTerritory(),
    SalesWatcher(),
    SalesContract(),
    SalesFiscalWindow(),
    SalesRemoveTemplate(),
    SalesSelfGrantForbid(),
    SalesMarketIsolation(),
]

for _m in MUTATIONS:
    register(_m)
