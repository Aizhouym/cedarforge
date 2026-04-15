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
