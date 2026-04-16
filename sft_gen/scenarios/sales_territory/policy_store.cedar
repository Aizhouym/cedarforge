
// --- Verified and appended ---
permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal in resource.territory &&
        (
            principal in resource.viewers ||
            principal in resource.editors
        )
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
        principal in resource.editors
    )
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal.job != Job::"customer" &&
        principal in resource.territory &&
        principal in resource.editors
    )
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            principal in resource.viewers ||
            principal in resource.editors
        )
    )
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    principal in resource.editors &&
    (
        context.target in resource.viewers ||
        context.target in resource.editors
    )
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
    (
        principal.job != Job::"internal" &&
        (
            principal in resource.viewers ||
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
            principal in resource.viewers ||
            principal in resource.viewerMarkets
        )
    )
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        (
            principal in resource.viewers ||
            principal in resource.editors
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
        principal in resource.editors
    )
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal in resource.editors
    )
};

permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal"
};

permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    (
        !(context has targetUser) ||
        (context has targetUser && context.targetUser.job == Job::"internal")
    )
};
