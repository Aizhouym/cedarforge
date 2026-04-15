permit (
    principal is User,
    action == Action::"ShareFolder",
    resource is Folder
)
when {
    principal == resource.owner &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
