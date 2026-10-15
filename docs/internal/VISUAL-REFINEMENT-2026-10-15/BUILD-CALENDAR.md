# Calendar chooser repair

Outcome: built and frozen for root SHIP. Worktree:
`/Users/karol/dev/tools/wt-visual-refinement-20261015`, base `94551006a`.
Root sent the settled canvas signal after reading
`.tmp/visual-refinement/canvas-settled` at 1440 and 393.

The compact chooser now uses the existing inset GadgetGroup named Choose
calendar, retains its IN USE/FOUND state, shows checking/unavailable/empty
read states, and offers an actual busy-aware Check again or Retry. Its
Calendar URL field remains available with an existing source. Noncompact
first use still renders the original Card and keeps its original URL and
permission visibility. This addresses Tenets 3/5/6: a visible next action
in the existing component grammar.

Product change is only `web/src/desk/firstrun/CalendarCard.tsx`: named inset
at line 28; read states at line 58 and line 97; compact Retry uses the
existing `checkAgain` at line 89; compact URL visibility at line 210.
No CSS, ConnectionsPane, calendarStep, sibling lane, or library edits.
Existing source IDs, Refresh name, permission presses, beforeUse/onUsed,
busy handling, URL host egress and first-use receipts retain their handlers.

Focused regressions are in
`web/src/pages/cores/__tests__/connections-pane.test.tsx`: existing-feed
Add/save gate at line 703; delayed initial read/named inset at line 730;
unavailable/empty recovery, retained URL/host and disabled concurrent
actions at line 750; failed-read Retry with no POST at line 790. The two
state cases use value changes to the recorded hub response, and every
recovery presses through to the rendered calendar candidate.

## Exact test proof

Commands were named before running. Each command used root's helper,
isolated temporary HOME, the machine test lock, Node 22, and disabled
native/device integrations. No build, browser, install, whole suite or
external service was run by this worker.

```sh
python3 .tmp/visual-refinement/locked.py calendar-collect-red --web ./node_modules/.bin/vitest list src/pages/cores/__tests__/connections-pane.test.tsx src/desk/firstrun/__tests__/OneScreen.test.tsx -t '[Cc]alendar' --maxWorkers=2
python3 .tmp/visual-refinement/locked.py calendar-red --web ./node_modules/.bin/vitest run src/pages/cores/__tests__/connections-pane.test.tsx src/desk/firstrun/__tests__/OneScreen.test.tsx -t '[Cc]alendar' --maxWorkers=2
python3 .tmp/visual-refinement/locked.py calendar-focused --web ./node_modules/.bin/vitest run src/pages/cores/__tests__/connections-pane.test.tsx src/desk/firstrun/__tests__/OneScreen.test.tsx -t '[Cc]alendar' --maxWorkers=2
```

Collection exited 0 and selected 31 tests. Exact output is
`.tmp/visual-refinement/calendar-collect-red.log`; the added/strengthened
cases appear verbatim as:

```text
src/pages/cores/__tests__/connections-pane.test.tsx > Accounts recovery > Settings calendar URL Add remains available with an existing feed, waits for the save gate and reconciles the accepted use
src/pages/cores/__tests__/connections-pane.test.tsx > Accounts recovery > Settings calendar chooser names its inset and shows loading until the read returns
src/pages/cores/__tests__/connections-pane.test.tsx > Accounts recovery > Settings calendar chooser distinguishes 'unavailable' from loading and reads again without a prompt
src/pages/cores/__tests__/connections-pane.test.tsx > Accounts recovery > Settings calendar chooser distinguishes 'full_access' from loading and reads again without a prompt
src/pages/cores/__tests__/connections-pane.test.tsx > Accounts recovery > Settings calendar chooser retries a failed read without calling native permission or URL writes
```

Before product edits, `.tmp/visual-refinement/calendar-red.log` exited 1:

```text
Test Files  1 failed | 1 passed (2)
     Tests  5 failed | 26 passed | 50 skipped (81)
  Duration  5.54s
```

The five failures reproduced hidden Add, absent named/loading sheet,
absent unavailable state, absent empty state and absent compact Retry.
Existing first-use Calendar coverage passed before the repair.

After the repair, `.tmp/visual-refinement/calendar-focused.log` exited 0:

```text
RUN  v4.1.9 /Users/karol/dev/tools/wt-visual-refinement-20261015/web
Test Files  2 passed (2)
     Tests  31 passed | 50 skipped (81)
  Start at  00:45:28
  Duration  2.88s (transform 1.10s, setup 136ms, import 1.50s, tests 3.22s, environment 385ms)
```

`git diff --check` on the two changed code/test paths exited 0. No product
or test edits or test reruns followed green. No stage or commit. Root owns the combined
check, production shots, PR and deployment. Hardware permissions and real
calendar hosts were not exercised; no worker visual validation is claimed.
