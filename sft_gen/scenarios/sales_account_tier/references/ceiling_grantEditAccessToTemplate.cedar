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
