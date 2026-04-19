permit (
    principal is Taxpreparer::Professional,
    action in [Taxpreparer::Action::"viewDocument", Taxpreparer::Action::"editDocument"],
    resource is Taxpreparer::Document
) when {
    principal.assigned_orgs.contains({
        organization: resource.owner.organization,
        serviceline: resource.serviceline,
        location: resource.location
    }) &&
    context.consent.client == resource.owner &&
    context.consent.team_region_list.contains(principal.location)
};