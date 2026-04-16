permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    context has subscriberPlan &&
    context.subscriberPlan.familyMembers.contains(principal) &&
    !resource.isEarlyAccess &&
    !principal.profile.isKid
};
