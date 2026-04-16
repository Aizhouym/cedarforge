permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
) when {
    resource.isFree && !principal.profile.isKid
};
