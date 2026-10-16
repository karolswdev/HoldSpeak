# Work and decisions — lane A

Built in `wt-cohesive-workflows-20261015`, branch
`feat/cohesive-workflows-20261015`. HOLD FOR SHIP: no staging, commit or push.

## Changes

- Workbench item instructions use the existing workspace draft authority,
  including an emptied instruction. Close flushes the debounce. Per-item body
  PUTs run in order across close/reopen; the receipt's exact Retry joins that
  same queue. A draft remains until the authoritative body contains it and
  outstanding writes have settled. This closes the reviewed A/B overlap.
- Add and its exact Retry share one pending guard. Accepted snapshots clear
  only themselves, including caret/reference state; newer inlet work stays.
- A successful empty template read shows the genuine empty state and Blank.
  A pending read still shows Loading.
- Gate decisions reread authoritative held proposals. Only HTTP409 with
  `error: already_decided` is a race; other failures reject with their original
  cause. An accepted/race POST followed by a failed read never becomes a
  retryable failed POST.
- Conductor retains the held call on read failure, reports decision failures
  next to the call and gives exact Retry. Settled calls with failed reads offer
  read recovery. The granted `LaneWindow.DecideVerbs` caller seam uses the same
  distinction and catches real refusal instead of an unhandled rejection.
- Coder replies have one pending send across typed/context sends. An accepted
  typed reply clears only its sent snapshot; newer text remains durable.

The existing library Buttons, SurfaceState, ActionNotice, footer receipts,
mic and API writers remain the material and authorities. No new framework,
hook, store, schema, route or service.

## Focused proof

All collection and runs used `.tmp/cohesive/locked.py`, the machine lock,
isolated HOME, `node node_modules/vitest/vitest.mjs`, and `--maxWorkers=2`.

| File | Final collected tests |
| --- | ---: |
| `components/__tests__/workbenchEditing.test.tsx` | 26 |
| `components/__tests__/workbenchTemplatePicker.test.tsx` | 9 |
| `conductor/__tests__/conductor.test.tsx` | 30 |
| `pullouts/CoderPullout.test.tsx` | 3 |
| `__tests__/gateDecision.test.ts` | 7 |
| `lane/__tests__/laneWindow.c2.test.tsx` | 55 |
| Total | 130 |

Exact final collected names: `.tmp/cohesive/lane-a-collected.json` and
`.tmp/cohesive/lane-a-collected-names.txt`.

Initial run `.tmp/cohesive/lane-a-focused.log`: 126 passed, one failed of127;
five files passed. The inherited Lane test tried Approve then Deny on the
same already-settled proposal. It is now two cases, one decision each, with
an assertion that the settled proposal has no further decision verbs.

Lane final run `.tmp/cohesive/lane-a-lane-final.log`: 55 passed in2.65s.
Workbench final run `.tmp/cohesive/lane-a-body-final.log`: 26 passed in7.84s,
including text and empty-body overlap cases. The four other files retain
their initial green results (49 tests). These focused run results cover all
130 final collected tests. Only Workbench product source changed after the
initial run; the Lane test correction is covered by its final rerun.

Root's release TypeScript check found Vitest's default mock implementation
union includes constructors in the template regression. The saved mock is
now narrowed to its callable URL/options signature. No product code or
collected names changed. `.tmp/cohesive/lane-a-template-typing.log`: 9 passed
in1.02s under the same isolated HOME and lock. Root reruns the release check.

The first collection used Vitest's optional `--json [path]` incorrectly;
Vitest wrote JSON to the first test filter path. It was detected immediately,
that JSON was parked under `.tmp/cohesive/lane-a-collect-first.json`, and the
owned test file was rebuilt from `git show HEAD:<path>` plus the regression
edits. Final collection uses an explicit JSON output path. No destructive git
verb ran.

## Limits

Focused tests use the existing controlled hub fixtures and deferred API
responses. They do not establish live provider, native input, tmux, owner DB,
or owner-machine outcomes. Root owns TypeScript/build/quick check and the
1440/393 built-bundle walks. No shots or broad suite were run by this lane.
No design criteria changed. No extra debt was found outside the scoped
caller/body overlap repairs.
