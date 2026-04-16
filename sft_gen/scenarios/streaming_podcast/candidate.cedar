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
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
) when {
    (!resource.isEarlyAccess ||
     principal.subscription.tier == "premium") &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
       context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")))
};

permit (
    principal is Subscriber,
    action == Action::"rent",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-02T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};

permit (
    principal is Subscriber,
    action == Action::"buy",
    resource is Movie
) when {
    resource.isOscarNominated &&
    context.now.datetime >= datetime("2025-02-02T00:00:00Z") &&
    context.now.datetime <= datetime("2025-03-02T23:59:59Z")
};

permit (
    principal is FreeMember,
    action == Action::"listen_podcast",
    resource is Podcast
) when {
    resource.isFree &&
    !resource.isExclusive
};

permit (
    principal is Subscriber,
    action == Action::"listen_podcast",
    resource is Podcast
) when {
    !resource.isExclusive ||
    principal.subscription.tier == "premium"
};

permit (
    principal is Subscriber,
    action == Action::"download_podcast",
    resource is Podcast
) when {
    true
};
