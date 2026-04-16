permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            principal in resource.viewers ||
            principal in resource.editors
        )
    )
};
