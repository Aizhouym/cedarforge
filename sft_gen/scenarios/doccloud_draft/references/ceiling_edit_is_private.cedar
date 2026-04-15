permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        (resource.isDraft && principal == resource.owner) ||
        (!resource.isDraft && (principal == resource.owner || principal in resource.manageACL))
    )
};
