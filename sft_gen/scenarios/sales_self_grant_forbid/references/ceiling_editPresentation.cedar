permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (resource.editors.contains(principal) &&
     principal.job != Job::"customer")
};
