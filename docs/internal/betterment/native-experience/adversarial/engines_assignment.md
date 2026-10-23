# engines_assignment

Job: Choose what runs where and verify engine readiness  
Baseline: `55572802181d6a8045f6d27e3c722aaf5694dbbd`  
Reviewer task: `review_engines_assignment`  
Evidence class: source and assertion inspection plus supplied 1440/393 captures; no test execution, provider call, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The canonical use case starts with an execution destination and ends with a run
record naming the real destination (`docs/USE_CASES.md:17`). This audit does
not decide whether the family ends at assignment or hands off to a run
workflow. `model.assignment` does not execute providers
(`docs/CAPABILITIES.md:32-37`); `WhatRunsWhere` is a configuration list whose
“Try it” is a fixed sample (`web/src/features/runson/WhatRunsWhere.tsx:1-9`).
It is not yet a sufficient implementation brief.

FINDINGS:

1. **P0 — The whole job and family boundary are missing.** Evidence:
`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2888-2919`
names assignment/readiness gaps while
`web/src/features/runson/useRunsOn.ts:444-478` stores only a transient probe result. Cost: Settings can
ship while “run on another machine” has no durable result or recovery. This
fails Tenets 2 and 3. Split `engines_assignment` from a named execution/
monitor workflow, or document the hand-off, first consumer, terminal states,
and return-to-task contract.

2. **P1 — configured placement and actual probe placement are not fully distinguished.** The row's engine chip describes its effective assignment (`web/src/features/runson/WhatRunsWhere.tsx:98`). The result does use the actual `answer.model` (`web/src/features/runson/useRunsOn.ts:462-470`), so model identity is not wholly dropped. The route also supplies actual boundary/host and route/execution IDs (`holdspeak/services/route_probe.py:372-399`), which the row result does not retain/display (`WhatRunsWhere.tsx:160-170`). Cost: the intended placement chip can be mistaken for the sample's actual egress. This fails Tenets 3 and 7 and Article III. Correction: label configured versus served facts, retain the existing runtime identity for inspection, and show actual off-device host/boundary with the result. Do not rewrite assignment on fallback.

3. **P1 — diagnostic samples and real-work recovery have no stated boundary.** The client receives route/execution IDs (`web/src/features/concierge/api.ts:181-209`), while `tryRow` keeps a transient result (`web/src/features/runson/useRunsOn.ts:444-478`). That can be appropriate for a clearly bounded sample. Cost: the audit could either inflate every probe into a retained task or mistake a sample for completion of the remote-work job. This fails Tenets 1 and 3. Correction: explicitly state sample lifetime/cancel semantics; hand real Ask/meeting work to its existing durable run/result path and verify return there. Engines does not need another run monitor.

4. **P1 — A readiness read can strand the fast path.** Bulk editor reads turn
errors into `"failed"` (`web/src/features/runson/useRunsOn.ts:374-388`); the face renders only `NOT READ`
with no retry (`web/src/features/runson/WhatRunsWhere.tsx:81-97`). A LIMITED fit may legitimately remain selectable; existing `accepts` already checks model record/revision, speech/text compatibility and broken fit (`web/src/features/runson/model.ts:346-367`). Cost: a transient failure
looks like a dead end. This fails Tenets 2, 3, and 6. Define check-time versus run-time readiness, name refusals, and provide an existing in-place retry/repair path. Preserve useful limited engines rather than introducing a blanket readiness gate.

## Convergence

Share one contract with `agent_result` and `mcp_tools`: assignment scope and
profile revision are configuration; operation/execution/route-plan ids,
winning deployment, egress, outcome, cancellation, and receipt are runtime.
First consumers should be `ask_whole_desk` and `meeting_intelligence`, whose
surfaces already own output and return. Keep Engines concise; do not merge all
workflows into a generic monitor because Ask and meeting recovery differ.

## User experience

The supplied captures show an honest empty state at 1440 and 393: “No engine
yet”, clear Find/Add actions, and no zero counters
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-engines-1440.png`,
`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-engines-393.png`). They do not
show assignment, remote result, fallback, or recovery. Assertions promise
two-press assignment and a sample answer
(`web/src/features/runson/__tests__/engines.app.test.tsx:461-535`), not live quality, craft, or durable return.
Trust breaks if the chip names an intended route and the run is elsewhere.

CONDITIONS: Bound configuration versus execution; preserve and display one
converged runtime identity; specify egress, terminal/recovery/cancel behavior;
add readiness refusal/retry semantics; and exercise the scenarios below.

MISSED: (1) remote timeout/fallback/indeterminate and restart; (2) stale
readiness or sign-in change; (3) return to Ask/meeting with the task intact;
(4) repeated jobs in two windows without duplicate execution.

TUESDAY: Not yet—the owner can choose a route, but cannot trust that it ran
there or recover the run from this screen.

## Acceptance challenges

1. Assign Answers to a LAN engine, leave Engines, run Ask, and verify the
   durable receipt names actual host/model; return to Ask without reconfiguration.
2. With an ordered LAN-then-cloud chain, make the first leg fail; verify one
   run id, explicit fallback legs, actual winning egress, and unchanged
   assignment.
3. Start a remote run, close/reopen the Desk, cancel through the supported
   path, and verify a terminal cancelled/indeterminate receipt with no duplicate.
4. Make an editor/readiness request fail transiently; verify the row says why,
   offers retry, and does not silently save or remove an assignment.

UNKNOWN: No tests were run; no live provider, native path, API walk, performance
measurement, or owner-state observation was made. Model quality, latency, cost,
provider sign-in, and owner delight remain unproved. Source anchors are baseline
specific and may drift.
