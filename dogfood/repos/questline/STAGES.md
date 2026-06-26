# questline — stages

What's shipped, what's open. One line of outcome per stage.

## Done

- **Stage 1 — Auth & onboarding** _(2026-01-15)_ — email auth, session
  cookies, 4-step onboarding wizard. D7 activation baseline 41%.
- **Stage 2 — Quest CRUD** _(2026-02-12)_ — create/edit/archive/complete
  quests with daily/weekly/N-per-week cadence; freemium gate at 3 active
  quests landed.
- **Stage 3 — Streaks & XP** _(2026-03-20)_ — streak engine, XP with
  streak multipliers, the 🔥 streak surface on the quests page.
- **Stage 4 — Analytics & events** _(2026-04-22)_ — the `track()` event
  pipeline + Event model; WAQC, activation, and funnel dashboards live.

## Open

- **Stage 5 — Guilds (social)** — _IN DISCOVERY._ Should social
  accountability be the next bet, or do we defer to fix activation
  first? Decision tracked in QL-310; draft spec in
  `docs/prd/guilds.md`. This is the open **product** question.
- **Q3 delivery milestone** — _PLANNING._ Draft quarter
  (`docs/roadmap-Q3.md`) bundles Guilds v1 + onboarding revamp + streak
  hardening; estimate is ~30% over capacity (QL-318). Needs a scope
  call. This is the open **delivery** question.
