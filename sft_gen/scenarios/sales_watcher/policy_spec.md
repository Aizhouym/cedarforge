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
### 6. Watcher Access (View-Only)
- Presentations have a `watchers: Set<User>` attribute for users granted view-only access
  with an explicit read-only restriction.
- A user in the `watchers` set may **viewPresentation** and **removeSelfAccessFromPresentation**.
- Watchers may NOT duplicate, edit, or grant access to the presentation.
- Watchers are separate from `viewers`: a user in `viewers` has the same view rights but
  is not explicitly marked read-only. A user in `watchers` has a forbid on edit actions
  even if they were later added to `editors`.

## Notes (Watcher)
- Dual permit for viewPresentation: `viewers` set OR `watchers` set.
- Explicit forbid for watchers on editPresentation: `forbid ... when resource.watchers.contains(principal)`.
- This tests a "read-only override" pattern where watcher membership blocks edits.
