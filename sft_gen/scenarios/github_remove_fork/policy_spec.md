---
pattern: "remove action"
difficulty: easy
features:
  - entity hierarchy (User/Team)
  - role-based permissions
  - archive blocking
  - fork removed
domain: software development
source: mutation (github domain)
---

# GitHub Repository Permissions — Policy Specification (No Fork)

## Context

This policy governs access control for a GitHub-like platform. Forking is not
supported on this deployment; the `fork` action has been removed entirely.

Repositories have five role tiers: readers, triagers, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** may **pull** a repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter**.

### 2. Triager Permissions
- A **triager** may **assign** issues.

### 3. Writer Permissions
- A **writer** may **push** to a repository and **edit** any issue.

### 4. Maintainer Permissions
- A **maintainer** may **delete** any issue.

### 5. Admin Permissions
- An **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 6. Archived Repository Block (Deny Rule)
- If `isArchived == true`, write operations are forbidden (push, add_*).
- Pull remains allowed on archived repos. Issue operations are unaffected.

## Notes
- The `fork` action does not exist in this variant — no permit or forbid for it is needed.
- All role checks use the same entity group membership pattern as the base.
