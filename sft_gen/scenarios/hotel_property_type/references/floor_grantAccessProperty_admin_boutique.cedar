permit (
    principal is User,
    action == Action::"grantAccessProperty",
    resource is Property
) when {
    resource.propertyType == "boutique" &&
    resource in principal.propertyAdminPermissions
};
