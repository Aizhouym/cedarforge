permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal) &&
    context.target != principal &&
    resource.editors.contains(context.target)
};
