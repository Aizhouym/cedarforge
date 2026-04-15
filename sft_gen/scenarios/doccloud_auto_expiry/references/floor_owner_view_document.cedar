permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    !(context.now > resource.expiresAt) &&
    principal == resource.owner &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};
