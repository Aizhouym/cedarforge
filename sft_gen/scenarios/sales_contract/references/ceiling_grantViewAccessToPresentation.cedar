permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    principal in resource.editors &&
    (context.target in resource.viewers || context.target in resource.editors)
};
