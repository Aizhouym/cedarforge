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
