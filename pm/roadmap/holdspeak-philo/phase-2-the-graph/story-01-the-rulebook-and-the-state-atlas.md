# PHILO-2-01 - The rulebook and the state atlas

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** none
- **Unblocks:** see the phase status doc
- **Owner:** both brains (co-authored; the other checks)

## Problem

Three audits measured properties and callers; the owner's sitting found two dead basics in two clicks: an edge with no effect (a receipt's Open) and a state with no face (an empty brief). Nothing in the tree defines the chain a verb must close, or the states a face must render. Without one rulebook, two passes cannot be compared and a council cannot rule.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] `docs/internal/philo/briefs/graph-audit-brief.md` is the ONE brief both brains run, verbatim (this story ratifies it; it is drafted at charter).
- [x] The four definitions (edge, interface, connection, action) and the four questions are pinned with examples from the sitting.
- [x] The outcome law (brief §3) is stated: a diff is evidence to inspect, not a success criterion; an enabled action that promises a change and produces neither it nor an intelligible refusal is a finding; an unexplained zero diff is unresolved, never pass; reads and presentation owe no receipt (Article XI.5).
- [x] The state atlas (brief §4) lists REACHABLE cases, each with a stable id, source evidence, edge ids, preconditions, a production setup recipe, fixture and clock settings, expected transition and presentation, and execution limits; derived from Phase 1 lifecycle/failure records and producer code, never a Cartesian product; `quiet` is not an attention_state.
- [x] The first-use candidates (brief §5) are mapped to job, starting state, trigger, expected result and source of priority, ordered by SITTING-07.md; the owner DEFERRED the selection to the two brains (2026-09-22) and the ruled selection is recorded below, checked by Astra.
- [x] The graph schema (brief §8) is delivered as a machine-validatable JSON Schema joining Phase 1 record ids: root provenance, nodes, links with relations, cases, observations (one per run/case/brain/pass/viewport, never overwritten), claim reviews, findings and resolutions; verdicts pass/fail/blocked/not-run/not-applicable.
- [x] Findings have three bins (product defect; doc drift; tooling debt) and one ranking: cost to the owner on a Tuesday.

## Test plan

- **Unit:** `tests/unit/test_philo_graph_schema.py` — the JSON Schema validates a worked example graph and rejects: an unresolved link endpoint, an observation without provenance, a finding without a bin, a case without an expected-result predicate; the atlas file validates against its own schema (no phrase-presence tests).
- **Integration:** n/a.
- **Manual / device:** the owner reads the brief once and says whether the twenty are his twenty.

## Notes / open questions

**ROUND FOUR PAID (2026-09-23, Opus 5.5 workers):** rig — captured values bind AFTER the trigger (J4's multipart upload fires and binds `meeting_id`; 0 uploads before, 1 after); a clicked verb's own network response is recorded (`trigger_route` pins it; else the first same-origin non-GET after the click) so `trigger:<path>` identity, `identity_display` (whole-token match) and `protocol_status` work for clicks; a different id beside unchanged content FAILS (Astra's probe, now a negative control); rig v1.1.0. Atlas — the same-day face case proves returned == displayed == retained headline, and its PROTOCOL SIBLING `case.j10.route_generate_again.same_day_same_id` proves the returned id equals the id captured before (`body_contains: {first_brief_id}`); the populated-brief cases MINT material via `POST /api/decisions` and inspect the ledger row; J11 verifies the saved words via `GET /api/notes` (`PATCH /api/thoughts/{id}/working` autosave, 450 ms). 71 cases (69 applicable, 2 unreachable), 111 states. Real-hub smoke: 7 passed (J4 import, J10 same-day, J10 empty, J1 Continue later, J9 receipt Open, plus the sample J9 at both widths).

**(paid) NEXT SESSION, FIRST TASK (Astra round three, 2026-09-23, DO-NOT-RATIFY for the live passes; `checks/story-01-built-astra.md`):** (1) rig — captured values (`capture_as`) bind AFTER the trigger fires, so a trigger that mints `{meeting_id}` can be used by its own `expected` (J4 currently blocks before uploading); (2) rig — a UI trigger's own network response is recorded as `trigger_response` (intercept the request the click fires) so `trigger:<path>` identity works for clicked verbs; (3) atlas — J10 same-day declares `identity_display` + a reload, and a different id beside unchanged content must FAIL; (4) atlas — the populated-brief case creates populated material in setup and inspects an item row (`ChairHome.tsx:1847`), never an empty headline element; (5) atlas — J11 verifies the saved words via the store (`GET /api/notes` or the thought read model), not the absence of one failure sentence (`CHANGED ELSEWHERE` is a failure that passed). Fence each against the ACTUAL atlas case. Then Astra round four; then the live passes.


**Astra's counsel on built (2026-09-22, `checks/story-01-built-astra.md`): DO-NOT-RATIFY, seven findings, all accepted and paid in this lane before re-ship — three reproduced false passes in the rig, predicates that would certify the hunted failures, an atlas not fully executable by the rig, wrong sampled expectations (J4 multipart, J9 restore, J10 same-day), and two wrong ledger lines (corrected below).**

**Astra round two (DO-NOT-RATIFY for the LIVE passes; static passes cleared to start): four atlas-to-rig integration defects reproduced against the real atlas — relative `goto` fails without base_url, fixture `capture_as` ignored, no working identity form, J10/speech/J6-host predicates still certify missing results, J4 triggers with JSON. Round three in the lane; the integration smoke now runs ACTUAL atlas cases.**

**Counsel round PAID (2026-09-22 evening) — the numbers after the round:** schema 17 fences (Phase 1 record/route/path references must resolve); atlas 71 cases + 1 council reading, 111 states, 21 reproduction chains, 87 executable `check` preconditions, 33 fences, 0 cases invalid against the graph case contract; rig 49 calibration fences incl. nine negative controls that fail pre-fix (replay identity must be produced by THIS operation; a result after the bound is incomplete; a missing scope blocks; closed `UI_ACTIONS`/`STEP_KINDS`; executable checks; `boundary` installs a recorded engine reply at the product's own seam inside the hub or blocks; words-only → blocked; unreachable keeps its reason; `capture_as`/`{var}` substitution), the rig's hub takes the owner lock, runs the product's intel drainer and REFUSES `POST /api/meeting/start` (microphone forbidden), `provenance.product_wiring` records has/lacks. Still honest UNKNOWNs: no summary has been driven end to end through the replayed engine; the restart adapter is calibrated on the fixture server only; `fixture` against a real hub and `--engine real` unexercised; `subject_counts` is a council reading, not a case.

**Built 2026-09-22 (three Opus workers, disjoint files; the orchestrator reconciled the contracts):**
- Schema: `docs/internal/philo/graph/graph.schema.json` (+ worked example for J9, `scripts/philo_graph_validate.py`, 10 fences). Two contract corrections found at build and paid in the brief §8: every applicable case carries a top-level `trigger` step (the rig fires it through the real entry point after setup and the before-capture), and steps are the rig's executable shape (`kind` + kind-specific fields, incl. `cli`/`tool`). The reason field is `reason`.
- Atlas: `docs/internal/philo/graph/atlas.json` — 61 cases, 110 states over the seven §4 families, 4 clocks, 12 excluded tuples, 18 fences each proven to bite; every case validates against the graph schema's case definition. J8 unexercised (native hotkey, other-app delivery). 31 states unexercised with the missing mechanism and its cost recorded in the atlas.
- Rig: `scripts/graph_walk.py` v1.0.0 — six calibration cases (no verdict from a diff), fresh-HOME guard, run-specific observation directories, one real-hub smoke (J9 at 1440 and 393: pass). The timer edge is triggered by the REAL scheduler (`scheduler-wait`: floor `sweep_every_minutes` to 1, wait ≤2 ticks); `POST /api/settings/heartbeat/run-now` is the owner-hand edge, a separate case (W2's ruling, upheld).

**Ledger (for the live passes and story 07), not blocking:**
- `record_only` EXISTS: it is the posture produced when speech admission fails (`holdspeak/meeting_session/intel_admission.py:219,286`) — the first cut of this ledger said no producer was found; Astra's counsel corrected it and the state is in the atlas with that producer (unexercised until a case mints a speech-admission failure).
- The brief §4 "continuity horizon" producer is `REPLAY_HORIZON_DAYS = 14` in `holdspeak/services/needs_you_aggregate.py:163` (the HS-200-15 last-known replay; `tests/unit/test_phase200_continuity.py` is red on main since the horizon passed). Unexercised: `clock.python_wall` and `clock.sqlite_now` have no mechanism in scope (tooling-debt).
- `next_day` and `week_boundary` are unreachable for the same reason; `clock.browser_date` (Playwright `Page.clock`) and `clock.heartbeat_scheduler` are available.
- Astra's MISSED on the selection: summary-to-decision follow-through is outside this first sitting.
- The rig's `scheduler-wait` observed the conductor's FIRST sweep (the `last_sweep_at is None` branch, `heartbeat.py:99`), so `sweep_every_minutes: 1` was set but not load-bearing; proving the interval branch needs a baseline taken after the first sweep. The rig starts the product's own `_heartbeat_loop` in its hub (`serve --scheduler`) without the rest of `WebRuntime.run` (microphone + hotkey are forbidden), so `_sweep_watch_service` takes its documented fallback; irrelevant with zero watches, material for a watch case.
- Predicates: the atlas's first cut stated expected results in prose; the rig refused to guess (BLOCKED, not failed) and the cases were converted to the rig's structured kinds (`text_contains`, `text_equals`, `text_absent`, `attr_equals`, `window_titled`, `presentation_change`, `unchanged`, `protocol_rows`) with the sentence kept as `words`.
- SUPERSEDED (2026-09-22 evening): the nine `words`-only cases were converted once the rig gained `protocol_status`, `protocol_rows_gone`, `protocol_field` and `input_value`; zero words-only cases remain; the `subject_counts` comparison is a council reading, not a case.
- FINDING for the council (found while replacing a placeholder trigger): J11's stated result ("a note, kept, with Kept · time") is NOT on the Thought window's face — its footer verbs are Change and Finish/Resume (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:491-494`), and the foot reads KEPT only when `filing_status === "filed"`, otherwise NOT IN A DRAWER (`:486`). The atlas case asserts what the face does promise (the save did not fail, `:485`); the gap stays in `words`. This is the owner's first gripe (2026-09-20, "it hides things") seen from the graph.
- `main.chair` was never a verified arrival root (the only `<main class="chair …">` is the first-value branch, `ChairHome.tsx:413`); every use is gone from the atlas.
- Validator limits (W1, honest): source paths are checked against the CURRENT tree, not the cited revision (a correct citation of a since-deleted file would be flagged); a `revision` is only checked for shape, not existence; cited line numbers are not read. Story 07's generator inherits these as known limits.
- Unexercised by any test yet: the `fixture` step against a real hub (the WAV import route), the `boundary` step, and `--engine real|replayed` beyond recording the mode — the live passes pay these or record them blocked.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.

## The owner's selection — ruled on his deferral, 2026-09-22

The owner, asked to select the first-use cases: "No, dude. You and Astra? You push this forward..." Per the standing rule (when he defers: rule, record, act, tell him), Muad'Dib rules and Astra checks. The selected set follows SITTING-07.md's journey, adds the two defects his sitting hit and the first gripe of his first use, and nothing else. Eleven jobs; the trigger count is whatever they need.

| # | Job (owner result) | Starting state | Triggers | Expected result | Priority source |
|---|---|---|---|---|---|
| J1 | Get past the gate | fresh desk, first screen VOICE TYPING; the voice branch additionally requires a READY speech assignment (a fresh desk has one migrated speech profile, `speech-migrated-…`; the rig verifies readiness before the branch or records it blocked) | Continue later; or speak one sentence (fixture WAV at the input boundary) → Kept | the desk; or the words kept with a receipt | SITTING-07 step 0; owner's first use 2026-09-20 |
| J2 | See what the desk asks of me | fresh desk | arrival (observation) | one SETUP row naming what is missing; the head counts what asks; an offer does not count | SITTING-07 step 1 |
| J3 | Give the desk a summary engine | speech READY; summary assignment missing or pointing at the missing profile `legacy-intel` | Choose an engine → Add an engine → address → Check → Use this for summaries | READY; the SETUP row gone ONLY because speech was already ready — with speech missing the row stays and says "No engine for speech" (`meetingPathBlocker.ts:83`), which is a second, separate case | SITTING-07 step 2; fresh-desk log 2026-09-21 |
| J4 | Have one meeting on the desk | speech READY (transcription needs it); summary engine set by J3 | Record → Stop (fixture WAV at the input boundary); or Import a sound file | a meeting row with its length; no summary yet; no error; import stops without an automatic summary | SITTING-07 step 3 (alternatives) |
| J5 | Know where the summary will run | one meeting | open the meeting (observation beside Run summary) | the planned host, before the click | SITTING-07 step 4; Article III |
| J6 | Get the summary | J5 | Run summary (real LAN engine) | the host that DID run it; the summary text; technical completion and usefulness reported separately | SITTING-07 step 5 |
| J7 | Find it again after a restart | J6 | stop the hub; start it; find the summary | the same summary in two moves or less | SITTING-07 step 6 |
| J8 | Type by voice into another app | hub up | hold ⌥R, speak, release | words at the cursor of the other app | SITTING-07 step 7 — UNEXERCISED by the rig (native hotkey, other-app delivery); the owner's sitting observes it |
| J9 | Open what the desk remembered | +1 sweep (15 min) | Desk memory → a receipt's Open | the Rhythm face opens; a doorless receipt shows no Open | sitting defect 1, 2026-09-21 |
| J10 | Get a brief, and another | fresh desk; then +1 day | Generate brief → (reload) → Generate again | the brief's own words stay on the face after the reload; after Generate again the RETURNED brief is the one DISPLAYED and it is RETAINED across another reload (not a stale face beside a new receipt); the same-day variant expects the producer to return the existing brief (`monday_brief_service.py:185`), the next-day variant must first PROVE the producer's date advanced (the clock mechanism named in the atlas) or is recorded blocked | sitting defect 2, 2026-09-21 |
| J11 | Develop a thought | desk | Write a thought → type → Kept | a note, kept, with "Kept · time"; nothing hidden | the owner's first gripe, 2026-09-20 ("completely unusable; hides things") |

Out, by this ruling: everything else on the platform is walked after these, with recorded engine replies. Astra's check of this selection (RATIFY-WITH-CONDITIONS, conditions paid in this table: speech readiness explicit in J1/J3/J4; J10 asserts the displayed and retained result with a proven date boundary) is recorded in `checks/selection-astra.md`. Astra's MISSED stands as a ledger line: summary-to-decision follow-through is not in this first sitting; these eleven jobs do not establish a working day.
