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
### 5. Partner Company Access
- Properties may have a `partnerCode: String` — a shared secret for authorized travel agencies.
- Context carries `providedPartnerCode: String`.
- If `context.providedPartnerCode == resource.partnerCode` (and the code is non-empty),
  any User may **viewProperty** without needing member or admin role.
- Partners may ONLY **viewProperty** — they cannot viewReservation, createReservation,
  updateReservation, or perform any admin actions.
- The standard member/admin paths for viewProperty still work as before.

## Notes (Partner Access)
- This is a third path for viewProperty: (member role) OR (admin role) OR (valid partner code).
- Empty string partner codes do not grant access; the host app ensures non-empty codes.
- Partner access is for viewProperty only — all reservation operations remain role-gated.
