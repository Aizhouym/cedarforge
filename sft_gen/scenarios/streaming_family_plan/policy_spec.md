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
### 6. Family Plan (Delegated Watch Access)
- Subscribers may have a `familyMembers: Set<FreeMember>` attribute listing FreeMember
  accounts that share the subscriber's plan.
- A FreeMember who appears in any Subscriber's `familyMembers` set inherits the
  Subscriber's watch permissions for Movies and Shows.
  - They may watch any Movie (including `needsRentOrBuy` content) if the subscribing
    account has an active subscription.
  - They may watch any Show, subject to the same early-access rules as the subscriber.
- Family members are still subject to the **kid bedtime restriction** if `profile.isKid == true`.
- Family members do NOT inherit rent/buy (Oscar promo) permissions.

## Notes (Family Plan)
- The check requires finding a Subscriber whose `familyMembers.contains(principal)`.
  Cedar cannot directly express "there exists a Subscriber s such that s.familyMembers.contains(me)".
  Use a context attribute: `context.subscriberPlan: Subscriber` (the plan holder), then check
  `context.subscriberPlan.familyMembers.contains(principal)`.
- This tests set-containment with cross-principal-type access delegation.
