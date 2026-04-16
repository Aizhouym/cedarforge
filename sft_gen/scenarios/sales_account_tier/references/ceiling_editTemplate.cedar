permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (resource.editors.contains(principal) &&
     principal.job != Job::"customer")
};
