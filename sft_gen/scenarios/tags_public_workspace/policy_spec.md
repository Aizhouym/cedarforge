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
### 3. Public Workspace Open Read
- If `resource.isPublic == true`, any User (regardless of Role-A or Role-B membership,
  and without any tag matching) may **ReadWorkspace**.
- **UpdateWorkspace** and **DeleteWorkspace** still require Role-A membership AND
  tag matching — the `isPublic` flag only relaxes ReadWorkspace.
- The public read path is a second permit for ReadWorkspace alongside the existing
  tag-based Role-A/Role-B permits.

## Notes (Public Workspace)
- Implement as an additional permit: `permit ReadWorkspace when resource.isPublic`.
- The existing role-and-tag-based permits remain for non-public workspaces.
- This is a common "published/shared" pattern in workspace platforms.
