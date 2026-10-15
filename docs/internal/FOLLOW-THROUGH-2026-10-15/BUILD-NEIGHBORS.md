# Neighbor attention faces — build report, 2026-10-15

Status: HOLD FOR SHIP. Parent owns independent review, live proof and release.
Worktree: `/Users/karol/dev/tools/wt-follow-through-20261015`; base `420a0eb28`.
Built the settled Neighbor faces direction in `DESIGN.md`, including the
parent's amendment to put the main Material inside a named inset GadgetGroup.

## Delivered

- Brief clears the previous person when selecting an item and clears the
  previous item when selecting a person. The actual selected row is marked,
  and the last selection supplies the footer subject and actions. Existing
  source opening, agenda and shelf writers remain. Source:
  `web/src/desk/pullouts/views/BriefView.tsx:496`, `:511`, `:556`.
- The decision window uses the library CycleGadget. Opening the real choice
  popup writes nothing. Explicit Proposed/Accepted/Replaced/Retired choices
  map to the existing proposed/accepted/superseded/deprecated values and PUT.
  A synchronous guard blocks duplicate pending writes. The previously saved
  state stays visible until success; a refused HTTP response or exception
  produces STATUS FAILED and an exact-choice Retry. Source:
  `web/src/desk/pullouts/DecisionPullout.tsx:91`, `:125`.
- Decision text sits in one inset Decision paper with Material. Context and
  Consequences use library folds; empty content stays omitted. Editing uses
  named inset groups with the same three drafts. The existing title update,
  Copy, Dictate, Send and filing paths remain. Previous/Next decision verbs
  use explicit words rather than an opaque key. Source:
  `web/src/desk/pullouts/DecisionPullout.tsx:140`, `:160`.
- The Decisions reader uses inset Material, named Context rows, and folded
  Evidence/History. Real quotes, speaker, rationale, alternatives, owner,
  review, linked work, chain and revision values remain available. Source,
  work and history verbs name Open meeting/decision/artifact/work and
  Previous/Next decision. Empty evidence/history sections are omitted.
  Source: `web/src/desk/pullouts/views/DecisionsView.tsx:436`, `:497`,
  `:511`, `:525`.
- Each requested decision/record read has its own destination and failure.
  Failure shows Try again and Results; the old record cannot appear as the
  requested result. Read generations fence older answers and Results
  invalidates an in-flight read. Source:
  `web/src/desk/pullouts/views/DecisionsView.tsx:248`, `:257`, `:285`, `:449`.
- New local `attention-records.css` composes library material, wrapping,
  record feedback and the Brief selection mark. No shared CSS or library was
  edited by this lane.

## Scope

Product files: BriefView.tsx, DecisionsView.tsx, DecisionPullout.tsx and
attention-records.css. Test files: BriefView.test.tsx, DecisionsView.test.tsx,
decision.app.test.tsx, plus the parent's explicit extension for presentation
adaptation in philo301DecisionFace.test.tsx and
philo605DecisionBodyDiagnosis.test.tsx. philo301DecisionNoLoss.test.tsx was run
unchanged.

Presentation assertions were adapted to the settled paper and folds:
`Decision context → Context`; Decision is read first; the old h3 lookup in
the body diagnosis now finds the accessible Decision region. Added assertions
retain all three real field bodies. Save, optimistic rollback, writer order,
new decision/title, reopen and no-loss assertions were not weakened.

No backend, host navigation, shared intelligence.css, library, canvas or
status edits by this lane. No browser, web build, install, staging, commit,
owner-state access or external action. Other lanes' changes in this shared
worktree were left alone.

## Collection and regression evidence

Every list/run used the parent's isolated-HOME lock helper from the worktree
root and exactly these six files:

```sh
.venv/bin/python .tmp/follow-through/locked.py neighbors-collect --web \
  ./node_modules/.bin/vitest list \
  src/desk/pullouts/views/BriefView.test.tsx \
  src/desk/pullouts/views/DecisionsView.test.tsx \
  src/desk/__tests__/decision.app.test.tsx \
  src/desk/__tests__/philo301DecisionFace.test.tsx \
  src/desk/__tests__/philo301DecisionNoLoss.test.tsx \
  src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx --maxWorkers=2
```

Full collection: `.tmp/follow-through/neighbors-collect.log`. The five added
regression names are present verbatim in that collection:

```text
src/desk/pullouts/views/DecisionsView.test.tsx > Intelligence → Decisions (PHILO-17: every decision, its date and its meeting) > a failed requested record shows its own failure, exact Retry and Results
src/desk/pullouts/views/DecisionsView.test.tsx > Intelligence → Decisions (PHILO-17: every decision, its date and its meeting) > a late record response cannot replace a later destination or Results
src/desk/__tests__/decision.app.test.tsx > the decision window chooses a named state > inspecting status writes nothing; a chosen state renders only after success
src/desk/__tests__/decision.app.test.tsx > the decision window chooses a named state > a refused status keeps the old state and Retry repeats the exact choice
src/desk/pullouts/views/BriefView.test.tsx > BriefView person sections > the latest person or item selection owns the row and footer
```

Before product edits, the same six-file run with the newly added checks was
red. `.tmp/follow-through/neighbors-red.log`:

```text
Test Files  3 failed | 3 passed (6)
     Tests  5 failed | 52 passed (57)
  Duration  4.24s
```

The red names are the five listed above. The red showed the retained Ewa
footer, hidden record failure, older record replacing the latest, and absent
named status choice. After the build, the status cases were strengthened to
open and pick from the real Workbench popup, and the failed-record case now
presses the real Next decision chain verb.

Initial completed build run used the same command and exact paths, with label `neighbors-green`
and Vitest verb `run`. `.tmp/follow-through/neighbors-green.log`:

```text
RUN  v4.1.9 /Users/karol/dev/tools/wt-follow-through-20261015/web

Test Files  6 passed (6)
     Tests  57 passed (57)
  Start at  13:37:35
  Duration  4.24s (transform 1.54s, setup 359ms, import 2.81s, tests 3.00s, environment 1.29s)
```

`git diff --check` over the eight modified owned source/test files was clean.
No wider test scope was run. Existing transport fixtures/doubles were reused;
this does not claim a live hub status change or a real People agenda write.

## Final review correction — source identity

The final reviewer found a new P2 regression in the Context source verb.
`DecisionRecordService.create_from_meeting` stores a **decision ID** in the
top-level `source_id`, even when `source_type` is `meeting`. Actual meeting
identity lives in the evidence sources. The initial build incorrectly treated
the top-level ID as a meeting ID.

Corrected `web/src/desk/pullouts/views/DecisionsView.tsx:484` to call the
existing `decisionRecordSourceRef` helper. The top-level source now uses
Open decision and the canonical `decision:<id>` / `desk_decision:<id>` ref.
Evidence meeting refs and their Open meeting path are unchanged. No route,
backend, library or other face was changed for this correction.

The new typed-shape regression keeps the real helper (only `openRef` is
replaced), follows the Context source and evidence source, and asserts their
different destination identities. Exact collection evidence in
`.tmp/follow-through/neighbors-origin-collect.log`:

```text
src/desk/pullouts/views/DecisionsView.test.tsx > Intelligence → Decisions (PHILO-17: every decision, its date and its meeting) > a meeting-derived record opens its source decision and keeps meeting evidence identity
```

The same six-file command above, verb `run`, was red before the source fix
(`neighbors-origin-red.log`):

```text
Test Files  1 failed | 5 passed (6)
     Tests  1 failed | 57 passed (58)
  Duration  4.50s
```

After the correction, the isolated locked exact six-file run
(`neighbors-origin-green.log`) passed:

```text
Test Files  6 passed (6)
     Tests  58 passed (58)
  Start at  13:45:19
  Duration  4.35s (transform 1.54s, setup 379ms, import 2.84s, tests 3.12s, environment 1.36s)
```

`git diff --check` on the corrected source/test was clean. The initial review's
second finding and final freeze are recorded below.

## Initial review correction — pending Brief request subject

The initial reviewer also found a P2 receipt regression: clearing a receipt
when the selection changes does not cancel an already pending attempt. A
late agenda/shelf refusal could replace the new selection's footer with an
unnamed failure and Retry for the earlier subject.

The actual pending request and exact Retry already held the correct target;
those closures remain. Agenda attempts now capture the person's display name
and a person subject key; shelf attempts capture the item's primary name and
an item subject key. The existing hook therefore renders an immutable named
failure such as `EWA · ADD TO 1:1 AGENDA FAILED · HTTP 503` or
`STANDUP · DEFERRED FAILED · HTTP 409`. When a failure is present, the footer
also retains the latest selected subject as a separate line. Local CSS wraps
the full named failure. Clean footer layout stays the same.

Source: `web/src/desk/pullouts/views/BriefView.tsx:274`, `:333`, `:361`,
`:604`; `web/src/desk/pullouts/attention-records.css:93`. No receipt hook,
framework, host, route or backend change.

BriefView's tests now use the real `useWriteReceipt` rather than the previous
always-success hook double. The new checks hold/reject the existing API
transport double and drive the rendered Retry. They prove Ewa → Standup
keeps Standup's footer/actions while the failure/Retry names and writes Ewa;
then reverse and clear selection. They also prove Standup shelf → Ewa → clear
keeps the late failure named Standup, and Retry repeats the exact original
item route and `state: deferred` payload without an agenda write.

Exact collection in `.tmp/follow-through/neighbors-custody-collect.log`:

```text
src/desk/pullouts/views/BriefView.test.tsx > BriefView person sections > a late agenda refusal names its original person while the item keeps the footer and Retry target
src/desk/pullouts/views/BriefView.test.tsx > BriefView person sections > a late shelf refusal after person selection clears names the original item and preserves exact Retry
```

Before the source correction, the same isolated locked exact six-file run
(`neighbors-custody-red.log`) showed both added checks fail:

```text
Test Files  1 failed | 5 passed (6)
     Tests  2 failed | 58 passed (60)
  Duration  4.38s
```

Final exact six-file run (`neighbors-custody-green.log`):

```text
Test Files  6 passed (6)
     Tests  60 passed (60)
  Start at  13:50:21
  Duration  4.54s (transform 1.64s, setup 364ms, import 2.93s, tests 3.36s, environment 1.30s)
```

The command is the same six-file command above, label `neighbors-custody-green`
and verb `run`; collection uses label `neighbors-custody-collect` and `list`.
`git diff --check` on the corrected Brief source/test was clean. These are
transport-double assertions, not real People or shelf writes.

Lane FROZEN after both initial-review corrections. HOLD FOR SHIP pending the
single recheck and the parent's live reading of the named footer at both
widths. No further source edits planned.

## Parent proof still owed

Read the production faces at 1440 and 393, including a status refusal, person
to item selection, and failed Next decision followed by Try again/Results.
Check actual paper fill, fold operation, wrapping, hit ownership and console.
This lane makes no live geometry, clipboard, encryption, network-send or
owner-desk claim. Owner judgment, independent finished review, quick check
and shipping remain with the parent.
