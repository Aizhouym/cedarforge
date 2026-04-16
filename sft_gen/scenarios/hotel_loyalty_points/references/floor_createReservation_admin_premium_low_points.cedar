permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    resource in principal.propertyAdminPermissions &&
    resource.isPremium &&
    principal.loyaltyPoints < 5000
};
