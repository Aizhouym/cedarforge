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
### 5. Premium Property Access (Deny Rule)
- Properties may be marked `isPremium: Bool`. Premium properties require the user to
  have accumulated at least **5000 loyalty points**.
- If `resource.isPremium == true` AND `principal.loyaltyPoints < 5000`, **createReservation**
  is **forbidden** for member-role users.
- Admin-role users bypass the loyalty restriction and can always createReservation
  regardless of loyalty points.
- The loyalty check applies only to createReservation; view and update are unaffected.

## Notes (Loyalty Points)
- This uses a numeric attribute on the principal (`loyaltyPoints`) combined with a boolean
  on the resource (`isPremium`). The condition is a cross-entity attribute comparison.
- Implement as: `forbid createReservation when resource.isPremium && principal.loyaltyPoints < 5000`
  with an `unless` clause for admin role.
- Compare with `hotel_add_loyalty_tier` (cedarbench) which uses a String tier enum.
  This variant uses raw numeric points.
