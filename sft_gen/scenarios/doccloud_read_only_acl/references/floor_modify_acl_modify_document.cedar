permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal in resource.modifyACL &&
    !(principal in resource.readOnlyACL) &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
