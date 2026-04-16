permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    resource.viewers.contains(principal) ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    resource.editors.contains(principal) &&
    (resource.viewers.contains(context.target) ||
     resource.editors.contains(context.target))
};

permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    resource.editors.contains(principal) &&
    resource.editors.contains(context.target)
};

forbid (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"customer"
};
