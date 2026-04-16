permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
) when {
    !resource.needsRentOrBuy &&
    !(principal.profile.isKid &&
      (context.now.datetime.offset(context.now.localTimeOffset).toTime() >= duration("21h")
       || context.now.datetime.offset(context.now.localTimeOffset).toTime() < duration("6h"))) &&
    (resource.contentRating != "R" || !principal.profile.isKid) &&
    (resource.contentRating != "NC-17"
     || (!principal.profile.isKid && principal.subscription.tier == "premium"))
};
