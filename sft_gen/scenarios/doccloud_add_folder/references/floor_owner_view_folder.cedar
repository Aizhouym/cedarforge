permit (
    principal is User,
    action == Action::"ViewFolder",
    resource is Folder
)
when {
    principal == resource.owner &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
