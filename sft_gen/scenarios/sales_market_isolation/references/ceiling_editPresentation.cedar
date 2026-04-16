permit (
    principal is User,
    action == Action::"editPresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal.job != Job::"customer" &&
        principal in resource.ownerMarket &&
        principal in resource.editors
    )
};
