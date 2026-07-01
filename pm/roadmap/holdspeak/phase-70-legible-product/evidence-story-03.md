# Evidence — HS-70-03: One arrival — consolidate the three first-run surfaces

**Date:** 2026-06-30
**Verdict:** done. A new user meets **one** arrival, not three. `/welcome` is
the single canonical first-run surface; `/setup` is demoted from a second
"Welcome" to the returning-user health surface; the `/` front door routes new
users to `/welcome` (the HS-70-02 guard).

## The three surfaces, before → after

Before, three surfaces competed to be the front door: `/welcome` (the
full-screen wizard), `/setup` (a second "Welcome to HoldSpeak" cockpit), and
the `/` first-run behavior. After:

- **`/welcome` — the one arrival.** The HS-70-02 guard sends every first-run
  user here; the CLI launch nudge already points first-run users here
  (`test_cli_nudge_points_first_run_user_at_the_wizard`). Verified it already
  **teaches both modes** (the hero: "Voice typing in any app and AI notes,
  action items, and summaries from your meetings"; the Done step's two cards
  "Dictate anywhere" + "Run a meeting") and **lands on Home** (both Done cards
  `href="/"`). No change needed to the wizard itself.
- **`/setup` — demoted to the returning-user health surface.** Its hero eyebrow
  "Welcome to HoldSpeak" (a duplicate arrival identity) became **"Setup &
  health"**. It keeps the doctor/health readout, the primary next-step, and the
  guided-first-dictation troubleshooting — the things a *returning* user needs to
  fix something — but no longer reads as a second onboarding.
- **`/settings`** gains a **"Setup & health check →"** link in its aside, so the
  health surface is discoverable from Settings (not only from a nudge).

## Why demote `/setup` rather than delete it

`/setup` is reached by many returning-user paths (Home's next-action band, the
Desk readiness chip, the CLI nudge, the wizard's troubleshoot link). Redirecting
all of them into the full-screen `/welcome` wizard would degrade a returning
user who just wants to fix one setting. Demoting + retitling removes the
duplicate *arrival* (the phase's actual goal) while keeping the calm fix-it
cockpit for maintenance. The arrival is genuinely one surface; `/setup` is no
longer an arrival.

## What shipped

- **`web/src/pages/setup.astro`** — hero eyebrow "Welcome to HoldSpeak" →
  "Setup & health".
- **`web/src/pages/settings.astro`** — a "Setup & health check →" link in the
  settings aside (+ its scoped `.set-health-link` style).

## Proof

- **`screenshots/welcome-arrival.png`** — `/welcome`, the single arrival (hero
  teaches both modes, 6-step rail, "Get started").
- **`screenshots/setup-health.png`** — `/setup` now reads "SETUP & HEALTH" (not
  a second Welcome), within the app chrome.
- **`screenshots/settings-health-link.png`** — the Settings aside surfaces the
  "Setup & health check →" link.
- **Tests:** `test_web_setup_route.py` + `test_web_welcome_wizard.py` + route
  pre-flight **13 passed** (the wizard still owns "Welcome to HoldSpeak"; the
  first-run guard + CLI nudge still route first-run users to `/welcome`); full
  suite **3045 passed, 37 skipped**; build green (17 pages).
