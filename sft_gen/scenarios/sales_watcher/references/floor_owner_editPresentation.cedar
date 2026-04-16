permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal == resource.owner &&
    !(principal in resource.watchers)
};
