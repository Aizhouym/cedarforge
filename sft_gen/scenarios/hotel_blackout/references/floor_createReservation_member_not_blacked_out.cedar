permit (
    principal is User,
    action == Action::"createReservation",
    resource is Property
) when {
    resource in principal.memberPermissions.propertyReservations &&
    (
        !(resource has blackoutUntil) ||
        (resource has blackoutUntil && context.now >= resource.blackoutUntil)
    )
};
