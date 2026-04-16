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
