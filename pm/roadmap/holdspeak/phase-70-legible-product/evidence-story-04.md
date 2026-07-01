# Evidence — HS-70-04: Dictation mode, made whole (Activity folded in)

**Date:** 2026-06-30
**Verdict:** done. Activity is no longer a separate top-level door. The
dictation-relevant part (the pre-briefing nudges) already lives in the
Dictation cockpit; the `/activity` ledger is reframed as a **Dictation
sub-view**, reached from the cockpit — nothing lost.

## What was already true

The Dictation cockpit (`/dictation`) already embeds the **pre-briefing nudges**
(`components/dictation/ActivityNudges.astro`, HS-53-04) — the "Dictate with
this" loop that grounds a dictation in a recent activity record. That is the
dictation-relevant half of Activity, and it was already in the mode.

## What shipped

- **`web/src/components/TopNav.astro`** — Activity **removed from the Studio
  tier** (where HS-70-01 had parked it transitionally). Studio is now six tools
  (Workbench, Desk, Agent Desk, Cadence, Commands, Profiles).
- **`web/src/pages/activity.astro`** — reframed as a Dictation sub-view:
  `current="activity"` → `current="dictation"` (the nav shows Dictation active),
  a **"← Dictation"** back link, and retitled "Local activity" → **"Activity
  ledger"** with a sub that names its role ("behind your dictation
  pre-briefing"). The full ledger UI (controls, sources, rules, connectors, the
  nudges panel) is untouched — nothing lost.
- **`web/src/components/dictation/ActivityNudges.astro`** — a **"Manage activity
  →"** link in the cockpit banner, so the ledger is reachable from Dictation.

## Why reframe rather than redirect/port

The `/activity` ledger is 825 lines of working Alpine (`activity-app.js`, 37 KB,
loaded via `?raw`+`new Function`). Porting it into the ES-module cockpit as a
tab, or redirecting `/activity` into `/dictation`, would either risk a large
paradigm-mixing rewrite or **lose the ledger UI entirely**. Reframing it as a
Dictation sub-view (nav shows Dictation, a back link, reached from the cockpit)
achieves the legibility goal — Activity is part of Dictation, not a separate
door — with zero loss and minimal risk.

## Test ripple

Two page-content assertions retargeted for the retitle
("Local activity" → "Activity ledger": `test_web_activity_api.py`,
`test_web_built_mount.py`) and the nav test's route list updated (Activity
removed, a Studio item asserted instead: `test_topnav_renders_with_aria_current`).

## Proof

- **`screenshots/activity-ledger.png`** — `/activity` as a Dictation sub-view:
  "Dictation" active in the nav, the "← Dictation" back link, "Activity ledger",
  the full ledger intact.
- **`screenshots/studio-no-activity.png`** — the Studio dropdown, now six tools
  (Activity gone), on the Dictation cockpit.
- **Tests:** activity API + built-mount + route pre-flight green; full suite
  **3045 passed, 37 skipped**; build green (17 pages).
