permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    (
        !(resource has availableFrom) ||
        (resource has availableFrom && context.now.datetime >= resource.availableFrom)
    ) &&
    !(
        principal.profile.isKid &&
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
        )
    )
};
