---
pattern: "compound mutation"
difficulty: hard
features:
  - watcher role (pull-only)
  - push allowlist (Set<User>)
  - issue severity (string enum)
  - deployment entity + env
domain: software development
source: mutation (github domain)
---

# GitHub Repository Permissions — Policy Specification (Full Expansion v2)

## Context

This policy extends the GitHub base with four simultaneous mutations:
a lightweight watcher role, an explicit push allowlist, issue severity levels,
and a Deployment entity for environment-scoped deploys.

Repositories: readers, triagers, writers, maintainers, admins, watchers (UserGroup),
pushAllowlist (Set<User>), isArchived (Bool).
Issues: repo, reporter, severity (String: "low"/"medium"/"high"/"critical").
Deployments: repo (Repository), env (String: "dev"/"staging"/"production").

## Requirements

### 1. Watcher Permissions
- A **watcher** may **pull** a repository. Watchers cannot fork, push, or manage issues.

### 2. Reader Permissions
- A **reader** may **pull** and **fork**. A reader may delete/edit issues they reported.

### 3. Triager, Writer, Maintainer, Admin Permissions
- Unchanged from base scenario.

### 4. Push Allowlist
- A user in `resource.pushAllowlist` may **push** (in addition to writers).
- Archive block still applies to allowlisted users.

### 5. Issue Severity Restriction
- For **critical** severity issues, **delete_issue** is restricted to maintainers only.
- Reader-reporter dual-path is blocked for critical issues.

### 6. Deployment Permissions
- A **maintainer** or **admin** of the deployment's repository may **deploy**.
- Deploy to `"production"` is forbidden when the repository is archived.

### 7. Archived Repository Block (Deny Rule)
- If `isArchived == true`, push + all add_* + production deploy are forbidden.

## Notes
- Four mutations compose independently; no interaction between severity and deploy rules.
- Watcher is a UserGroup (entity hierarchy); pushAllowlist is a Set<User> (set containment).
