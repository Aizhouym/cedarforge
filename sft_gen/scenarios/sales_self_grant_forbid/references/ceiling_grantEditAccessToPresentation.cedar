permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    resource.editors.contains(principal) &&
    context.target != principal &&
    resource.editors.contains(context.target)
};
