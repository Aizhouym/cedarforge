---
pattern: "base franchise-hierarchy"
difficulty: easy
features:
  - franchise hierarchy
  - viewer/member/admin roles
  - attribute-based permissions
domain: hospitality / hotel chains
source: mutation (hotel domain)
---

# Hotel Chains — Policy Specification

## Context

This policy governs access control for a hotel chain with Hotels, Properties,
Reservations, and Users. The hierarchy is: Hotel → Property → Reservation.

Users have three permission tiers stored as attributes:
- `viewPermissions: PermissionsMap` — view role (hotelReservations, propertyReservations sets)
- `memberPermissions: PermissionsMap` — member/editor role
- `hotelAdminPermissions: Set<Hotel>` and `propertyAdminPermissions: Set<Property>`

## Requirements

### 1. View Permissions (Reservations)
- viewReservation permitted if `resource in principal.viewPermissions.hotelReservations`
  OR `resource in principal.viewPermissions.propertyReservations` (or member/admin equivalent).

### 2. Member Permissions
- updateReservation and createReservation permitted for member or admin role holders.

### 3. Admin Permissions
- grantAccessReservation, grantAccessProperty, grantAccessHotel permitted for admin only.

### 4. Property and Hotel Actions
- Standard view/update/grantAccess pattern mirrors reservations, scoped to Property or Hotel.
- createReservation on Property, createProperty on Hotel: member or admin role required.

## Notes
- Cedar entity hierarchy: `Reservation in Property in Hotel` — transitive `in` is used.
- Admin sets cover both hotel-level and property-level scopes.
- Cedar denies by default.
### 5. Guest Blocklist (Deny Rule)
- Properties may have a `blockedGuests: Set<User>` attribute listing users who are
  banned from making reservations at that property.
- If `resource.blockedGuests.contains(principal)`, the **createReservation** action is
  **forbidden** for that user, regardless of their member or admin role.
- Admins who are in the blockedGuests list cannot createReservation at that property,
  but they retain grantAccess and management permissions (blocklist only affects reservations).
- viewProperty, updateProperty, and other actions are unaffected.

## Notes (Guest Blocklist)
- Set containment: `resource.blockedGuests.contains(principal)`.
- Unlike UserGroup membership (entity hierarchy), Set<User> uses `.contains()`.
- Admins are not excepted from the reservation block but retain all non-reservation permissions.
