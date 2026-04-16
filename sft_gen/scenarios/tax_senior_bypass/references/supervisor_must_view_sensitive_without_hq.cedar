permit (
    principal is Taxpreparer::Supervisor,
    action == Taxpreparer::Action::"viewDocument",
    resource is Taxpreparer::Document
) when {
    principal.supervised_orgs.contains(resource.owner.organization)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && resource.isSensitive
    && !context.consent.team_region_list.contains("HQ")
};
