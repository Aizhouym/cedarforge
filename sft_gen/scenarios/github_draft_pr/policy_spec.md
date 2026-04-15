---
pattern: "base RBAC"
difficulty: easy
features:
  - entity hierarchy (User/Team)
  - role-based permissions
  - archive blocking
domain: software development
source: mutation (github domain)
---

# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have five role tiers, represented as UserGroup attributes:
readers, triagers, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 4. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 5. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 6. Archived Repository Block (Deny Rule)
- If a repository is archived (`isArchived == true`), no **write operations** are allowed.
  Write operations include: push, add_reader, add_writer, add_maintainer, add_admin, add_triager.
- Read operations (pull, fork) remain allowed on archived repos.
- Issue operations are unaffected by archive status.

## Notes
- Roles are checked via entity group membership: `principal in resource.readers` (for repo actions)
  or `principal in resource.repo.readers` (for issue actions, traversing Issue → Repository).
- There is no explicit deny-by-default policy needed — Cedar denies by default.
### 7. Pull Request Permissions
- A **writer** (or above: maintainer, admin) of the PR's repository may **merge_pr**.
- A **reader** (or above) of the PR's repository may **approve_pr**.
- Role is checked via cross-entity traversal: `principal in resource.repo.writers`, etc.
- The **author** of a pull request may NOT **approve_pr** their own PR (self-approval forbidden).
- Merging is blocked on archived repositories (same as push).

### 8. Draft PR Block (Deny Rule)
- If a pull request has `isDraft == true`, the **merge_pr** action is **forbidden** for all users,
  including maintainers and admins.
- Draft PRs can still be approved (approve_pr is not blocked by draft status).
- Only after `isDraft` becomes `false` (PR published) can it be merged.

## Notes (Draft PR)
- Two independent forbid rules interact: archive block (on merge_pr via repo traversal)
  and draft block (on merge_pr via isDraft flag).
- Self-exclusion for approve_pr: `forbid ... when { principal == resource.author }`.
