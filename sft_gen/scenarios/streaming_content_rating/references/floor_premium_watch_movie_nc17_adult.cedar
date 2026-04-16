permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    principal.subscription.tier == "premium" &&
    !principal.profile.isKid &&
    resource.contentRating == "NC-17"
};
