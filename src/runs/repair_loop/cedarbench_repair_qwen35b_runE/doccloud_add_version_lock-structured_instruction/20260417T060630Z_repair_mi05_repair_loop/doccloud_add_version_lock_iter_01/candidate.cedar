permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.viewACL ||
    (resource.publicAccess == "view" && principal is Public) ||
    (resource.publicAccess == "edit" && principal is Public)
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.modifyACL ||
    (resource.publicAccess == "edit" && principal is Public)
};

permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.manageACL
};

permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.manageACL
};

permit (
    principal is User,
    action == Action::"EditPublicAccess",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.manageACL
};

permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.manageACL
};

permit (
    principal is User,
    action == Action::"ModifyGroup",
    resource is Group
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"DeleteGroup",
    resource is Group
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"CreateDocument",
    resource is Drive
) when {
    true
};

permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
) when {
    true
};

forbid (
    principal is User,
    action in [Action::"ViewDocument", Action::"ModifyDocument"],
    resource is Document
) when {
    principal in resource.owner.blocked ||
    resource.owner in principal.blocked
};

forbid (
    principal is User,
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess",
        Action::"AddToShareACL",
        Action::"ModifyGroup",
        Action::"DeleteGroup",
        Action::"CreateDocument",
        Action::"CreateGroup"
    ],
    resource
) when {
    !context.is_authenticated
};

forbid (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    resource.isLocked
};