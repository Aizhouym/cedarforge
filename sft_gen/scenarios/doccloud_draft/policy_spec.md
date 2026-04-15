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
