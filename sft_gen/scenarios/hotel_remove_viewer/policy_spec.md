---
pattern: "remove role"
difficulty: medium
features:
  - franchise hierarchy
  - member/admin roles (no viewer)
  - role simplification
domain: hospitality / hotel chains
source: mutation (hotel domain)
---

# Hotel Chains — Policy Specification (Two-Role Model)

## Context

This policy simplifies the hotel access model to two roles: **member** and **admin**.
The viewer role has been removed. Users who previously had view-only access must now
be granted member access, which implicitly includes view.

Users have:
- `memberPermissions: PermissionsMap` — member role (includes view + edit)
- `hotelAdminPermissions: Set<Hotel>` and `propertyAdminPermissions: Set<Property>`

## Requirements

### 1. Member Permissions (View + Edit)
- A member may **viewReservation**, **updateReservation**, and **createReservation**
  at any Property or Hotel in their `memberPermissions` sets.
- A member may **viewProperty** and **viewHotel** where they have member permissions.
- A member may **updateProperty** and **updateHotel** where they have member permissions.

### 2. Admin Permissions
- An admin may perform all actions including grantAccess at their scoped Hotel/Property.
- Admin implies member for all access purposes.

### 3. Property and Hotel Actions
- **createReservation** on a Property: member or admin.
- **createProperty** on a Hotel: member or admin.
- **createHotel** on a Hotel: admin only.
- **grantAccess*** actions: admin only.

## Notes
- viewPermissions attribute removed; all view access now comes through memberPermissions.
- This simplifies the role model but means all collaborators have edit access.
- Cedar denies by default.
