---
pattern: "remove entity"
difficulty: easy
features:
  - subscriber-only access
  - no free tier
  - simplified model
domain: streaming service
source: mutation (streaming domain)
---

# Streaming Service — Policy Specification (Subscriber-Only)

## Context

This policy governs a streaming service with only Subscriber principals.
FreeMember accounts have been removed. All access requires an active subscription.

Subscribers have `subscription.tier` (String) and `profile.isKid` (Bool).
Movies: `needsRentOrBuy`, `isOscarNominated` (Bool).
Shows: `isEarlyAccess` (Bool), `releaseDate` (datetime).

## Requirements

### 1. Subscriber Watch — Shows
- A Subscriber may watch any Show, UNLESS `isEarlyAccess == true` AND
  `context.now < resource.releaseDate`.
- Premium subscribers may watch early-access shows up to 24h before release.

### 2. Subscriber Watch — Movies
- A Subscriber may watch any Movie, UNLESS `needsRentOrBuy == true`.

### 3. Oscar Promo (Rent/Buy)
- A Subscriber may rent or buy an Oscar-nominated Movie within the promo window.

### 4. Kid Bedtime Restriction (Deny Rule)
- If `profile.isKid == true`, watch is forbidden before 06:00 or after 21:00.

## Notes
- FreeMember entity and `isFree` attributes removed entirely.
- No free-tier logic needed: all content access is subscription-gated by default.
- Cedar denies by default.
