permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor") &&
    resource.studyPhase != "Phase-3"
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor")
};

permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal in Role::"DataManager" &&
    principal.clearanceLevel > 5 &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor")
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal in Role::"ClinicalResearcher" &&
    principal.clearanceLevel > 3 &&
    resource.classification != "HighlyRestricted" &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor") &&
    resource.studyPhase != "Phase-3"
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal in Role::"PrincipalInvestigator" &&
    context.networkRiskScore < 20 &&
    context.isCompliantDevice &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor")
};

permit (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    principal in Role::"DataManager" &&
    principal.clearanceLevel > 5 &&
    resource.projectStatus == "Active" &&
    (principal.department == resource.projectManagingDepartment ||
     principal in Role::"GlobalAuditor")
};

forbid (
    principal is User,
    action == Action::"Edit",
    resource is Document
) when {
    !context.hasPatientConsent
};

forbid (
    principal is User,
    action in [Action::"View", Action::"Edit"],
    resource is Document
) when {
    resource.classification == "HighlyRestricted" &&
    !context.isCompliantDevice
};