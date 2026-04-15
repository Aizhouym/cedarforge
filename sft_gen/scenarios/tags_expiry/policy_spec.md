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
### 3. Workspace Expiry (Deny Rule)
- Workspaces may have an `expiresAt: datetime` attribute.
- If `context.now > resource.expiresAt`, ALL actions on the workspace are **forbidden**
  for ALL users regardless of role or tag match.
- Workspaces without `expiresAt` (attribute absent) never expire.
  Guard: `resource has expiresAt` before comparing.
- Context carries `now: datetime` from the host application.

## Notes (Expiry)
- Cedar datetime comparison: `context.now > resource.expiresAt`.
- The `has` guard is critical for the optional attribute pattern.
- Expiry is orthogonal to the tag-matching access logic — even a perfect tag match
  cannot access an expired workspace.
