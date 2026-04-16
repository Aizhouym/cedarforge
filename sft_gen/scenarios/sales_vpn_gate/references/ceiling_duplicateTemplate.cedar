permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            resource.viewers.contains(principal) ||
            principal in resource.viewerMarkets
        )
    )
};
