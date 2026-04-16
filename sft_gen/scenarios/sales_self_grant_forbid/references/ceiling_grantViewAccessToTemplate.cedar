permit (
    principal is User,
    action == Action::"grantViewAccessToTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    (
        ((context has targetUser) && (!(context has targetMarket)) && context.targetUser != principal) ||
        ((context has targetMarket) && (!(context has targetUser)))
    )
};
