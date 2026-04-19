permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
) when {
    principal.isLegalTeam
};

permit (
    principal is User,
    action == Action::"editDocument",
    resource is Document
) when {
    principal == resource.owner &&
    context.now.datetime < resource.expiryDate
};

permit (
    principal is User,
    action == Action::"editDocument",
    resource is Document
) when {
    principal.isLegalTeam &&
    resource.legalHold
};

permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
) when {
    principal == resource.owner &&
    context.now.datetime < resource.expiryDate &&
    !resource.legalHold
};