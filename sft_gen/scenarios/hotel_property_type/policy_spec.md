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
### 5. Property Type Restriction
- Properties have `propertyType: String` with values: `"standard"`, `"resort"`, `"boutique"`.
- For **boutique** properties (`propertyType == "boutique"`):
  - **grantAccessProperty** is restricted to **admin** role only (hotel or property admin).
  - Member role is insufficient to grantAccess on boutique properties, even though members
    can grantAccess on standard and resort properties per the base rules.
- For `"standard"` and `"resort"` types, the base access rules apply unchanged.
- createReservation, viewProperty, updateProperty are not affected by property type.

## Notes (Property Type)
- Implement as: `forbid grantAccessProperty when resource.propertyType == "boutique"`
  with an `unless` clause for admin role holders.
- The admin check traverses: `resource in principal.hotelAdminPermissions ||
  resource in principal.propertyAdminPermissions`.
