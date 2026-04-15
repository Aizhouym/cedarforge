permit (
    principal is User,
    action == Action::"AddComment",
    resource is Comment
)
when {
    principal == resource.document.owner &&
    !principal.blocked.contains(resource.document.owner) &&
    !resource.document.owner.blocked.contains(principal)
};
