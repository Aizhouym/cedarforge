permit (
    principal is User,
    action == Action::"viewContract",
    resource is Contract
) when {
    principal.job == Job::"internal" ||
    (principal.job != Job::"customer" &&
     principal in resource.presentation.editors)
};
