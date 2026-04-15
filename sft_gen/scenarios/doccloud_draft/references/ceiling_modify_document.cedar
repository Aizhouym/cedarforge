permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal) &&
    (
        (resource.isDraft && principal == resource.owner) ||
        (!resource.isDraft && (principal == resource.owner || principal in resource.modifyACL))
    )
};
