# HS-201-07 - Run it from main and the sitting

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** HS-201-01, HS-201-02, HS-201-03, HS-201-04, HS-201-05, HS-201-06
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The last hub on the owner's desk ran from a worktree, not main, and is now down; startup logs the URL but not the commit or the DB path (audits/runtime-astra.md facts 1, 2). Three loops start at boot with no ownership gate (`web_runtime.py:529`, `web_server.py:1264`). Nobody has watched the owner use the product since 2026-09-04. This story is the run and the sitting.

## Scope

- **In:** `holdspeak web` prints commit, frontend build and DB path at startup (the identity route already has them); the documented one-liner from main on `HOLDSPEAK_WEB_PORT=8765`; the three ungated loops (`web_runtime.py:529`, `web_server.py:1264`) are PROVED inactive for the sitting (zero relevant jobs on the live DB, audits/runtime-astra.md fact 8) and gated only if one is shown unable to stay inactive (conditional, tenet 1); the dictation regression check (`tests/unit/test_transcriber_init_race.py` classified and paid if it is a real regression); then the owner starts the hub from main, records one real meeting, asks for the summary, reads it, restarts, finds it, and dictates one sentence. His verdict and the sitting notes are the phase's final summary.
- **Out:** worktree pruning (after this story, separately); the other five red tests (classified, off-path, ledgered); any new platform scope.

## Acceptance criteria

- [ ] Startup line names commit, build and DB path; shot of the terminal or log.
- [ ] The three ungated loops are shown inactive on the sitting's DB (a read-only count before and after), or the one that cannot stay inactive is gated with a fence.
- [ ] The transcriber-race test is classified (a/b/c) and, if (b), fixed.
- [ ] On the owner's desk, observed: one real meeting, one useful summary traceable to it, found after restart in at most 2 moves, one dictation delivered. His words recorded.
- [ ] Nothing on this path required an agent's help to complete.

## Test plan

- **Unit:** the loop gate fence; the startup identity line.
- **Integration:** the full suite in a quiet tree before the sitting.
- **Manual / device:** the sitting itself; shots from his desk.

## Notes / open questions

Lane B (Muad'Dib), checked by Astra. Depends on 01 to 06. The sitting boundary: the OWNER starts, restarts and gestures on his desk; agents never start a hub on his HOME, never terminate a PID they did not verify (the audit's PID 39433 was a scratch rig, not his hub), never inject into a focused application, never capture room audio at all: worker rigs use controlled fixture audio (a checked-in WAV) as the meeting source, never the microphone. Worker rigs: isolated HOME, isolated keychain, env-scoped subprocesses, no desktop typing. The startup identity line and any conditional loop gate are lane A edits; lane B verifies them and runs the sitting. Serves exit criteria 1, 5, 6, 8. This story cannot close on "accepted, not observed".
