permit (
    principal is FreeMember,
    action == Action::"listen_podcast",
    resource is Podcast
) when {
    resource.isFree &&
    !resource.isExclusive
};
