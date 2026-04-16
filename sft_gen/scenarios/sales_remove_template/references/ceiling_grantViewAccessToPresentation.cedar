permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    resource.editors.contains(principal) &&
    (resource.viewers.contains(context.target) ||
     resource.editors.contains(context.target))
};
