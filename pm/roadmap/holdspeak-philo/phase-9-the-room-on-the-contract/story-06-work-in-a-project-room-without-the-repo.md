# PHILO-9-06 - Work in a project room without the repo (Codex)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-05
- **Unblocks:** the phase close
- **Owner:** Astra (Luna) drives Codex; Muad'Dib checks
- **Closure finding:** the owner's D1 and D3 (2026-09-27); Phase 7 ledger row 8, "find it cold" (BACKLOG "PHILO-7-04 follow-ups" row 3)
- **Canvas:** none

## Problem

D1's closing test: a cold-context client runs a real project job from the MCP catalogue alone, and the Room's face shows it at 1440 and 393. D3: the client is Codex. Phase 7's closing run proved "find it again", not "find it cold" (`../phase-7-the-desk-on-the-contract/final-summary.md` THE LEDGER row 8). The precedent driver is `scripts/philo7_file_and_find.py` and its launch setup (`../phase-7-the-desk-on-the-contract/current-phase-status.md` "Discovery without repository access"; handover XXIX "Late addendum": Codex 0.155 sends the DESK bearer over HTTP, a scratch `CODEX_HOME` with only `auth.json` logs in, `--disable apps --disable plugins` is required).

## Scope

- **In:** the driver adapted for the project job (or a sibling of it) with the R3 setup: an empty scratch directory outside every checkout, a scratch `HOME`/`CODEX_HOME` with only the auth file, `--ignore-user-config --ignore-rules`, `--disable apps --disable plugins`, no preamble, the isolated hub the only MCP server. The owner's words for the job: make a project, add a milestone and a risk, ask what needs him, run the steward, draft and send the update. A second cold session, given only the project's name in his words, finds it ("find it cold"). Each result read back from the hub and shown on the Room's face at 1440 and 393. The zero-read fence (a repository resource read is a read, Phase 7 story 04 C1), red on the Phase 5 logs. Redaction at capture and its leak fence (handover XXX law 12). Rehearsed shots for the owner's review.
- **Out:** an agent leg, unless Q2 (b); a sitting (never claimed).

## Acceptance criteria

- [ ] The job completes from the catalogue alone: every tool choice comes from `tools/list`; zero repository reads in the retained log; the zero-read fence fails on the Phase 5 logs.
- [ ] "Find it cold": the second session finds the project without its id.
- [ ] Each write is read back from the hub (and its kernel receipt, as Q1 rules) and shown on the Room's face at 1440 and 393.
- [ ] The retained sessions carry no account data (the leak fence).
- [ ] The owner reviews the shots before merge. The evidence reads "REHEARSED; OWNER REVIEW PENDING" until he does.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day, plus the owner's review.

## Test plan

- **Integration:** the driver's own fences (the Phase 7 story 04 set, adapted); the run inside `.githooks/dw evidence capture holdspeak-philo 9 06 -- …` with `HOLDSPEAK_EVIDENCE_WRITE=1`.
- **Manual / device:** the owner's review of the shots.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The rehearsal runs on the owner's Codex account; a quota stop blocks it (Phase 7 story 04 precedent).
