permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    resource.viewers.contains(principal) ||
    resource.editors.contains(principal)
};
