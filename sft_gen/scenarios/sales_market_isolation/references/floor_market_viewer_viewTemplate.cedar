permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job != Job::"internal" &&
    principal in resource.viewerMarkets
};
