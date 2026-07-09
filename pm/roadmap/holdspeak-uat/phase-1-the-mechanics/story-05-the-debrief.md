# HSU-1-05 — The debrief + the triage protocol

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** done
- **Depends on:** HSU-1-04
- **Owner:** agent

## Problem

A pile of verdicts is not the deliverable — the *joint review* is: the
owner and the agent looking at the same record and deciding, finding
by finding, fix / won't-fix / by-design. That needs two things the
verdicts alone don't give: a debrief packet shaped for both readers
(markdown for the human, JSON for the agent), and a written protocol
for the ritual so it happens the same way every sitting and its output
lands somewhere durable.

## Scope

- In:
  - **The debrief packet** — generated at sitting end into
    `uat/_runs/<run_id>/debrief/`: `debrief.md` (the sitting header —
    date, pack, recipes/deck(s), machine, product version/commit,
    which surfaces sat; the score **per surface and overall**, a
    surface never sat named as such, not averaged away; coverage %
    against the ledger per surface; every non-pass verdict with its
    step, **surface**, note, screenshot link, and the product log
    slice around the step's time window; the pass list collapsed) and
    `debrief.json` (the same, machine-shaped, stable schema). The
    log-slice correlation is the agent's head start: a FAIL arrives
    with the server's own words attached. Cross-surface disagreement
    is first-class: a step that passed on web and failed on iPhone is
    one finding wearing both verdicts — the split IS the signal.
  - **Findings** — each non-pass verdict becomes a finding with a
    stable ID (`UAT-<run>-<n>`), a triage state
    (`untriaged | fix | wont-fix | by-design | duplicate`), and a
    disposition note. Triage states are written back to the run DB
    (via conductor API — the site's sitting-end screen and the agent
    can both set them).
  - **The triage protocol** — `uat/TRIAGE.md`: the ritual. (1) The
    human finishes the sitting. (2) The agent reads `debrief.json` +
    the log slices and annotates each finding with a first-pass
    hypothesis. (3) Owner + agent walk the findings together and set
    dispositions. (4) Every `fix` is appended to
    `pm/roadmap/holdspeak/BACKLOG.md` in that file's existing
    candidate format, citing the finding ID and the debrief path —
    the harness *proposes* the append (a generated block to paste or
    apply), the commit rides the normal PMO gate.
  - Conductor API: `POST /api/runs/{id}/debrief` (generate),
    `GET /api/runs/{id}/debrief`, `PATCH /api/findings/{id}` (triage),
    `GET /api/runs/{id}/findings/backlog-block` (the BACKLOG-ready
    text).
- Out: auto-filing GitHub issues (the product's actuator flow exists
  for that; a UAT finding feeds BACKLOG, and BACKLOG feeds phases);
  any automatic edit to `pm/roadmap/holdspeak/BACKLOG.md` (human-held
  paste/apply, gate-committed); trend dashboards across sittings
  (Phase 2 candidate).

## Acceptance criteria

- [x] A finished sitting generates both packet files (`debrief.md` +
      `debrief.json`) into `uat/_runs/<run>/debrief/`; `debrief.md` opens
      readable with every non-pass finding carrying note + screenshot
      link + a product log slice windowed around the step's timestamp.
- [x] `debrief.json` is schema-stable and tested — the agent-side
      contract (`test_debrief.py::test_debrief_json_schema_stable`).
- [x] Coverage % in the packet is HSU-1-03's `pack_coverage`, per surface
      and overall; a cross-surface split renders as one finding carrying
      both verdicts (`cross_surface.passed_on`).
- [x] Findings triage round-trips: `PATCH /api/findings/<id>` to `fix`,
      regenerate, the disposition survives (upsert preserves triage).
- [x] The backlog block renders in `BACKLOG.md`'s real candidate-table
      format and cites finding ID + debrief path; the harness proposes,
      the human pastes (gate-committed).
- [x] `uat/TRIAGE.md` states the four-step ritual and the disposition
      vocabulary; tests green under `uv run pytest -q tests/uat/` (81 local).

## Test plan

- Unit: packet assembly from a fixture run DB (all verdict verbs
  represented), log-window slicing, backlog-block formatting.
- Integration: full loop — staged run, scripted verdicts via the
  conductor API, generate, triage, regenerate.
- Manual / device: the real triage of the first sitting is HSU-1-06's
  closing beat.

## Notes / open questions

- Debrief packets live under gitignored `uat/_runs/`; a triaged
  sitting worth keeping gets its packet copied into the relevant
  roadmap evidence dir when a finding ships — the debrief cites, the
  evidence file proves.
