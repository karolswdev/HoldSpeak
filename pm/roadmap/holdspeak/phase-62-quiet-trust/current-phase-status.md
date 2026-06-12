# Phase 62 — Quiet Trust

**Status:** scaffolded (0/4). Opened 2026-06-12 on direct owner feedback:
the privacy-reassurance prose across the UI is "really cringey" — replace
the novels on cards and notifications with a compact **egress badge**
(local · local+cloud · cloud) and redo the affected screenshots. This
reverses the locked Phase-56 "three privacy answers verbatim on every
actionable card" decision.

**Last updated:** 2026-06-12 (scaffolded — the full prose inventory and
every lock pinning the old copy are recorded in the brief §3).

## The thesis — why this phase

Trust should be ambient, not narrated. The header LocalPill already proves
the pattern: one glyph carries the posture. Reading a privacy paragraph on
every Qlippy card and notification is noise that makes the product feel
insecure about itself. One badge, three states, and the prose goes quiet.

## Goal

No UI card or notification narrates privacy. The Qlippy card shell renders
a three-state egress badge from structured data; every reassurance tail in
the web UI is cut or shortened to its functional core; behavioral warnings
stay; docs describe the badge; every user-facing screenshot showing the
old copy is re-shot live.

## Scope

- **In:** the badge component + card shell (HS-62-01); the prose sweep
  across history/welcome/settings/components + flashes (HS-62-02); docs +
  the voice rule + re-shot doc screenshots (HS-62-03); closeout
  (HS-62-04).
- **Out:** the SECURITY/README documentation posture (docs explain once —
  that is allowed); behavioral warnings (wake type-action, shell macros);
  the journal's "Preview only" state string; any backend change.

## Exit criteria (evidence required)

- The Qlippy cards render the badge, never a privacy paragraph; the
  cloud state keeps the target label; locks pin the new pattern.
  (HS-62-01)
- Zero "nothing leaves / stored locally / never sent" reassurance tails
  in web/src outside the allowed explain-once surfaces; build clean.
  (HS-62-02)
- Docs aligned + POSITIONING voice rule + every user-facing-doc
  screenshot showing old copy re-shot from a live run. (HS-62-03)
- Live dogfood proves the badge on real cards with zero page errors;
  full suite green; final-summary; PR merged on green. (HS-62-04)

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-62-01 | The egress badge on Qlippy cards | backlog | none |
| HS-62-02 | The sweep | backlog | HS-62-01 |
| HS-62-03 | Docs + re-shot screenshots | backlog | HS-62-02 |
| HS-62-04 | Closeout | backlog | HS-62-01..03 |

## Where we are

Scaffolded. Next is **HS-62-01 — the egress badge on Qlippy cards**.
