# agent_result — adversarial review

Workflow id: `agent_result`  
Job: Read an agent result, review it and answer or approve  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_agent_result`  
Evidence class: source and assertion inspection; no execution or owner observation

VERDICT: DO-NOT-RATIFY

## Totality

The job starts from an Agents, Needs you, Today, or handed-item row and must
bind one launch to its session and completed turn. The owner needs last words,
changed files/branch/PR, and resources read or written.
If the turn waits, the same place must answer its current `wait_id` or show
the held command before Approve/Deny. Stale reads, a missing pane, restart,
gate races, and an unknown result belong to the job. Reopen must return to the
same launch with an honest receipt and seen state.

The audit names only `LaneWindow.tsx` and says “one monitor contract”. Active
source already divides this contract: the lane endpoint returns launch,
review, session, worktree, `used`, and `last_words`
(`holdspeak/services/launch_lane.py:478-549`); `ResultBlock` renders those
facts and the review result (`web/src/desk/lane/ResultBlock.tsx:32-65`); and
the lane store binds sends and stops to the launch session
(`web/src/desk/lane/laneStore.ts:243-303,385-421`). The brief does not state
which facts are authoritative, when a result becomes terminal, or how the
owner returns to the row.

FINDINGS:

1. **P1 — the result/review contract is not specified end to end.** The
   listed `tests/unit/test_process_input_kernel.py:100-159` proves terminal
   command receipts, not result identity, review rounds, or reopening. Actual
   result coverage is in `tests/unit/test_agent_result.py:16-33` and
   `tests/integration/test_desk_agents_wire.py:1186-1221`; the lane exposes a
   done Result at `web/src/desk/lane/LaneWindow.tsx:287-300`. Without
   `launchId + sessionKey + turnId`, read-failure shapes, and durable seen/close,
   the owner can see the wrong turn. Cost: lost trust and repeated inspection;
   Tenets 2, 3 and 6. Correction: specify fields/transitions and assert two
   launches plus close/reopen.

2. **P1 — answer, approve, and recovery are collapsed into “input ownership”.**
   The answer path names the current wait and refuses stale delivery
   (`web/src/desk/lane/laneStore.ts:267-294`); gate approval has separate
   whole-command/race behavior (`web/src/desk/lane/LaneWindow.tsx:349-411,
   759-829`; assertions at `web/src/desk/lane/__tests__/laneWindow.c2.test.tsx:314-344,795-837`).
   Specify terminal-gone, unread, delayed, already-decided, and retry receipts
   or the owner cannot tell “not delivered” from “delivered but not read”.
   This fails Tenets 3 and 6. Correction: one launch monitor, distinct
   answer, gate, and terminal contracts with return behavior.

3. **P1 — convergence is asserted by generic codes, not actual consumers.**
   `docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2650-2689`
   lists `APP_ID`, `SCROLL`, and `OP_OUTCOME`, but not reusable state or its
   first owner; active consumers include
   `web/src/desk/conductor/ConductorWindow.tsx:434-465` and
   `web/src/pages/cores/ProcessCore.tsx:1-100`. Cost: duplicate state and a
   wrong return path. This fails Tenets 1, 3 and 5. Correction: name
   `agents_conductor` (row, New/seen, open),
   `terminals_processes` (session input, follow/pause, stop), `agent_hand`
   (origin and launch), and `today_followthrough` (attention and return).
   Share launch identity, turn/result receipts, focus and read-failure facts;
   keep gate authority, terminal rendering, and review-loop ownership separate.

## Convergence

First consumers are `ConductorWindow`/`fleetTile`, `LaneWindow`/`ResultBlock`,
`ProcessCore`, HandSheet, and Today/Needs. Reuse `launchId`, `sessionKey`,
`turnId`, `originRef`, `seen`, and terminal receipts. Do not merge into a
universal monitor: a held gate is an owner decision, terminal keys are
pane-scoped, and a reviewer pair has bounded authority.

## User experience

The captures show a recognizable Agents shell at 1440 and 393
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/conductor-1440.png`,
`conductor-393.png`), and source suggests a fast Open-to-lane path. No result
capture was inspected. A result hidden behind Open or a receipt lost on refresh would
break the fast path. Keep the result in-world and provide one return to Agents.

CONDITIONS: Expand to backend wire, `ResultBlock`, `agentFlights`,
Conductor/Today/Needs consumers, and lane assertions; define
identity/result/review/answer/approval/recovery/return transitions; name the
shared contracts and retained boundaries; then add the challenges below.

MISSED:

1. Highest cost: two launches finish near each other and a late result must
   not paint into the wrong launch.
2. A review pair ends with MUST findings after round two and remains actionable.
3. Restart or pane loss leaves a named stopped/unknown state and preserves the
   result and return path.
4. Approval is decided elsewhere while the owner has a stale Raw view.

TUESDAY: The happy path may be quick, but this audit cannot ensure the owner
can identify, trust, act on, and return from one result without competing faces.

## Acceptance challenges

1. Open two completed launches in alternating order; each shows its own
   `turnId`, last words, files, review result, and receipt after refresh.
2. Open a done launch with `used` unreadable; the result says NOT READ and still
   shows independent worktree/last-word facts, then recovers on Retry.
3. Answer a current wait once, then replay the old `wait_id`; the first press is
   delivered and the second is refused without duplicate text.
4. Show a whole held command, decide it in another face, reopen Raw, and show
   the authoritative outcome rather than a second approval.
5. Kill or lose the pane, reopen the launch from Agents, and retain a named
   stopped/unknown state plus the result and return action.

UNKNOWN: No tests were run. No lane/result capture, live Desk walk, real agent
output-quality check, native terminal acceptance, accessibility/performance
proof, or owner acceptance was observed.
