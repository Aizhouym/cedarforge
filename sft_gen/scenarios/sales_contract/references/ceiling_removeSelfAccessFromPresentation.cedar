permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal in resource.viewers ||
    principal in resource.editors
};
