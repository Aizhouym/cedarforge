permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal) &&
    (
        (resource.classification == "confidential" &&
         (principal == resource.owner || principal in resource.manageACL)) ||
        (resource.classification != "confidential" &&
         (principal == resource.owner || principal in resource.viewACL || principal in resource.manageACL))
    )
};
