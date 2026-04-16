permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"distributor" &&
    principal in resource.territory &&
    principal in resource.editors
};
