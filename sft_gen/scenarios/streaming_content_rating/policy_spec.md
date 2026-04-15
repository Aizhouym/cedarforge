---
pattern: "base subscription tiers"
difficulty: easy
features:
  - subscriber/freemember tiers
  - datetime-based rules
  - oscar promo window
domain: streaming service
source: mutation (streaming domain)
---

# Streaming Service — Policy Specification

## Context

This policy governs access control for a streaming video platform.
Principal types: FreeMember and Subscriber. Resources: Movie and Show.
Subscribers have `subscription.tier` (String) and `profile.isKid` (Bool).
Movies have: `isFree`, `needsRentOrBuy`, `isOscarNominated` (Bool).
Shows have: `isEarlyAccess`, `isFree` (Bool) and `releaseDate` (datetime).
Context carries `now: datetime`.

## Requirements

### 1. Subscriber Watch — Shows
- A Subscriber may watch any Show, UNLESS `isEarlyAccess == true` AND
  `context.now < resource.releaseDate`.
- Premium subscribers may watch early-access shows up to 24h before release.

### 2. Subscriber Watch — Movies
- A Subscriber may watch any Movie, UNLESS `needsRentOrBuy == true`.

### 3. FreeMember Watch
- A FreeMember may watch any Movie or Show where `isFree == true`.

### 4. Oscar Promo (Rent/Buy)
- A Subscriber may rent or buy an Oscar-nominated Movie within the promo window
  (2025-02-01 to 2025-03-31).

### 5. Kid Bedtime Restriction (Deny Rule)
- If `profile.isKid == true`, watch is forbidden before 06:00 or after 21:00 local time.

## Notes
- Cedar extension types: `datetime(...)` and `duration(...)`.
- duration() uses Go-style syntax: "24h", "-24h", "1h30m".
- Cedar denies by default.
### 6. Content Rating Restriction (Deny Rules)
- Movies and Shows have a `contentRating: String` attribute with values:
  `"G"`, `"PG"`, `"PG-13"`, `"R"`, `"NC-17"`.
- For **NC-17** rated content:
  - **watch** is **forbidden** for Subscribers whose `profile.isKid == true`.
  - **watch** is **forbidden** for Subscribers whose `subscription.tier != "premium"`.
  - FreeMember principals cannot watch NC-17 content regardless of isFree status.
- For **R** rated content:
  - **watch** is **forbidden** for Subscribers whose `profile.isKid == true`.
  - Non-kid adult subscribers of any tier may watch R-rated content.
- G, PG, and PG-13 ratings have no additional restrictions beyond base rules.

## Notes (Content Rating)
- NC-17 requires two conditions to both pass: adult account AND premium tier.
- String comparison: `resource.contentRating == "NC-17"`.
- The kid bedtime restriction (§5) and content rating restriction (§6) are independent.
