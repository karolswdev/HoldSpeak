# PHILO-7-04 - File it and find it without the repo

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** PHILO-7-03
- **Unblocks:** the phase close
- **Owner:** Astra (Luna); Muad'Dib checks
- **Council tag:** the owner's D4; Astra's check of the drafts, finding 7 and MISSED 1, 4

## Problem

The Phase 5 rehearsal proved ordinary prompts with client discovery in this repository; "it does not prove discovery without repository access" (`docs/internal/philo/phase-5/his-words/rehearsal.md:49-50`). Codex read repository docs and source, and the `scripts/astra ask` preamble led it to the canon documents (`rehearsal.md:49`); the decision turn took 201 s (`:43`) and 25 repository reads (`pm/roadmap/holdspeak/BACKLOG.md:1216`). In the Phase 6 driver run Codex chose `door.add_item` for a desk decision (`BACKLOG.md:1225`). D4 makes discovery from the catalogue alone an acceptance criterion.

## Scope

- **In:** Astra drives Codex from a session WITHOUT repository access (a working directory outside the repository; no preamble that points at repository files; the MCP proxy configured as in Phase 5 story 01, HOME = the isolated hub's HOME) through ordinary requests: "file this note into <zone>", "find it", "put this decision on my review list", "make my brief"; the MCP transcript, the Codex event log and the Desk shots at 1440 and 393 retained; readbacks through the contract; the receipts of the filed and decided writes read back; Muad'Dib checks; the owner reviews the shots.
- **Out:** "attach it to a meeting" (dropped: no durable relationship in this slice); already-open Desk refresh (D4: a reopened Desk read); a live sitting; any face change.

## Acceptance criteria

- [ ] The requests are ordinary words; no operation name, argument, id or test clock appears in them.
- [ ] Discovery from `tools/list` alone: the Codex event log shows ZERO reads of repository files, source or roadmap documents (a fence over the retained event log, red on the Phase 5 rehearsal's log); every tool chosen appears in the session's `tools/list` answer.
- [ ] The note is filed into the named zone and found again; the decision is on his review list; the brief is made; each read back through the contract (`op`), not from Codex's own text.
- [ ] The receipts of the filed and decided writes (the D3 set) are read back; one per write.
- [ ] Run against an isolated HOME; the effective HOME, lock and DB path retained; never the desk.
- [ ] The Desk reopened and shot at 1440 and 393: the note in its zone, the decision in the review rows, the brief. Real-engine and replayed runs labelled separately.
- [ ] Technical rehearsal completes with Muad'Dib's check recorded; the evidence reads "REHEARSED; OWNER REVIEW PENDING", never an observed sitting.
- [ ] The owner reviews the published shots; the review recorded in the tree.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

Not yet grounded. Phase 5's rehearsal (326 s run; about 1 engineering day with its repairs) is the precedent.

## Test plan

- **Unit:** the no-repository-read fence over a Codex event log (red on the Phase 5 log); the transcript-to-server pairing audit carried from Phase 5.
- **Integration:** the rehearsal driver against an isolated hub; the transcript, config, DB and lock proof, and shots retained under this phase's assets.
- **Manual / device:** the owner reviews the shots (rehearsed, owner-reviewed).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B, Astra's check of the drafts and the owner's D4; unratified. "Attach to a meeting" dropped from the closing job (Astra MISSED 4).
