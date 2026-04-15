"""DocCloud domain — new SFT mutations.

Already in cedarbench (excluded):
  doccloud_base, doccloud_add_admin_group, doccloud_add_comment_acl,
  doccloud_add_expiry, doccloud_add_version_lock, doccloud_graduated_sharing,
  doccloud_org_isolation, doccloud_remove_blocking, doccloud_remove_public,
  doccloud_temporal_sharing.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
---
pattern: "base ACL"
difficulty: easy
features:
  - ACL-based sharing
  - owner/viewer/editor roles
  - blocking semantics
domain: document management
source: mutation (doccloud domain)
---

# Document Cloud — Policy Specification

## Context

This policy governs access control for a cloud document management platform
with Documents, Users, Groups, Drives, and DocumentShare entities.

Documents have three ACL attributes (viewACL, modifyACL, manageACL) each
pointing to a DocumentShare. The `publicAccess` String attribute controls
unauthenticated access. The `owner` attribute is the owning User.

## Requirements

### 1. Owner Permissions
- The **owner** may perform ALL actions: ViewDocument, ModifyDocument,
  DeleteDocument, EditIsPrivate, EditPublicAccess, AddToShareACL.

### 2. View ACL
- A user in the document's **viewACL** may **ViewDocument**.

### 3. Modify ACL
- A user in the document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL
- A user in the document's **manageACL** may: AddToShareACL, DeleteDocument,
  EditIsPrivate, EditPublicAccess.

### 5. Public Access
- `publicAccess == "view"` → Public principal may ViewDocument.
- `publicAccess == "edit"` → Public principal may ViewDocument and ModifyDocument.

### 6. Blocking (Deny Rules — Bidirectional)
- If the principal is in the owner's blocked set, or the owner is in the
  principal's blocked set, forbid ViewDocument and ModifyDocument.

### 7. Authentication Requirement (Deny Rule)
- All User actions are forbidden unless `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may DeleteGroup and ModifyGroup.

## Notes
- ACL membership uses Cedar `in` operator: `principal in resource.viewACL`.
- Cedar denies by default.
"""


# ── 1. Folder hierarchy — documents inherit folder permissions (S6+S14+S7+P2+P9) ─

class DocCloudAddFolder(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_add_folder",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add Folder entity; Document in [Folder]; folder-level ViewFolder/ShareFolder actions",
            operators=["S6", "S14", "S7", "P2", "P9"],
            features_tested=["new_entity", "hierarchy_change", "cascade_permit", "cross_traversal"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Folder = {
    owner: User,
    viewACL: DocumentShare,
    modifyACL: DocumentShare,
};""")
        schema = schema_ops.add_action(schema, """\
// Folder actions
action ViewFolder, ShareFolder appliesTo {
    principal: [User, Public],
    resource: [Folder],
    context: {
        "is_authenticated": Bool,
    }
};""")
        spec = _BASE_SPEC + """\
### 9. Folder Entity and Permissions
- Documents may belong to a Folder (`Document in [Folder]`). Permissions on the Folder
  cascade to contained Documents via Cedar's transitive `in` operator.
- A user in a Folder's `viewACL` may **ViewFolder** on that Folder.
- A user who is the Folder's `owner` may **ShareFolder** (manage folder-level sharing).
- A user in a Folder's `modifyACL` may also **ViewFolder** (modify implies view).

### 10. Folder Permission Cascade
- Because Documents are `in` Folders, a user who can view a Folder can also view
  Documents within it via ACL membership: `principal in resource.viewACL` where
  `resource` is a Document whose parent is the Folder that the user is in via viewACL.
  (The ACL check traverses the entity hierarchy automatically.)
- All base Document permissions (owner, modifyACL, manageACL, blocking) still apply.

## Notes (Folder)
- Folder hierarchy allows coarse-grained sharing: add a user to a Folder's viewACL
  to grant them view access to all documents in that folder.
- The authentication gate and blocking rules still apply to folder actions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Viewer cap — AddToShareACL blocked when viewerCount >= maxViewers (S2+P6) ─

class DocCloudViewerCap(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_viewer_cap",
            base_scenario="doccloud",
            difficulty="easy",
            description="Add viewerCount + maxViewers Long to Document; AddToShareACL forbidden when at cap",
            operators=["S2", "P6"],
            features_tested=["numeric_threshold", "resource_side_limit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "viewerCount", "Long")
        schema = schema_ops.add_attribute(schema, "Document", "maxViewers", "Long")
        spec = _BASE_SPEC + """\
### 9. Viewer Cap (Deny Rule)
- Documents have `viewerCount: Long` (current number of users with view access) and
  `maxViewers: Long` (configured limit).
- If `resource.viewerCount >= resource.maxViewers`, the **AddToShareACL** action is
  **forbidden** for all principals, including the owner and manageACL members.
- Other actions (ViewDocument, ModifyDocument, DeleteDocument, etc.) are not affected.
- The cap is enforced at the policy level; the host application updates `viewerCount`
  when users are added or removed from ACLs.

## Notes (Viewer Cap)
- Numeric comparison: `resource.viewerCount >= resource.maxViewers`.
- Both attributes are on the Document; no cross-entity traversal needed.
- The owner cannot bypass this limit — the forbid applies universally.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. Document expiry via datetime (S4 + P1) ─────────────────────────────────

class DocCloudAutoExpiry(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_auto_expiry",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add expiresAt datetime to Document; all access forbidden after expiry",
            operators=["S4", "S8", "P1"],
            features_tested=["datetime_comparison", "universal_forbid", "context_field"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "expiresAt", "datetime")
        # doccloud base has 3 distinct Document-resource action blocks:
        #   solo: ViewDocument, ModifyDocument
        #   grouped: AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess
        # One call per block is enough; add_context_field matches the whole block.
        for action_name in ["ViewDocument", "ModifyDocument", "AddToShareACL"]:
            schema = schema_ops.add_context_field(schema, action_name, "now", "datetime")
        spec = _BASE_SPEC + """\
### 9. Document Auto-Expiry (Deny Rule)
- Documents have an `expiresAt: datetime` attribute. Once the current time exceeds
  `expiresAt`, **all** actions on that document are **forbidden** for all principals
  including the owner.
- Formally: forbid any action when `context.now > resource.expiresAt`.
- Documents without an expiry date (where the attribute is absent) do not expire.
  Guard with `resource has expiresAt` before comparing.
- Context carries `now: datetime` representing the current UTC timestamp.

## Notes (Auto-Expiry)
- Cedar datetime comparison: `context.now > resource.expiresAt`.
- The `has` guard is essential for optional `expiresAt`: if missing, no expiry applies.
- The expiry forbid overrides all permits including owner access — expired docs are
  fully locked regardless of ACL membership.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Device trust gate — modify/delete require trusted device (S8 + P1) ─────

class DocCloudDeviceTrust(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_device_trust",
            base_scenario="doccloud",
            difficulty="easy",
            description="Add deviceTrusted Bool context; ModifyDocument and DeleteDocument forbidden on untrusted devices",
            operators=["S8", "P1"],
            features_tested=["context_gate", "write_protection"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # ModifyDocument is a solo block; DeleteDocument is in the grouped block with
        # AddToShareACL/EditIsPrivate/EditPublicAccess — one call covers all four.
        schema = base_schema
        for action_name in ["ModifyDocument", "DeleteDocument"]:
            schema = schema_ops.add_context_field(schema, action_name, "deviceTrusted", "Bool")
        spec = _BASE_SPEC + """\
### 9. Device Trust Gate (Deny Rule)
- **ModifyDocument** and **DeleteDocument** are **forbidden** when
  `context.deviceTrusted == false`.
- Read actions (ViewDocument) are not restricted by device trust.
- ACL management actions (AddToShareACL, EditIsPrivate, EditPublicAccess) are also
  restricted: they require a trusted device.
- Context provides `deviceTrusted: Bool`, set by the authentication layer based on
  device enrollment status.

## Notes (Device Trust)
- The forbid pattern: `forbid ... action in [ModifyDocument, DeleteDocument, ...]
  when { !context.deviceTrusted }`.
- Blocking and authentication gate still apply independently.
- A user on an untrusted device can still view documents but cannot mutate them.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Document classification — confidential requires manageACL (S3 + P7 + P4) ─

class DocCloudClassification(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_classification",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add classification String; confidential docs: viewACL insufficient, must be in manageACL",
            operators=["S3", "P7", "P4"],
            features_tested=["string_enum", "elevated_permission", "forbid_with_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "classification", "String")
        spec = _BASE_SPEC + """\
### 9. Document Classification (Deny Rule with Exception)
- Documents have a `classification: String` attribute with values:
  `"public"`, `"internal"`, `"confidential"`.
- For **confidential** documents (`classification == "confidential"`):
  - Membership in `viewACL` alone is **insufficient** to view the document.
  - Only the document **owner** or a user in `manageACL` may **ViewDocument** on
    confidential documents. (viewACL grant is overridden.)
  - **ModifyDocument** on confidential documents additionally requires manageACL membership
    (even modifyACL members cannot modify confidential docs without manageACL access).
- For `"internal"` and `"public"` classifications, the base ACL rules apply unchanged.

## Notes (Classification)
- Implement as: `forbid ViewDocument when resource.classification == "confidential"
  unless (principal == resource.owner || principal in resource.manageACL)`.
- This narrows the effective permission for confidential docs: owner or manageACL only.
- The blocking and authentication rules still apply across all classifications.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Comment entity — author-only edit/delete (S6 + S7 + P2 + P10) ─────────

class DocCloudComment(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_comment",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add Comment entity; document viewers can add comments; only comment author can edit/delete",
            operators=["S6", "S7", "P2", "P9", "P10"],
            features_tested=["new_entity", "cross_traversal", "self_exclusion", "author_ownership"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Comment = {
    document: Document,
    author: User,
};""")
        schema = schema_ops.add_action(schema, """\
// Comment actions
action AddComment, EditComment, DeleteComment appliesTo {
    principal: [User],
    resource: [Comment],
    context: {
        "is_authenticated": Bool,
    }
};""")
        spec = _BASE_SPEC + """\
### 9. Comment Permissions
- Any user who can **ViewDocument** on a comment's parent document may **AddComment**.
  (Check: `principal in resource.document.viewACL` OR `principal == resource.document.owner`, etc.)
- Only the **author** of a comment may **EditComment** or **DeleteComment** that comment.
- Document owners and manageACL members may also **DeleteComment** on any comment in their document.
- Comments inherit the blocking rule: if the commenter is blocked by the document owner (or vice versa),
  viewing/adding comments is also blocked.

## Notes (Comments)
- AddComment: viewACL (or owner or modifyACL or manageACL) on the parent document.
- EditComment: `principal == resource.author` only.
- DeleteComment: `principal == resource.author` OR `principal == resource.document.owner`
  OR `principal in resource.document.manageACL`.
- Cross-entity traversal for document ownership: `resource.document.owner`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Draft documents — only owner can view/modify drafts (S1 + P1 + P4) ────

class DocCloudDraft(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_draft",
            base_scenario="doccloud",
            difficulty="easy",
            description="Add isDraft Bool to Document; draft docs visible only to owner; manageACL can also view",
            operators=["S1", "P1", "P4"],
            features_tested=["boolean_forbid", "owner_exclusivity", "unless_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "isDraft", "Bool")
        spec = _BASE_SPEC + """\
### 9. Draft Document Restriction (Deny Rule with Exception)
- If a document has `isDraft == true`:
  - **ViewDocument** is **forbidden** for all principals EXCEPT:
    - The document's **owner**, OR
    - A user in the document's **manageACL** (editors who have been explicitly granted draft access).
  - **ModifyDocument** is forbidden for all principals except the owner.
  - All share/ACL management actions are also forbidden on drafts — a draft cannot be
    shared until it is published.
- Publishing (setting `isDraft` to `false`) is an EditIsPrivate-equivalent action controlled
  by the owner only. No separate "publish" action is modeled — the host app updates the attribute.

## Notes (Draft)
- The forbid pattern: `forbid ... when { resource.isDraft } unless { principal == resource.owner }`.
- Draft restriction is orthogonal to `isPrivate` — a document can be both draft and private.
- Blocking rules still apply: even the owner cannot view a draft if mutually blocked.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Link sharing — context token grants view (S3 + S8 + P2) ───────────────

class DocCloudLinkShare(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_link_share",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add shareToken String to Document; context providedToken grants ViewDocument if tokens match",
            operators=["S3", "S8", "P2"],
            features_tested=["string_comparison", "context_permit", "link_based_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "shareToken", "String")
        schema = schema_ops.add_context_field(schema, "ViewDocument", "providedToken", "String")
        spec = _BASE_SPEC + """\
### 9. Link-Based Sharing (Token Grant)
- Documents have a `shareToken: String` attribute (a shareable URL token set by the owner).
- Context carries `providedToken: String` — the token value the requester presents.
- If `context.providedToken == resource.shareToken`, then **any** User (or Public principal)
  may **ViewDocument**, regardless of ACL membership.
- Token access grants ViewDocument ONLY — not ModifyDocument, DeleteDocument, or ACL management.
- The authentication gate still applies to User principals with token access.
- The blocking rule applies to User principals: a blocked user cannot use a token to view
  a document owned by the user who blocked them.

## Notes (Link Share)
- The token permit is a third path for ViewDocument: ACL, owner, OR valid token.
- Empty shareToken string (`""`) should not grant access; the host app ensures tokens are
  non-empty before setting them. The policy matches exact string equality.
- Public principals can use token access without authentication (subject to is_authenticated
  check not applying to Public principal type).
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Read-only ACL — separate from viewACL, no modify path (S9 + P2) ────────

class DocCloudReadOnlyACL(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_read_only_acl",
            base_scenario="doccloud",
            difficulty="easy",
            description="Add readOnlyACL DocumentShare; readOnly members can view but are explicitly barred from modify",
            operators=["S9", "P2", "P1"],
            features_tested=["new_acl_tier", "explicit_forbid", "acl_separation"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "readOnlyACL", "DocumentShare")
        spec = _BASE_SPEC + """\
### 9. Read-Only ACL
- Documents have a fourth ACL attribute: `readOnlyACL: DocumentShare`.
- A user in the document's **readOnlyACL** may **ViewDocument** — same as viewACL.
- However, unlike viewACL, readOnlyACL membership is accompanied by an explicit
  **forbid** on ModifyDocument. Even if the user is also in modifyACL, readOnlyACL
  membership triggers a forbid on Modify.
- This models a "view-only with explicit lock" pattern: administrators can grant view
  access while simultaneously ensuring the user cannot edit, regardless of other ACL membership.
- The owner can override the readOnlyACL forbid — owner permission is never blocked by ACLs.

## Notes (Read-Only ACL)
- Two separate permits: `principal in resource.viewACL` OR `principal in resource.readOnlyACL` → ViewDocument.
- Explicit forbid: `principal in resource.readOnlyACL` → forbid ModifyDocument.
- The forbid takes priority over any modifyACL permit for read-only members.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 10. Org-scoped context — cross-org view forbidden (S8 + P1) ───────────────

class DocCloudOrgContext(Mutation):
    def meta(self):
        return MutationMeta(
            id="doccloud_org_context",
            base_scenario="doccloud",
            difficulty="medium",
            description="Add ownerOrg String to Document; context userOrg; cross-org ViewDocument forbidden unless manageACL",
            operators=["S3", "S8", "P1", "P4"],
            features_tested=["context_gate", "org_isolation", "string_comparison", "unless_exception"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Document", "ownerOrg", "String")
        # Add userOrg to all Document-resource action blocks (one call per block).
        # ViewDocument and ModifyDocument are solo blocks; AddToShareACL covers the
        # grouped block (AddToShareACL, DeleteDocument, EditIsPrivate, EditPublicAccess).
        for action_name in ["ViewDocument", "ModifyDocument", "AddToShareACL"]:
            schema = schema_ops.add_context_field(schema, action_name, "userOrg", "String")
        spec = _BASE_SPEC + """\
### 9. Organization Scope Gate (Deny Rule with Exception)
- Documents have an `ownerOrg: String` attribute identifying the owning organization.
- Context carries `userOrg: String` — the organization of the requesting user.
- If `context.userOrg != resource.ownerOrg`, **ViewDocument**, **ModifyDocument**, and all
  other Document write actions are **forbidden** UNLESS the user is in the document's
  **manageACL** (cross-org access requires explicit elevation).
- ModifyDocument and other write actions are also forbidden cross-org without manageACL.
- The blocking rule applies as before.

## Notes (Org Context)
- This differs from `doccloud_org_isolation` which uses a `User.org` attribute.
  Here the org is provided via context (no User entity attribute change needed).
- Cross-org users with manageACL membership can still access the document; this is the
  "unless" exception for cross-org collaboration.
- String equality: `context.userOrg != resource.ownerOrg` triggers the forbid.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    DocCloudAddFolder(),
    DocCloudViewerCap(),
    DocCloudAutoExpiry(),
    DocCloudDeviceTrust(),
    DocCloudClassification(),
    DocCloudComment(),
    DocCloudDraft(),
    DocCloudLinkShare(),
    DocCloudReadOnlyACL(),
    DocCloudOrgContext(),
]

for _m in MUTATIONS:
    register(_m)
