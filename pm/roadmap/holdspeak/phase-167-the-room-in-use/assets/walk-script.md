# The Tuesday walk — the owner's first real project through the whole Room

Written 2026-09-03 (charter+1, before 04 lands) per story-06. Two
legs: the ORCHESTRATOR's dry run on the real desk first (a fresh
project the owner archives afterwards — never deleted), every defect
recorded and paid; then the OWNER's attended walk at his hub (1440)
and on the 393 glass. Real HOME, real gh (karolswdev), real acli
(karolsaneapple.atlassian.net / KAN). The runner: live167-06.py
mirrors tests/e2e/test_hs166_jira_walk.py's real-HOME pattern and
skips honestly without gh/acli auth (a collectable skipif).

Preconditions (asserted, never assumed): the web bundle BUILT from
the branch head; the hub reachable; `gh auth status` and `acli jira
auth status` both authenticated; the desk DB is the owner's real one
(`~/.local/share/holdspeak/holdspeak.db`) — count projects BEFORE.

| # | Step | The face (D-section) | Wire it drives | What is asserted, both widths |
| --- | --- | --- | --- | --- |
| 1 | New project by voice: the interview for `HoldSpeak 167` — outcome "The first real project through the whole Room, attended"; notice "PR activity, KAN due dates, stale decisions" | D2 the interview | POST /api/project-setup (start) → /answers ×2 → /suggest | ProgressPlan lights Outcome → Notice → Sources; answered rows collapse with Edit; THE BRIEF fills; the mic on the well; `2 of 4` in the footer |
| 2 | The GitHub connection through the wizard: select the GitHub suggestion, Check, pick `karolswdev/HoldSpeak`, ITEMS issues + PRs | D3 the GitHub wizard | /proposals/{id}/select → clarify-scope → /test | Connection card `Connected` with `gh · github.com`; repo card facts (branch/issues/PRs) from the live API; EgressChip `github.com` on Check/Test; the test ProgressPlan lights all four; matches ≥ 1 real issue |
| 3 | The Jira connection: select the Jira suggestion, the one acli account, project KAN, TYPES enumerated, STATUS observed | D8 the Jira wizard | /proposals/{id}/select → clarify-jira-scope → /test | Account card `Connected` naming the site; KAN card; preview `N issues · M calls`; KAN-1 with its DUE token (2026-09-10 — the day-early law holds) |
| 4 | Activate: review WHAT WILL RUN (2 watches), Activate | D4 the activation review | /finalize | Two ledger rows with CheckGadgets; footer EgressChips name BOTH hosts; the Baseline plan lights for both providers; baseline_state=established with a REAL snapshot (the 166 false-baseline law) |
| 5 | The Room lands: identity band, FOCUS, THE WEEK | D1 the Room | GET /api/projects/{id} + /delta | StateChip lifecycle + posture from the wire (no health chip); REV token; four wings present; ledger rows never ellipsize; ScrollHint on the stream when it scrolls |
| 6 | A real change on each source: one commit/PR touch on the repo and one KAN transition (reverted in a finally, as 166 does) → Review the two Deltas, Accept one, Defer one (two-step), Dismiss none | D5 the Review posture | POST /reviews (delta) → /decide ×2 | Queue sections with counts; the expanded row's CURRENT/PROPOSED facts; keyboard j/k/a/l; the footer tally; ONE Delta per transition, no duplicate on refresh |
| 7 | One manual steward run, watched to RECORD; the door item on the Door; then Unattended ON with a cadence set ON THE FACE (the 02 write) and one unattended tick observed | D7 the Steward posture | POST /steward/runs; PUT /steward/policy; the trigger route (02) | THE RUN plan with counts/durations/receipt chips (Observe carries `calls`); RUNS ledger; the policy sheet saves the cadence and the next-tick token updates; a second manual press at the same watermark creates a run that reconciles (the 163 law); the door item appears once |
| 8 | An update drafted from the week's deltas, Save, then Publish; read it on the desk | D6 the Update posture | POST /updates/draft → PUT /updates/{id} → /publish | DRAFTS ledger; citation rows under each section; an unverified claim as an ActionNotice; the footer's egress chip honest (deterministic vs model host); Receipt after publish; the published update readable in TIMELINE |

After step 8: the owner's verdict question, verbatim: **"Will you use
this on a Tuesday?"** Recorded verbatim in story-06 and the record.

Cleanup (the orchestrator's leg only): the KAN transition reverted in
a finally; the repo touch reverted; the project ARCHIVED (never
deleted — the never-delete law); the DB project count read back.

Defect ledger: every defect found live gets a failing-then-passing
test under tests/unit/test_hs167_walk_fixes.py (the 166 precedent) or
the owner's word that it is ledgered.
