permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    resource.projectStatus == "Active" &&
    (principal in Role::"ClinicalResearcher" || principal in Role::"PrincipalInvestigator")
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    resource.projectStatus == "Active" &&
    (principal in Role::"ClinicalResearcher" || principal in Role::"PrincipalInvestigator")
};

forbid (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
) unless {
    principal in Role::"GlobalAuditor"
} when {
    principal.department != resource.projectManagingDepartment
};