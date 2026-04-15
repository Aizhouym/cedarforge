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
