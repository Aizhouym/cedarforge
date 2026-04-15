permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    context.deviceTrusted &&
    principal in resource.modifyACL &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
