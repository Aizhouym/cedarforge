"""Tags domain — new SFT mutations.

Already in cedarbench (excluded):
  tags_base, tags_add_approval, tags_add_fourth_dimension, tags_add_owner_bypass,
  tags_add_role_c, tags_add_sensitivity, tags_remove_all_wildcard,
  tags_sensitivity_and_owner.

Base schema:
  entity Role;
  entity User in [Role] { allowedTagsForRole: { "Role-A"?: {production_status?, country?, stage?}, "Role-B"?: {...} } }
  entity Workspace { tags: { production_status?, country?, stage? } }
  actions: UpdateWorkspace (Role-A), DeleteWorkspace (Role-A), ReadWorkspace (Role-A + Role-B)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
---
pattern: "base tag-matching RBAC"
difficulty: medium
features:
  - tag-based access control
  - role-scoped tag namespaces
  - optional tag dimensions
  - ALL wildcard
domain: workspace platform
source: mutation (tags domain)
---

# Tags & Roles Workspace Permissions — Policy Specification

## Context

This policy governs access to Workspaces via tag-based matching scoped by Role.
Users belong to Roles (via `User in [Role]`). Each User has `allowedTagsForRole`
with optional entries for Role-A and Role-B. Each Workspace has `tags` with
optional `production_status`, `country`, and `stage` dimensions (Set<String>).

Access is granted if, for each dimension present in both user and workspace:
- the user's set contains `"ALL"`, OR
- the workspace's set contains `"ALL"`, OR
- the user's set containsAll of the workspace's set.

## Requirements

### 1. Role-A Access
- Users in Role-A may UpdateWorkspace, DeleteWorkspace, ReadWorkspace when
  all tag dimensions match using the containsAll / ALL rule.

### 2. Role-B Access
- Users in Role-B may ReadWorkspace only, using the same tag-matching logic.

## Notes
- Missing optional dimensions pass automatically (no restriction for that dimension).
- Cedar denies by default.
"""


# ── 1. Tag expiry — datetime on Workspace (S4 + S8 + P1) ─────────────────────

class TagsExpiry(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_expiry",
            base_scenario="tags",
            difficulty="medium",
            description="Add expiresAt datetime to Workspace; context now; all access forbidden after expiry",
            operators=["S4", "S8", "P1"],
            features_tested=["datetime_comparison", "universal_forbid", "context_field"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Workspace", "expiresAt", "datetime")
        for action_name in ["ReadWorkspace", "UpdateWorkspace", "DeleteWorkspace"]:
            schema = schema_ops.add_context_field(schema, action_name, "now", "datetime")
        spec = _BASE_SPEC + """\
### 3. Workspace Expiry (Deny Rule)
- Workspaces may have an `expiresAt: datetime` attribute.
- If `context.now > resource.expiresAt`, ALL actions on the workspace are **forbidden**
  for ALL users regardless of role or tag match.
- Workspaces without `expiresAt` (attribute absent) never expire.
  Guard: `resource has expiresAt` before comparing.
- Context carries `now: datetime` from the host application.

## Notes (Expiry)
- Cedar datetime comparison: `context.now > resource.expiresAt`.
- The `has` guard is critical for the optional attribute pattern.
- Expiry is orthogonal to the tag-matching access logic — even a perfect tag match
  cannot access an expired workspace.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Usage limit — numeric cap on workspace access (S2 + P6) ───────────────

class TagsUsageLimit(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_usage_limit",
            base_scenario="tags",
            difficulty="easy",
            description="Add accessCount + maxAccess Long to Workspace; ReadWorkspace forbidden when over limit",
            operators=["S2", "P6"],
            features_tested=["numeric_threshold", "usage_cap"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Workspace", "accessCount", "Long")
        schema = schema_ops.add_attribute(schema, "Workspace", "maxAccess", "Long")
        spec = _BASE_SPEC + """\
### 3. Usage Cap (Deny Rule)
- Workspaces have `accessCount: Long` (cumulative read operations) and
  `maxAccess: Long` (daily or lifetime limit).
- If `resource.accessCount >= resource.maxAccess`, **ReadWorkspace** is **forbidden**
  for all users regardless of role or tag match.
- Update and Delete actions are not restricted by the usage cap.
- The host application increments `accessCount` on each read and resets it periodically.

## Notes (Usage Cap)
- Numeric comparison: `resource.accessCount >= resource.maxAccess`.
- Both attributes are on the Workspace entity; no cross-entity traversal.
- This tests a "rate limiting" pattern at the policy level.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. MFA gate — updates require MFA (S8 + P1) ──────────────────────────────

class TagsMfaGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_mfa_gate",
            base_scenario="tags",
            difficulty="easy",
            description="Add mfaVerified Bool context; UpdateWorkspace and DeleteWorkspace forbidden without MFA",
            operators=["S8", "P1"],
            features_tested=["context_gate", "write_protection"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema
        for action_name in ["UpdateWorkspace", "DeleteWorkspace"]:
            schema = schema_ops.add_context_field(schema, action_name, "mfaVerified", "Bool")
        spec = _BASE_SPEC + """\
### 3. MFA Gate for Write Actions (Deny Rule)
- **UpdateWorkspace** and **DeleteWorkspace** are **forbidden** when
  `context.mfaVerified == false`, regardless of role membership or tag matching.
- **ReadWorkspace** is not restricted by MFA status.
- Context carries `mfaVerified: Bool` from the authentication layer.

## Notes (MFA Gate)
- The MFA check is in addition to the tag-based access check, not a replacement.
- Both conditions must hold for write operations: tag match AND MFA verified.
- Forbid pattern: `forbid ... action in [UpdateWorkspace, DeleteWorkspace] ... when { !context.mfaVerified }`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Environment tier — production workspaces add restriction (S3 + P7 + P1) ─

class TagsEnvironment(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_environment",
            base_scenario="tags",
            difficulty="medium",
            description="Add environment String to Workspace; production workspaces require explicit production_status tag match",
            operators=["S3", "P7", "P1"],
            features_tested=["string_enum", "conditional_restriction", "production_gate"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Workspace", "environment", "String")
        spec = _BASE_SPEC + """\
### 3. Production Environment Restriction
- Workspaces have an `environment: String` attribute: `"dev"`, `"staging"`, `"production"`.
- For **production** workspaces (`environment == "production"`):
  - **UpdateWorkspace** and **DeleteWorkspace** require that the user's
    `allowedTagsForRole["Role-A"]` explicitly includes a `production_status` set
    (not absent). An absent `production_status` on the user's tags does NOT grant
    access to production workspaces for write operations.
  - **ReadWorkspace** is not additionally restricted by environment.
- For dev and staging environments, the standard tag-matching rules apply (absent
  dimensions still pass).

## Notes (Environment)
- Production gate: `resource.environment == "production"` triggers the stricter check.
- The stricter check: `principal.allowedTagsForRole has "Role-A"` AND
  `principal.allowedTagsForRole["Role-A"] has production_status` — must be present.
- String comparison for environment: `resource.environment == "production"`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Public workspace — isPublic bypasses tag match for read (S1 + P2) ──────

class TagsPublicWorkspace(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_public_workspace",
            base_scenario="tags",
            difficulty="easy",
            description="Add isPublic Bool to Workspace; public workspaces allow any User to ReadWorkspace (no tag match needed)",
            operators=["S1", "P2"],
            features_tested=["boolean_permit", "open_read_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Workspace", "isPublic", "Bool")
        spec = _BASE_SPEC + """\
### 3. Public Workspace Open Read
- If `resource.isPublic == true`, any User (regardless of Role-A or Role-B membership,
  and without any tag matching) may **ReadWorkspace**.
- **UpdateWorkspace** and **DeleteWorkspace** still require Role-A membership AND
  tag matching — the `isPublic` flag only relaxes ReadWorkspace.
- The public read path is a second permit for ReadWorkspace alongside the existing
  tag-based Role-A/Role-B permits.

## Notes (Public Workspace)
- Implement as an additional permit: `permit ReadWorkspace when resource.isPublic`.
- The existing role-and-tag-based permits remain for non-public workspaces.
- This is a common "published/shared" pattern in workspace platforms.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Report entity — Role-A with full match can generate (S6 + S7 + P2 + P9) ─

class TagsReport(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_report",
            base_scenario="tags",
            difficulty="medium",
            description="Add Report entity linked to Workspace; only Role-A with full tag match can generateReport",
            operators=["S6", "S7", "P2", "P9"],
            features_tested=["new_entity", "cross_traversal", "elevated_permission"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Report = {
    workspace: Workspace,
    isConfidential: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Report actions
action generateReport, viewReport appliesTo {
    principal: [User],
    resource: [Report],
};""")
        spec = _BASE_SPEC + """\
### 3. Report Permissions
- Reports are linked to Workspaces (`Report.workspace: Workspace`).
- **generateReport**: Only Role-A users who have a full tag match on the linked Workspace
  may generate a report. The tag match is evaluated against `resource.workspace.tags`.
  (Cross-entity traversal: `resource.workspace.tags`.)
- **viewReport**: Role-A and Role-B users with a tag match on the linked Workspace may
  view a report.
- If `resource.isConfidential == true`, **viewReport** is restricted to Role-A users only.
  Role-B users cannot view confidential reports.

## Notes (Report)
- generateReport requires Role-A membership (not Role-B).
- The workspace tag check for Reports uses cross-entity traversal: the Report's workspace
  tags must match the user's allowed tags.
- isConfidential creates a split between Role-A and Role-B for viewReport.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. IP allowlist — context clientIP must be in user's allowlist (S5 + S8 + P1) ─

class TagsIpAllowlist(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_ip_allowlist",
            base_scenario="tags",
            difficulty="medium",
            description="Add allowedIPs Set<String> to User; context clientIP; write actions forbidden if IP not allowed",
            operators=["S5", "S8", "P1"],
            features_tested=["set_containment_forbid", "context_gate", "ip_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "User", "allowedIPs", "Set<String>")
        for action_name in ["UpdateWorkspace", "DeleteWorkspace"]:
            schema = schema_ops.add_context_field(schema, action_name, "clientIP", "String")
        spec = _BASE_SPEC + """\
### 3. IP Allowlist Gate (Deny Rule)
- Users may have an `allowedIPs: Set<String>` attribute listing permitted IP addresses.
- Context carries `clientIP: String` (the requester's IP address).
- If the user has a non-empty `allowedIPs` set AND `!principal.allowedIPs.contains(context.clientIP)`,
  **UpdateWorkspace** and **DeleteWorkspace** are **forbidden**.
- Users with an empty `allowedIPs` set have no IP restriction (open access).
- ReadWorkspace is not restricted by IP allowlist.

## Notes (IP Allowlist)
- Guard: `principal.allowedIPs` must be non-empty before applying the restriction.
  An empty set means "no IP restriction."
- Set containment: `principal.allowedIPs.contains(context.clientIP)`.
- This tests a principal-side set attribute checked against a context string value.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Role-D — write-only (unusual pattern) (S9 + P2 + P1) ──────────────────

class TagsRoleD(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_role_d",
            base_scenario="tags",
            difficulty="hard",
            description="Add Role-D with UpdateWorkspace permission but explicit forbid on ReadWorkspace (write-only role)",
            operators=["S9", "P2", "P1"],
            features_tested=["unusual_permission_pattern", "write_only_role", "explicit_read_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add Role-D tag dimension to User's allowedTagsForRole record
        # This requires modifying the type definition — use string replacement
        schema = base_schema.replace(
            '"Role-B"?: {\n        production_status?: Set<String>,\n        country?: Set<String>,\n        stage?: Set<String>,\n    },',
            '"Role-B"?: {\n        production_status?: Set<String>,\n        country?: Set<String>,\n        stage?: Set<String>,\n    },\n    "Role-D"?: {\n        production_status?: Set<String>,\n        country?: Set<String>,\n        stage?: Set<String>,\n    },'
        )
        spec = _BASE_SPEC + """\
### 3. Role-D Permissions (Write-Only)
- Role-D is an unusual role: users in Role-D with a tag match may **UpdateWorkspace**
  but are explicitly **forbidden** from **ReadWorkspace**.
- This models a "blind write" pattern where Role-D users can push updates to workspaces
  they cannot observe — useful for system/automation accounts.
- Role-D users may NOT DeleteWorkspace.
- Role-D tag matching uses the same containsAll/ALL rule as Role-A and Role-B,
  checking `allowedTagsForRole["Role-D"]`.

## Notes (Role-D — Write-Only)
- This tests an explicit forbid on a read action for a role that has write access.
- The forbid on ReadWorkspace for Role-D must use an `unless` to allow Role-A and Role-B
  members to still read even if they happen to also be in Role-D.
- `forbid ReadWorkspace when principal in Role::"Role-D" unless (principal in Role::"Role-A" || principal in Role::"Role-B")`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    TagsExpiry(),
    TagsUsageLimit(),
    TagsMfaGate(),
    TagsEnvironment(),
    TagsPublicWorkspace(),
    TagsReport(),
    TagsIpAllowlist(),
    TagsRoleD(),
]

for _m in MUTATIONS:
    register(_m)
