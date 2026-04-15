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
        principal == resource.owner ||
        (! (principal in resource.readOnlyACL) &&
         (principal == resource.owner || principal in resource.modifyACL))
    )
};
