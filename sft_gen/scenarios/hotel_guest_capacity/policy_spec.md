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
### 5. Guest Capacity Limit (Deny Rule)
- In the schema, `Property` has `currentGuests: Long` (current occupancy) and `maxGuests: Long` (capacity).
- If `resource.currentGuests >= resource.maxGuests`, **createReservation** is **forbidden**
  for ALL principals attempting **createReservation** on that `Property` — members and admins alike.
- This is a hard limit: no role override exists. The host application must update
  `currentGuests` atomically when reservations are created or cancelled.
- All other actions (viewReservation, updateReservation, grantAccess, etc.) are unaffected.

## Notes (Capacity)
- Numeric comparison: `resource.currentGuests >= resource.maxGuests`.
- Both attributes are on the Property entity.
- Compare with `hotel_add_renovation_lock` (boolean forbid) — this uses a numeric threshold
  instead of a boolean flag.
