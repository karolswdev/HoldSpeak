# PHILO-2-01 - The rulebook and the state atlas

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** see the phase status doc
- **Owner:** both brains (co-authored; the other checks)

## Problem

Three audits measured properties and callers; the owner's sitting found two dead basics in two clicks: an edge with no effect (a receipt's Open) and a state with no face (an empty brief). Nothing in the tree defines the chain a verb must close, or the states a face must render. Without one rulebook, two passes cannot be compared and a council cannot rule.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `docs/internal/philo/briefs/graph-audit-brief.md` is the ONE brief both brains run, verbatim (this story ratifies it; it is drafted at charter).
- [ ] The four definitions (edge, interface, connection, action) and the four questions are pinned with examples from the sitting.
- [ ] The outcome law (brief §3) is stated: a diff is evidence to inspect, not a success criterion; an enabled action that promises a change and produces neither it nor an intelligible refusal is a finding; an unexplained zero diff is unresolved, never pass; reads and presentation owe no receipt (Article XI.5).
- [ ] The state atlas (brief §4) lists REACHABLE cases, each with a stable id, source evidence, edge ids, preconditions, a production setup recipe, fixture and clock settings, expected transition and presentation, and execution limits; derived from Phase 1 lifecycle/failure records and producer code, never a Cartesian product; `quiet` is not an attention_state.
- [ ] The first-use candidates (brief §5) are mapped to job, starting state, trigger, expected result and source of priority, ordered by SITTING-07.md; the owner DEFERRED the selection to the two brains (2026-09-22) and the ruled selection is recorded below, checked by Astra.
- [ ] The graph schema (brief §8) is delivered as a machine-validatable JSON Schema joining Phase 1 record ids: root provenance, nodes, links with relations, cases, observations (one per run/case/brain/pass/viewport, never overwritten), claim reviews, findings and resolutions; verdicts pass/fail/blocked/not-run/not-applicable.
- [ ] Findings have three bins (product defect; doc drift; tooling debt) and one ranking: cost to the owner on a Tuesday.

## Test plan

- **Unit:** `tests/unit/test_philo_graph_schema.py` — the JSON Schema validates a worked example graph and rejects: an unresolved link endpoint, an observation without provenance, a finding without a bin, a case without an expected-result predicate; the atlas file validates against its own schema (no phrase-presence tests).
- **Integration:** n/a.
- **Manual / device:** the owner reads the brief once and says whether the twenty are his twenty.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.

## The owner's selection — ruled on his deferral, 2026-09-22

The owner, asked to select the first-use cases: "No, dude. You and Astra? You push this forward..." Per the standing rule (when he defers: rule, record, act, tell him), Muad'Dib rules and Astra checks. The selected set follows SITTING-07.md's journey, adds the two defects his sitting hit and the first gripe of his first use, and nothing else. Eleven jobs; the trigger count is whatever they need.

| # | Job (owner result) | Starting state | Triggers | Expected result | Priority source |
|---|---|---|---|---|---|
| J1 | Get past the gate | fresh desk, first screen VOICE TYPING | Continue later; or speak one sentence (fixture WAV) → Kept | the desk; or the words kept with a receipt | SITTING-07 step 0; owner's first use 2026-09-20 |
| J2 | See what the desk asks of me | fresh desk | arrival (observation) | one SETUP row naming what is missing; the head counts what asks; an offer does not count | SITTING-07 step 1 |
| J3 | Give the desk an engine | no engine / missing profile `legacy-intel` | Choose an engine → Add an engine → address → Check → Use this for summaries | READY; the SETUP row gone | SITTING-07 step 2; fresh-desk log 2026-09-21 |
| J4 | Have one meeting on the desk | engine set | Record → Stop (fixture WAV at the input boundary); or Import a sound file | a meeting row with its length; no summary yet; no error | SITTING-07 step 3 (alternatives) |
| J5 | Know where the summary will run | one meeting | open the meeting (observation beside Run summary) | the planned host, before the click | SITTING-07 step 4; Article III |
| J6 | Get the summary | J5 | Run summary (real LAN engine) | the host that DID run it; the summary text; technical completion and usefulness reported separately | SITTING-07 step 5 |
| J7 | Find it again after a restart | J6 | stop the hub; start it; find the summary | the same summary in two moves or less | SITTING-07 step 6 |
| J8 | Type by voice into another app | hub up | hold ⌥R, speak, release | words at the cursor of the other app | SITTING-07 step 7 — UNEXERCISED by the rig (native hotkey, other-app delivery); the owner's sitting observes it |
| J9 | Open what the desk remembered | +1 sweep (15 min) | Desk memory → a receipt's Open | the Rhythm face opens; a doorless receipt shows no Open | sitting defect 1, 2026-09-21 |
| J10 | Get a brief, and another | fresh desk; then +1 day | Generate brief → (reload) → Generate again | the brief's own words stay on the face; a second POST; a receipt | sitting defect 2, 2026-09-21 |
| J11 | Develop a thought | desk | Write a thought → type → Kept | a note, kept, with "Kept · time"; nothing hidden | the owner's first gripe, 2026-09-20 ("completely unusable; hides things") |

Out, by this ruling: everything else on the platform is walked after these, with recorded engine replies. Astra's check of this selection is recorded in `checks/selection-astra.md`.
