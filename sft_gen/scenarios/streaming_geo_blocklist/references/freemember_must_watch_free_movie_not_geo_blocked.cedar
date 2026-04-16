permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    resource.isFree &&
    !resource.blockedRegions.contains(context.now.userRegion)
};
