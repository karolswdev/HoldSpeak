# Tracked items

## QL-301 — Churn spike after onboarding step 3 (product / growth)
**Status:** open · **Owner:** Dana · **Severity:** high
New users drop sharply at onboarding **step 3** (first quest setup):
D7 activation fell from 41% to 33% after the March onboarding redesign.
Funnel shows users reaching the quest-cadence picker and abandoning.
Hypothesis: cadence choice is overwhelming and there is no template.
Drives the customer-signals analysis (`docs/CUSTOMER-SIGNALS-2026Q2.md`).
North-star: directly suppresses WAQC by starving the top of the funnel.

## QL-310 — Guilds: build now vs defer (product decision)
**Status:** in discovery · **Owner:** Priya
Should Stage 5 (Guilds / social) be the next big bet, or do we defer in
favor of fixing activation (QL-301)? Strong qualitative pull for social
accountability, but guilds add moderation, abuse, and privacy surface
and may not move WAQC if activation is the real leak. See
`docs/prd/guilds.md`. **This is the product meeting decision.**

## QL-318 — Q3 milestone scope risk (delivery)
**Status:** planning · **Owner:** Marcus
The draft Q3 roadmap (`docs/roadmap-Q3.md`) bundles Guilds v1, an
onboarding revamp (QL-301 fix), and a streak-engine hardening (QL-322)
into one quarter. Engineering estimate exceeds capacity by ~30%.
Something must be cut or sequenced. **This is the delivery meeting
scope-risk decision.**

## QL-322 — Streak resets on timezone boundary (bug, sev-2)
**Status:** open · **Owner:** Marcus · **Severity:** sev-2
Users in non-UTC timezones (esp. UTC-7/-8 and UTC+9) report streaks
breaking at midnight UTC instead of their local midnight, and an extra
streak loss across the DST spring-forward. Root cause: UTC date math in
`src/server/streaks.ts`. Violates the "streaks never reset on a timezone
bug" invariant. Fix must add non-UTC timezone tests.

## QL-330 — Freemium gate event missing on guild-join path (instrumentation)
**Status:** open · **Owner:** Dana · **Severity:** medium
The `freemium_gate_hit` event fires on quest-create but not on the
guild-join cap, so growth cannot size the guild upgrade funnel. Needs an
event at the 1-guild free cap before any guild rollout.
