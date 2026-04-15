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
