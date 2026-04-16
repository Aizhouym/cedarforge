permit (
    principal is User,
    action == Action::"viewPresentation",
    resource is Presentation
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" &&
    (
        principal == resource.owner ||
        principal in resource.viewers ||
        principal in resource.editors
    )
};

permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal == resource.owner ||
    (principal in resource.editors && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromPresentation",
    resource is Presentation
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal")
    ) &&
    (
        context.target.job != Job::"customer" ||
        (principal.job == Job::"distributor" &&
         principal.customerId == context.target.customerId)
    )
};

permit (
    principal is User,
    action == Action::"grantEditAccessToPresentation",
    resource is Presentation
) when {
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal")
    ) &&
    context.target.job == Job::"internal" &&
    (
        context.target.job != Job::"customer" ||
        (principal.job == Job::"distributor" &&
         principal.customerId == context.target.customerId)
    )
};

permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    principal in resource.viewerMarkets ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"duplicateTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    principal in resource.viewers ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    principal in resource.viewerMarkets ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    (principal in resource.viewers && principal.job == Job::"internal") ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    principal == resource.owner ||
    (principal in resource.editors && principal.job == Job::"internal") ||
    (principal in resource.editorMarkets && principal.job == Job::"internal")
};

permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal") ||
        (principal in resource.editorMarkets && principal.job == Job::"internal")
    ) &&
    (
        !(context has targetUser) ||
        (context has targetUser &&
         context.targetUser.job != Job::"customer") ||
        (context has targetUser &&
         principal.job == Job::"distributor" &&
         principal.customerId == context.targetUser.customerId)
    )
};

permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal") ||
        (principal in resource.editorMarkets && principal.job == Job::"internal")
    ) &&
    (
        !(context has targetUser) ||
        (context has targetUser &&
         context.targetUser.job == Job::"internal")
    ) &&
    (
        !(context has targetUser) ||
        (context has targetUser &&
         context.targetUser.job != Job::"customer") ||
        (context has targetUser &&
         principal.job == Job::"distributor" &&
         principal.customerId == context.targetUser.customerId)
    )
};
