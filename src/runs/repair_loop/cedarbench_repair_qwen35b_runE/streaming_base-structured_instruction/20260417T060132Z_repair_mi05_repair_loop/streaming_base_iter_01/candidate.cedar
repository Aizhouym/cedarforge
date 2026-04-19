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
    (
        principal.subscription.tier == "premium" &&
        context.now.datetime >= resource.releaseDate.offset(-duration("24h")) &&
        context.now.datetime < resource.releaseDate
    )
};

permit (
    principal is FreeMember,
    action == Action::"rent",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime < datetime("2025-03-01T00:00:00Z")
};

permit (
    principal is FreeMember,
    action == Action::"buy",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime < datetime("2025-03-01T00:00:00Z")
};

permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime < datetime("2025-03-01T00:00:00Z")
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime < datetime("2025-03-01T00:00:00Z")
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() > duration("21:00:00") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("06:00:00")
    )
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset).toTime() > duration("21:00:00") ||
        context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("06:00:00")
    )
};