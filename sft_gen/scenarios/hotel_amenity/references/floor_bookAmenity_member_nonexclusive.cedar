permit (
    principal is User,
    action == Action::"bookAmenity",
    resource is Amenity
) when {
    !resource.isExclusive &&
    resource in principal.memberPermissions.propertyReservations
};
