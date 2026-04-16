permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal.job != Job::"customer" &&
        principal in resource.editors
    )
};
