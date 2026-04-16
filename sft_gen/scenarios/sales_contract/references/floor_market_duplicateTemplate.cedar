permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal in resource.viewerMarkets
};
