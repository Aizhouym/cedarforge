permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job != Job::"customer" &&
    principal in resource.editors
};
