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
### 4. Supervisor Role
- Supervisors have `supervised_orgs: Set<String>` and `location: String`, and may
  viewDocument on Documents in their supervised organizations.
- The same consent gate applies to supervisors too:
  `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.

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
