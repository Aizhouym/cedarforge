permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job != Job::"internal" &&
    principal.job != Job::"customer" &&
    resource.editors.contains(principal) &&
    resource.fiscalYear == context.currentYear
};
