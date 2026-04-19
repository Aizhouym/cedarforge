permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    resource.isFree
};

permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    resource.isFree
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    !resource.isEarlyAccess ||
    context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
};

permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z")
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
    )
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
    )
};

forbid (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    context.activeStreams >= 1
};

forbid (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    context.activeStreams >= 1
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    principal.subscription.tier == "standard" &&
    context.activeStreams >= 2
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    principal.subscription.tier == "standard" &&
    context.activeStreams >= 2
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    principal.subscription.tier == "premium" &&
    context.activeStreams >= 5
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    principal.subscription.tier == "premium" &&
    context.activeStreams >= 5
};