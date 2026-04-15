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
### 3. Report Permissions
- Reports are linked to Workspaces (`Report.workspace: Workspace`).
- **generateReport**: Only Role-A users who have a full tag match on the linked Workspace
  may generate a report. The tag match is evaluated against `resource.workspace.tags`.
  (Cross-entity traversal: `resource.workspace.tags`.)
- **viewReport**: Role-A and Role-B users with a tag match on the linked Workspace may
  view a report.
- If `resource.isConfidential == true`, **viewReport** is restricted to Role-A users only.
  Role-B users cannot view confidential reports.

## Notes (Report)
- generateReport requires Role-A membership (not Role-B).
- The workspace tag check for Reports uses cross-entity traversal: the Report's workspace
  tags must match the user's allowed tags.
- isConfidential creates a split between Role-A and Role-B for viewReport.
