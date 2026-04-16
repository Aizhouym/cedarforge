permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal) &&
    context.target != principal &&
    resource.viewers.contains(context.target)
};
