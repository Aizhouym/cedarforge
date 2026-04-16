permit (
    principal is Subscriber,
    action == Action::"watch_replay",
    resource is LiveEvent
)
when {
    context.now.datetime > resource.endTime &&
    !resource.requiresPremium
};
