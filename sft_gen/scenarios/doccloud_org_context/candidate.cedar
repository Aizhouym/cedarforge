permit (
    principal is User,
    action in [Action::"CreateDocument", Action::"CreateGroup"],
    resource is Drive
)
when { context.is_authenticated };

permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        (context.userOrg == resource.ownerOrg &&
         (principal == resource.owner || principal in resource.viewACL)) ||
        (context.userOrg != resource.ownerOrg &&
         (principal == resource.owner || principal in resource.manageACL))
    )
};

permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when { resource.publicAccess == "view" || resource.publicAccess == "edit" };

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        (context.userOrg == resource.ownerOrg &&
         (principal == resource.owner || principal in resource.modifyACL)) ||
        (context.userOrg != resource.ownerOrg &&
         (principal == resource.owner || principal in resource.manageACL))
    )
};

permit (
    principal is User,
    action in [
        Action::"AddToShareACL",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess"
    ],
    resource is Document
)
when {
    context.is_authenticated &&
    (
        (context.userOrg == resource.ownerOrg &&
         (principal == resource.owner || principal in resource.manageACL)) ||
        (context.userOrg != resource.ownerOrg &&
         (principal == resource.owner || principal in resource.manageACL))
    )
};

permit (
    principal is User,
    action in [Action::"ModifyGroup", Action::"DeleteGroup"],
    resource is Group
)
when {
    context.is_authenticated &&
    principal == resource.owner
};

forbid (
    principal is User,
    action in [Action::"ViewDocument", Action::"ModifyDocument"],
    resource is Document
)
when {
    principal.blocked.contains(resource.owner) ||
    resource.owner.blocked.contains(principal)
};

forbid (
    principal is User,
    action in [
        Action::"CreateDocument",
        Action::"CreateGroup",
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"AddToShareACL",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess",
        Action::"ModifyGroup",
        Action::"DeleteGroup"
    ],
    resource
)
when { !context.is_authenticated };
