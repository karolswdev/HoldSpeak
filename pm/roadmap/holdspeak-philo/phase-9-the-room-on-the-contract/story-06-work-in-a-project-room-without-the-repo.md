# PHILO-9-06 - Work in a project room without the repo (Codex)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-05; the owner's answers to Q0–Q3 (they fix the job)
- **Unblocks:** the phase close
- **Owner:** Astra (Luna) drives Codex; Muad'Dib checks
- **Closure finding:** the owner's D1 and D3 (2026-09-27); Phase 7 ledger row 8, "find it cold" (BACKLOG "PHILO-7-04 follow-ups" row 3); Codex Astra r1 F1, F5, F9 (`checks/charter-astra-r1.md`)
- **Canvas:** none

## Problem

D1's closing test: a cold-context client runs a real project job from the MCP catalogue alone, and the Room's face shows it at 1440 and 393. D3: the client is Codex. Phase 7's run proved "find it again", not "find it cold". The precedent driver `scripts/philo7_file_and_find.py` defaults to the Claude client and both owner and agent legs (`:1538-1542`). A green run could hide an empty outcome: no attention item, a steward run with no action, a publication nobody reads back. And publishing is local: it sends nothing (`holdspeak/services/project_update_service.py:1901`), so the job must not claim delivery (Q0).

## Scope

- **In:** the driver (or a sibling) run exactly as the charter's "The closing contract" pins it:
  - `--client codex --legs owner` (under Q2 (a); an OWNER-token run proves OWNER behaviour only; agent refusals are story 02's fences). Under Q2 (b) an agent leg is added.
  - Two sessions — creation and "find it cold" — each with its own fresh scratch directory, `HOME` and `CODEX_HOME` (only `auth.json`), distinct session ids, no resumed transcript; `--ignore-user-config --ignore-rules --disable apps --disable plugins`; no preamble; the isolated hub the only MCP server.
  - The complete initial context of each session retained; the client's events reconciled with the hub's recorded exchanges; zero repository reads (a repository resource read is a read); the zero-read fence red on the Phase 5 logs; redaction at capture and its leak fence (handover XXX law 12).
  - **The fixture, written to this story's fixture file before the run** (Q3 (a) shown; the charter's "Q3 propagation" gives the (b) and (c) jobs): project "Payments ledger cutover"; milestone "Cutover rehearsal" due the run date minus 3 days, `planned`; risk "Old ledger freeze slips", likelihood "medium", impact "high", mitigation "Freeze the schema by Friday"; expected attention: NEEDS YOU lists "Cutover rehearsal" as overdue, health not ON TRACK; steward: policy `eligible_effect_kinds: ["draft_update"]`, one run, completed, COMPARE's review exists, ACT drafts one update, the face's counts equal the run; publication: the client publishes that draft in the Room; readback: `published`, read-only, the body names "Cutover rehearsal" and "Old ledger freeze slips"; find it cold: the second session gets only "Payments ledger cutover" in the owner's words, finds the project and reads its published update.
  - Each expectation confirmed reachable on the rig before the run; one that is not goes back to its story, never softened.
  - Each result read back from the hub (and its kernel receipt, as Q1 rules) and shown on the Room's face at 1440 and 393; checks compare the fixture's values, not success flags.
- **Out:** delivery of the update (Q0 (a)); an agent leg unless Q2 (b); a sitting (never claimed).

## Acceptance criteria

- [ ] The launch matches the pinned contract (client, legs, homes, session ids, flags); the retained initial contexts prove it.
- [ ] The job completes from the catalogue alone: every tool choice comes from `tools/list`; zero repository reads; the zero-read fence fails on the Phase 5 logs; client events reconcile with hub exchanges.
- [ ] Every fixture value is read back and matches: the milestone and risk facts, the overdue attention item, the steward run (review, one drafted update, counts), the publication lifecycle and body content, and each admitted write's receipt.
- [ ] "Find it cold": the second, fresh session finds the project from its name alone and reads its published update.
- [ ] The Room's face at 1440 and 393 shows each result; the retained sessions carry no account data (the leak fence).
- [ ] The owner reviews the shots before merge; the evidence reads "REHEARSED; OWNER REVIEW PENDING" until he does.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day, plus the owner's review.

## Test plan

- **Integration:** the driver's own fences (the Phase 7 story 04 set, adapted); the run inside `.githooks/dw evidence capture holdspeak-philo 9 06 -- …` with `HOLDSPEAK_EVIDENCE_WRITE=1`.
- **Manual / device:** the owner's review of the shots.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The rehearsal runs on the owner's Codex account; a quota stop blocks it (Phase 7 story 04 precedent).
- 2026-09-27 — round two (Codex Astra r1 F1, F5, F9 paid): the job ends at publication in the Room; the launch pinned; the fixture fixed before the run; content checks.
