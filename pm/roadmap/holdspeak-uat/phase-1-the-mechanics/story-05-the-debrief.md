# HSU-1-05 — The debrief + the triage protocol

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-04
- **Owner:** unassigned

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
    date, pack, deck(s), machine, product version/commit; the score;
    coverage % against the ledger; every non-pass verdict with its
    step, note, screenshot link, and the product log slice around the
    step's time window; the pass list collapsed) and `debrief.json`
    (the same, machine-shaped, stable schema). The log-slice
    correlation is the agent's head start: a FAIL arrives with the
    server's own words attached.
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

- [ ] A finished sitting generates both packet files; `debrief.md`
      opens readable with every non-pass finding carrying note +
      screenshot link + a correctly-windowed product log slice.
- [ ] `debrief.json` is schema-stable and tested (the agent-side
      contract).
- [ ] Coverage % in the packet matches HSU-1-03's math exactly.
- [ ] Findings triage round-trips: set `fix` via the API, regenerate,
      the disposition survives.
- [ ] The backlog block renders in `BACKLOG.md`'s real candidate
      format and cites finding ID + debrief path.
- [ ] `uat/TRIAGE.md` states the four-step ritual and the disposition
      vocabulary; tests green under `uv run pytest -q tests/uat/`.

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
