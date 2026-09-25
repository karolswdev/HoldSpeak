# PHILO-7-03 - The atlas for the desk

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** PHILO-7-02
- **Unblocks:** PHILO-7-04
- **Owner:** Astra (Luna); Muad'Dib checks on built
- **Council tag:** Astra's check of the drafts, finding 7; Phase 5's Proof position

## Problem

The atlas has note cases (`case.j1.first_words_keep_as_note.kept`, the `case.j11.*` Thought cases in `docs/internal/philo/graph/atlas.json`) but no directory, KB, zone-membership, decision-status or supersede case in `atlas.json` (85 cases at `f93e76fa`) or `atlas-phase3.json` (36). `case.j11.thought_keep.receipt_time.op` seeds `POST /api/directories` in setup only. So the slice has no browser proof and no `op` pair for what the owner files or decides. The headless `op` tier exists (Phase 5 story 03: the registry inside the owning hub through `/api/mcp`, setup, waiting, observation and restart without a page).

## Scope

- **In:** NEW browser cases at 1440 and 393 for the phase status's named list (zone create, zone file, re-file moves, unfile, kb create, kb member add/remove, decision status to the review list, supersede with successor, decision delete); `.op` siblings for their durable outcomes and for the existing note cases where the outcome is durable; the equivalence run (durable outcome, identity relationships, refusals); the receipts of the D3 writes read in the `op` observation; the rig's headless mode as built in Phase 5.
- **Out:** any face change — a case records what the Desk shows today, and "not on the face" is a lawful result with an `op`-only pair. "Not on the face" delimits THIS story's coverage only; it never waives story 04's note, review-row and brief shots; replacing any existing case; `api` steps (they stay for HTTP contracts).

## Acceptance criteria

- [ ] Every named new case is minted and run at 1440 and 393, or recorded "not on the face" with the reason and the source line that shows it. No such record waives story 04's shots (the note in its zone, the decision in the review rows, the brief).
- [ ] Every named pair has its `.op` sibling, minted and run headless against the owning isolated hub.
- [ ] Equivalence = durable outcome + identity relationships + refusals; never identical envelopes.
- [ ] For each admitted write (the admission table), the `op` observation reads its kernel receipt, refusal receipts included; the browser case does not claim it.
- [ ] Real-engine and replayed runs retained and labelled separately; a replay is never reported as real-engine.
- [ ] Face walks retained independently; no face case is "proved" by `op`; `readable_text` (visible, in viewport, unobscured), not text containment.
- [ ] Atlas counts reported over both named files at the branch commit; durations measured, not promised.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

PROVISIONAL: 3–4 engineering days (includes the new browser cases, the part Phase 5 did not have). Calibrated after story 01's first kind.

## Test plan

- **Unit:** atlas schema validation of the new cases; the rig's `op` steps for the membership and decision operations.
- **Integration:** `scripts/graph_walk.py` runs of every named case (`op`, `api`, browser at 1440 and 393) with `--out` under this phase's assets; real and replayed runs in separate folders.
- **Manual / device:** none (story 04).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B and Astra's check of the drafts; unratified. The case ids in the phase status are proposals fixed here against the atlas schema.
