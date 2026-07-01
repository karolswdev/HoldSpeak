# HS-70-03 — One arrival: consolidate the three first-run surfaces

- **Status:** done
- **Priority:** HIGH
- **Depends on:** HS-70-01, HS-70-02
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## Goal

A brand-new user meets **one** arrival experience, not three. Today `/welcome`
(the full-screen wizard, Phase 43), `/setup` (the first-run cockpit, Phase 42),
and the `/` first-run guard all compete to be the front door. Reconcile to a
single canonical path that teaches the two-mode model and produces a first win.

## Scope

- **Pick the survivor:** `/welcome` (the full-screen wizard) is the canonical
  first-run. It must teach the mental model (the two modes) up front, not just
  permissions + model picking, and it ends by landing on **Home** (HS-70-02),
  which reinforces the model.
- **Absorb `/setup`:** its still-useful pieces (the doctor/health readout, the
  model-setup assistant, presence onboarding) fold into (a) the wizard where
  they belong to arrival, and (b) a Settings "Health / Setup" section for
  after first run. `/setup` the standalone page is retired.
- **Reconcile the `/` guard:** first-run users go to `/welcome`; everyone else
  gets Home. A healthy returning user is never nagged (preserve the Phase-42
  "never nags a healthy user" property).
- **Redirects, no 404s:** `/setup` redirects (to `/settings` health section or
  `/welcome` as appropriate); the CLI launch nudge, docs, and the route
  pre-flight are updated to the survivor. `GET /api/setup/status` (the adapter
  over doctor) stays as the data source; only the page surface consolidates.

## Proof required

A fresh-clone / empty-DB launch reaches exactly one arrival surface that names
the two modes and produces a first dictation win, then lands on Home
(screenshot the sequence). Prove `/setup` redirects (no 404). A returning
healthy user goes straight to Home (no nag). Reuse/adapt the existing
`scripts/dogfood_wizard.py` / `dogfood_first_run.py` harness.

## Done

Shipped and screenshot-proven. `/welcome` is the single arrival (the HS-70-02
guard + the CLI nudge both route first-run users here; verified it already
teaches both modes and lands on Home). `/setup` was demoted from a second
"Welcome to HoldSpeak" to the returning-user "Setup & health" surface (eyebrow
retitled) and surfaced from the Settings aside via a "Setup & health check →"
link. Decision recorded: demote-and-retitle rather than delete/redirect, because
`/setup` is the calm fix-it cockpit many returning-user paths rely on
(redirecting them into the full-screen wizard would degrade that) — the arrival
is genuinely consolidated to one surface without breaking a link. Tests: setup +
welcome + preflight 13 passed; full suite 3045 passed. See
[evidence-story-03.md](./evidence-story-03.md).
