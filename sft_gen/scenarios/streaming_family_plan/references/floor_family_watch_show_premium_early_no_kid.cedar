permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    context has subscriberPlan &&
    context.subscriberPlan.familyMembers.contains(principal) &&
    resource.isEarlyAccess &&
    context.subscriberPlan.subscription.tier == "premium" &&
    context.now.datetime >= resource.releaseDate.offset(duration("-24h")) &&
    context.now.datetime < resource.releaseDate &&
    !principal.profile.isKid
};
