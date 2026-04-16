permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job != Job::"customer" &&
    principal in resource.editors
};
