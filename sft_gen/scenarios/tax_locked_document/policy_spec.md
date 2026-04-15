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
