permit (
    principal is User,
    action == Action::"viewAmenity",
    resource is Amenity
) when {
    resource in principal.memberPermissions.propertyReservations
};
