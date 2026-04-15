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
### 3. Production Environment Restriction
- Workspaces have an `environment: String` attribute: `"dev"`, `"staging"`, `"production"`.
- For **production** workspaces (`environment == "production"`):
  - **UpdateWorkspace** and **DeleteWorkspace** require that the user's
    `allowedTagsForRole["Role-A"]` explicitly includes a `production_status` set
    (not absent). An absent `production_status` on the user's tags does NOT grant
    access to production workspaces for write operations.
  - **ReadWorkspace** is not additionally restricted by environment.
- For dev and staging environments, the standard tag-matching rules apply (absent
  dimensions still pass).

## Notes (Environment)
- Production gate: `resource.environment == "production"` triggers the stricter check.
- The stricter check: `principal.allowedTagsForRole has "Role-A"` AND
  `principal.allowedTagsForRole["Role-A"] has production_status` — must be present.
- String comparison for environment: `resource.environment == "production"`.
