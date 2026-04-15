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
        (resource.isDraft &&
         (principal == resource.owner || principal in resource.manageACL)) ||
        (!resource.isDraft &&
         (principal == resource.owner || principal in resource.viewACL))
    )
};

permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    !resource.isDraft &&
    (resource.publicAccess == "view" || resource.publicAccess == "edit")
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        (resource.isDraft && principal == resource.owner) ||
        (!resource.isDraft && (principal == resource.owner || principal in resource.modifyACL))
    )
};

permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    !resource.isDraft &&
    (principal == resource.owner || principal in resource.manageACL)
};

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

permit (
    principal is User,
    action in [Action::"EditPublicAccess", Action::"AddToShareACL"],
    resource is Document
)
when {
    context.is_authenticated &&
    !resource.isDraft &&
    (principal == resource.owner || principal in resource.manageACL)
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
