permit (
    principal is User,
    action == Action::"read",
    resource is Resource
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"read",
    resource is Resource
) when {
    context has activeGrant &&
    context.activeGrant.grantee == principal &&
    context.activeGrant.allowedAction == "read" &&
    context.activeGrant.expiresAt > context.now.datetime
};

permit (
    principal is User,
    action == Action::"write",
    resource is Resource
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"write",
    resource is Resource
) when {
    context has activeGrant &&
    context.activeGrant.grantee == principal &&
    context.activeGrant.allowedAction == "write" &&
    context.activeGrant.expiresAt > context.now.datetime
};

permit (
    principal is User,
    action == Action::"createGrant",
    resource is Resource
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"revokeGrant",
    resource is Resource
) when {
    principal == resource.owner
};