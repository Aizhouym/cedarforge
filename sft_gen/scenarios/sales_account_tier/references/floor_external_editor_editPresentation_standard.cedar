permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    principal.job != Job::"customer" &&
    resource.editors.contains(principal) &&
    resource.tier == "standard"
};
