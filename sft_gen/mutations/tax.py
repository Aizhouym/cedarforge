"""Tax domain — new SFT mutations.

Already in cedarbench (excluded):
  tax_base, tax_add_auditor, tax_add_client_profile, tax_add_edit,
  tax_add_sensitivity, tax_add_supervisor, tax_full_expansion, tax_remove_consent.

Base schema (Taxpreparer namespace):
  Professional { assigned_orgs: Set<orgInfo>, location: String }
  Document { serviceline, location: String, owner: Client }
  Client { organization: String }
  Consent { client: Client, team_region_list: Set<String> }
  action viewDocument appliesTo { principal: [Professional], resource: [Document], context: { consent: Consent } }
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
---
pattern: "base org-match + consent"
difficulty: medium
features:
  - organization-scoped access
  - consent-based forbid
  - namespaced entities
domain: finance / tax preparation
source: mutation (tax domain)
---

# Tax Preparer Permissions — Policy Specification

## Context

This policy governs access for a tax preparation platform (Taxpreparer namespace).
Principals: Professional. Resources: Document. Client owns Documents.

Professionals have `assigned_orgs: Set<orgInfo>` where orgInfo = {organization, serviceline, location}.
Documents have `serviceline`, `location: String`, and `owner: Client`.
Clients have `organization: String`.

Context carries `consent: Consent` where Consent = {client: Client, team_region_list: Set<String>}.

## Requirements

### 1. Organization-Level Access
- A Professional may **viewDocument** if `assigned_orgs.contains({organization: resource.owner.organization,
  serviceline: resource.serviceline, location: resource.location})`.

### 2. Ad-Hoc Template Access
- Individual (principal, resource) pairs may be granted viewDocument via policy templates.

### 3. Consent Gate (Deny Rule)
- All viewDocument is forbidden unless: `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.

## Notes
- All entities are in the `Taxpreparer` namespace.
- Cedar denies by default.
"""


# ── 1. Filing deadline — editDocument forbidden after deadline (S4 + S8 + P1) ──

class TaxDeadlineGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_deadline_gate",
            base_scenario="tax",
            difficulty="medium",
            description="Add filingDeadline datetime to Document; editDocument forbidden after deadline; viewDocument unaffected",
            operators=["S7", "S4", "S8", "P1"],
            features_tested=["datetime_comparison", "new_action", "temporal_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add editDocument action (reusing the pattern from tax_add_edit but with deadline)
        schema = base_schema.replace(
            "action viewDocument appliesTo {",
            "action viewDocument, editDocument appliesTo {"
        )
        schema = schema_ops.add_attribute(schema, "Document", "filingDeadline", "datetime")
        # Add now to context
        schema = schema.replace(
            "context: { consent: Consent }",
            "context: { consent: Consent, now: datetime }"
        )
        spec = _BASE_SPEC + """\
### 4. Edit Document Action
- A Professional may **editDocument** using the same org-match rule as viewDocument:
  `assigned_orgs.contains({organization, serviceline, location})`.
- The consent gate applies to editDocument as well.

### 5. Filing Deadline Gate (Deny Rule)
- Documents have a `filingDeadline: datetime` attribute.
- If `context.now > resource.filingDeadline`, **editDocument** is **forbidden** for ALL
  professionals, regardless of org match or consent.
- **viewDocument** is NOT restricted by the filing deadline.
- The deadline allows post-deadline review but prevents modification.

## Notes (Deadline)
- Cedar datetime comparison: `context.now > resource.filingDeadline`.
- Context carries both `consent` and `now`.
- The deadline forbid is additional to the consent gate — both must pass for editDocument.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Corporate network gate — viewDocument requires on-network (S8 + P1) ────

class TaxNetworkGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_network_gate",
            base_scenario="tax",
            difficulty="easy",
            description="Add onCorporateNetwork Bool to context; viewDocument forbidden off-network",
            operators=["S8", "P1"],
            features_tested=["context_gate", "network_restriction", "compliance"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema.replace(
            "context: { consent: Consent }",
            "context: { consent: Consent, onCorporateNetwork: Bool }"
        )
        spec = _BASE_SPEC + """\
### 4. Corporate Network Gate (Deny Rule)
- All **viewDocument** actions are **forbidden** when `context.onCorporateNetwork == false`.
- This is a compliance requirement: tax documents may only be accessed from the corporate
  network or approved VPN endpoints.
- The network check is applied before the org-match and consent checks — off-network
  requests are blocked universally.
- Context carries `onCorporateNetwork: Bool` set by the network authentication layer.

## Notes (Network Gate)
- The forbid applies to both org-matched access and ad-hoc template access.
- Combined with the consent gate, both conditions must hold: on-network AND valid consent.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. Review entity — supervisors approve documents (S6 + S7 + P2 + P9) ─────

class TaxReview(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_review",
            base_scenario="tax",
            difficulty="medium",
            description="Add Supervisor role + Review entity; supervisors can approveDocument; approval blocks further edits",
            operators=["S6", "S7", "S9", "P2", "P9"],
            features_tested=["new_entity", "new_role", "cross_traversal", "state_machine"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add Supervisor entity
        schema = schema_ops.add_entity(base_schema, """\
  entity Supervisor = {
    supervised_orgs: Set<String>,
    location: String,
  };""")
        # Add Review entity
        schema = schema_ops.add_entity(schema, """\
  entity Review = {
    document: Document,
    reviewer: Supervisor,
    approved: Bool,
  };""")
        # Add approveDocument action
        schema = schema_ops.add_action(schema, """\
  action approveDocument appliesTo {
    principal: [Supervisor],
    resource: [Document],
    context: { consent: Consent }
  };""")
        spec = _BASE_SPEC + """\
### 4. Supervisor and Review Permissions
- Supervisors have `supervised_orgs: Set<String>` and `location: String`.
- A Supervisor may **approveDocument** if `principal.supervised_orgs.contains(resource.owner.organization)`.
- The consent gate applies to approveDocument: `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.

### 5. Review State
- A Review entity links a Document to a Supervisor and records `approved: Bool`.
- Once a Review has `approved == true`, no additional approvals are needed.
  (Policy models the approval action; review state is tracked by the host application.)

## Notes (Review)
- Supervisor access: org match only (no serviceline/location triple like Professional).
- approveDocument is Supervisor-only — Professionals cannot approve documents.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Page limit — auditors restricted by document length (S2 + P6) ──────────

class TaxAuditorPageLimit(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_auditor_page_limit",
            base_scenario="tax",
            difficulty="medium",
            description="Add Auditor role + pageCount Long to Document; auditors cannot view documents over 100 pages",
            operators=["S6", "S2", "P2", "P6"],
            features_tested=["new_role", "numeric_forbid", "resource_attribute"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add Auditor entity
        schema = schema_ops.add_entity(base_schema, """\
  entity Auditor = {
    auditScope: Set<String>,
    location: String,
  };""")
        schema = schema_ops.add_attribute(schema, "Document", "pageCount", "Long")
        schema = schema_ops.add_action(schema, """\
  action auditDocument appliesTo {
    principal: [Auditor],
    resource: [Document],
    context: { consent: Consent }
  };""")
        spec = _BASE_SPEC + """\
### 4. Auditor Access
- Auditors have `auditScope: Set<String>` listing servicelines they may audit.
- An Auditor may **auditDocument** if `principal.auditScope.contains(resource.serviceline)`.
- The consent gate applies: `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.
- Auditors may NOT viewDocument (different action) or editDocument.

### 5. Page Count Restriction (Deny Rule)
- Documents have `pageCount: Long`.
- If `resource.pageCount > 100`, **auditDocument** is **forbidden** for Auditors.
- This models a workload constraint: auditors may not review very large documents
  without supervisor escalation.
- The 100-page limit does not apply to Professionals (who use viewDocument, not auditDocument).

## Notes (Page Limit)
- Numeric comparison: `resource.pageCount > 100`.
- Auditors and Professionals are separate principal types with separate actions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Document type — amendments supervisor-only edit (S3 + P7 + P8) ─────────

class TaxDocumentType(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_document_type",
            base_scenario="tax",
            difficulty="medium",
            description="Add docType String to Document + editDocument action; amendments require Supervisor",
            operators=["S3", "S7", "P7", "P8"],
            features_tested=["string_enum", "new_action", "role_redistribution"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "docType", "String")
        schema = schema_ops.add_entity(schema, """\
  entity Supervisor = {
    supervised_orgs: Set<String>,
    location: String,
  };""")
        schema = base_schema.replace(
            "action viewDocument appliesTo {\n    principal: [Professional],",
            "action viewDocument, editDocument appliesTo {\n    principal: [Professional, Supervisor],"
        )
        schema = schema_ops.add_attribute(schema, "Document", "docType", "String")
        spec = _BASE_SPEC + """\
### 4. Supervisor Role
- Supervisors have `supervised_orgs: Set<String>` and may viewDocument and editDocument
  on Documents in their supervised organizations.

### 5. Document Type Restriction
- Documents have `docType: String` with values: `"return"`, `"amendment"`, `"extension"`.
- For **amendment** documents (`docType == "amendment"`):
  - **editDocument** is restricted to Supervisors only. Professionals may NOT edit amendments.
  - **viewDocument** is not restricted by document type.
- For `"return"` and `"extension"` types, both Professionals and Supervisors may editDocument
  if they have org-match access and valid consent.

## Notes (Document Type)
- Professional role redistribution: for amendments, edit permission moves to Supervisor only.
- Forbid: `forbid editDocument when resource.docType == "amendment" unless principal is Supervisor`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Multi-professional — team-based access via Set (S5 + P2) ───────────────

class TaxMultiProfessional(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_multi_professional",
            base_scenario="tax",
            difficulty="medium",
            description="Add assignedProfessionals Set<Professional> to Document; any assigned professional can viewDocument",
            operators=["S5", "P2"],
            features_tested=["set_membership_permit", "team_access", "dual_path"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "assignedProfessionals", "Set<Taxpreparer::Professional>")
        spec = _BASE_SPEC + """\
### 4. Team Assignment Access (Second Permit Path)
- Documents may have an `assignedProfessionals: Set<Professional>` attribute listing
  professionals directly assigned to work on that document.
- A Professional in `resource.assignedProfessionals` may **viewDocument** regardless of
  whether their org match succeeds.
- The consent gate still applies: even assigned professionals need valid consent in context.
- This creates a dual-path for viewDocument:
  (a) org-match (existing rule), OR
  (b) direct assignment (`resource.assignedProfessionals.contains(principal)`).

## Notes (Multi-Professional)
- Set containment: `resource.assignedProfessionals.contains(principal)`.
- Set<Professional> with Taxpreparer namespace: `Set<Taxpreparer::Professional>`.
- The consent gate applies to BOTH paths — neither path bypasses consent.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Senior bypass — sensitivity restriction exemption (S9 + P4) ────────────

class TaxSeniorBypass(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_senior_bypass",
            base_scenario="tax",
            difficulty="medium",
            description="Add isSensitive Bool to Document + Supervisor role; senior professionals bypass sensitivity restriction",
            operators=["S1", "S6", "P1", "P4"],
            features_tested=["boolean_forbid", "unless_exception", "new_role", "sensitivity"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "isSensitive", "Bool")
        schema = schema_ops.add_entity(schema, """\
  entity Supervisor = {
    supervised_orgs: Set<String>,
    location: String,
  };""")
        schema = base_schema.replace(
            "action viewDocument appliesTo {\n    principal: [Professional],",
            "action viewDocument appliesTo {\n    principal: [Professional, Supervisor],"
        )
        schema = schema_ops.add_attribute(schema, "Document", "isSensitive", "Bool")
        spec = _BASE_SPEC + """\
### 4. Supervisor Role
- Supervisors have `supervised_orgs: Set<String>` and may viewDocument on Documents
  in their supervised organizations.

### 5. Sensitivity Restriction (Deny Rule with Supervisor Bypass)
- Documents have `isSensitive: Bool`.
- If `resource.isSensitive == true`, **viewDocument** is **forbidden** for Professionals
  whose consent region list does not contain `"HQ"`:
  i.e., forbidden when `!context.consent.team_region_list.contains("HQ")`.
- **Exception**: Supervisors bypass the sensitivity restriction entirely. A Supervisor
  with valid org-scope access may viewDocument even on sensitive documents without
  needing `"HQ"` in the consent region list.
- Professionals still need the `"HQ"` region in consent for sensitive documents.

## Notes (Senior Bypass)
- Implement as: `forbid viewDocument when resource.isSensitive && !... "HQ" ...
  unless principal is Supervisor`.
- The bypass is role-type based (Supervisor entity type), not a group membership.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Emergency access — context flag grants any-professional view (S8 + P2) ──

class TaxEmergencyAccess(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_emergency_access",
            base_scenario="tax",
            difficulty="hard",
            description="Add isEmergency Bool to context; emergency allows any Professional to view any Document, bypassing org-match",
            operators=["S8", "P2"],
            features_tested=["context_permit", "org_match_bypass", "emergency_override"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema.replace(
            "context: { consent: Consent }",
            "context: { consent: Consent, isEmergency: Bool }"
        )
        spec = _BASE_SPEC + """\
### 4. Emergency Access Override
- Context may carry `isEmergency: Bool`. When `context.isEmergency == true`, any
  Professional may **viewDocument** on any Document, bypassing the org-match requirement.
- The consent gate still applies in emergency mode: `context.consent.client == resource.owner`
  AND `context.consent.team_region_list.contains(principal.location)` must hold.
- Emergency access is a break-glass mechanism and does NOT bypass consent — consent
  from the document owner is still required even in emergencies.
- The host application is responsible for auditing all emergency access events.

## Notes (Emergency)
- Emergency permit: `permit viewDocument when context.isEmergency`.
- The consent forbid still overrides: emergency access requires consent.
- This tests: `context.isEmergency` as a permit path, combined with the existing consent forbid.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Org hierarchy — client parentOrg for cascade access (S14 + P2 + P9) ────

class TaxOrgHierarchy(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_org_hierarchy",
            base_scenario="tax",
            difficulty="hard",
            description="Add parentOrg String to Client; Professional org match cascades to subsidiary orgs",
            operators=["S3", "P2", "P9"],
            features_tested=["org_cascade", "hierarchy_access", "string_comparison"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Client", "parentOrg", "String")
        spec = _BASE_SPEC + """\
### 4. Organization Hierarchy Access
- Clients have a `parentOrg: String` attribute identifying a parent organization.
  (Example: Client `"Acme_Subsidiary"` has `parentOrg == "Acme_Corp"`.)
- A Professional whose `assigned_orgs` contains a match for the `parentOrg` (treating
  it as the organization) may also **viewDocument** on Documents owned by Clients in
  subsidiary organizations.
- Formally: if `principal.assigned_orgs.contains({organization: resource.owner.parentOrg,
  serviceline: resource.serviceline, location: resource.location})`, viewDocument is permitted.
- The consent gate still applies: consent must be from `resource.owner` (the subsidiary client).

## Notes (Org Hierarchy)
- This adds a second path for viewDocument: direct org match OR parent-org match.
- String comparison: `resource.owner.parentOrg` vs. organization field in assigned_orgs.
- The cascade is single-level (parent only, not grandparent) — no recursive hierarchy.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 10. Locked document — once reviewed, cannot be edited (S1 + P1) ──────────

class TaxLockedDocument(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_locked_document",
            base_scenario="tax",
            difficulty="medium",
            description="Add isLocked Bool to Document + editDocument; locked documents cannot be edited by anyone",
            operators=["S1", "S7", "P1"],
            features_tested=["boolean_forbid", "new_action", "universal_lock"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "isLocked", "Bool")
        schema = base_schema.replace(
            "action viewDocument appliesTo {\n    principal: [Professional],",
            "action viewDocument, editDocument appliesTo {\n    principal: [Professional],"
        )
        schema = schema_ops.add_attribute(schema, "Document", "isLocked", "Bool")
        spec = _BASE_SPEC + """\
### 4. Edit Document Action
- A Professional may **editDocument** using the same org-match rule as viewDocument.
- The consent gate applies to editDocument as well.

### 5. Document Lock (Deny Rule)
- Documents have `isLocked: Bool`. Once locked, a document is immutable.
- If `resource.isLocked == true`, **editDocument** is **forbidden** for ALL principals
  — no role override exists.
- **viewDocument** is not restricted by the lock.
- The host application sets `isLocked` to `true` after document finalization or approval.
  The policy cannot set this attribute — it is managed externally.

## Notes (Locked Document)
- Boolean forbid: `forbid editDocument when resource.isLocked`.
- The lock is universal: no principal type or role can bypass it.
- Compare with the filing deadline (tax_deadline_gate) which uses datetime; this uses boolean.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    TaxDeadlineGate(),
    TaxNetworkGate(),
    TaxReview(),
    TaxAuditorPageLimit(),
    TaxDocumentType(),
    TaxMultiProfessional(),
    TaxSeniorBypass(),
    TaxEmergencyAccess(),
    TaxOrgHierarchy(),
    TaxLockedDocument(),
]

for _m in MUTATIONS:
    register(_m)
