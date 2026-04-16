permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    (
        !resource.isEarlyAccess ||
        context.now.datetime >= resource.releaseDate ||
        (
            principal.subscription.tier == "premium" &&
            context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
        )
    ) &&
    !(
        principal.profile.isKid &&
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
        )
    )
};
