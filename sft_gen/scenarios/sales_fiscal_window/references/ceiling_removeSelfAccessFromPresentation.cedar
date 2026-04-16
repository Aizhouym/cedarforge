permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    (
        resource.viewers.contains(principal) ||
        resource.editors.contains(principal)
    )
};
