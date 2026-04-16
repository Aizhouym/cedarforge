permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    principal in resource.editors &&
    context.target in resource.editors
};
