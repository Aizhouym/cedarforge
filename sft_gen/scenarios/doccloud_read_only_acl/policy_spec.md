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
