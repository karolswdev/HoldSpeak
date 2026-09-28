# PHILO-9-06 - Work in a project room without the repo (Codex)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** in-progress
- **Depends on:** PHILO-9-05, PHILO-9-07; the owner's rulings on Q0–Q3 (they fix the job)
- **Unblocks:** the phase close
- **Owner:** Astra (Luna) drives Codex; Muad'Dib checks
- **Closure finding:** the owner's D1 and D3 (2026-09-27) and his Q0–Q3 rulings; Phase 7 ledger row 8, "find it cold" (BACKLOG "PHILO-7-04 follow-ups" row 3); Codex Astra r1 F1, F5, F9 (`checks/charter-astra-r1.md`)
- **Canvas:** none

## Problem

D1's closing test: a cold-context client runs a real project job from the MCP catalogue alone, and the Room's face shows it at 1440 and 393. D3: the client is Codex. The owner ruled the job's end (Q0: copy to clipboard, marked delivered when he confirms) and a bounded project delegation for agents (Q2), so the run has an OWNER leg and an AGENT leg, as Phase 7 story 04 did. The precedent driver is `scripts/philo7_file_and_find.py` (defaults `claude` and `owner,agent`, `:1538-1542`). A green run could hide an empty outcome; checks are on content.

## Scope

- **In:** the driver (or a sibling) run as the charter's "The closing contract" pins it:
  - `--client codex --legs owner,agent`. OWNER leg: the owner token. AGENT leg: a real Settings-issued PROJECT credential.
  - Three sessions — OWNER creation, OWNER "find it cold", AGENT — each with its own fresh scratch directory, `HOME` and `CODEX_HOME` (only `auth.json`), distinct session ids, no resumed transcript; `--ignore-user-config --ignore-rules --disable apps --disable plugins`; no preamble; the isolated hub the only MCP server.
  - The complete initial context of each session retained; the client's events reconciled with the hub's recorded exchanges; zero repository reads (a repository resource read is a read); the zero-read fence red on the Phase 5 logs; redaction at capture and its leak fence (handover XXX law 12).
  - **The fixture, written to this story's fixture file before the run:** project "Payments ledger cutover"; milestone "Cutover rehearsal" due the run date minus 3 days, `planned`; risk "Old ledger freeze slips", likelihood "medium", impact "high", mitigation "Freeze the schema by Friday"; expected attention: NEEDS YOU lists "Cutover rehearsal" as overdue, health not ON TRACK; steward: the owner sets `eligible_effect_kinds: ["draft_update"]`, one run, completed, its recorded review id equals the open review, ACT drafts one update, the face's counts equal the run; publication: published, read-only, the body names "Cutover rehearsal" and "Old ledger freeze slips"; **delivery:** the client reads the published text "for delivery" (`body_md`), marks it delivered twice, `delivered_to` "Priya" then "Tomas"; readback: two delivery rows in order, each with its confirmation time, its To and its own receipt, both on the face; **AGENT leg:** before the grant, `project.run_steward` and `project.publish_update` refused `project_delegation_required` with receipts; the owner grants the ratified bound on that project; the agent runs the steward (one draft) and publishes it, each receipt naming the delegation; the agent's `project.mark_update_delivered` still refused (owner-only); the owner marks that update delivered; **find it cold:** the second OWNER session gets only "Payments ledger cutover" in the owner's words, finds the project and reads its published, delivered update.
  - Codex Astra r2 already reproduced the steward and publication half on a real hub (grounding "Round three"): one draft effect, the draft names both titles, publication persists, an edit after is refused `published_update`.
  - Each expectation confirmed reachable on the rig before the run; one that is not goes back to its story, never softened.
  - Each result read back from the hub (and its kernel receipt) and shown on the Room's face at 1440 and 393; checks compare the fixture's values, not success flags.
  - The run proves the MCP contract (reading `body_md`, recording the owner's confirmation). It claims nothing about the clipboard (story 03's glass) or about delivery outside HoldSpeak (R4-4).
- **Out:** automated send (the owner ruled copy only); a sitting (never claimed).

## Acceptance criteria

- [ ] The launch matches the pinned contract (client, legs, homes, session ids, flags); the retained initial contexts prove it.
- [ ] The job completes from the catalogue alone: every tool choice comes from `tools/list`; zero repository reads; the zero-read fence fails on the Phase 5 logs; client events reconcile with hub exchanges.
- [ ] Every fixture value is read back and matches: the milestone and risk facts; the overdue milestone in NEEDS YOU; the steward run (review id, one drafted update, counts); the publication lifecycle and body content; both delivery rows (times, "Priya" and "Tomas", two receipts, both shown); each admitted write's receipt.
- [ ] The AGENT leg: refused with receipts before the grant; executing with receipts naming the delegation after it; marking delivered refused throughout.
- [ ] "Find it cold": the fresh session finds the project from its name alone and reads its published, delivered update.
- [ ] The Room's face at 1440 and 393 shows each result; the retained sessions carry no account data (the leak fence).
- [ ] The owner reviews the shots before merge; the evidence reads "REHEARSED; OWNER REVIEW PENDING" until he does.

## Effort (not a promise)

PROVISIONAL: about 1.5 engineering days (two legs), plus the owner's review.

## Test plan

- **Integration:** the driver's own fences (the Phase 7 story 04 set, adapted); the run inside `.githooks/dw evidence capture holdspeak-philo 9 06 -- …` with `HOLDSPEAK_EVIDENCE_WRITE=1`.
- **Manual / device:** the owner's review of the shots.

## Notes

- 2026-09-28 — round two (Muad'Dib's ruling on rehearsal one): the two catalogue gaps paid red → green (an owner-only operation refuses an agent `owner_principal_required`; `project.list` names "find a project by its name", `memory.search` no longer reads as a project search); the grant pointer to BACKLOG. Rehearsal two completed with no blocker; find it cold took `project.list`.
- 2026-09-28 — the driver `scripts/philo9_room_job.py` (the Phase 7 machinery reused) and its fences (`tests/unit/test_philo9_room_job.py`); the fixture `story-06-fixture.json`; one rehearsal of the three MCP legs, every fixture value read back (`docs/internal/philo/phase-9/room-job/rehearsal.md`; it becomes `evidence-story-06.md` with the done flip). The AGENT leg runs as two fresh sessions (before and after the grant; the owner grants between them), the Phase 7 precedent. The face leg waits for PHILO-9-03. Status stays in-progress — Fedaykin lane (Opus 5.5).
- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The rehearsal runs on the owner's Codex account; a quota stop blocks it (Phase 7 story 04 precedent).
- 2026-09-27 — round seven (the owner's "Several per update"): the fixture marks delivered twice and reads both back.
- 2026-09-27 — round six (Codex Astra r4, R4-4): three sessions; MCP-contract proof kept apart from clipboard and external-delivery claims.
- 2026-09-27 — round five (the owner's rulings): the job ends at copy and a confirmed delivery; the AGENT leg (`--legs owner,agent`); the Q3 (c) branch removed.
- 2026-09-27 — round three (Codex Astra r2 F4 paid) and round four (r3 C4): acceptance conditional on Q3, now ruled (a).
- 2026-09-27 — round two (Codex Astra r1 F1, F5, F9 paid): the launch pinned; the fixture fixed before the run; content checks.
