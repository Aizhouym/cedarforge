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
### 6. Live Event Permissions
- **stream_live**: A Subscriber may stream a live event IF `resource.isLive == true`.
  If `resource.isLive == false`, stream_live is forbidden for all users (event not live).
- **watch_replay**: A Subscriber may watch the replay ONLY after the event ends:
  `context.now > resource.endTime`. Replay before the event ends is forbidden.
- If `resource.requiresPremium == true`, both stream_live and watch_replay require
  the Subscriber to have `subscription.tier == "premium"`.
- FreeMember principals cannot stream live events or watch replays.

## Notes (Live Event)
- stream_live forbid: `forbid ... when { !resource.isLive }`.
- watch_replay forbid: `forbid ... when { context.now <= resource.endTime }`.
- Premium gate: `forbid ... when { resource.requiresPremium && principal.subscription.tier != "premium" }`.
