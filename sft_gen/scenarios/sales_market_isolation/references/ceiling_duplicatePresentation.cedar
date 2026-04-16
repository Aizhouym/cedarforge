permit (
    principal is User,
    action == Action::"duplicatePresentation",
    resource is Presentation
) when {
    principal.job == Job::"internal" ||
    (
        principal.job != Job::"internal" &&
        principal in resource.ownerMarket &&
        principal in resource.editors
    )
};
