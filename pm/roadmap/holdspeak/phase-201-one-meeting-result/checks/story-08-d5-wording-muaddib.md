# HS-201-08 — Continuity claim scope

CLI confirms claude-fable-5-1 session 416adc59-a8c4-43b4-9a49-e9db0e8faf36.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the D5 wording for HS-201-08, 2026-09-20.** I used no tools, and no confirmed session id is available.

```
VERDICT: RATIFY

FINDINGS:
1. Root is right. My second D5 sentence claimed more than I had verified.
   - It read: "No current product path creates the decision or the commitment that
     day 2 carries".
   - I read the daily-loop test and the lane-A amendment. I did not audit every route.
   - The phase ledger itself names surviving hashless entry points outside the
     first-use path:
     - `meeting_import.py:_persist_import`;
     - `db/meetings.py:recover_capture`;
     - the retained `_on_intel_complete` / intel_queue bridge.
   - A universal absence is therefore not known, and the ledger gives evidence against
     it.
   - I withdraw that sentence. The original D5 stays verbatim in the earlier record,
     with this correction beside it.

2. The replacement wording is ratified exactly as proposed:
   - "Day 2 continuity is proven from a seeded day-1 state."
   - "The current first-use summary path does not create the decision or commitment
     that day 2 carries."
   - "No current owner creation path is proven by this rig."
   The BACKLOG return path sits next to these sentences. This wording states only what
   the evidence supports and no less. It keeps the owner-facing cost visible, which was
   the purpose of D5.

3. Recording the seven other `_boot`-without-`.stop()` sites as CANDIDATES is the
   right strength.
   - A same-function syntax scan cannot see teardown in a fixture finalizer, in a class
     teardown, or in a shared helper.
   - "Candidates, no claim" is therefore accurate. "No other fix in this story" is
     also correct.
   - Put the list under the fd-accumulation ledger item, because that is the question
     it serves.

4. The credential producer detail is a stronger (c) proof than I asked for.
   - Both loopback tests, happy_path and pipeline_events, issue a credential without
     revoking it.
   - Each paired probe reproduces 1 fail and 1 pass.
   - That is a named source, a reproduced mechanism, and an honest "full-run
     predecessor unknown".
   - Ledger it as two producers, and leave the loopback file untouched (R1).

CONDITIONS:
None new. D1-D4, D6, R1-R5 and X1-X2 stand as accepted. D5 stands as amended in
finding 2. F1-F6 and the closing sequence stand unchanged: web check, fresh T1, eleven
docs commands under Python 3.12, one complete worksteal run to 100% with zero failed
and zero errors.

MISSED:
1. Make "proven by this rig" equally honest in the other direction.
   - The ledger's legacy entry points are possible creators that nobody has verified.
   - They are not known to work either.
   - Avoid any phrasing that suggests the owner could reach proposals through import
     or recovery today.

TUESDAY: Unchanged. He can get the summary. Nothing here proves that he can create the
carried decision himself.

UNKNOWN:
- Whether any current route can create a decision or commitment end to end. Nobody has
  audited it, and the wording is ratified for that reason.
- Whether the seven candidate fixtures actually leak.
- The outcome of the next complete run and of the PR's CI.
```
