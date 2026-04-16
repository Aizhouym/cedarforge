permit (
    principal is Subscriber,
    action == Action::"stream_live",
    resource is LiveEvent
)
when {
    resource.isLive &&
    (!resource.requiresPremium || principal.subscription.tier == "premium")
};
