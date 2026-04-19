permit (
    principal is Subscriber,
    action == Action::"stream",
    resource is Content
) when {
    principal.isActive &&
    (resource.isPreview ||
     (principal.plan == "free" && resource.tier == "free") ||
     (principal.plan == "basic" && (resource.tier == "free" || resource.tier == "basic")) ||
     (principal.plan == "premium" &&
      (resource.tier == "free" || resource.tier == "basic" || resource.tier == "premium")))
};

permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Content
) when {
    principal.isActive &&
    (principal.plan == "basic" || principal.plan == "premium") &&
    (principal.plan == "basic" && (resource.tier == "free" || resource.tier == "basic")) &&
    (principal.plan == "premium" &&
     (resource.tier == "free" || resource.tier == "basic" || resource.tier == "premium"))
};

permit (
    principal is Subscriber,
    action == Action::"share",
    resource is Content
) when {
    principal.isActive &&
    principal.plan == "premium"
};