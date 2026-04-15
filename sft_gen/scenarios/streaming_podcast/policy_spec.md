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
### 6. Podcast Permissions
- **listen_podcast**: Any Subscriber or FreeMember may listen to a Podcast where
  `isFree == true`. A Subscriber may listen to any Podcast (free or not).
  FreeMember can only listen to free podcasts.
- **download_podcast**: Only Subscribers may download podcasts.
  FreeMember cannot download podcasts.
- If `isExclusive == true`, **listen_podcast** requires a `"premium"` subscription tier.
  Non-premium Subscribers and FreeMember cannot listen to exclusive podcasts.
- The **kid bedtime restriction** does NOT apply to Podcasts — audio-only content
  has no time restriction.

## Notes (Podcast)
- Podcast is a new resource type parallel to Movie and Show.
- The tier split (listen vs. download) is a common monetization pattern.
- No bedtime forbid: the bedtime rule is scoped to `watch` action only.
