"""Hotel domain — new SFT mutations.

Already in cedarbench (excluded):
  hotel_base, hotel_add_franchise, hotel_add_guest, hotel_add_loyalty_tier,
  hotel_add_renovation_lock, hotel_add_cancel, hotel_franchise_loyalty,
  hotel_remove_hierarchy, hotel_temporal_rates.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
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
"""


# ── 1. Blackout dates — createReservation forbidden during blackout (S4 + P1) ──

class HotelBlackout(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_blackout",
            base_scenario="hotel",
            difficulty="medium",
            description="Add blackoutUntil datetime to Property; createReservation forbidden before blackoutUntil",
            operators=["S4", "S8", "P1"],
            features_tested=["datetime_comparison", "forbid_rule", "context_field"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Property", "blackoutUntil", "datetime")
        schema = schema_ops.add_context_field(schema, "createReservation", "now", "datetime")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Property type — boutique requires admin for grantAccess (S3 + P7 + P4) ──

class HotelPropertyType(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_property_type",
            base_scenario="hotel",
            difficulty="medium",
            description="Add propertyType String to Property; boutique properties require admin (not member) for grantAccess",
            operators=["S3", "P7", "P4"],
            features_tested=["string_enum", "elevated_requirement", "role_scoping"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Property", "propertyType", "String")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. MFA gate — grantAccess actions require MFA (S8 + P1) ──────────────────

class HotelMfaGate(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_mfa_gate",
            base_scenario="hotel",
            difficulty="easy",
            description="Add mfaVerified Bool context; all grantAccess actions forbidden without MFA",
            operators=["S8", "P1"],
            features_tested=["context_gate", "admin_mfa", "multi_action_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema
        for action_name in ["grantAccessReservation", "grantAccessProperty", "grantAccessHotel"]:
            schema = schema_ops.add_context_field(schema, action_name, "mfaVerified", "Bool")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. VIP blocked users — Set<User> on Property (S5 + P1) ───────────────────

class HotelVipBlocked(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_vip_blocked",
            base_scenario="hotel",
            difficulty="easy",
            description="Add blockedGuests Set<User> to Property; blocked users cannot createReservation",
            operators=["S5", "P1"],
            features_tested=["set_membership_forbid", "explicit_blocklist"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Property", "blockedGuests", "Set<User>")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Concierge role — can createReservation, no grantAccess (S9 + P2 + P4) ──

class HotelConcierge(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_concierge",
            base_scenario="hotel",
            difficulty="medium",
            description="Add conciergePermissions PermissionsMap to User; concierge can createReservation but not grantAccess",
            operators=["S13", "S9", "P2", "P4"],
            features_tested=["new_role", "partial_admin", "record_type"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Add conciergePermissions as a new PermissionsMap attribute on User
        # PermissionsMap type already exists in the hotel schema
        schema = schema_ops.add_attribute(base_schema, "User", "conciergePermissions", "PermissionsMap")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Remove viewer role — two-tier model (S10 + P3 + P8) ───────────────────

class HotelRemoveViewer(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_remove_viewer",
            base_scenario="hotel",
            difficulty="medium",
            description="Remove viewPermissions; view perms absorbed into memberPermissions (two-role model)",
            operators=["S10", "P3", "P8"],
            features_tested=["role_removal", "role_redistribution", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_attribute(base_schema, "User", "viewPermissions")
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Amenity entity — viewAmenity/bookAmenity (S6 + S7 + P2 + P9) ─────────

class HotelAmenity(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_amenity",
            base_scenario="hotel",
            difficulty="medium",
            description="Add Amenity entity in Property; members can viewAmenity; admins can bookAmenity/manageAmenity",
            operators=["S6", "S7", "P2", "P9"],
            features_tested=["new_entity", "cross_traversal", "resource_type_extension"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Amenity in [Property] = {
    isExclusive: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Amenity actions
action viewAmenity, bookAmenity, manageAmenity appliesTo {
    principal: [User],
    resource: [Amenity],
};""")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Guest capacity — createReservation blocked when full (S2 + P6) ─────────

class HotelGuestCapacity(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_guest_capacity",
            base_scenario="hotel",
            difficulty="easy",
            description="Add currentGuests + maxGuests Long to Property; createReservation forbidden when at capacity",
            operators=["S2", "P6"],
            features_tested=["numeric_threshold", "capacity_limit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Property", "currentGuests", "Long")
        schema = schema_ops.add_attribute(schema, "Property", "maxGuests", "Long")
        spec = _BASE_SPEC + """\
### 5. Guest Capacity Limit (Deny Rule)
- Properties have `currentGuests: Long` (current occupancy) and `maxGuests: Long` (capacity).
- If `resource.currentGuests >= resource.maxGuests`, **createReservation** is **forbidden**
  for ALL principals — members and admins alike.
- This is a hard limit: no role override exists. The host application must update
  `currentGuests` atomically when reservations are created or cancelled.
- All other actions (viewReservation, updateReservation, grantAccess, etc.) are unaffected.

## Notes (Capacity)
- Numeric comparison: `resource.currentGuests >= resource.maxGuests`.
- Both attributes are on the Property entity.
- Compare with `hotel_add_renovation_lock` (boolean forbid) — this uses a numeric threshold
  instead of a boolean flag.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Loyalty points — numeric unlock for premium properties (S2 + P2) ───────

class HotelLoyaltyPoints(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_loyalty_points",
            base_scenario="hotel",
            difficulty="medium",
            description="Add loyaltyPoints Long to User + isPremium Bool to Property; premium requires 5000+ points",
            operators=["S2", "S1", "P1", "P6"],
            features_tested=["numeric_permit_threshold", "boolean_guard", "cross_attr_condition"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "User", "loyaltyPoints", "Long")
        schema = schema_ops.add_attribute(schema, "Property", "isPremium", "Bool")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 10. Partner company context — partner gets limited view (S8 + S3 + P2 + P9) ─

class HotelPartnerAccess(Mutation):
    def meta(self):
        return MutationMeta(
            id="hotel_partner_access",
            base_scenario="hotel",
            difficulty="medium",
            description="Add partnerCode String to Property; context partnerCode grants viewProperty to external partners",
            operators=["S3", "S8", "P2"],
            features_tested=["context_permit", "string_comparison", "partner_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Property", "partnerCode", "String")
        schema = schema_ops.add_context_field(schema, "viewProperty", "providedPartnerCode", "String")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    HotelBlackout(),
    HotelPropertyType(),
    HotelMfaGate(),
    HotelVipBlocked(),
    HotelConcierge(),
    HotelRemoveViewer(),
    HotelAmenity(),
    HotelGuestCapacity(),
    HotelLoyaltyPoints(),
    HotelPartnerAccess(),
]

for _m in MUTATIONS:
    register(_m)
