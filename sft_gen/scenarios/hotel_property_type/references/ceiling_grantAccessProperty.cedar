permit (
    principal is User,
    action == Action::"grantAccessProperty",
    resource is Property
) when {
    (
        (resource.propertyType == "standard" || resource.propertyType == "resort") &&
        (
            resource in principal.memberPermissions.propertyReservations ||
            resource in principal.memberPermissions.hotelReservations ||
            resource in principal.propertyAdminPermissions ||
            resource in principal.hotelAdminPermissions
        )
    ) ||
    (
        resource.propertyType == "boutique" &&
        (
            resource in principal.propertyAdminPermissions ||
            resource in principal.hotelAdminPermissions
        )
    )
};
