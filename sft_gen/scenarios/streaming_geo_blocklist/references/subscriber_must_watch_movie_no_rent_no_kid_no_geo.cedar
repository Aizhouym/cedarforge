permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !principal.profile.isKid &&
    !resource.blockedRegions.contains(context.now.userRegion)
};
