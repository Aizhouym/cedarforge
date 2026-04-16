permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    resource.editors.contains(principal)
};
