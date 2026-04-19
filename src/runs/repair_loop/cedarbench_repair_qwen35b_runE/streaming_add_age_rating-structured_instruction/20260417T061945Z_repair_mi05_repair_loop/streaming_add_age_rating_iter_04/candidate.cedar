permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid && (resource.rating != "G" && resource.rating != "PG")) &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    (!resource.isEarlyAccess ||
     (principal.subscription.tier == "premium" &&
      context.now.datetime >= resource.releaseDate.offset(duration("-24h")))) &&
    !(principal.profile.isKid && (resource.rating != "G" && resource.rating != "PG")) &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
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
    resource is Show
) when {
    principal.profile.isKid &&
    resource.isEarlyAccess &&
    principal.subscription.tier == "premium" &&
    context.now.datetime < resource.releaseDate.offset(duration("-24h"))
};