permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    principal.subscription.tier == "premium" &&
    resource.isEarlyAccess &&
    context.now.datetime >= resource.releaseDate.offset(duration("-24h")) &&
    context.now.datetime < resource.releaseDate &&
    !principal.profile.isKid &&
    context.activeStreams < principal.maxStreams
};
