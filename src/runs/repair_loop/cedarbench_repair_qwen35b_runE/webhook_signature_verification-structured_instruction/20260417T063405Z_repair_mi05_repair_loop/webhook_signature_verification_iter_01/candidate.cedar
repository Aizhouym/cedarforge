permit (
    principal is WebhookEndpoint,
    action == Action::"deliver",
    resource is Event
) when {
    principal.isVerified &&
    principal.allowedEvents.contains(resource.eventType) &&
    !resource.isInternal
};

permit (
    principal is WebhookEndpoint,
    action == Action::"retry",
    resource is Event
) when {
    principal.isVerified &&
    principal.allowedEvents.contains(resource.eventType) &&
    !resource.isInternal
};

permit (
    principal is WebhookEndpoint,
    action == Action::"inspect",
    resource is Event
) when {
    true
};