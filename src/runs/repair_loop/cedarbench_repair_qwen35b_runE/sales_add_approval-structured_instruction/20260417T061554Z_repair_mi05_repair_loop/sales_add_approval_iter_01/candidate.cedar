permit (
    principal is User,
    action == Action::"ExternalPrezViewActions",
    resource is Presentation
) when {
    principal in resource.viewers
};

permit (
    principal is User,
    action == Action::"InternalPrezViewActions",
    resource is Presentation
) when {
    principal.job == Job::"internal" &&
    principal in resource.viewers
};

permit (
    principal is User,
    action == Action::"PrezEditActions",
    resource is Presentation
) when {
    resource.owner == principal ||
    principal in resource.editors
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
    action == Action::"MarketTemplateViewActions",
    resource is Template
) when {
    principal in resource.viewerMarkets
};

permit (
    principal is User,
    action == Action::"InternalTemplateViewActions",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    principal in resource.viewers
};

permit (
    principal is User,
    action == Action::"TemplateEditActions",
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

forbid (
    principal is User,
    action in [Action::"TemplateEditActions", Action::"MarketTemplateViewActions"],
    resource is Template
) when {
    !resource.isApproved &&
    principal.job != Job::"internal"
};