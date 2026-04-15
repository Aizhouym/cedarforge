permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
)
when {
    context.is_authenticated &&
    resource.viewerCount < resource.maxViewers &&
    (principal == resource.owner || principal in resource.manageACL)
};
