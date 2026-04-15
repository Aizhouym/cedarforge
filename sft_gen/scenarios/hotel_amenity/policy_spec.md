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
### 5. Amenity Permissions
- Amenities belong to Properties (`Amenity in [Property]`).
- A user with **member** or **admin** role at the Amenity's containing Property (or Hotel)
  may **viewAmenity** and **bookAmenity**.
- A user with **admin** role at the Amenity's containing Property (or Hotel) may
  **manageAmenity** (create/configure/delete amenities).
- Role checking uses cross-entity traversal via the entity hierarchy:
  `resource in principal.memberPermissions.propertyReservations` is not directly applicable
  to Amenity; instead check `resource in principal.hotelAdminPermissions` (because Amenity
  is `in Property in Hotel`, transitive membership applies).

### 6. Exclusive Amenities
- If `resource.isExclusive == true`, the **bookAmenity** action requires **admin** role
  (member role is insufficient for exclusive amenity booking).
- viewAmenity is not restricted by exclusivity.

## Notes (Amenity)
- Amenity uses the existing Property hierarchy (`Amenity in [Property]`).
- The existing PermissionsMap does not cover Amenity; admin sets cover by transitive hierarchy.
