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
