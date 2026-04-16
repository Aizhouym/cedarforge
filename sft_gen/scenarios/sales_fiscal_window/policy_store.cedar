
// --- Verified and appended ---
permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            resource.viewers.contains(principal) ||
            resource.editors.contains(principal)
        )
    )
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    (
        resource.viewers.contains(principal) ||
        resource.editors.contains(principal)
    )
};

permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        resource.editors.contains(principal)
    )
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    (
        principal.job == Job::"internal" ||
        (
            principal.job != Job::"internal" &&
            principal.job != Job::"customer" &&
            resource.editors.contains(principal) &&
            resource.fiscalYear == context.currentYear
        )
    )
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal) &&
    (
        resource.viewers.contains(context.target) ||
        resource.editors.contains(context.target)
    )
};

permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal) &&
    resource.editors.contains(context.target)
};

permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            resource.viewers.contains(principal) ||
            principal in resource.viewerMarkets
        )
    )
};

permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            resource.viewers.contains(principal) ||
            principal in resource.viewerMarkets
        )
    )
};

permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal.job != Job::"customer" &&
        resource.editors.contains(principal) &&
        resource.fiscalYear == context.currentYear
    )
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job != Job::"internal" &&
    resource.editors.contains(principal)
};
