permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.viewACL ||
    resource.publicAccess == "view" ||
    (resource.publicAccess == "edit" && principal in resource.modifyACL)
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.modifyACL ||
    (resource.publicAccess == "edit" && principal in resource.modifyACL)
};

permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
) when {
    principal == resource.owner
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
    action == Action::"CreateDocument",
    resource is Drive
);

permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
);

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
        Action::"AddToShareACL",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess"
    ],
    resource is Document
) when {
    resource.expiryDate != null &&
    context.currentTime > resource.expiryDate
};

forbid (
    principal is User,
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"AddToShareACL",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess",
        Action::"CreateDocument",
        Action::"CreateGroup",
        Action::"ModifyGroup",
        Action::"DeleteGroup"
    ],
    resource
) when {
    !context.is_authenticated
};