permit (
    principal is User,
    action == Action::"bookAmenity",
    resource is Amenity
) when {
    (
        !resource.isExclusive &&
        (
            resource in principal.memberPermissions.propertyReservations ||
            resource in principal.memberPermissions.hotelReservations ||
            resource in principal.propertyAdminPermissions ||
            resource in principal.hotelAdminPermissions
        )
    ) ||
    (
        resource.isExclusive &&
        (
            resource in principal.propertyAdminPermissions ||
            resource in principal.hotelAdminPermissions
        )
    )
};
