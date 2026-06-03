# HS-35-04 — Spoken-e2e breadth: incident retro

- **Status:** not-started.

## Goal

The one spoken-meeting e2e scenario (`tests/e2e/test_spoken_meeting_e2e.py`) covers
balanced / architecture / delivery / product only. The **incident** and **comms**
plugin chains have no spoken end-to-end coverage. Add the second scenario Phase 29's
handoff named — an incident retro — so `incident_timeline`, `runbook_delta`,
`risk_heatmap`, `stakeholder_update_drafter`, and `decision_announcement_drafter`
get real `say` → Whisper → MIR → plugins → web coverage.

## Scope

- A second spoken scenario in `tests/e2e/test_spoken_meeting_e2e.py`: a short
  incident-postmortem script (detection → impact → timeline → root cause → runbook
  change → stakeholder update / decision announcement) driving the **incident**
  profile/intents (and comms via the announcement language).
- Assert the incident + comms plugins fire and produce artifacts (mirror the
  existing scenario's assertions); capture screenshots if the existing harness does.
- Opt-in exactly like the existing scenario: module-skips without
  `HOLDSPEAK_SPOKEN_E2E=1`; runs against the real LAN LLM (`.43`) + Whisper `tiny` +
  Chromium (transient install). Committed green-or-skipped; **verified** by running
  it once via the `.43` box.

## Test plan

- `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s` (dangerouslyDisableSandbox
  to reach `.43`) — the new incident scenario passes; incident + comms artifacts
  present.
- Default `uv run pytest -q --ignore=tests/e2e/test_metal.py` — module-skips the
  spoken e2e (no opt-in), full suite green.

## Done when

- [ ] A second spoken-e2e scenario (incident retro) exercises the incident + comms
      chains end-to-end; assertions confirm those plugins' artifacts.
- [ ] Opt-in/skip behavior matches the existing scenario; full suite green without
      the opt-in.
- [ ] Verified once against the real `.43` LLM (evidence: run output / screenshots).
