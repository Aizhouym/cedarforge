permit (
    principal is Subscriber,
    action == Action::"listen_podcast",
    resource is Podcast
) when {
    !resource.isExclusive ||
    principal.subscription.tier == "premium"
};
