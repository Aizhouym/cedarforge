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
