permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal in resource.viewers ||
    principal in resource.viewerTeams
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal in resource.viewers ||
    principal in resource.viewerTeams
};

permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" &&
    principal in resource.viewers
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorTeams
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorTeams
};

permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorTeams
};

forbid (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    context has target &&
    context.target.job == Job::"customer" &&
    (principal.job != Job::"distributor" ||
     principal.customerId != context.target.customerId)
};

forbid (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    context has target &&
    context.target.job != Job::"internal"
};

permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal in resource.viewers ||
    principal in resource.viewerMarkets
};

permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal in resource.viewers ||
    principal in resource.viewerMarkets
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets ||
    (principal.job == Job::"internal" && principal in resource.viewers)
};

permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};

permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};

permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};

forbid (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    context has targetUser &&
    context.targetUser.job == Job::"customer" &&
    (principal.job != Job::"distributor" ||
     principal.customerId != context.targetUser.customerId)
};

forbid (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    context has targetUser &&
    context.targetUser.job != Job::"internal"
};