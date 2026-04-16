permit (
    principal is User,
    action == Action::"grantAccessProperty",
    resource is Property
) when {
    resource.propertyType == "standard" &&
    resource in principal.memberPermissions.propertyReservations
};
