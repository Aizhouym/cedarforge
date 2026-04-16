permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    principal in resource.viewers ||
    principal in resource.viewerMarkets
};
