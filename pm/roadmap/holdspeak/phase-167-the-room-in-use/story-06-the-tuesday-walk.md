# HS-167-06 - The Tuesday walk: the owner's first project on his real desk (OWNER VERDICT)

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
- **Depends on:** HS-167-02, HS-167-04, HS-167-05
- **Unblocks:** HS-167-07, HS-167-08
- **Owner:** unassigned

## Problem

The owner's real desk has never held a project. Every Rooms face
has only ever met a rig. The phase's exit is his word after his
FIRST real project goes through the whole Room, attended.

## Scope

- **In:** a walk SCRIPT (assets/walk-script.md), written at charter+1
  and dry-run on the current faces before 04 lands so cold-start
  defects surface early: (1) from the desk, new project — the
  interview by voice, real answers about one of his real repos;
  (2) the GitHub connection through the wizard (his real gh auth;
  the badge names github.com); (3) the Jira connection to
  karolsaneapple.atlassian.net / KAN through the Jira wizard (his
  one acli account); (4) a watch on each, tested live, finalized
  with a real baseline; (5) a real change on the repo and one KAN
  transition — one Delta each, reviewed, accepted; (6) one manual
  steward run, watched to RECORD, the door item on his Door; (7)
  the unattended policy enabled with a cadence he sets on the face
  and one unattended tick observed; (8) an update drafted from the
  week's deltas, published, read on his desk. The orchestrator
  walks it first on the real desk (a fresh project the owner can
  archive — never delete — afterwards), records every defect, pays
  what is product, then the owner walks it attended at his hub
  (1440) and on the 393 glass. Every defect found live gets a test.
  The verdict question, verbatim: "will you use this on a Tuesday?"
- **Out:** a second Jira account; fixture walks (the glass rigs
  already exist).

## Acceptance criteria

- [x] The eight steps complete on the owner's real desk with real providers; each step's evidence (API read-backs, run receipts, the door item, the published update) captured under assets/story-06-walk/.
- [x] Every inherited defect found live is paid with a failing-then-passing test or ledgered with his word.
- [x] The owner's verdict recorded verbatim ("Walk it later — close on the dry run."); the exit met on the orchestrator's real-desk leg; the attended leg ledgered.

## The orchestrator's leg (2026-09-03)

The runner tests/e2e/live167_walk.py (real HOME; HS167_WALK=1;
HS167_WALK_DB=isolated|real; skip-guarded on gh + acli auth; every
step asserted at the wire AND on the glass at both widths; no
conditional skips) was built through four rounds in isolated mode.
Live truths it found: a PRODUCT DEFECT — the Jira blockers template
compiled `status in ("Blocked")` for a board with no such status and
Jira refused the whole evaluation (so the OBSERVE receipt was empty)
— paid in holdspeak/jira_templates.py with tests; `accept` on a
`conflict` proposal is refused by contract (400 `capability`); an
empty issue_types list means ALL; the door path needs an overdue or
blocking candidate; lifecycle/revision live on the room projection
and baseline_state on the watch rows. Step 6 proves the Deltas
honestly: a throwaway PR probe on karolswdev/HoldSpeak (closed and
its branch deleted in the finally) and a KAN transition (reverted),
polled through Jira's eventual consistency → ONE transition per
source, seven proposals, ZERO new on a second trigger. Step 7: the
OBSERVE receipt carries calls=5; the policy cadence written on the
face and read back; the trigger route runs; the second same-watermark
run is created and reconciles; ONE door item across both runs.
THE REAL DESK (1440): `HS167_WALK_DB=real` against
~/.local/share/holdspeak/holdspeak.db (backed up first as
holdspeak.db.bak-hs167-163032; projects count 0 before) — `1 passed in
78.12s`; the project `The first real project through the whole Room,
attended` created, walked through the eight steps, and ARCHIVED (never
deleted) — the first project the owner's desk ever held. **THE OWNER'S WORD (2026-09-03), verbatim: "Walk it later — close on the
dry run."** The phase closes on the orchestrator's real-desk leg; the
owner's attended walk is LEDGERED PENDING (his desk is set up: the
branch built, the runner + script in the repo; restart the hub, walk
the eight steps, the Tuesday question). Evidence: assets/story-06-walk/
real-1440/ (the twelve shots + the transcript of the real-desk run)
and isolated-1440/ (the transcript).

## Test plan

- **Live (real HOME):** the walk script driven by a python live runner (live167-06.py) mirroring tests/e2e/test_hs166_jira_walk.py's real-HOME pattern, skip-guarded honestly without gh/acli auth.
- **Eye:** the attended walk; both widths.
