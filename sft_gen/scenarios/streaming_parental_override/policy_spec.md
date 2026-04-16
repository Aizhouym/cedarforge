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
For `watch` requests, context carries `now: { datetime, localTimeOffset }`
and `parentalOverride: Bool`.

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
### 6. Parental Override for Bedtime Restriction
- The kid bedtime restriction (§5) can be bypassed when a parent or guardian explicitly
  approves late viewing.
- Context carries `parentalOverride: Bool`. When `context.parentalOverride == true`, the
  bedtime forbid rule does NOT apply — a kid profile may watch outside the 06:00–21:00 window.
- The parental override does NOT bypass content rating restrictions (future scenarios).
- A non-kid subscriber's `parentalOverride` value is irrelevant — the bedtime rule only
  applies when `profile.isKid == true`.

## Notes (Parental Override)
- Implement as an `unless` clause on the bedtime forbid:
  `forbid watch when <bedtime condition> unless { context.parentalOverride }`.
- Compare with `streaming_parental_controls` (cedarbench) which adds controls;
  this adds an override mechanism for the existing bedtime rule.
