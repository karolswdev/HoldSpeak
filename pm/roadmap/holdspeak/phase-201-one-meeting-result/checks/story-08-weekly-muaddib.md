# HS-201-08 — Weekly brief counter assertion

CLI confirms claude-fable-5-1 session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Root accepts conditions; implementation pending.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the WEEKLY BRIEF family for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - the summary at the end of `.tmp/hs201-green/full-worksteal.log`
  - `tests/e2e/test_hs175_rhythm_brief_glass.py:392-432` and `:466-482`
  - `web/src/desk/pullouts/views/BriefView.tsx:108-119`, `:236-246` and `:324-345`
  - `web/src/desk/surface/count.ts:32-41`
  - a grep of `BriefView.test.tsx`
- **Not read:** `weekly-before.log`. The test code shows the mechanism by itself.
- **Scope:** this ruling covers the brief family only. The other three families are still unchecked.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. Classification (a) is correct. The fault is wider than "around midnight".
   - test_hs175_rhythm_brief_glass.py:413-417 applies `\b00\b` to the WHOLE text of the
     face.
   - BriefView.tsx:115-119 deliberately renders
     `GENERATED <MON> <DD> <HH>:<mm>` in local time, zero-padded.
   - The regex therefore fires when the hour is 00. It also fires when the MINUTE is 00
     at any hour.
     - The component's own docstring example, "GENERATED SEP 05 08:00", trips it.
     - So does the unit fixture at BriefView.test.tsx:57.
   - In total it fires on roughly one run in fifteen, at any time of day.
   - This is the same wall-clock family as the notification tests. The assertion is an
     invalid proxy for a valid law.

2. The law (A.8, no counters of zero) holds in the product by construction.
   - `countToken` returns null for n <= 0 (count.ts:37-38).
   - BriefView.tsx:240-246 and :332-345 render no row when the token is null.
   - A positive count renders as "3 MEETINGS", unpadded, so "00" can never be a counter
     on this face.
   - Nothing in the UI needs to change, and I agree with making no UI edit. Tenets 1-3
     and A.8 are satisfied without any redesign.

3. Removing the swallowed escape makes the test stricter, and I ratify it.
   - :398-400 wraps EVERY assertion in `if pullout_visible:`.
   - A brief that never opens currently passes all seven checks without running any of
     them.
   - Removing the guard may expose a second red. If it does, classify that as a new
     finding in its own right. Do not put the guard back.

CONDITIONS:
B1. Scope the glass counter assertion to the three primary labels:
    `brief-tw-meetings`, `brief-tw-armed` and `brief-tw-due`, via
    `.intelligence-brief-tw-primary`.
    - Assert the law positively. Each label that is present must match `^[1-9]\d* `.
    - A row whose count is zero must be ABSENT. Assert absence with `count() == 0` for a
      seeded zero where the rig allows it.
    - Do not replace one text regex with another narrower text regex over the whole
      face.
B2. The unit pins in BriefView.test.tsx cover BOTH trip cases.
    - Use a generated instant with hour 00, such as 00:33, AND one with minute 00. The
      existing 08:00 fixture will serve for the second.
    - For each, assert that the timestamp is visible, that zero rows are absent and that
      positive rows are present.
    - Drive the real BriefView with real `this_week` inputs, not a stub of countToken.
B3. The negative canary is captured in evidence.
    - A rendered "0 MEETINGS" or "00 ARMED" primary must FAIL the new glass assertion.
      Inject it in a modified harness only, and never in product code.
    - A 00:33 timestamp and an 08:00 timestamp must each PASS.
    - Capture the red first. weekly-before.log is that capture. Record its content
      through dw.
B4. Only two files change: the glass test and BriefView.test.tsx.
    - All other layout assertions in the glass test are retained. These are the
      one-gutter check, the no-period check and the NEXT-inside-MEETINGS check.
    - Both shots are retained.
    - Root views the 1440 and 393 shots after the change.
B5. After these test inputs change, the closing sequence restarts, and F1-F6 stand
    unchanged.
    - Rerun the web check and record the exit file plus zero BRANCH-NEW.
    - Take a fresh T1.
    - Rerun the eleven docs commands under Python 3.12.
    - Run a new complete final run to 100% with zero failed and zero errors.
B6. Amend the story and the ledger visibly.
    - This is a fourth repair family.
    - The PR body lists it, and it says plainly that the first complete worksteal run
      was RED with 6 failed.

MISSED:
1. The other three families are not covered by this ruling:
   - test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id;
   - test_remote_on_issue_revoke, at both widths;
   - test_a_project_carries_work_across_two_working_days, at both widths.
   Points on those:
   - The daily-loop pair is the ledgered inherited failure. The status doc says it fails
     "at the brief before meeting creation".
   - Check whether it shares THIS brief root cause before diagnosing it separately.
   - The SIGKILL test and the remote-settings pair each need their own red trace.
   - If any of them is class (b), it outranks this repair.
2. `\b00\b`-style proxies for "no zero counters" may exist in other glass files. A
   one-line grep would show them. Put the result in the ledger. Do not fix any others in
   this story unless they are red.
3. The run's tail shows a mermaid-cli stack trace (npx, `@mermaid-js/mermaid-cli`)
   printed just before the XFAIL lines.
   - It did not produce a FAILED node.
   - Confirm that it belongs to a passing or skipped test, and that it is not a
     swallowed error.

TUESDAY: Not applicable. No face changes. The brief he would open already shows the
right thing.

UNKNOWN:
- The content of weekly-before.log and the exact `body_text` that tripped the regex. I
  inferred the mechanism from the code.
- Whether removing the `if pullout_visible:` guard exposes a further red.
- Whether the daily-loop failures share this cause.
- The three unchecked families, the PR's CI run, and the outcome of any rerun.
```
