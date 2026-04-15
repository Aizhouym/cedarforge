permit (
    principal is User,
    action == Action::"AddComment",
    resource is Comment
)
when {
    principal in resource.document.viewACL &&
    !principal.blocked.contains(resource.document.owner) &&
    !resource.document.owner.blocked.contains(principal)
};
