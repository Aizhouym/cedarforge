---
pattern: "remove entity"
difficulty: easy
features:
  - job-based access (internal/distributor/customer)
  - presentation-only (templates removed)
domain: sales / CRM
source: mutation (sales domain)
---

# Sales Platform — Policy Specification (Presentation-Only)

## Context

This policy governs access for a sales platform where Templates have been removed.
Only Presentations and their associated actions remain.

## Requirements

### 1. Presentation — Internal Users
- Any **internal** user may view, duplicate, and edit any Presentation.

### 2. Presentation — Non-Internal Users
- A non-internal user may **viewPresentation** and **removeSelfAccessFromPresentation**
  if they are in the Presentation's `viewers` or `editors` set.
- A non-internal user may **duplicatePresentation** and **editPresentation** only if
  they are in the Presentation's `editors` set.
- A non-internal user may grant view/edit access only if they are in the `editors` set.

### 3. Customer Restriction (Deny Rule)
- Users with `job == "customer"` may NOT editPresentation.

## Notes
- The Template entity and all template-related actions have been removed.
- Policy is simpler with no market-based template sharing logic.
- Cedar denies by default.
