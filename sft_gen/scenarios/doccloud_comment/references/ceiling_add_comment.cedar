permit (
    principal is User,
    action == Action::"AddComment",
    resource is Comment
)
when {
    !principal.blocked.contains(resource.document.owner) &&
    !resource.document.owner.blocked.contains(principal) &&
    (
        principal == resource.document.owner ||
        principal in resource.document.viewACL ||
        principal in resource.document.modifyACL ||
        principal in resource.document.manageACL
    )
};
