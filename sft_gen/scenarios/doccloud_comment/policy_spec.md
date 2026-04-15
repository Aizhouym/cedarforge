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
