permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal) &&
    context.onVPN
};
