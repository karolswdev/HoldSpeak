# PRD (draft): Guilds — social accountability

**Status:** Discovery · **Owner:** Priya · **Issue:** QL-310
**Stage:** 5 · **Last updated:** 2026-06-08

## Problem

Habit formation is lonely. Our strongest qualitative signal is that
users who tell someone about their goals stick around longer, but
questline today is single-player. Churned users repeatedly cite "I just
forgot / nobody noticed" (see `docs/CUSTOMER-SIGNALS-2026Q2.md`). We
believe lightweight social accountability could lift retention and,
through it, **WAQC**.

## Goals

- Let a user create or join a **guild** (small group, ~3–12 people).
- Show guildmates' streak progress on a shared board (read-only first).
- Send opt-in nudges when a guildmate is about to lose a streak.
- Emit `guild_created` / `guild_joined` and a guild-scoped
  `freemium_gate_hit` (free = 1 guild).

## Non-goals (v1)

- Public/discoverable guilds. v1 is invite-only.
- Chat / free-text messaging (moderation cost too high for v1).
- Leaderboards with competitive ranking (motivation risk — can demoralize).
- Cross-guild membership beyond the free 1-guild cap.

## Open questions

1. **Does social actually move WAQC, or just feel good?** We have no
   experiment yet. Risk: it's a feature we *want* more than users *need*.
2. **Activation vs social — what's the real leak?** QL-301 says we lose
   people at onboarding step 3. Fixing that may beat any social feature.
   Sequencing is the core QL-310 decision.
3. **Moderation surface.** Even invite-only guilds enable harassment via
   nudges/names. What's the minimum safe v1 (report + kill switch)?
4. **Privacy.** What guildmate data is shared by default, and is it
   opt-in? Sharing streaks implies sharing failure.

## Success metric

A 10% guild experiment is **WAQC-positive** vs control over 4 weeks,
with no retention regression and no moderation incidents.
