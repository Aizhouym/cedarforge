permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
) when {
    (
        resource.isFree ||
        (
            context has subscriberPlan &&
            context.subscriberPlan.familyMembers.contains(principal)
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

permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    (
        resource.isFree ||
        (
            context has subscriberPlan &&
            context.subscriberPlan.familyMembers.contains(principal) &&
            (
                !resource.isEarlyAccess ||
                context.now.datetime >= resource.releaseDate ||
                (
                    context.subscriberPlan.subscription.tier == "premium" &&
                    context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
                )
            )
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

permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !(
        principal.profile.isKid &&
        (
            context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h") ||
            context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h")
        )
    )
};

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
