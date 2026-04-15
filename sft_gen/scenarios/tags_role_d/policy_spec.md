---
pattern: "base tag-matching RBAC"
difficulty: medium
features:
  - tag-based access control
  - role-scoped tag namespaces
  - optional tag dimensions
  - ALL wildcard
domain: workspace platform
source: mutation (tags domain)
---

# Tags & Roles Workspace Permissions — Policy Specification

## Context

This policy governs access to Workspaces via tag-based matching scoped by Role.
Users belong to Roles (via `User in [Role]`). Each User has `allowedTagsForRole`
with optional entries for Role-A and Role-B. Each Workspace has `tags` with
optional `production_status`, `country`, and `stage` dimensions (Set<String>).

Access is granted if, for each dimension present in both user and workspace:
- the user's set contains `"ALL"`, OR
- the workspace's set contains `"ALL"`, OR
- the user's set containsAll of the workspace's set.

## Requirements

### 1. Role-A Access
- Users in Role-A may UpdateWorkspace, DeleteWorkspace, ReadWorkspace when
  all tag dimensions match using the containsAll / ALL rule.

### 2. Role-B Access
- Users in Role-B may ReadWorkspace only, using the same tag-matching logic.

## Notes
- Missing optional dimensions pass automatically (no restriction for that dimension).
- Cedar denies by default.
### 3. Role-D Permissions (Write-Only)
- Role-D is an unusual role: users in Role-D with a tag match may **UpdateWorkspace**
  but are explicitly **forbidden** from **ReadWorkspace**.
- This models a "blind write" pattern where Role-D users can push updates to workspaces
  they cannot observe — useful for system/automation accounts.
- Role-D users may NOT DeleteWorkspace.
- Role-D tag matching uses the same containsAll/ALL rule as Role-A and Role-B,
  checking `allowedTagsForRole["Role-D"]`.

## Notes (Role-D — Write-Only)
- This tests an explicit forbid on a read action for a role that has write access.
- The forbid on ReadWorkspace for Role-D must use an `unless` to allow Role-A and Role-B
  members to still read even if they happen to also be in Role-D.
- `forbid ReadWorkspace when principal in Role::"Role-D" unless (principal in Role::"Role-A" || principal in Role::"Role-B")`.
