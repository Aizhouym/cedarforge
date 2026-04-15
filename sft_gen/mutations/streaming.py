"""Streaming domain — new SFT mutations.

Already in cedarbench (excluded):
  streaming_base, streaming_add_age_rating, streaming_add_download,
  streaming_add_geo_restriction, streaming_add_trial_tier,
  streaming_full_expansion, streaming_multidevice, streaming_parental_controls,
  streaming_remove_bedtime, streaming_remove_oscars.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

_BASE_SPEC = """\
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
"""


# ── 1. Family plan — Set<FreeMember> on Subscriber (S5 + P2) ─────────────────

class StreamingFamilyPlan(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_family_plan",
            base_scenario="streaming",
            difficulty="medium",
            description="Add familyMembers Set<FreeMember> to Subscriber; family members inherit subscriber watch perms",
            operators=["S5", "P2"],
            features_tested=["set_membership_permit", "delegated_access", "cross_principal"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Subscriber", "familyMembers", "Set<FreeMember>")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 2. Live event — isLive bool + replay (S6 + S7 + P2 + P1 + P9) ────────────

class StreamingLiveEvent(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_live_event",
            base_scenario="streaming",
            difficulty="medium",
            description="Add LiveEvent entity; stream_live requires isLive==true; replay permitted after event ends",
            operators=["S6", "S7", "P2", "P1", "P9"],
            features_tested=["new_entity", "boolean_forbid", "temporal_permit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity LiveEvent = {
    isLive: Bool,
    endTime: datetime,
    requiresPremium: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Live event actions
action stream_live, watch_replay appliesTo {
    principal: [Subscriber],
    resource: [LiveEvent],
    context: {
        now: {
            datetime: datetime,
            localTimeOffset: duration
        }
    }
};""")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 3. Content rating — NC-17 forbidden for kids and non-premium (S3 + P7 + P1) ─

class StreamingContentRating(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_content_rating",
            base_scenario="streaming",
            difficulty="medium",
            description="Add contentRating String to Movie and Show; NC-17 forbidden for kids or non-premium subscribers",
            operators=["S3", "P7", "P1"],
            features_tested=["string_enum", "multi_condition_forbid", "content_gate"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Movie", "contentRating", "String")
        schema = schema_ops.add_attribute(schema, "Show", "contentRating", "String")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 4. Release window — watch forbidden before availableFrom (S4 + P1) ────────

class StreamingReleaseWindow(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_release_window",
            base_scenario="streaming",
            difficulty="easy",
            description="Add availableFrom datetime to Movie; watch forbidden before availableFrom for all users",
            operators=["S4", "P1"],
            features_tested=["datetime_comparison", "universal_forbid", "release_embargo"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Movie", "availableFrom", "datetime")
        spec = _BASE_SPEC + """\
### 6. Release Window (Deny Rule)
- Movies may have an `availableFrom: datetime` attribute defining when the movie becomes
  available for streaming.
- If `context.now < resource.availableFrom`, **watch** is **forbidden** for ALL principals
  — Subscribers and FreeMember alike.
- No role or subscription tier can bypass the release window.
- Guard with `resource has availableFrom`: movies without this attribute are immediately available.
- This differs from the `isEarlyAccess` show rule (which allows premium early access).
  Movie release windows are hard cutoffs with no exceptions.

## Notes (Release Window)
- Cedar datetime: `context.now < resource.availableFrom`.
- The `has` guard is required for optional attribute safety.
- Compare with streaming_base early access (premium exception exists for shows);
  this scenario has NO exceptions for movies.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 5. Geo blocklist — blocked regions forbidden (S5 + S8 + P1) ───────────────

class StreamingGeoBlocklist(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_geo_blocklist",
            base_scenario="streaming",
            difficulty="medium",
            description="Add blockedRegions Set<String> to Movie; context userRegion; watch forbidden if in blocklist",
            operators=["S5", "S8", "P1"],
            features_tested=["set_containment_forbid", "context_gate", "geo_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Movie", "blockedRegions", "Set<String>")
        schema = schema_ops.add_context_field(schema, "watch", "userRegion", "String")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 6. Podcast — new resource type, subscribe-gated download (S6 + S7 + P2) ───

class StreamingPodcast(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_podcast",
            base_scenario="streaming",
            difficulty="medium",
            description="Add Podcast entity; all users can listen; download requires Subscriber; no bedtime on podcasts",
            operators=["S6", "S7", "P2"],
            features_tested=["new_resource_type", "tier_split", "action_differentiation"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Podcast = {
    isFree: Bool,
    isExclusive: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Podcast actions
action listen_podcast appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Podcast],
};

action download_podcast appliesTo {
    principal: [Subscriber],
    resource: [Podcast],
};""")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 7. Concurrent stream limit — context activeStreams (S2 + S8 + P6) ─────────

class StreamingConcurrentLimit(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_concurrent_limit",
            base_scenario="streaming",
            difficulty="medium",
            description="Add maxStreams Long to Subscriber; context activeStreams Long; watch forbidden at limit",
            operators=["S2", "S8", "P6"],
            features_tested=["numeric_threshold", "context_gate", "principal_side_limit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Subscriber", "maxStreams", "Long")
        schema = schema_ops.add_context_field(schema, "watch", "activeStreams", "Long")
        spec = _BASE_SPEC + """\
### 6. Concurrent Stream Limit (Deny Rule)
- Subscribers have a `maxStreams: Long` attribute defining how many concurrent streams
  they are allowed (e.g., standard tier: 1, premium tier: 4).
- Context carries `activeStreams: Long` — the current number of active streams on the account.
- If `context.activeStreams >= principal.maxStreams`, **watch** is **forbidden**.
- The concurrent limit applies to Subscribers only; FreeMember has no stream limit.
- Rent and buy actions are not affected by the stream limit.

## Notes (Concurrent Limit)
- Numeric comparison: `context.activeStreams >= principal.maxStreams`.
- This is a principal-side limit (attribute on Subscriber) checked against context.
- Compare with `streaming_multidevice` (cedarbench) which uses a device-count attribute
  differently. This scenario uses a simpler context-based active-stream count.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 8. Remove FreeMember — subscriber-only model (S11 + S12 + P3) ─────────────

class StreamingRemoveFreeMember(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_remove_freemember",
            base_scenario="streaming",
            difficulty="easy",
            description="Remove FreeMember entity and isFree attribute; subscribers-only platform",
            operators=["S11", "S10", "P3"],
            features_tested=["entity_removal", "attribute_removal", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_entity(base_schema, "FreeMember")
        schema = schema_ops.remove_attribute(schema, "Movie", "isFree")
        schema = schema_ops.remove_attribute(schema, "Show", "isFree")
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 9. Parental override — context flag bypasses bedtime (S8 + P4) ────────────

class StreamingParentalOverride(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_parental_override",
            base_scenario="streaming",
            difficulty="easy",
            description="Add parentalOverride Bool context; bedtime restriction bypassed when parent approves",
            operators=["S8", "P4"],
            features_tested=["context_exception", "unless_clause", "forbid_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_context_field(base_schema, "watch", "parentalOverride", "Bool")
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── 10. Trailer entity — free preview for all (S6 + S7 + P2) ──────────────────

class StreamingTrailer(Mutation):
    def meta(self):
        return MutationMeta(
            id="streaming_trailer",
            base_scenario="streaming",
            difficulty="easy",
            description="Add Trailer entity; any User (unauthenticated) can watch_trailer; no subscription required",
            operators=["S6", "S7", "P2"],
            features_tested=["new_entity", "open_access", "unauthenticated_permit"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity Trailer = {
    movie: Movie,
    durationSeconds: Long,
};""")
        # Add a generic User entity or allow both principal types
        schema = schema_ops.add_action(schema, """\
// Trailer actions
action watch_trailer appliesTo {
    principal: [FreeMember, Subscriber],
    resource: [Trailer],
};""")
        spec = _BASE_SPEC + """\
### 6. Trailer Permissions (Open Access)
- **watch_trailer** is permitted for ANY principal — FreeMember and Subscriber alike,
  with no subscription or tier requirement.
- Trailers are marketing previews; no authentication or subscription gate applies.
- The kid bedtime restriction does NOT apply to trailers (previews are safe for all ages).
- If a Trailer's `durationSeconds > 300` (more than 5 minutes), it is treated as a
  "feature preview" and requires a FreeMember or Subscriber account (no anonymous access).

## Notes (Trailer)
- Trailer is a new entity referencing Movie (`Trailer.movie: Movie`).
- The open-access permit: `permit (principal is [FreeMember, Subscriber], action == watch_trailer, ...)`.
- No forbids beyond the 5-minute preview gate.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    StreamingFamilyPlan(),
    StreamingLiveEvent(),
    StreamingContentRating(),
    StreamingReleaseWindow(),
    StreamingGeoBlocklist(),
    StreamingPodcast(),
    StreamingConcurrentLimit(),
    StreamingRemoveFreeMember(),
    StreamingParentalOverride(),
    StreamingTrailer(),
]

for _m in MUTATIONS:
    register(_m)
