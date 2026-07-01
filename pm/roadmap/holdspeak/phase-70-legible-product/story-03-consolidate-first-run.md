# HS-70-03 — One arrival: consolidate the three first-run surfaces

- **Status:** todo
- **Priority:** HIGH
- **Depends on:** HS-70-01, HS-70-02
- **Evidence:** _(added at close)_

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

_(filled at close)_
