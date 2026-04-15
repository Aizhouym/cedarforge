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
