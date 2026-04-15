permit (
    principal is User,
    action == Action::"ViewFolder",
    resource is Folder
)
when {
    principal in resource.modifyACL &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
