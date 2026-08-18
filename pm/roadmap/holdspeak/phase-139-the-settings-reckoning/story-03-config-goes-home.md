# HS-139-03 — Config goes home

- **Project:** holdspeak
- **Phase:** 139
- **Status:** done
- **Depends on:** 139-01
- **Unblocks:** 139-05
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

Seven settings configure one specific object but live in the global
panel (census FOLD-TO-OBJECT rows 31, 32, 39, 40, 43, 66): mic device,
system-audio device, auto-export, export format, intel realtime model,
companion GitHub repo. Edit-in-world law: config lives on the thing.

## Scope

- **In:** Meetings surface gains its own capture/export config section
  (mic device, system audio device, auto-export, format) using the same
  `withRevision()` write path; intel realtime model joins the Models
  module beside the other model paths; companion GitHub repo moves to
  the Delivery/integration surface it actually configures
  (trust_destinations.py:63,83 names the consumer). The Settings panel
  rows are removed. The Delivery module's existing "CONFIG LIVES IN
  DELIVERY" pattern (settingsPrefs pattern) is the model to follow.
- **Out:** redesigning the Meetings surface beyond adding the config
  section; new persistence (same config fields, new render home).

## Acceptance criteria

- [ ] Each of the seven renders exactly once, on its object's surface,
  and nowhere in the Settings panel.
- [ ] Writes still round-trip through /api/settings with revision
  concurrency; a stale write still refuses honestly.
- [ ] The Meetings config section follows the surface grammar (no modal,
  no prose, mic on text inputs where applicable).

## Test plan

- **Unit:** settings route tests green; consumer paths unchanged.
- **Web:** vitest for the Meetings config section + updated settings
  vitest proving removal.
