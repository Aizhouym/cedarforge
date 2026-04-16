permit (
    principal is User,
    action == Action::"signContract",
    resource is Contract
) when {
    principal.job == Job::"internal" &&
    !resource.isSigned
};
