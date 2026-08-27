# HS-144-03 — Kanban on glass: implementation plan

**Planning ground truth:** committed `feat/hs144-02-calendar-ingest` at `dff2ac01`, inspected 2026-08-27. This is a glass-only plan. It deliberately does not rely on uncommitted Calendar/DB/settings work, and it does not add a route, schema, store, or board-position persistence.

## 0. Non-negotiable transport finding — resolve before implementation

The Door projection at `holdspeak/services/door_service.py:83-147` can name four
verb families, but only three of those families have browser-reachable equivalents
at committed HEAD:

| Aggregate lawful verb | Exact browser route | Result |
| --- | --- | --- |
| `follow_through.complete` (`done`, `dismiss`, `snooze`, `delegate`) | `POST /api/follow-through/complete`, body `{card_id, verb, payload}` — `holdspeak/web/routes/follow_through.py:47-57` | Reachable. `snooze` needs `payload.until`; `delegate` needs `payload.to`, so their in-world controls cannot send an incomplete descriptor. |
| `cadence.set_status` (`closed`, `killed`) | `POST /api/cadence/loops/{loop_id}/close` and `POST /api/cadence/loops/{loop_id}/kill` — `holdspeak/web/routes/cadence.py:73-83` | Reachable through a fixed, typed mapping; never by constructing a URL from a descriptor string. |
| `thought.complete` | `POST /api/thoughts/{thought_id}/complete` — `holdspeak/web/routes/primitives/thoughts.py:323-337`; existing client construction is `web/src/desk/thoughts.ts:310-320` | Reachable. Supply a fresh `request_id`; the Door card already carries both expected revisions. |
| `people.commitment.transition` (`done`, `dismiss`) | **None.** The only commitment write on the browser router is `POST /api/people/commitments/{id}/satisfy`, `holdspeak/web/routes/people.py:252-286`, which calls a different `satisfy` operation with rationale/evidence. The MCP-only transition dispatch is `holdspeak/mcp/families/people.py:252-256`. | **Blocker / finding.** A Door people card has lawful verbs but the glass cannot truthfully execute either named verb. Do not substitute `/satisfy`, hide a server-named action, or invent a browser route in HS-144-03. Return this to HS-144-01 for a reciprocal HTTP adapter or for an amended Door descriptor. |

Two further aggregate/charter mismatches must be recorded rather than papered over:

- `/api/follow-through/commit-decision` exists (`follow_through.py:59-69`), but **no current Door `lawful_verbs` descriptor names it**. The Door board must not add a Commit decision button on its own authority.
- `POST /api/thoughts/{id}/resume` exists (`thoughts.py:339+` and client `web/src/desk/thoughts.ts:322+`), but Door active cards currently name **only** `thought.complete` (`door_service.py:137-147`). The board may offer `open_ref` as navigation to the working note; it must not call resume as a card verb until the aggregate names it.

**Implementation stop condition:** start the live-card verb slice only after the People discrepancy has an explicit parent-story disposition. If HS-144-01 adds the HTTP adapter, this story consumes it; if it removes/unexposes the descriptor, the card follows the returned descriptor exactly. Either outcome preserves the story boundary: no backend change ships in HS-144-03.

## 1. Obligation register

| Story acceptance obligation | Implementation slice(s) | Concrete proof |
| --- | --- | --- |
| Five Door columns and honest headline counts from `GET /api/door` | 1, 2 | `DoorBoardLane.test.tsx` fixtures assert all five projected columns, server counts, source/owner/due/age presentation, and no derived count; Door glass asserts a populated real hub. |
| Brief and Follow-Through Chair slots are replaced, never duplicated | 1, 3 | Registry/ChairHome test asserts `door`, `meetings`, `agents` only; source grep in the evidence shows `BriefLane` and `FollowThroughLane` are absent from `LANE_ORDER`/`LANE_COMPONENTS` and ChairHome. |
| Every rendered action is a named, real verb and refusal is in-flow | 2 | Dispatch-matrix unit tests inspect method/body per descriptor and local `useWriteReceipt` receipt/retry behavior; glass test forces a refusal and observes the in-board receipt without an overlay. The People route finding is a prerequisite. |
| First Sentence remains byte-identical on a fresh HOME | 3 | Existing `DeskApp.test.tsx`, `ChairHome.test.tsx`, `FirstWords.test.tsx`, and four named fresh-HOME glass files remain in the shared net. No HS-144-03 edit enters `DeskApp.tsx`. |
| Brief access and pre-existing Meetings access remain reachable | 1, 3 | The board’s compact `Brief` action calls `openIntelligence({ view: "brief" })`; the `meetings` registry slot survives unchanged until HS-144-04. Unit and real-hub click paths prove both. |
| 1440, 393, 200%; populated, empty, error; no console/page overflow | 4, 5 | New parametrised real-hub `test_hs144_door_glass.py`, saved shots, and a manual beauty review after functional green. |
| Neighbor tests accompanying shared Chair files | 3, 4 | The complete named net in §4 runs in the story capture, not merely the newly added tests. |

## 2. Verified glass inventory and resulting boundaries

### 2.1 Chair composition and registry

| Verified location | What it does now | HS-144-03 disposition |
| --- | --- | --- |
| `web/src/desk/chair/ChairHome.tsx:26-35` | Builds the lane node map by mapping `LANE_ORDER` to `LANE_COMPONENTS`. | Preserve generic construction. Register the Door board as the new first lane rather than bypassing the composition contract. |
| `ChairHome.tsx:38-63` | Holds the arrival fork; normal Chair currently receives `hero={<ThoughtEntry />}`, `activeWork={<FinishThoughtsLane />}`, and the four lanes. | Leave the arrival branch and hero expression byte-for-byte untouched. Pass `activeWork={null}` under the dedup ruling; Door active cards become the sole normal-Chair active-thought rendering. |
| `web/src/desk/chair/Chair.tsx:19-60` | Renders the hero, active-work slot, empty invitation, then each registered lane. | No new surface/window. Retain the active-work slot in the reusable Chair contract, but do not populate it from ChairHome for the Door composition. |
| `web/src/desk/chair/laneContract.ts:8-33` | Defines `LaneProps`, then the static four IDs/order: brief → follow-through → meetings → agents. | Replace the Chair-only order with `door → meetings → agents`; update its old counsel-order comment so it does not state a false invariant. |
| `web/src/desk/chair/lanes/index.ts:5-17` | Imports and registers all four old lanes. | Remove `BriefLane` and `FollowThroughLane` **from this Chair registry only**, add `DoorBoardLane`, retain Meetings and Agents. |
| `web/src/desk/chair/chair.css:77-104` | The lane region is one column below 1200px and two columns at/above it; every lane wrapper has `min-width: 0`. | Make `[data-lane="door"]` span both wide tracks. The board itself owns any five-column horizontal overflow; the document and Chair must never widen. |

### 2.2 What is replaced, what is re-homed, and what stays

| Existing component | Verified behavior | HS-144-03 outcome |
| --- | --- | --- |
| `web/src/desk/chair/lanes/BriefLane.tsx:56-229` | Independently fetches `/api/brief/latest` on mount (`:66-82`), renders Chair BRIEF rows, and its header opens `openIntelligence({ view: "brief" })` (`:144-145`). | It is unseated from Chair; it does not sit next to the Door board. Do **not** delete it in this story. The surviving owner capability is re-homed as the board header’s explicit Brief entry into the existing Intelligence Brief pullout. `BriefView` remains the full Brief owner. |
| `web/src/desk/chair/lanes/FollowThroughLane.tsx:75-205` | Independently fetches the old four-lane board (`:85-101`) and directly posts only `done`/`dismiss` (`:103-118`); its header opens the Intelligence Follow-Through wing (`:140-142`). | It is unseated from Chair. Its capability survives as the pre-existing Intelligence Follow-Through view, while DoorBoardLane is the only Chair obligation rendering. It must not be cosmetically retained under the new board. |
| `web/src/desk/chair/FinishThoughtsLane.tsx:45-162` | Fetches unfinished thoughts (`:75-93`) when global `updatedAt` changes and renders them through Chair’s separate active-work slot. | Door `active` is the canonical Chair rendering after the [ORCH-CALL] in §6. Park this module; unmount it from ChairHome rather than deleting it. The two sources must not render the same thought twice. |
| `web/src/desk/chair/lanes/MeetingsLane.tsx:117-174` | Reads store meeting/recording/schedules (`:121-129`), retains scheduled-recording rows, and opens the existing meetings surface. | Keep it registered and visually below the Door board as the explicit interim until HS-144-04 owns the upcoming rail. HS-144-03 does not consume `door.upcoming`. |
| `web/src/desk/chair/lanes/AgentsLane.tsx` | The fourth existing lane. | Keep unchanged, following Meetings in the shortened Chair lane order. |

### 2.3 Existing freshness patterns — no invented store

- `BriefLane` and `FollowThroughLane` are component-local, mount-fetch-only data readers; neither polls or subscribes (`BriefLane.tsx:60-82`, `FollowThroughLane.tsx:80-101`).
- Meetings is a Zustand-store consumer; schedules load at mount through `loadSchedules` (`MeetingsLane.tsx:121-129`). The general store’s `refresh()` loads the Desk snapshot and increments `updatedAt`, but has no Door fetch (`web/src/desk/store/dataSlice.ts:159-176`).
- FinishThoughts is the only Chair child listening to `updatedAt` (`FinishThoughtsLane.tsx:46,75-93`).
- `RuntimeBus` permits typed subscriptions (`web/src/runtime/RuntimeBus.tsx:26-39,59-72`), but the committed WS router’s initial message is only `duration` (`holdspeak/web/routes/system/ws.py:75-86`) and there is no Door invalidation frame/broadcast. Existing Chair WS use is recording-specific (`hero/CaptureHero.tsx:78-97`).

**Result:** DoorBoardLane owns a small local `reload()` for `GET /api/door`, reloads after a landed local verb, and revalidates on normal-Chair remount/`updatedAt` change. Do not add a Door Zustand slice or pretend the existing WS publishes a Door update. The cadence choice is recorded in §6.

### 2.4 In-flow receipt and material grammar

- The house failure channel is `web/src/desk/hooks/useWriteReceipt.ts:1-9,116-175`: success clears quietly; a refusal gets a named, retryable in-flow strip. `useDeskWriteReceipt({fallback:true})` in `DeskChrome.tsx:136-139` is deliberately the distant system-bar backstop, not the desired placement for a card verb.
- DoorBoardLane uses **local** `useWriteReceipt()` and renders `receipt` immediately below the board summary/action seat. It never overlays cards, toast-floats, or silently swallows an error. Loading/initial error/empty use the in-flow `SurfaceState` treatment (`web/src/desk/surface/Surface.tsx:141-225`).
- Use `Button` only for verbs (`web/src/components/signal/Signal.tsx:21-45`); use `StringGadget` for any required delegate value, which carries the click-to-toggle speak-to-fill mic by default (`web/src/desk/surface/gadgets.tsx:217-280`). No modal, dialog, or free-form browser prompt.
- Material comes from `web/src/styles/tokens.css:84-211,267-319`: opaque `--surface-*` fills, `--border`/`--border-strong`, raised bevel (`--desk-window-bevel`), sunken etch (`--desk-window-etch`), 2px radii, mono labels, and the existing Workbench density tokens. Do not use translucent glass, pill radii, gradients, or a second page-grid language.
- Follow the Phase 143 rooms rather than inventing a dashboard dialect: Model Library’s server-projection `reload` + `SurfaceState` + `SurfaceVerbs` + in-world face pattern is at `web/src/pages/cores/ModelLibraryCore.tsx:83-124,408-454`; Capability Assignments’ server-summary rows, local receipt, and in-world editor is at `CapabilityAssignmentsCore.tsx:33-105`. Door differs only in being a Chair lane, so it takes the same honest state/receipt discipline in the Chair material.

## 3. Target implementation shape

### New Door lane contract

Create `web/src/desk/chair/lanes/DoorBoardLane.tsx` and its focused test. It owns:

1. Explicit TypeScript wire types for the exact `GET /api/door` JSON: `board.now`, `waiting`, `unassigned`, `overdue`, `active`; `counts.overdue`, `now`, `waiting`, `active`, `upcoming_today`; and the documented fields `source`, `target_ref`, `lawful_verbs`, owner/due/card-specific thought continuity data.
2. A fixed visual column order **Overdue, Now, Waiting, Unassigned, Active**. Values are server projections; no client classification, sorting into a different semantic lane, count calculation, or position persistence.
3. A terse headline strip sourced only from `counts` (for example `3 overdue · 2 waiting`), with no fake zero theatre. `upcoming_today` is held for HS-144-04’s rail, not rendered by this story.
4. Card provenance/ownership/due-age display where the aggregate actually supplies it. Active thought cards show source/continuity/updated truth and never fabricate owner, due, or priority.
5. An explicit, compact `Brief` entry that calls `openIntelligence({ view: "brief" })`, plus normal access to the existing Intelligence surface. It preserves the one-click Brief capability without restoring the old Brief lane.
6. A typed descriptor dispatcher, not `fetch(descriptor.name)`: whitelist the three proven mappings in §0 and copy only descriptor arguments plus owner-entered required payload. A no-verb card has no action seat. A descriptor with required arguments first expands its **own card** in-world; it does not open a modal.
7. Local in-flow `useWriteReceipt` around every actual write; one busy card at a time, reload after success, and retry exactly the same command through the receipt.

The descriptor dispatcher must have exhaustive, tested behavior for unknown or unimplemented names: no button is rendered and the implementation records the contract mismatch for the parent story; it never guesses an HTTP route. The People case is not silently treated as a normal no-verb card because the aggregate explicitly says the verbs are lawful.

### File map

| Change | Exact file(s) |
| --- | --- |
| New board/read/client/typed dispatcher | `web/src/desk/chair/lanes/DoorBoardLane.tsx` |
| Board unit tests | `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` |
| Reforge composition and unmount duplicate active thought lane | `web/src/desk/chair/ChairHome.tsx` |
| Replace Chair lane IDs/order | `web/src/desk/chair/laneContract.ts` |
| Replace the old Chair registry entries | `web/src/desk/chair/lanes/index.ts` |
| Full-width board and contained mobile scroller, using existing tokens | `web/src/desk/chair/chair.css` |
| Update composition assertions | `web/src/desk/chair/ChairHome.test.tsx`, `web/src/desk/chair/Chair.test.tsx` |
| New real-hub glass/shot proof | `tests/e2e/test_hs144_door_glass.py` |
| Saved review shots (test output, not a product bundle) | `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-03-shots/` |

Files intentionally **not** changed by this story: `web/src/desk/DeskApp.tsx` (First Sentence gate), `holdspeak/services/door_service.py`, every web route, settings/DB code, Calendar code, and `web/dist` (gitignored).

## 4. Shared-file net — mandatory for any ChairHome round

### Existing real-hub e2e files (4)

These are all current e2es that exercise the normal Chair/fresh arrival path; all run even though HS-144-03 does not edit their source files:

1. `tests/e2e/test_hs141_chair_geometry.py` — Chair geometry, hero, active-work appearance, 1440/393/short phone, and page overflow.
2. `tests/e2e/test_hs14104_refinement_glass.py` — fresh FirstWords exit path (currently marked skipped as superseded; retain it in the named net so its status remains explicit).
3. `tests/e2e/test_hs14105_context_glass.py` — fresh FirstWords exit before Thought context work.
4. `tests/e2e/test_hs14105a_default_context_glass.py` — fresh FirstWords exit before default-context work.

Add `tests/e2e/test_hs144_door_glass.py` as the fifth e2e proof. It is the first real-hub test that directly verifies the Door board, Brief entry, retained interim Meetings lane, descriptor action/reload/refusal, and the 1440/393/200% shots.

### Existing Vitest files (14), plus the new board test

Run this entire group when `ChairHome`, `laneContract`, `lanes/index`, or Chair CSS changes:

1. `web/src/desk/chair/Chair.test.tsx`
2. `web/src/desk/chair/ChairHome.test.tsx`
3. `web/src/desk/chair/FinishThoughtsLane.test.tsx`
4. `web/src/desk/chair/ThoughtEntry.test.tsx`
5. `web/src/desk/chair/hero/CaptureHero.test.tsx`
6. `web/src/desk/chair/lanes/AgentsLane.test.tsx`
7. `web/src/desk/chair/lanes/BriefLane.test.tsx`
8. `web/src/desk/chair/lanes/FollowThroughLane.test.tsx`
9. `web/src/desk/chair/lanes/MeetingsLane.test.tsx`
10. `web/src/desk/DeskApp.test.tsx`
11. `web/src/desk/components/FirstWords.test.tsx`
12. `web/src/desk/pullouts/IntelligencePullout.test.tsx`
13. `web/src/desk/pullouts/IntelligenceTruth.test.tsx`
14. `web/src/desk/pullouts/IntelligenceWalk.test.tsx`
15. **new:** `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`

This is a **20-file net** when counting the five e2es. The existing Brief/FollowThrough tests remain part of the net even after those components are unseated: they protect the re-homed Intelligence-backed capabilities and prove removal was from Chair composition, not a silent loss of behavior.

## 5. Delivery slices

### Slice 1 — Reforge the Chair composition and render the read model

**Files**

- Create `web/src/desk/chair/lanes/DoorBoardLane.tsx`.
- Modify `web/src/desk/chair/laneContract.ts`, `web/src/desk/chair/lanes/index.ts`, `web/src/desk/chair/ChairHome.tsx`, and `web/src/desk/chair/chair.css`.
- Create `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`; update `ChairHome.test.tsx` and `Chair.test.tsx`.

**Work**

- Replace `brief`/`follow-through` Chair registrations with a full-width `door` lane, retain `meetings` and `agents`, and pass no duplicate active-work node from ChairHome.
- Fetch the Door aggregate once on mount; render the exact five server columns and aggregate headline counts.
- Add the explicit Brief pullout entry; do not render `upcoming` or change Meetings.
- Prove source/owner/due/age only where fields exist, and source/continuity/updated truth for active thoughts.

**Focused proof**

- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` — read shape, five order-stable columns, count-source integrity, card facts, loading/empty/initial error/retry, Brief entry, no next-rail rendering.
- `web/src/desk/chair/ChairHome.test.tsx` and `Chair.test.tsx` — `door` exists; `brief`/`follow-through` do not; `activeWork` is empty in the normal Door Chair; hero and arrival behavior remain unchanged.

```bash
(cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run \
  src/desk/chair/lanes/DoorBoardLane.test.tsx \
  src/desk/chair/ChairHome.test.tsx \
  src/desk/chair/Chair.test.tsx)
```

### Slice 2 — Lawful descriptor actions and the nearest receipt

**Files**

- Modify `web/src/desk/chair/lanes/DoorBoardLane.tsx` and `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` only.

**Work**

- Implement the fixed adapter table for follow-through, cadence close/kill, and thought complete; generate the thought request ID locally and use aggregate revisions verbatim.
- Put snooze date and delegate-to `StringGadget` inside the expanded card action seat. Do not send an action until its descriptor’s required argument is satisfied; retain the gadget mic.
- Wrap the actual requests in local `useWriteReceipt`; ensure response success reloads and failure remains adjacent to the board with exact retry.
- Keep the People card mismatch behind the §0 stop condition. No substitute route, no dynamically constructed endpoint, and no global overlay.

**Focused proof**

- `DoorBoardLane.test.tsx` — exact endpoint/body for every reachable descriptor, no request for incomplete payload, fresh thought `request_id`, busy-card isolation, post-success reload, failure label/retry, and an explicit failing expectation/contract guard for an unadapted People descriptor.
- Existing `FollowThroughLane.test.tsx`, `IntelligenceTruth.test.tsx`, and `FinishThoughtsLane.test.tsx` — preserve their independently established verb/error and thought continuity behavior.

```bash
(cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run \
  src/desk/chair/lanes/DoorBoardLane.test.tsx \
  src/desk/chair/lanes/FollowThroughLane.test.tsx \
  src/desk/chair/FinishThoughtsLane.test.tsx \
  src/desk/pullouts/IntelligenceTruth.test.tsx)
```

### Slice 3 — Reachability and shared Chair/First Sentence regression pass

**Files**

- Modify only the Slice 1 files/tests if a regression demands it; do not edit `DeskApp.tsx`, `FirstWords.tsx`, `MeetingsLane.tsx`, `BriefLane.tsx`, or `FollowThroughLane.tsx` merely to make the new board fit.
- Add reachability assertions to `DoorBoardLane.test.tsx` and update `ChairHome.test.tsx` only where registry expectations changed.

**Work**

- Assert Brief opens the existing Intelligence Brief view and that the existing Meetings lane remains visible/reachable beneath the board.
- Assert old Chair lane IDs are gone from composition and duplicate thought titles cannot appear in both active-work and the Door active column.
- Preserve the First Sentence gate untouched; this slice is its shared-file proof, not an opportunity to refactor it.

**Focused proof**

```bash
(cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run \
  src/desk/chair/Chair.test.tsx \
  src/desk/chair/ChairHome.test.tsx \
  src/desk/chair/FinishThoughtsLane.test.tsx \
  src/desk/chair/ThoughtEntry.test.tsx \
  src/desk/chair/hero/CaptureHero.test.tsx \
  src/desk/chair/lanes/AgentsLane.test.tsx \
  src/desk/chair/lanes/BriefLane.test.tsx \
  src/desk/chair/lanes/FollowThroughLane.test.tsx \
  src/desk/chair/lanes/MeetingsLane.test.tsx \
  src/desk/DeskApp.test.tsx \
  src/desk/components/FirstWords.test.tsx \
  src/desk/pullouts/IntelligencePullout.test.tsx \
  src/desk/pullouts/IntelligenceTruth.test.tsx \
  src/desk/pullouts/IntelligenceWalk.test.tsx \
  src/desk/chair/lanes/DoorBoardLane.test.tsx)
```

### Slice 4 — Real hub, states, dimensions, and receipt path

**Files**

- Create `tests/e2e/test_hs144_door_glass.py`.
- Test writes shots into `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-03-shots/`.

**Work**

- Start `MeetingWebServer` through the production composition against an isolated HOME/DB.
- Populate actual projected follow-through/cadence/thought records through production services or already-reachable routes; never mock the browser fetch client. Produce empty from a clean projection and error by controlled Door service refusal at the server seam.
- At 1440 and 393: prove all five columns/counts, contained board scroller at 393, source facts, one real reachable verb round trip/reload/receipt refusal, Brief-to-Intelligence entry, retained Meetings lane, no console errors, and no body/document horizontal overflow.
- At 200%: use the Phase 143 convention (720×450 CSS viewport, `device_scale_factor=2` for the 1440×900 review artifact), reduced motion, keyboard-visible actions, and no page overflow.

**Focused proof**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME_REAL="$HOME"; HOME="$(mktemp -d)"; PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q tests/e2e/test_hs144_door_glass.py
```

Then run the required existing Chair/First Sentence neighbor e2es from the repo root, still with an isolated HOME and the warm browser cache:

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME_REAL="$HOME"; HOME="$(mktemp -d)"; PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q \
  tests/e2e/test_hs141_chair_geometry.py \
  tests/e2e/test_hs14104_refinement_glass.py \
  tests/e2e/test_hs14105_context_glass.py \
  tests/e2e/test_hs14105a_default_context_glass.py
```

### Slice 5 — Beauty pass and owner-facing shot review

**Files**

- Modify `web/src/desk/chair/chair.css` only for evidence-backed material/layout refinements.
- Refresh `tests/e2e/test_hs144_door_glass.py` assertions if the visual contract changes.
- Refresh named shot files under `assets/story-03-shots/`; do not commit a generated web bundle.

**Work**

- Perform only after Slices 1–4 are functional and the complete shared net is green.
- Review populated, empty, and error at 1440 and 393; include the 200% populated leg. Check typography hierarchy, column headers/counts, touch targets, no clipped card action/receipt, scroll containment, opaque/beveled material, and no duplicated active thought.
- Owner sees the shot set before any merge claim. Re-run the focused board and e2e commands after any CSS change.

## 6. Required [ORCH-CALL] dispositions

| [ORCH-CALL] | Recommendation | Why / implementation consequence |
| --- | --- | --- |
| **FinishThoughtsLane vs Door `active`** | **Rule: the Door active column supersedes ChairHome’s activeWork render.** Keep `FinishThoughtsLane.tsx` parked, but pass `activeWork={null}` from ChairHome. | The same unfinished thought must appear once on the front door. Door’s active projection already supplies state, continuity, and `open_ref`; duplicate rendering would violate replace-never-sit-beside and make the count dishonest. |
| **Interim Meetings placement** | **Keep the existing `meetings` lane directly below the full-width Door board through HS-144-03.** | Story 04 owns `upcoming`; moving/removing Meetings now would orphan live/recent meeting and scheduled-recording access mid-phase. Door `upcoming` remains unread in Story 03. |
| **Brief reachability shape** | **One compact Door-header `Brief` action opens the existing Intelligence pullout with `{view:"brief"}`.** | It preserves the current one-click direct path without restoring Brief real estate or adding a surface/window. The command must remain visible at both widths. |
| **Drag-and-drop vs click verbs** | **No drag/drop in HS-144-03; use explicit click/tap verbs only.** | There is no board-position store, and a drag target cannot be translated universally into a lawful status transition. A card only presents an action that its descriptor names. |
| **Five columns at 393** | **One horizontally scrollable board viewport inside the Door lane; fixed/min-width columns; page itself never scrolls horizontally.** | Stacking or tabs hides the simultaneous truth the kanban exists to show. The scroller carries accessible label/focus and touch scrolling; 393 shots prove its own overflow is contained. |
| **Polling vs WS freshness** | **No new WS dependency and no ambient timer in this story. Fetch on mount, after successful local verb, and when `updatedAt` changes; revalidate on remount.** | The committed runtime bus has no Door invalidation frame. A fake subscription would go stale silently, while blind polling adds churn without an event contract. A future owner need can add one named invalidation frame or deliberate visible-only polling. |

## 7. Evidence checklist for the story capture

- [ ] Record the §0 People-route disposition before claiming all descriptor actions are covered.
- [ ] Capture the focused Vitest output for the 15-file web net after reading it, not just the new board test.
- [ ] Capture the new Door glass and the four existing e2es using the isolated-HOME commands above; explicitly record the expected skip for the retired HS-14104 test if it remains skipped.
- [ ] Save six state/width shots minimum (populated/empty/error at 1440 and 393) plus the populated 200% shot; keep zero-console-error and zero-document-overflow assertions in the test.
- [ ] Include a source grep/evidence line proving `BriefLane` and `FollowThroughLane` are absent from the Chair registry/order while `BriefView`, `FollowThroughView`, Meetings, and the explicit Brief Door entry remain reachable.
- [ ] Perform and record the beauty review after functional proof, before any merge word.

## Orchestrator dispositions (ruled 2026-08-27)

All recommendations ACCEPTED as written: the full-width `door` lane
replacing the Brief + Follow-Through lane registrations; Brief
surviving as the Door-header entry into the existing Intelligence
Brief pullout; MeetingsLane unchanged below the board until HS-144-04;
the Door `active` column superseding FinishThoughtsLane (thoughts
render once — the superseded lane's test net stays in the round per
the shared-file law); the contained horizontal board scroller at 393
(page overflow stays forbidden); no drag-and-drop (settled design §2 —
every action is an explicit lawful verb); freshness by
mount/post-write/updatedAt revalidation, no fake WS and no ambient
polling.

**The transport finding is ruled as a VISIBLE scope amendment, not a
workaround:** `people.commitment.transition` ships only as an MCP tool
— the aggregate advertises a verb the browser cannot call. HS-144-03
gains **slice 0**: one thin browser HTTP route (POST, people
commitments transition) calling the EXACT application service the MCP
tool calls, with a parity-style proof against the MCP twin, and the
glass maps the descriptor to it. The story's "no backend changes"
out-scope clause is amended for this one route, recorded in the story
file and the phase decision log; the owner may overrule at the
sitting. `commit-decision` and thought `resume` stay un-invented on
the board — descriptors are the whole vocabulary.
