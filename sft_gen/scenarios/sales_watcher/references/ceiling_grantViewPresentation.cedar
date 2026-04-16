permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
) when {
    !(principal in resource.watchers) &&
    (
        principal == resource.owner ||
        (principal in resource.editors && principal.job == Job::"internal")
    ) &&
    (
        context.target.job != Job::"customer" ||
        (principal.job == Job::"distributor" && principal.customerId == context.target.customerId)
    )
};
