# Roadmap (draft) — Q3 2026

**Status:** Planning · **Owner:** Marcus (delivery) / Priya (product)
**Scope-risk issue:** QL-318 · **Last updated:** 2026-06-10

## Theme

Stop the leaks, then place the social bet. Q2 surfaced two bleeds
(activation at onboarding step 3, streak fairness for non-UTC users) and
one big opportunity (guilds). Q3 must decide how much of all three fits.

## Candidate milestones

| # | Milestone | Drives | Est. (eng-weeks) | Confidence |
|---|-----------|--------|------------------|------------|
| M1 | Onboarding revamp (template quests at step 3) | QL-301 | 4 | High |
| M2 | Streak engine timezone hardening | QL-322 | 2 | High |
| M3 | Guilds v1 (invite-only, read-only board, nudges) | QL-310 | 8 | Medium |
| M4 | Guild freemium gate event + funnel | QL-330 | 1 | High |

**Total estimate: ~15 eng-weeks. Q3 capacity: ~11 eng-weeks.**

## The scope risk (QL-318)

The bundle is **~30% over capacity**. All four cannot ship at quality in
Q3. Engineering flags Guilds v1 (M3) as the single biggest, least
certain line — and the one most likely to slip and starve the high-
confidence fixes.

### Options on the table

- **A — Fixes first, defer Guilds.** Ship M1 + M2 + M4 (~7 wks), run a
  small Guilds discovery spike with the slack, decide Guilds for Q4.
  Safest for WAQC; honors QL-301 being the real leak.
- **B — Guilds-led, cut a fix.** Ship M3 + M2, defer the onboarding
  revamp. Highest upside if social moves WAQC, but bets on the unproven
  and leaves the known activation leak bleeding.
- **C — Thin-slice everything.** Reduce Guilds v1 scope (board only, no
  nudges) to fit M1 + M2 + M4 + thin-M3. Risk: a half-guild that proves
  nothing and still costs moderation review.

## Recommendation (for the delivery review)

Lean **A** unless the product review (QL-310) produces evidence that
social moves WAQC. Sequence: M2 (sev-2 fix) → M1 → M4, then a Guilds
discovery spike. The scope call is the meeting's job.
