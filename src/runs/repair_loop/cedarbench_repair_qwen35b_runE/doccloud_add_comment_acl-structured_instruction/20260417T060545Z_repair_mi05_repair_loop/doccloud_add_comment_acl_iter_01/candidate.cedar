permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.viewACL ||
    (resource.publicAccess == "view" && principal is Public) ||
    (resource.publicAccess == "edit" && principal is Public)
} unless {
    (principal in resource.owner.blocked || resource.owner in principal.blocked) &&
    (principal == resource.owner || principal in resource.viewACL ||
     (resource.publicAccess == "view" && principal is Public) ||
     (resource.publicAccess == "edit" && principal is Public))
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
    (principal in resource.owner.blocked || resource.owner in principal.blocked) &&
    (principal == resource.owner || principal in resource.modifyACL ||
     (resource.publicAccess == "edit" && principal is Public))
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
    action == Action::"CommentOnDocument",
    resource is Document
) when {
    principal == resource.owner ||
    principal in resource.commentACL
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
);

permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
);