permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    resource in principal.memberPermissions.propertyReservations &&
    resource.isPremium &&
    principal.loyaltyPoints >= 5000
};
