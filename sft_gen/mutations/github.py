"""GitHub domain — new SFT mutations.

None of these overlap with cedarbench scenarios:
  github_base, github_add_private, github_add_close_issue, github_remove_triager,
  github_add_locked_issue, github_no_archive, github_add_pullrequest,
  github_add_contributor, github_private_and_locked, github_add_visibility,
  github_add_security_admin, github_pr_review_workflow, github_full_expansion,
  github_numeric_constraints.

Operator key (schema / policy):
  S1=add Bool attr  S2=add Long attr  S3=add String attr  S4=add datetime attr
  S5=add Set<E> attr  S6=add entity  S7=add action  S8=add context field
  S9=add UserGroup attr  S10=remove attr  S11=remove entity  S12=remove action
  S13=add typedef  S14=modify hierarchy
  P1=forbid(bool)  P2=permit(new)  P3=remove permit  P4=unless exception
  P5=dual-path  P6=numeric forbid  P7=string-enum condition  P8=role redist
  P9=cross-entity traversal  P10=self-exclusion forbid
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
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
"""


# ── 1. SSO gate on admin actions (S8 + P1) ───────────────────────────────────

class GitHubSsoGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_sso_gate",
            base_scenario="github",
            difficulty="easy",
            description="Add ssoVerified Bool context; all role-management (add_*) forbidden unless SSO verified",
            operators=["S8", "P1"],
            features_tested=["context_gate", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # All 5 role-management actions share ONE appliesTo block in the base schema.
        # A single add_context_field call on any of them updates the shared block.
        schema = schema_ops.add_context_field(base_schema, "add_reader", "ssoVerified", "Bool")
        spec = _BASE_SPEC + """\
### 7. SSO Verification Gate (Deny Rule)
- All **role-management** actions (add_reader, add_triager, add_writer, add_maintainer, add_admin)
  are **forbidden** unless `context.ssoVerified == true`.
- This applies regardless of the principal's admin role. Even an admin cannot add collaborators
  without a verified SSO session.
- Read and write operations (pull, fork, push, issue actions) are unaffected by SSO status.

## Notes (SSO Gate)
- The SSO check is enforced via a `forbid` with a `when { !context.ssoVerified }` clause.
- Context is only declared on the role-management action group; other actions have no context requirement.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Watcher role — pull only, no fork (S9 + P2) ───────────────────────────

class GitHubWatcher(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_watcher",
            base_scenario="github",
            difficulty="easy",
            description="Add watchers UserGroup to Repository; watchers can pull but NOT fork",
            operators=["S9", "P2"],
            features_tested=["new_role", "fine_grained_permit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "watchers", "UserGroup")
        spec = _BASE_SPEC + """\
### 7. Watcher Permissions
- A user who is a **watcher** of a repository may **pull** that repository.
- A watcher may NOT **fork** a repository (read without clone rights).
- A watcher has no issue, push, or admin permissions.
- Watcher is a lighter-weight role than reader: reader can pull AND fork; watcher can only pull.

## Notes (Watcher Role)
- Watchers are stored in `resource.watchers` (a UserGroup), checked via `principal in resource.watchers`.
- Reader role still grants both pull AND fork; the watcher role is additive and separate.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. Public repository — anonymous pull (S1 + P2) ──────────────────────────

class GitHubPublicRepo(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_public_repo",
            base_scenario="github",
            difficulty="easy",
            description="Add isPublic Bool to Repository; public repos allow any User to pull without reader membership",
            operators=["S1", "P2"],
            features_tested=["boolean_permit", "open_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "isPublic", "Bool")
        spec = _BASE_SPEC + """\
### 7. Public Repository Open Read
- If a repository has `isPublic == true`, then **any** authenticated User may **pull** that repository,
  regardless of whether they are in the `readers` group.
- **fork** is still restricted to users in the `readers` group even on public repositories.
- All write and admin operations remain role-gated regardless of `isPublic`.
- The archived block still applies: a public archived repo cannot be pushed to.

## Notes (Public Repos)
- This adds a second path for the `pull` permit: role-based OR public flag.
- Combine carefully with the archive forbid — the archive forbid blocks push, not pull.
- `isPublic == false` (or absent) means the repo behaves as the base scenario.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Remove fork action entirely (S12 + P3) ────────────────────────────────

class GitHubRemoveFork(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_remove_fork",
            base_scenario="github",
            difficulty="easy",
            description="Remove fork action from schema and all permits; platform does not support forking",
            operators=["S12", "P3"],
            features_tested=["action_removal", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_action(base_schema, "fork")
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Issue severity — maintainer-only delete on critical (S3 + P7 + P8) ────

class GitHubIssueSeverity(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_issue_severity",
            base_scenario="github",
            difficulty="medium",
            description="Add severity String to Issue; critical issues can only be deleted by maintainers, not readers",
            operators=["S3", "P7", "P8"],
            features_tested=["string_enum", "role_redistribution", "conditional_permit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Issue", "severity", "String")
        spec = _BASE_SPEC + """\
### 7. Issue Severity Restriction
- Issues have a `severity` attribute with values: `"low"`, `"medium"`, `"high"`, `"critical"`.
- For issues with `severity == "critical"`:
  - **delete_issue** may only be performed by a **maintainer** of the issue's repository.
  - Readers who are the issue reporter may NOT delete critical issues, unlike lower-severity issues.
- For issues with `severity != "critical"` (low, medium, high):
  - The base dual-path delete rule applies: maintainer OR reporter-reader.
- The `edit_issue` permission is not affected by severity — writers can edit any issue regardless.

## Notes (Severity)
- This restricts the reader-reporter dual-path for `delete_issue` on critical issues only.
- Implement as: forbid delete_issue when `resource.severity == "critical"` unless principal is maintainer.
- String comparison: `resource.severity == "critical"` must be exact.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Team admin — limited admin role (S9 + P2 + P4) ────────────────────────

class GitHubTeamAdmin(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_team_admin",
            base_scenario="github",
            difficulty="medium",
            description="Add teamAdmins UserGroup; teamAdmins can add_reader/add_writer but NOT add_maintainer/add_admin",
            operators=["S9", "P2", "P4"],
            features_tested=["partial_admin", "role_hierarchy", "permit_scoping"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "teamAdmins", "UserGroup")
        spec = _BASE_SPEC + """\
### 7. Team Admin Permissions (Limited Admin)
- A user in the repository's **teamAdmins** group may perform **add_reader** and **add_writer**.
- Team admins may NOT perform **add_maintainer**, **add_admin**, or **add_triager**.
- Full admins (in `resource.admins`) retain all role-management permissions as before.
- The archived block applies to team admins the same as regular admins: add_reader/add_writer
  are blocked on archived repositories.

## Notes (Team Admin)
- This introduces a two-tier admin model: teamAdmin (limited) and admin (full).
- teamAdmin: `principal in resource.teamAdmins` → permits add_reader, add_writer only.
- Regular admin: `principal in resource.admins` → permits all add_* actions.
- The two groups are checked independently; a user in both gets the union of permissions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Push allowlist — explicit set-based push (S5 + P2) ────────────────────

class GitHubPushAllowlist(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_push_allowlist",
            base_scenario="github",
            difficulty="medium",
            description="Add pushAllowlist Set<User> to Repository; allowlisted users can push even without writer role",
            operators=["S5", "P2"],
            features_tested=["set_membership_permit", "dual_path_push"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "pushAllowlist", "Set<User>")
        spec = _BASE_SPEC + """\
### 7. Push Allowlist (Explicit Set Permit)
- A user may **push** to a repository if they are in the repository's `pushAllowlist`
  set, regardless of whether they are in the `writers` group.
- Users in the `writers` group may also push (existing rule unchanged).
- The allowlist is a flat `Set<User>` — no group hierarchy, just direct user references.
- The **archived block** applies to allowlisted users the same as writers: push is forbidden
  on archived repositories regardless of allowlist membership.

## Notes (Push Allowlist)
- This creates a dual-path for push: `principal in resource.writers` OR
  `resource.pushAllowlist.contains(principal)`.
- Allowlist takes precedence in the permit sense but cannot override the archive forbid.
- Unlike UserGroup (which uses entity hierarchy), Set<User> uses `.contains()` for membership.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Draft PR — isDraft blocks merge, self-approval forbidden (S6+S7+P1+P10) ─

class GitHubDraftPR(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_draft_pr",
            base_scenario="github",
            difficulty="medium",
            description="Add PullRequest{isDraft:Bool}; draft PRs cannot be merged; author cannot approve own PR",
            operators=["S6", "S7", "P1", "P2", "P9", "P10"],
            features_tested=["new_entity", "boolean_forbid", "self_exclusion", "cross_traversal"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity PullRequest = {
    repo: Repository,
    author: User,
    isDraft: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Pull request actions
action merge_pr, approve_pr appliesTo {
    principal: [User],
    resource: [PullRequest],
};""")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Deployment entity — deploy action, env-scoped (S6+S7+P2+P9+P1) ────────

class GitHubDeployEnv(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_deploy_env",
            base_scenario="github",
            difficulty="medium",
            description="Add Deployment{env:String}; deploy action; only maintainers deploy; prod blocked on archived",
            operators=["S6", "S7", "S3", "P2", "P9", "P1"],
            features_tested=["new_entity", "cross_traversal", "string_enum", "forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Deployment = {
    repo: Repository,
    env: String,
};""")
        schema = schema_ops.add_action(schema, """\
// Deployment actions
action deploy appliesTo {
    principal: [User],
    resource: [Deployment],
};""")
        spec = _BASE_SPEC + """\
### 7. Deployment Permissions
- A **maintainer** (or admin) of the deployment's repository may **deploy**.
- Role is checked via cross-entity traversal: `principal in resource.repo.maintainers`.
- Writers and below cannot deploy to any environment.

### 8. Production Deploy Block (Deny Rule)
- If the deployment targets the production environment (`resource.env == "production"`) AND
  the repository is archived (`resource.repo.isArchived == true`), the **deploy** action
  is **forbidden** even for maintainers.
- Deployments to `"staging"` or `"dev"` environments on archived repos are still allowed.

## Notes (Deployment)
- Deployment is a new entity type with a reference back to its Repository.
- The production+archive combined forbid requires both conditions to hold simultaneously.
- Environment values are strings: `"production"`, `"staging"`, `"dev"`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 10. Release entity — self cannot delete own release (S6+S7+P2+P9+P10) ────

class GitHubRelease(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_release",
            base_scenario="github",
            difficulty="medium",
            description="Add Release entity; maintainers create; author cannot delete own release (self-exclusion)",
            operators=["S6", "S7", "P2", "P9", "P10"],
            features_tested=["new_entity", "cross_traversal", "self_exclusion"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Release = {
    repo: Repository,
    author: User,
};""")
        schema = schema_ops.add_action(schema, """\
// Release actions
action create_release, delete_release appliesTo {
    principal: [User],
    resource: [Release],
};""")
        spec = _BASE_SPEC + """\
### 7. Release Permissions
- A **maintainer** (or admin) of the release's repository may **create_release**.
- A **maintainer** (or admin) may **delete_release**, EXCEPT the author of the release
  cannot delete their own release (self-exclusion policy).
- Writers and below have no release management permissions.
- Release permissions require cross-entity traversal: `principal in resource.repo.maintainers`.

## Notes (Release Self-Exclusion)
- The self-exclusion forbid: `forbid ... action == delete_release ... when { principal == resource.author }`.
- This means a maintainer who authored a release cannot delete it — another maintainer must.
- create_release is NOT self-excluded: a maintainer can create and publish their own release.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 11. Rate-limit push per repo (S2 + P6) ───────────────────────────────────

class GitHubRepoPushLimit(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_repo_push_limit",
            base_scenario="github",
            difficulty="hard",
            description="Add dailyPushCount + maxDailyPushes Long to Repository; push forbidden when count >= limit",
            operators=["S2", "S2", "P6"],
            features_tested=["numeric_comparison", "resource_side_threshold"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "dailyPushCount", "Long")
        schema = schema_ops.add_attribute(schema, "Repository", "maxDailyPushes", "Long")
        spec = _BASE_SPEC + """\
### 7. Repository Push Rate Limit (Deny Rule)
- If a repository's `dailyPushCount >= maxDailyPushes`, the **push** action is **forbidden**
  for all users, including writers, maintainers, and admins.
- This is a per-repository limit tracked externally and stored as attributes on the Repository entity.
- The limit resets at the start of each UTC day (reset is handled by the host application, not policy).
- The archive block and push-rate-limit are independent forbids; either alone is sufficient to block push.

## Notes (Push Rate Limit)
- Numeric comparison: `resource.dailyPushCount >= resource.maxDailyPushes`.
- Both attributes are on the same entity (Repository); no cross-entity traversal needed.
- Compare with the base `github_numeric_constraints` scenario which uses: (a) a collaborator cap
  on add_* actions, and (b) a user-side account-age gate on push. This scenario uses a
  resource-side rate cap on push.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 12. Full expansion v2 — watcher + deploy + severity (compound) ────────────

class GitHubFullExpansionV2(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_full_expansion_v2",
            base_scenario="github",
            difficulty="hard",
            description="Compound: watcher role + Deployment entity + issue severity + push allowlist; 4 mutations",
            operators=["S9", "S6", "S7", "S3", "S5", "P2", "P2", "P7", "P8", "P9"],
            features_tested=["multi_mutation", "new_entity", "string_enum", "set_permit", "role_hierarchy"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add watcher role
        schema = schema_ops.add_attribute(base_schema, "Repository", "watchers", "UserGroup")
        # Add push allowlist
        schema = schema_ops.add_attribute(schema, "Repository", "pushAllowlist", "Set<User>")
        # Add severity to Issue
        schema = schema_ops.add_attribute(schema, "Issue", "severity", "String")
        # Add Deployment entity + deploy action
        schema = schema_ops.add_entity(schema, """\
entity Deployment = {
    repo: Repository,
    env: String,
};""")
        schema = schema_ops.add_action(schema, """\
action deploy appliesTo {
    principal: [User],
    resource: [Deployment],
};""")
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    GitHubSsoGate(),
    GitHubWatcher(),
    GitHubPublicRepo(),
    GitHubRemoveFork(),
    GitHubIssueSeverity(),
    GitHubTeamAdmin(),
    GitHubPushAllowlist(),
    GitHubDraftPR(),
    GitHubDeployEnv(),
    GitHubRelease(),
    GitHubRepoPushLimit(),
    GitHubFullExpansionV2(),
]

for _m in MUTATIONS:
    register(_m)
