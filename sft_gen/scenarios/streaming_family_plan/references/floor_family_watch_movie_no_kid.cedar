permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    context has subscriberPlan &&
    context.subscriberPlan.familyMembers.contains(principal) &&
    !principal.profile.isKid
};
