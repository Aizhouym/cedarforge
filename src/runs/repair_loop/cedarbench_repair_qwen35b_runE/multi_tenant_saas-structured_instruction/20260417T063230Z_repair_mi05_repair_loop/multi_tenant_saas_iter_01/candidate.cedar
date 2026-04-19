permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
) when {
    principal.tenant == resource.tenant
};

permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
) when {
    principal.isGlobalSupport &&
    context.supportSessionActive &&
    context.ticketId != ""
};

permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
) when {
    principal.tenant == resource.tenant
};

permit (
    principal is User,
    action == Action::"deleteResource",
    resource is Resource
) when {
    principal.tenant == resource.tenant
};