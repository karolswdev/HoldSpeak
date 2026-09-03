# HS-167-06 - The Tuesday walk: the owner's first project on his real desk (OWNER VERDICT)

- **Project:** holdspeak
- **Phase:** 167
- **Status:** backlog
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

- [ ] The eight steps complete on the owner's real desk with real providers; each step's evidence (API read-backs, run receipts, the door item, the published update) captured under assets/story-06-walk/.
- [ ] Every inherited defect found live is paid with a failing-then-passing test or ledgered with his word.
- [ ] The owner's verdict recorded verbatim; PASS = the phase exit met.

## Test plan

- **Live (real HOME):** the walk script driven by a python live runner (live167-06.py) mirroring tests/e2e/test_hs166_jira_walk.py's real-HOME pattern, skip-guarded honestly without gh/acli auth.
- **Eye:** the attended walk; both widths.
