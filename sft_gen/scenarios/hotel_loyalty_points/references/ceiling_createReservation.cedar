permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    (
        (
            resource in principal.memberPermissions.propertyReservations ||
            resource in principal.memberPermissions.hotelReservations
        ) &&
        (
            !resource.isPremium ||
            principal.loyaltyPoints >= 5000
        )
    ) ||
    resource in principal.propertyAdminPermissions ||
    resource in principal.hotelAdminPermissions
};
