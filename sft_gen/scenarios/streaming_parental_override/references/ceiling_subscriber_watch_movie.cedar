permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy &&
    (
        !principal.profile.isKid ||
        context.parentalOverride ||
        (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("6h") &&
         context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("21h"))
    )
};
