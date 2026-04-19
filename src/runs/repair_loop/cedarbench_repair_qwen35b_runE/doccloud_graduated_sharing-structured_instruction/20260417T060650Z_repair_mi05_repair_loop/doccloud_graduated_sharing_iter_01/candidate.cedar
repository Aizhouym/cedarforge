permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.viewACL ||
    principal in resource.modifyACL ||
    principal in resource.manageACL ||
    (resource.publicAccess == "view" && principal is Public) ||
    (resource.publicAccess == "edit" && principal is Public)
} unless {
    (resource.owner has blocked && principal in resource.owner.blocked) ||
    (principal has blocked && resource.owner in principal.blocked)
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.modifyACL ||
    (resource.publicAccess == "edit" && principal is Public)
} unless {
    (resource.owner has blocked && principal in resource.owner.blocked) ||
    (principal has blocked && resource.owner in principal.blocked)
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
    action == Action::"ViewMetadata",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.viewACL ||
    principal in resource.modifyACL ||
    principal in resource.manageACL ||
    (resource.publicAccess == "preview" && principal is Public) ||
    (resource.publicAccess == "view" && principal is Public) ||
    (resource.publicAccess == "edit" && principal is Public)
};

permit (
    principal is User,
    action == Action::"CreateDocument",
    resource is Drive
) when {
    context.is_authenticated
};

permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
) when {
    context.is_authenticated
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