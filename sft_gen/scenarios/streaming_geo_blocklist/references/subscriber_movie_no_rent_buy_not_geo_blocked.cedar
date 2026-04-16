permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !resource.blockedRegions.contains(context.now.userRegion)
};
