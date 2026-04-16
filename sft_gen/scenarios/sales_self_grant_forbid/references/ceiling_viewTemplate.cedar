permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    principal in resource.viewerMarkets ||
    resource.editors.contains(principal)
};
