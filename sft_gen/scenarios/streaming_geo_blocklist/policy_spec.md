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
### 6. Geographic Blocklist (Deny Rule)
- Movies have a `blockedRegions: Set<String>` attribute listing regions where the movie
  is geographically blocked (e.g., `{"FR", "DE", "IT"}`).
- Context carries `userRegion: String` (e.g., `"FR"`) set by the geolocation layer.
- If `resource.blockedRegions.contains(context.userRegion)`, **watch** is **forbidden**
  for ALL principals in the blocked region.
- No subscription tier bypasses a geographic block — this is a licensing restriction.
- Movies with an empty `blockedRegions` set are available globally.

## Notes (Geo Blocklist)
- Set containment: `resource.blockedRegions.contains(context.userRegion)`.
- Compare with `streaming_add_geo_restriction` (cedarbench) which uses an allowlist
  (`allowedRegions: Set<String>`). This mutation uses a blocklist (inverse logic).
- The blocklist is checked via `.contains()` on a Set<String> (not entity set).
