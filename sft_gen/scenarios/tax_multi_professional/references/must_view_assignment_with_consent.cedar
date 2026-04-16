permit (
    principal is Taxpreparer::Professional,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
)
when {
    resource.assignedProfessionals.contains(principal)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
};
