permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal.job != Job::"internal" &&
    principal in resource.viewerMarkets
};
