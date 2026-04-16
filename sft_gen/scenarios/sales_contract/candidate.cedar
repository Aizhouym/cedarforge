permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    principal in resource.viewers ||
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal in resource.viewers ||
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    principal in resource.editors &&
    (context.target in resource.viewers || context.target in resource.editors)
};

permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    principal in resource.editors &&
    context.target in resource.editors
};

permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    principal in resource.viewers ||
    principal in resource.viewerMarkets
};

permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    principal in resource.viewers ||
    principal in resource.viewerMarkets
};

permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job != Job::"customer" &&
    principal in resource.editors
};

permit (
    principal is User,
    action == Action::"viewContract",
    resource is Contract
) when {
    principal.job == Job::"internal" ||
    (principal.job != Job::"customer" &&
     principal in resource.presentation.editors)
};

permit (
    principal is User,
    action == Action::"signContract",
    resource is Contract
) when {
    principal.job == Job::"internal" &&
    !resource.isSigned
};

forbid (
    principal is User,
    action in [Action::"editPresentation", Action::"editTemplate"],
    resource
) when {
    principal.job == Job::"customer"
};

forbid (
    principal is User,
    action == Action::"signContract",
    resource is Contract
) when {
    resource.isSigned
};
