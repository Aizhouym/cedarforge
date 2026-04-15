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
