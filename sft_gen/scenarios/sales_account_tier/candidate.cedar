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

permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    principal in resource.viewerMarkets ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    principal in resource.viewerMarkets ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.viewers.contains(principal) ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    resource.editors.contains(principal)
};

permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    (
        ((context has targetUser) && (!(context has targetMarket))) ||
        ((context has targetMarket) && (!(context has targetUser)))
    )
};

permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    (
        ((context has targetUser) && (!(context has targetMarket))) ||
        ((context has targetMarket) && (!(context has targetUser)))
    )
};

forbid (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"customer"
};

forbid (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    resource.tier == "enterprise"
} unless {
    principal.job == Job::"internal"
};

forbid (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"customer"
};
