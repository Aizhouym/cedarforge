
// --- Verified and appended ---
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
        principal == resource.owner ||
        (principal in resource.viewACL && resource.isPrivate == false)
    )
};

permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    resource.isPrivate == false &&
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
        principal == resource.owner ||
        (principal in resource.modifyACL && resource.isPrivate == false)
    )
};

permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
)
when {
    context.is_authenticated &&
    principal == resource.owner
};

permit (
    principal is User,
    action in [Action::"AddToShareACL", Action::"EditPublicAccess"],
    resource is Document
)
when {
    context.is_authenticated &&
    (
        principal == resource.owner ||
        (principal in resource.manageACL && resource.isPrivate == false)
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
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"AddToShareACL",
        Action::"EditPublicAccess"
    ],
    resource is Document
)
when {
    principal.blocked.contains(resource.owner) ||
    resource.owner.blocked.contains(principal)
};

forbid (
    principal is User,
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"AddToShareACL",
        Action::"EditPublicAccess"
    ],
    resource is Document
)
when {
    principal != resource.owner &&
    resource.isPrivate
};

forbid (
    principal is User,
    action in [
        Action::"CreateDocument",
        Action::"CreateGroup",
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"AddToShareACL",
        Action::"EditPublicAccess",
        Action::"ModifyGroup",
        Action::"DeleteGroup"
    ],
    resource
)
when { !context.is_authenticated };

forbid (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when { !context.is_authenticated };
