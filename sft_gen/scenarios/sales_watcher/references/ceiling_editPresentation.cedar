permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    !(principal in resource.watchers) &&
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal")
    )
};
