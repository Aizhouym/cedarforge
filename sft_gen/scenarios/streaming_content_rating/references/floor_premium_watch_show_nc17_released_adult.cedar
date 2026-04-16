permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    !resource.isEarlyAccess &&
    principal.subscription.tier == "premium" &&
    !principal.profile.isKid &&
    resource.contentRating == "NC-17"
};
