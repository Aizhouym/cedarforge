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
### 5. MFA Gate for Access Grants (Deny Rule)
- **grantAccessReservation**, **grantAccessProperty**, and **grantAccessHotel** are
  **forbidden** when `context.mfaVerified == false`.
- Admins must present a verified MFA session to grant access to others.
- View, update, and create actions are not restricted by MFA status.
- Context carries `mfaVerified: Bool` set by the authentication layer.

## Notes (MFA Gate)
- The MFA gate is an additional security layer on top of the admin role check.
- Both conditions must hold to grant access: admin role AND mfaVerified.
- Forbid pattern: `forbid ... action in [grantAccessReservation, ...] when { !context.mfaVerified }`.
