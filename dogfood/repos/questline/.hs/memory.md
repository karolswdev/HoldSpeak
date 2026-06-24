# Durable product facts

**North-star metric.** The one number we move is **WAQC** — Weekly
Active Quests Completed per user. Every roadmap bet is justified by its
expected effect on WAQC. Activation (D7) and W4 retention are read as
inputs to it, never as substitutes.

**Everything ships behind a flag.** No user-facing change reaches
production without a feature flag in `src/lib/flags.ts`. Flags follow
the rollout ladder: off → dogfood (team) → 10% → GA. There is no
"just merge it" path.

**Everything is tracked.** Every meaningful interaction emits a tracked
event through `src/lib/analytics.ts` (`track(event, props)`). If a new
feature does not emit at least one event, it is not done — we cannot
move a number we cannot see.

**Streaks must never reset on a timezone bug.** Streak continuity is the
emotional core of the product. A streak may only break when the user
genuinely misses their quest window in *their own* local timezone.
Server-UTC date math that drops a day across a DST boundary or a
non-UTC user is a sev-2 incident, not a nicety. See QL-322.

**Freemium gate.** Free tier: max **3 active quests** and **1 guild**.
Paid (questline Pro) removes both caps and unlocks XP boosts. The gate
lives at quest-create and guild-join time and must always emit a
`freemium_gate_hit` event so growth can size the upgrade funnel.

**Guilds are social and risky.** Anything multiplayer (guilds, shared
streaks, leaderboards) raises moderation, abuse, and privacy surface.
Social features get an explicit non-goals list and a kill switch.

**We are consumer, not B2B.** Decisions optimize for individual
motivation and habit formation, not team/admin/seat features.
