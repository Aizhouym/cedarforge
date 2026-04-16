permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job != Job::"customer" &&
    principal in resource.editors
};
