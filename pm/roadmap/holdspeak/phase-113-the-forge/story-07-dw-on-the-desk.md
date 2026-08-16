# HS-113-07 - DW on the Desk

- **Project:** holdspeak
- **Phase:** 113
- **Status:** done
- **Depends on:** HS-113-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Delivery Workbench projects, phases, and stories must be real objects
on the Desk. An architect managing a DW roadmap should see a Roadmap
object on their desk, open it into a window with Timeline, Stories,
and Health wings, act on stories (start, block, mark done, capture
evidence), and see honest health from `dw check` — all without
leaving the Desk world. The Desk reads DW state from the filesystem;
status transitions go through the DW CLI via the kernel. The roadmap
Markdown files remain the source of truth.

**Articles served:** I (the Desk is the front door — delivery too),
II (capabilities are primitives), V (status transitions are armed
acts with receipts), VII (no prose, labels state what), IX (evidence
is the object, proof over claim), XI (consequential operations
admitted through the kernel).

## Ground (from the pre-charter survey)

- `.githooks/dw` — the DW CLI. Subcommands: `context`, `next`,
  `check`, `doctor`, `story status`, `evidence capture`, `contract
  new`, `gate`, `verify`. Each returns structured output.
- `.mcp.json` — MCP tool wiring for `dw_context`, `dw_next`,
  `dw_check`, `dw_doctor`, `dw_verify`, `dw_gate`,
  `dw_story_status`, `dw_evidence_capture`, `dw_contract_new`.
- `pm/roadmap/holdspeak/README.md` — a real DW project with 112+
  phases.
- `pm/roadmap/holdspeak/phase-112-enough/current-phase-status.md` —
  a real phase charter with story status table, where-we-are
  section, and build record.
- `pm/roadmap/holdspeak/phase-112-enough/story-01-one-dial.md` — a
  real story file with thesis, ground, method, test plan, status,
  depends-on, unblocks.
- `pm/roadmap/PMO-CONTRACT.md` — the commit gate rules.
- `web/src/lib/primitives.ts` — `PrimitiveKind` union type. Adding
  `"roadmap"` and `"story"` extends the Desk grammar.

## Method

1. **New primitive kinds:**
   - Add `"roadmap"` and `"story"` to `PrimitiveKind`.
   - `Roadmap` interface: kind, id, name, projectSlug, phaseCount,
     currentPhase, currentPhaseStatus, nextStoryId, health
     (green/warn/red), issues, lastUpdated.
   - `Story` interface: kind, id, title, phase, projectSlug,
     status (backlog/ready/in-progress/blocked/done), thesis,
     hasEvidence, dependsOn, unblocks.
   - Add `PrimitiveDescriptor` entries with labels, syncClass,
     blurbs, icons.
   - New desk group: `{ label: "Delivery", kinds: ["roadmap", "story"] }`.

2. **Backend routes (`routes/roadmaps.py`):**
   - `GET /api/roadmaps` — scans `pm/roadmap/*/` for DW projects.
     Returns roadmap primitives with phase/story counts and health.
   - `GET /api/roadmaps/{slug}` — full project detail: phases,
     stories, current phase status, dw check output.
   - `GET /api/roadmaps/{slug}/phases/{n}` — phase detail with all
     stories and their metadata.
   - `GET /api/roadmaps/{slug}/stories/{id}` — full story detail:
     thesis, ground, method, test plan, evidence.
   - `POST /api/roadmaps/{slug}/stories/{id}/status` — status
     transition. Calls `dw story status` via subprocess. Returns
     receipt (old status, new status, timestamp). Refuses without
     evidence when transitioning to done (mirrors `dw` gate).
   - `POST /api/roadmaps/{slug}/stories/{id}/evidence` — evidence
     capture. Calls `dw evidence capture` via subprocess. Returns
     receipt (command, exit code, output summary).
   - `GET /api/roadmaps/{slug}/health` — runs `dw check` and
     returns structured issue list.
   - `GET /api/roadmaps/{slug}/next` — runs `dw next` and returns
     the next actionable story.

3. **Frontend data layer (`web/src/desk/roadmap.ts`):**
   - Zustand store for roadmap/phase/story data.
   - Polling or manual refresh from the API routes.
   - Story status transition actions with optimistic updates.

4. **Roadmap window (`RoadmapWindow.tsx`):**
   - Three wings via `SurfaceWings` (from the shared kit):
   - **Timeline wing** (headline posture): `DeskSortableTable`
     with phase rows (number, title, done/total, status lamp).
     Click to expand phase into indented story sub-rows.
     Double-click a story to open its own window.
   - **Stories wing** (working posture): `DeskSearchFilter` by
     status + `DeskSortableTable` filtered to active phase, grouped
     by status column. "What's next?" verb highlights the
     `dw next` result with an accent band.
   - **Health wing** (reviewing posture): `DeskSortableTable` of
     issues from `dw check` (severity lamp, path, issue text).
     Zero issues = one line "0 issues", no congratulatory prose.
   - `DeskWindowFooter` with issue count and "What's next?" verb.

5. **Story window (`StoryCard.tsx`):**
   - Single-face window (no wings — stories are simple).
   - `DeskPropertySheet` for status (cycle gadget for transitions),
     phase, depends-on/unblocks (grounding chips — click to pull
     the referenced story out on the desk).
   - `Material` renderer for thesis + ground markdown.
   - `DeskReceiptInset` for evidence output (command, exit code,
     timestamp, expandable output).
   - `DeskComposer` for evidence capture command input (with mic).
   - Status transitions fire through the kernel: the cycle labels
     the transition, the receipt bar names the result.
   - Evidence "Capture" verb opens the composer with the command
     field focused.

6. **Drop matrix:**
   - `story` accepts `note` and `artifact` → "Attach as evidence"
     (holds content beside the verb per drop law rule 3).

7. **Sprites:**
   - Roadmap: bound ledger book (64x64). `_sel`: brightened with
     accent rim. `_stale`: desaturated (48h since last story flip).
     Badge: health dot top-right (green/amber/red).
   - Story: task card (64x64). Five sprite state sets per status
     (backlog=gray, ready=white, in-progress=amber band,
     blocked=red band, done=green check). Plus `_sel` and `_stale`.

8. **Cross-reference with repo drawers:**
   - Roadmap window story rows show a commit-SHA chip when the
     story shipped (derived from `PMO-Story` trailer grep).
   - Repo drawer commit rows show a story-ID chip when the commit
     has a `PMO-Story` trailer.
   - Both chips are grounding chips: click to pull the referenced
     object out on the desk.

## Test plan

- Unit: `Roadmap` and `Story` primitives register in `PRIMITIVES`
  table, appear in `DESK_GROUPS` under "Delivery".
- Unit: `GET /api/roadmaps` returns holdspeak with correct phase
  count and health.
- Unit: `GET /api/roadmaps/holdspeak/next` returns the next
  actionable story.
- Unit: `POST /api/roadmaps/holdspeak/stories/HS-112-01/status`
  refuses done without evidence.
- Unit: `RoadmapWindow` Timeline wing renders phases with
  done/total counts and status lamps.
- Unit: `RoadmapWindow` Health wing renders `dw check` issues.
- Unit: `StoryCard` renders thesis, status cycle gadget, evidence.
- Unit: story status cycle gadget fires transition and shows receipt.
- Integration: open a roadmap on the desk, navigate to a story,
  view its evidence, see the health wing — all from one window.
- Screenshot walk: 1440px — roadmap window open with Timeline wing
  showing 3+ phases expanded. Story card open beside it showing
  evidence.
- Screenshot walk: 393px — roadmap window and story card responsive.
- Error leg: `dw check` returns errors — Health wing shows them
  with severity lamps.
- Error leg: transition to done without evidence — cycle gadget
  refuses with "No evidence captured."
