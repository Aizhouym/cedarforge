
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
    (principal == resource.owner || principal in resource.viewACL)
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
    (principal == resource.owner || principal in resource.modifyACL)
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

permit (
    principal is User,
    action == Action::"AddComment",
    resource is Comment
)
when {
    principal == resource.document.owner ||
    principal in resource.document.viewACL ||
    principal in resource.document.modifyACL ||
    principal in resource.document.manageACL
};

permit (
    principal is User,
    action == Action::"EditComment",
    resource is Comment
)
when { principal == resource.author };

permit (
    principal is User,
    action == Action::"DeleteComment",
    resource is Comment
)
when {
    principal == resource.author ||
    principal == resource.document.owner ||
    principal in resource.document.manageACL
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

forbid (
    principal is User,
    action == Action::"AddComment",
    resource is Comment
)
when {
    principal.blocked.contains(resource.document.owner) ||
    resource.document.owner.blocked.contains(principal)
};
