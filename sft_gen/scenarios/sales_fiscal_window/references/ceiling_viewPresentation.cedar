permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            resource.viewers.contains(principal) ||
            resource.editors.contains(principal)
        )
    )
};
