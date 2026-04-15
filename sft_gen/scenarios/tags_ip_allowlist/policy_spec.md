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
### 3. IP Allowlist Gate (Deny Rule)
- Users may have an `allowedIPs: Set<String>` attribute listing permitted IP addresses.
- Context carries `clientIP: String` (the requester's IP address).
- If the user has a non-empty `allowedIPs` set AND `!principal.allowedIPs.contains(context.clientIP)`,
  **UpdateWorkspace** and **DeleteWorkspace** are **forbidden**.
- Users with an empty `allowedIPs` set have no IP restriction (open access).
- ReadWorkspace is not restricted by IP allowlist.

## Notes (IP Allowlist)
- Guard: `principal.allowedIPs` must be non-empty before applying the restriction.
  An empty set means "no IP restriction."
- Set containment: `principal.allowedIPs.contains(context.clientIP)`.
- This tests a principal-side set attribute checked against a context string value.
