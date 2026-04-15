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
