# Work object views — bounded source audit

Status: DRAFT — source candidates, awaiting root's isolated live inspection.
Base: `94551006a`; worktree `wt-visual-refinement-20261015`, branch
`feat/visual-refinement-20261015`. Anchors below were read on 2026-10-15.
HOLD FOR SHIP. No browser, tests, build, install, staging or commit ran.
Only this report was authored.

The strongest visual target is the Workbench result reader. It repeats the
output when the owner presses Open and puts a scrolling result inside the
scrolling item list. The strongest failure target is the same window's
Runs/Memory branches, which can label failed reads as empty. Neither claim
below is a live result; root owns confirmation at 1440 and 393.

## Ranked candidates

### 1. Workbench result Open repeats the output and adds another hierarchy

**Owner job:** read an agent's completed output, inspect what was kept, then
copy, re-run or park the item.

**Opening path:** command palette → Workbenches, or `/workbenches`
(`open-workbenches`;
`web/src/desk/applications.ts:287`), named workbench card
(`web/src/pages/cores/WorkbenchesHomeCore.tsx:123`), Items → item title →
Open. The named workbench owns window `workbench:<id>`
(`web/src/desk/components/WorkbenchWindow.tsx:1626`).

**Current defect:** `WorkbenchWindow.tsx:862` always renders the result's
`Material`. Open toggles `artifactExpanded` at `WorkbenchWindow.tsx:909`
and adds the same `Material` again at `WorkbenchWindow.tsx:873`. The second
copy adds a raw artifact ID (`WorkbenchWindow.tsx:870`) and repeats the
literal `pending-review` label (`WorkbenchWindow.tsx:843`,
`WorkbenchWindow.tsx:869`). This branch does not read the artifact itself;
the owner gets another copy of the result with additional metadata.
`web/src/desk/components/workbench-config.css:374` caps the first result at
300px and scrolls it, inside the scrolling `.wb-items` at
`workbench-config.css:249`. Its nonwrapping result header is at
`workbench-config.css:360`; whether its chips clip at 393 needs glass.

**Existing species:** `SurfaceWell` (`web/src/desk/surface/Surface.tsx:440`),
`Material`, the existing library Button, `EgressChip`, and `SurfaceState`.
Use one result presentation and one scroll owner in the settled canvas.
Keep Copy on that result, real artifact state when available, Re-run/Park
on the item, and all write/copy/Park receipts in the existing footer.

**Fails:** Tenets 3/5/6/7; UX-CANON B/D; DESIGN_SYSTEM composition rules
1–3. **Live check needed:** long stored result with a real artifact link;
expand, Open, Collapse, Copy, Re-run and Park/Restore at both widths.

### 2. Workbench Runs and Memory can present failed reads as empty

**Owner job:** see what ran and what the agent retained; retry a failed
read without launching more work.

**Opening path:** the same workbench → Runs or Memory wing.

**Current defect:** `WorkbenchWindow.tsx:1007` and
`WorkbenchWindow.tsx:1008` create independent reads. Their data becomes
`[]` at `WorkbenchWindow.tsx:1014` and `WorkbenchWindow.tsx:1015`; the only
read error carried to the face is `detailHook.error` at
`WorkbenchWindow.tsx:1019`. No Runs/Memory loading, error or retry reaches
their render branches. On a failed first read,
`web/src/desk/components/workbench/WorkbenchRunsWing.tsx:30` says No runs
yet/No agent bound and can offer Run now or Bind an agent. Memory says No
memories yet at `WorkbenchWindow.tsx:2039`. The owner cannot distinguish a
failed read from successful emptiness.

**Existing species:** the hook already exposes loading/error/refresh
(`web/src/desk/hooks/usePrimitiveDetail.ts:43`); `SurfaceState` already
renders an in-flow failure and retry (`Surface.tsx:256`). Reuse the same
pattern the item-detail error uses at `WorkbenchWindow.tsx:1702`.

**Fails:** Tenets 3/5/7; UX-CANON A10; Constitution VI. **Live check needed:**
first-load failure of `/api/workbenches/<id>/runs`, then `/memory`; the
successful detail and item draft must stay available. Restore each read
and retry it. A prior cached read may remain visible, so cold and warm
failure states must be distinguished.

### 3. Project Room History has no unavailable or no-match face

**Owner job:** find what changed in a project and tell an unread history
from a quiet day or a filter with no matches.

**Opening path:** Projects → named project → Room → History. Project refs
open the Room at `web/src/desk/openObject.ts:153`; History can also be
requested by `openProjectRoomAt(id, "history")` at `openObject.ts:97`.

**Current defect:**
`web/src/features/project-room/ProjectRoomCore.tsx:2413` turns every
non-OK changes section into an empty array. `ProjectRoomCore.tsx:2829`
then returns zero history counts, and `ProjectRoomCore.tsx:2435` renders
Nothing today. `ProjectRoomCore.tsx:2464` only maps rows: no failure or
empty/no-search-match state is rendered. The decoder preserves a real
degraded section (`web/src/features/project-room/model.ts:550`), while
the controller's readError at
`web/src/features/project-room/useProjectRoomController.ts:151` catches a
failed whole request; a successful Room response with a degraded changes
subread takes the silent branch. A search with no matches also leaves the
stream blank. The search is a raw input at `ProjectRoomCore.tsx:2449`.

**Existing species:** keep the already merged `FilterTokens`
(`ProjectRoomCore.tsx:2441`) and `SurfaceStream`; reuse `StringGadget` for
search and `SurfaceState` for unavailable/retry and no matching changes.
The current PLAN unavailable/Retry branch at `ProjectRoomCore.tsx:1245`
is a good local pattern. Do not flatten the Room into a new configuration
framework.

**Fails:** Tenets 3/5/7; UX-CANON A10/B; Constitution VI.
**Live check needed:** degraded `changes` section, truly empty history,
source filter with no rows, and text query with no matches. Current main
Room composition already has a plan, signals and in-flow Ask; those are
not findings.

### 4. Knowledge reader silently drops unavailable members

**Owner job:** inspect a Knowledge collection and open a member, including
under a partial desk read.

**Opening path:** New → New Knowledge (verb registry
`web/src/desk/verbRegistry.ts:213`) opens its editor; Done opens its reader.
For an existing collection use its `kb:<id>` pullout, then Edit/Done.
The read and write endpoints are `/api/kbs/<id>` and
`/api/kbs/<id>/members` (the editor reads membership itself).

**Current defect:** `web/src/desk/pullouts/KbPullout.tsx:34` resolves the
stored member refs against the aggregate desk items and filters out every
unresolved member at `KbPullout.tsx:36`. If all members are unavailable,
the reader says No entries at `KbPullout.tsx:66`. With only some
unavailable, their rows disappear. Copy also copies only this shortened
list (`KbPullout.tsx:81`). The editor already keeps the refs and renders
Item unavailable, without a false Open, at
`web/src/desk/pullouts/editors/KbEditor.tsx:99` and `KbEditor.tsx:107`.
Read and Edit therefore give different accounts of the same collection.

**Existing species:** reuse the editor's `SurfaceLedgerRow` unavailable
row and `SurfaceState` for the actual membership-read failure. Preserve
member identity and the real Open only when a member resolves. Keep the
current editor's flush-before-Open and footer writer receipts.

**Fails:** Tenets 3/5/7; UX-CANON A10/D; Constitution VI.
**Live check needed:** real stored membership with a missing aggregate
member, plus partial collection-read failure. An absent object may be
legitimately parked; this report does not infer loss of stored membership.

### 5. Plain Conductor session's Open terminal may open below the report

**Owner job:** inspect the live terminal of an unlaunched coding session,
then return to the work view.

**Opening path:** Conductor → a live session without a launch → Open →
Open terminal. `web/src/desk/conductor/open.ts:16` dispatches the member;
`web/src/desk/openObject.ts:159` sends `coder:<agent>:<session>` to the
plain session window. A launched member uses `launch:<id>` and the lane;
it must not be used to prove this candidate.

**Current defect:** `web/src/desk/components/SessionPullout.tsx:802`
always mounts the session head, question and full Latest report. Terminal
is appended at `SessionPullout.tsx:817`. The footer press at
`SessionPullout.tsx:859` only toggles a boolean; there is no scroll/focus
handoff. A long report can keep the newly opened terminal below the
viewport, while the footer already says Back to session. The body scrolls
at `web/src/desk/components/session-pullout.css:387` and preserves each
child's height at `session-pullout.css:395`.

**Existing species:** keep `PaneWell`, `AskWell`, `AgentWords`, the folded
Details, library Buttons and the current footer. Root should settle the
body ownership or visible handoff only if glass proves a scroll hunt.
The launched lane also appends RawPane (`web/src/desk/lane/LaneWindow.tsx:270`);
it is not evidence of an existing complete body-switch pattern.

**Fails if reproduced:** Tenets 3/5/7; UX-CANON D (a view that owns the body
must unmount the rest). **Live check needed:** plain session with a long
latest report; press Open terminal at 393 without manually scrolling,
check the resulting terminal and unavailable/Retry branch, then Back.
The current session arrival already uses AppHead, AgentWords, AskWell and
folded controls. The old terminal-first/configuration-dump complaint is
not repeated here.

## Workbench reproduction and action boundaries

Minimal source-valid route setup, on root's isolated hub only:

1. `POST /api/workbenches` with `{ "name": "Result audit" }`.
2. `POST /api/workbenches/<wb>/items` with a title, optional body and
   priority 3. Read `item.id` from the answer.
3. `PUT /api/workbenches/<wb>/items/<item>` with `status: "done"`, a long
   markdown `result`, optional `result_egress: { "boundary": "local" }`
   and an ISO `completed_at`.

The route producers are
`holdspeak/web/routes/primitives/workbenches.py:59`,
`workbenches.py:115`, and `workbenches.py:133`;
`holdspeak/services/workbench_service.py:234` lists the accepted item
patch fields. `tests/integration/test_desk_workbenches.py:41` uses the
same POST/POST/PUT seed. The route patch does not set an artifact link.
To exercise Open, use an actual completed output or the isolated
repository producers: `Database.plugins.record_artifact` as used at
`test_desk_workbenches.py:54`, plus
`Database.workbench_items.upsert(..., result_artifact_id=<real id>)`
(`holdspeak/db/workbenches.py:205`). The current real run publication
atomically creates output plus artifact at
`holdspeak/kernel/workbench_projection.py:34`; an isolated seed is not
proof that a real run completed.

Action custody to retain: item body debounce/local draft
(`WorkbenchWindow.tsx:684`); Copy (`WorkbenchWindow.tsx:823`); Re-run
(`WorkbenchWindow.tsx:681`); retry mint (`WorkbenchWindow.tsx:733`);
legacy Keep (`WorkbenchWindow.tsx:715`); Dismiss/Park and Parked Restore;
current footer receipt priority (`WorkbenchWindow.tsx:2100`). Keep egress
on the result. Do not touch run authority or inference routing for this
visual repair.

Existing affected test sources, read only, not run:

- `web/src/desk/components/__tests__/workbenchEditing.test.tsx` — body
  draft, failed save and inlet custody.
- `web/src/desk/components/__tests__/writeReceipts.test.tsx` — Re-run,
  retry mint and write failure receipts.
- `web/src/desk/components/__tests__/workbenchPark.test.tsx` — Park,
  Clear done and Restore.
- `web/src/desk/components/__tests__/workbenchFrames.test.tsx` — run bus
  transitions.
- `web/src/desk/components/workbench/WorkbenchRunsWing.test.tsx` — current
  runs presentation.
- `web/src/desk/components/__tests__/sessionWork.surface.test.tsx` — current
  plain session composition.
- `web/src/features/project-room/__tests__/room.app.test.tsx` — current
  Room application behavior.

## Corrections, good patterns and limits

The early hidden-failure-reason hypothesis is withdrawn as a normal-run
finding. The real runner stores its reason in result
(`holdspeak/services/workbench_runner.py:321`); the current wire has no
`error_reason`/`error` (`holdspeak/db/models/__init__.py:1186`). Inventing
either field in a fixture would not prove the current owner path.

A separate producer gap needs classification before any build:
`WorkbenchItemRecord` has `mint_attempted` at `__init__.py:1178`, but its
`to_dict` at `__init__.py:1186` omits it. The UI branches on it at
`WorkbenchWindow.tsx:746`; `writeReceipts.test.tsx:65` supplies it in a
double. The old `_mark_mint_attempted` helper persists it but has no
current caller. Current run publication atomically mints the artifact.
This audit therefore does not claim a present failed-mint run can reach
that recovery state. Do not expand the visual cycle around this without
evidence of the affected stored row.

Current good material to retain: folded Workbench configuration replaces
the item body; Knowledge membership editing uses library gadgets and
keeps unavailable refs; Room PLAN and HEALTH failures name the failed
read and offer Retry; Conductor's present session head/report/question
hierarchy is already substantially refined. None warrants another
framework.

Unknown: live fit, clipping, scroll reach, button target ownership,
contrast and the owner's current rows. Root's live inspection and settled
canvas decide which candidates proceed. This source pass is frozen.
