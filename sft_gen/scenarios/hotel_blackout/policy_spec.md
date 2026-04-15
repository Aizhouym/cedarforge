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
### 5. Blackout Period (Deny Rule)
- Properties may have a `blackoutUntil: datetime` attribute defining a blackout end date.
- If `context.now < resource.blackoutUntil`, the **createReservation** action is **forbidden**
  for ALL principals, including members and admins. No override exists.
- Once the current time exceeds `blackoutUntil`, the property opens normally.
- Properties without `blackoutUntil` (attribute absent) are never blacked out.
  Guard with `resource has blackoutUntil` before comparing.
- `viewReservation`, `updateReservation`, and all other actions are unaffected by blackout.

## Notes (Blackout)
- Cedar datetime comparison: `context.now < resource.blackoutUntil`.
- The `has` guard is required since `blackoutUntil` is effectively optional.
- Context carries `now: datetime` provided by the host application.
