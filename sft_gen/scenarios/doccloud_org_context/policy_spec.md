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
