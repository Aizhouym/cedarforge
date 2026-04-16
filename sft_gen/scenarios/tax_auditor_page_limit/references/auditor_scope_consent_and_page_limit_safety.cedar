permit (
    principal is Taxpreparer::Auditor,
    action == Taxpreparer::Action::"auditDocument",
    resource is Taxpreparer::Document
)
when {
    principal.auditScope.contains(resource.serviceline)
    && context.consent.client == resource.owner
    && context.consent.team_region_list.contains(principal.location)
    && resource.pageCount <= 100
};
