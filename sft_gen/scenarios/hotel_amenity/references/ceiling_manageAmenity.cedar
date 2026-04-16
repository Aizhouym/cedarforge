permit (
    principal is User,
    action == Action::"manageAmenity",
    resource is Amenity
) when {
    resource in principal.propertyAdminPermissions ||
    resource in principal.hotelAdminPermissions
};
