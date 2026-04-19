permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid && (resource.rating != "G" && resource.rating != "PG"))
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    !(resource.isEarlyAccess && context.now.datetime < resource.releaseDate) ||
    (principal.subscription.tier == "premium" &&
     context.now.datetime >= resource.releaseDate.offset(duration("-24h"))) &&
    !(principal.profile.isKid && (resource.rating != "G" && resource.rating != "PG"))
};

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
    action == Action::"rent",
    resource is Movie
) when {
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z") &&
    resource.isOscarNominated
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
) when {
    context.now.datetime >= datetime("2025-02-01T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-31T23:59:59Z") &&
    resource.isOscarNominated
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset) < datetime("2025-01-01T06:00:00Z") ||
        context.now.datetime.offset(context.now.localTimeOffset) >= datetime("2025-01-01T21:00:00Z")
    )
};

forbid (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    principal.profile.isKid &&
    (
        context.now.datetime.offset(context.now.localTimeOffset) < datetime("2025-01-01T06:00:00Z") ||
        context.now.datetime.offset(context.now.localTimeOffset) >= datetime("2025-01-01T21:00:00Z")
    )
};