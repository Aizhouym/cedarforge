permit (
    principal is User,
    action == Action::"ViewFolder",
    resource is Folder
)
when {
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal) &&
    (principal == resource.owner || principal in resource.viewACL || principal in resource.modifyACL)
};
