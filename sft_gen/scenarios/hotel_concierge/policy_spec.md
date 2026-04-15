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
### 5. Concierge Role
- Users may have `conciergePermissions: PermissionsMap` defining properties and hotels
  where they act as concierge staff.
- A user with concierge permissions for a Reservation's Property or Hotel may:
  - **createReservation** on that Property (or any property of that Hotel)
  - **viewReservation** on reservations at that Property/Hotel
  - **updateReservation** on reservations at that Property/Hotel
- A concierge may NOT **grantAccessReservation**, **grantAccessProperty**, or
  **grantAccessHotel**. Access grant actions remain admin-only.
- Concierge is an additive role: if a user also has member or admin permissions,
  they get the union of all permissions.

## Notes (Concierge)
- Concierge permissions use the same PermissionsMap type as viewPermissions/memberPermissions.
- Checking: `resource in principal.conciergePermissions.propertyReservations` (for property scope)
  or `resource in principal.conciergePermissions.hotelReservations` (for hotel scope).
- The grantAccess exclusion is important: concierge is NOT an admin role.
