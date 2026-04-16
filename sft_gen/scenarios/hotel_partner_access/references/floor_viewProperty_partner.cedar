permit (
    principal is User,
    action == Action::"viewProperty",
    resource is Property
) when {
    resource.partnerCode != "" &&
    context.providedPartnerCode == resource.partnerCode
};
