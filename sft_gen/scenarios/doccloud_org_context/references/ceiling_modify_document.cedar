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
        (context.userOrg == resource.ownerOrg &&
         (principal == resource.owner || principal in resource.modifyACL)) ||
        (context.userOrg != resource.ownerOrg &&
         (principal == resource.owner || principal in resource.manageACL))
    )
};
