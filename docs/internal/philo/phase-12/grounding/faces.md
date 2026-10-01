# PHILO Phase 12 grounding: the faces half

**Date:** 2026-09-30. **Base:** main `22c0acc4` (Phase 11 stories 01–05 merged). **Lane:** the Fedaykin docs lane (Opus 5.5) for Muad'Dib.
**Other half:** Astra's lane grounds the backend in `backend.md`: the artifact source kind, the brief as a Floor object, the destinations data, the drag-to-send wire.
**Isolation:** the shots came from a real hub on a throwaway HOME (`mktemp -d`, removed after the run), booted by `tests/e2e/glass_infra.py` `_boot`. The seed: one project, one desk decision, one note, one knowledge, one folder destination (through the real routes), one meeting with a summary and one meeting artifact (through the DB layer in that HOME). The fresh HOME also carries the product's own presets (6 zones, 4 notes, 1 knowledge, 6 personas). No real HOME, no owner DB. Nothing was sent.

**The owner's pick (2026-09-30).** Surface: "The web Desk's Floor". Sendable from an icon: "What's sendable today" (decisions, the meeting summary, digest and follow-up, project updates, plus a brief icon) and "Artifacts".

**Muad'Dib's proposal, grounded here (not assumed):** (1) destinations become icons on the Floor; (2) drag a document icon onto a destination icon: the exact preview opens in place and he presses Send (never auto-send); (3) right-click a document icon: `Send to ▸` with his saved destinations; (4) artifacts become sendable.

## Shots (`shots/`, today's product, before any Phase 12 change)

| File | What it shows |
|---|---|
| `00-chair-dock-1440.png`, `00-chair-dock-393.png` | The Chair (the black "wall"). The meeting row already carries SEND with the Summary form and the folder destination (Phase 11). The Dock: Intelligence, Speak, Meetings, Agents, Settings, Floor, Desk memory, Delivery, Panes. No brief item on the Dock. |
| `01-floor-1440.png` | The Floor: 6 zone drawers, 17 objects. The decision "Freeze the old ledger on Nov 5" wears a **note** sprite. No destination is on the Floor. |
| `01-floor-393.png` | The spatial Floor at 393 (reached through the palette, `Spatial view`). Labels and cells overlap: `Weekly update` under the `Reference` drawer, `Ledger cutover sync` under `Egress guard`, `Payments ledger cutover` under `Interview`. |
| `01a-floor-list-393.png` | What the phone opens by default: the **list**, not the spatial Floor (23 items > 16). |
| `02-decision-menu-1440.png`, `02-decision-menu-393.png`, `02a-decision-row-menu-list-393.png` | The object menu on the decision: Open, Get Info, `Ask this project · Select a Project`, `Ask AI · Ask unavailable`, Continue in thread, `Edit · Not editable`, `Rename · Not renameable`, Duplicate, Move to Zone, Delete. Four of ten rows are ghosts. No Send. At 393 the panel is full width (spatial and list are the same menu). |
| `03-drag-hover-tag-1440.png` | The drop tag today: the note held over the knowledge, the tag `Add to Knowledge` at the cursor, the target lit with its `_sel` image. |

No drag shot at 393: on the crowded 393 Floor my rig picked up a persona (`Chase`), not the note; I removed that shot. The drag code is the same at both widths (`engine.ts:853-883`).

## 1. The map

### 1a. What sits on the Floor

- The Floor draws primitives only, in the `ORDER` list (`web/src/desk/world.ts:33-48`); `directory`, `game`, `layout`, `intelligence`, `people` have their own path (`WORLD_ONLY_EXCLUDE`, `world.ts:19-25`); `roadmap` is withheld (`world.ts:99-103`). The list is a compile-time gate over `PrimitiveKind` (`world.ts:50-56`).
- Zones are the precedent for a **non-object layer**: built apart from objects (`web/src/desk/gl/sceneModel.ts:210-252`), drawn as a drawer cell, hit-tested **before** objects (`sceneModel.ts:285-327`), with their own menu target (`engine.ts:133-136`) and their own drop (file into the zone, `engine.ts:1129-1132`).
- Sendable kinds as icons today:

| Document (owner's pick) | On the Floor today? | Its window | SEND well in that window today |
|---|---|---|---|
| Desk decision (`desk_decision`) | yes, kind `decision` | `DecisionPullout` | yes, when not editing (`web/src/desk/pullouts/DecisionPullout.tsx:150`) |
| Meeting summary / digest / follow-up | yes, kind `meeting` | `MeetingPullout` | yes, only with a summary; one well with a form picker (`MeetingPullout.tsx:152-155`; `web/src/meetings/MeetingSendWell.tsx:31-54`) |
| Project update (`project_update`) | the **project** is; the update is not | the Room (a surface, `web/src/desk/store/compositorSlice.ts:158-168`), Update posture (`web/src/features/project-room/ProjectRoomCore.tsx:2167-2174`) | yes, in the Update posture only |
| Monday brief (`monday_brief`) | **no** (not a primitive) | Intelligence → BRIEF; the Chair's BRIEF | yes (`web/src/desk/pullouts/views/BriefView.tsx:463`; `ChairHome.tsx:1398`, `:1436`) |
| Meeting decision / decision record | **no** | Intelligence → DECISIONS; Room rows | yes (`DecisionsView.tsx:260`; `ProjectRoomCore.tsx:1445`) |
| Artifact | yes, kind `artifact` | `ArtifactPullout` | **no**; not a source kind (`holdspeak/services/document_sources.py:435-444` lists eight kinds, no artifact) |

### 1b. The menus

- One verb registry; object verbs `web/src/desk/verbRegistry.ts:399-591` (ten, no Send). A `Verb` is flat: no submenu field (`verbRegistry.ts:51-75`).
- The **menu species does nest**: `WorkMenuEntry` has `type: "sub"` (`web/src/desk/components/DeskMenu.tsx:182-201`), rendered with hover intent and ArrowRight (`:322-360`). At ≤720 px the submenu **replaces** the panel with a back row (`DeskMenu.tsx:592`); the panel is full width (`clampStyle`, `:209-225`). The Floor menu already uses it (`New`, `Launch`: `web/src/desk/floorMenu.ts:38-52`).
- `objectMenuEntries` builds the same list for every kind (`floorMenu.ts:59-71`). Three faces call it: the spatial Floor (`web/src/desk/gl/WorldStage.tsx:303-313`), the list (`web/src/desk/components/DeskListView.tsx:405`), and the menu bar's Object menu reads the same verbs (`web/src/desk/components/DeskMenuBar.tsx:80`, a `WorkMenu` at `:139-145`). So `Send to ▸` built as a `sub` entry in `objectMenuEntries` reaches all three.
- The capability gate exists per kind: `primitiveCan(kind, cap)` (`web/src/lib/primitives.ts:704-711`). Today a decision has only `duplicate`, `delete` (`primitives.ts:491`); a meeting and an artifact only `ask` (`:457`, `:469`). A `send` capability is the natural gate.
- Right-click on a touch screen: a 500 ms still press (< 8 px) opens the same menu (`engine.ts:790-830`).

### 1c. The drop

- The drop matrix is **kind × kind** (`web/src/desk/dropMatrix.ts:17-48`): `recipe`/`chain`/`workflow` accept groundables (`Hold as source`), `kb` accepts filables (`Add to Knowledge`). The engine looks it up on every move (`engine.ts:533-566`); the tag is DOM at the cursor (`WorldStage.tsx:278-290`). The tag must state exactly what release does (`dropMatrix.ts:13-14`).
- `ground-into` is the exact precedent for "drop opens a window, he presses": release selects the dropped object and opens the **target's** window at the drop point, the run verb beside it (`engine.ts:1110-1118`). A send drop is the mirror: open the **dragged document's** window with the destination picked.
- Glass drop: an object dropped on a DOM element marked `data-glass-accept~='desk-object'` gets a `desk:glass-drop` event and goes home (`engine.ts:1087-1101`; one acceptor today, `GroundingSection.tsx:150`). No hover tag on that path.
- Touch drag works on objects: a touch press on an object becomes a drag after 4 px (`engine.ts:853-883`, `:917-930`).

### 1d. Where the preview opens

- The SEND well species (`web/src/desk/surface/send/SendWell.tsx`; contract `web/src/desk/surface/contract.md:400-460`): the pick opens the preview and Send in place, under the row (Phase 10 ruling A1). The pick lives in a module store `picked: Map<ref, destinationId>` (`SendWell.tsx:63-64`, set only at `:572`). It is private: a drop cannot pre-pick today. One exported setter is the whole seam.
- The meeting form pick is private too (`MeetingSendWell.tsx:28`, `formPick`).
- No modal anywhere on this path: the document's own window opens at the drop point (`openPullout(id, origin)`, `compositorSlice.ts:137-152`).

### 1e. Icons

- Sprites are 64 × 64 pixel art, one cell for every kind (`sceneModel.ts:36-55`). The law: a distinct silhouette per kind, and every sprite ships as rest, `_sel`, `_stale` (`web/ICON-DISCIPLINE.md`, "The cell", "States are images"; states derived by `scripts/gen-sprite-states.py`). The `_sel` image is what lights a drop target (`engine.ts:554-560`).
- No channel art exists: the families on disk are cassette, note, tome, drawer, paper, cartridge, automaton, people-ledger (`web/public/desk/sprites/`). The pools: `web/src/desk/sprites.ts:23-49`.
- Badges on a cell are counts and marks only, never prose (`engine.ts:704-706`).

### 1f. The Dock and the brief

- The Dock is DOM, not the GL world (`web/src/desk/components/window/Dock.tsx`). It cannot be a drag source or a drop target for Floor icons today.
- The brief's only Dock sign: Intelligence wears `•` when the brief has untriaged items (`Dock.tsx:66-70`; `intelligenceAttention.ts:47`). `openIntelligence({ view: "brief" })` opens it (`web/src/desk/intelligenceNavigation.ts:3`, `:18`).

### 1g. 393

- The phone Floor opens as the **list** past 16 objects (`COMPACT_LIST_THRESHOLD = 16`, `web/src/desk/store/types.ts:75`, `defaultViewFor` `:78-85`). A fresh HOME has 17 objects + 6 zones (shot `01a`). He will see the list.
- The list has no drag. Its row menu is the same `objectMenuEntries` (`DeskListView.tsx:405`).
- So on the phone, `Send to ▸` in the menu **is** the path. Drag stays a 1440 gesture.

## 2. FINDINGS, ranked by what they cost the owner

- **F1: on the phone there is no drag; the menu is the only path.** The phone opens the list (1g). If the charter builds drag first, the phone gets nothing. `Send to ▸` must ship with (or before) drag.
- **F2: a decision looks like a note.** The decision pool is the note pool (`sprites.ts:28`; shot `01-floor-1440`). ICON-DISCIPLINE requires a distinct silhouette per kind. When "drag a decision onto Slack" is the gesture, he cannot find the decision by shape. One new sprite family (rest, `_sel`, `_stale`).
- **F3: the menu is already crowded with ghosts.** Four of ten rows on a decision are ghosts (shot `02`). A ghosted `Send to ▸` on every note, persona and knowledge adds one more. UX-CANON A.11 says withhold a verb that cannot run. The registry's own rule says ghost (`verbRegistry.ts:10-11`). The owner picks (Q3).
- **F4: the drop tag must not say Send.** Release opens the preview; it does not send. `dropMatrix.ts:13-14` and A.11 forbid a tag that names an act release does not do. `SEND TO SLACK #leads` is the Phase 11 F2 bug again (the aftercare `Send` that only proposed). The tag names the destination and the open (Q4).
- **F5: the drop matrix is kind × kind; a send drop needs per-object answers.** A meeting with no summary has no well (C4, `MeetingPullout.tsx:153`). A parked destination takes nothing. The engine lights a target by kind only (`engine.ts:540-543`). The rule needs `accepts(dragged, target) → verb | refusal`, and a refusal shows on the tag (the glass-drop precedent: never a silent no-op, `web/src/desk/glassDrop.ts:41-47`).
- **F6: the 393 spatial Floor is already over-full.** Cells and labels overlap at 393 with 23 items (shot `01-floor-393`). Destination icons there add more. Recommendation: no destination icons at 393 (Q2).
- **F7: three of the six documents are not icons.** The brief, the meeting decision and the decision record are not on the Floor (1a). The owner asked for a brief icon; the other two stay with their faces (Phase 11 wells) unless he asks.
- **F8: a project icon is not a document.** The update lives inside the Room, behind the Update posture; `openSurfaceWhenReady(key, scope)` takes a project scope only (`web/src/desk/shell.ts:34-36`). A project dropped on a destination must name one update (Q5). No deep link to the Update posture with one update open was found (unknown below).
- **F9: the pre-pick seam is two private maps.** `SendWell.tsx:63-64` (`picked`) and `MeetingSendWell.tsx:28` (`formPick`). Small: export one setter each. Contract.md gains one line.
- **F10: the artifact window has three raw `<button>`s** (`web/src/desk/pullouts/ArtifactPullout.tsx:38`, `:57`, `:64`). The SEND well will sit in that window. UX-CANON A.1: they become library Buttons in the same story.
- **F11: destinations need a new world layer, not a new primitive.** A new `PrimitiveKind` drags the pullout registry, the descriptor table and `ORDER` with it (`world.ts:50-56`, `pullouts/registry.ts:26-47`). The zone layer is the precedent (1a). Data shape is Astra's half.

## 3. The canvases the charter will owe

Each board at 1440 × 900 and 393 × 852, on the real product with a harness shim for the new wire (the Phase 10/11 pattern: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/README.md`, "What the boards are").

**Canvas F: destinations on the Floor**
- F1 the Floor with three destinations (folder, Slack, GitHub) at the right edge; parked ones absent (393: the list, no destination icons, per Q2)
- F2 a destination icon selected; its menu (`Open`, `Park`)
- F3 no destinations: no icons, nothing in their place (A.8)
- F4 the new decision sprite beside a note (F2), rest / selected / stale

**Canvas G: drag a document onto a destination (1440; 393 shows the same end state reached by the menu)**
- G1 a decision held over `Slack #leads`: the lit `_sel` target and the tag (Q4)
- G2 released: the decision window opens at the drop point, `Slack #leads` picked, the preview and Send open, the egress chip `HOOKS.SLACK.COM`
- G3 sent: POSTED in the same well
- G4 a meeting with no summary held over a destination: the refusal on the tag, release does nothing
- G5 a meeting with a summary dropped: the window, form `Summary`, the destination picked
- G6 a project dropped: the Room at the Update posture, the latest published update, the destination picked (Q5)

**Canvas H: `Send to ▸`**
- H1 the decision menu at 1440 with `Send to ▸` open: the saved destinations by name
- H2 the same at 393 in the list (the submenu replaces the panel, back row first)
- H3 no destinations: `Send to ▸` holds one row, `Add destination` (opens Settings at the form, Phase 10 B2)
- H4 a kind that cannot send (a note): the menu per Q3
- H5 the menu bar Object menu with the same `Send to ▸`

**Canvas I: the brief icon**
- I1 the brief icon on the Floor (its place per Q6), its label `BRIEF SEP 29`
- I2 opened: Intelligence → BRIEF
- I3 dragged onto a destination: Intelligence → BRIEF with the destination picked
- I4 no brief yet: no icon

**Canvas J: artifacts**
- J1 the artifact window with its SEND well (library Buttons, F10)
- J2 an artifact dropped on a folder: picked, preview, Send

## 4. Questions for the owner (each with the lane's default)

1. **Where do destinations sit on the Floor?** Default: **a column at the right edge, like Workbench's disk icons**; he can drag them anywhere (saved like zones). One icon per saved destination; parked ones hidden.
2. **Destination icons at 393?** Default: **no**. The phone uses `Send to ▸` (F1, F6).
3. **`Send to ▸` on a kind that cannot send?** Default: **withhold it** (A.11; the menu has four ghosts already).
4. **The drop tag word.** Default: **`Preview for Slack #leads`** (release opens the preview; nothing is sent until he presses Send). The egress chip stays in the well, where the send happens (A.9).
5. **A project dropped on a destination sends which update?** Default: **the latest published update**; a project with none refuses on the tag.
6. **Where is the brief icon?** Default: **one icon on the Floor for the latest brief**, beside the destinations column; opening it opens Intelligence → BRIEF. No Dock change.
7. **The icon art.** Default: **one silhouette per channel** (folder, GitHub, Jira, Confluence, email, Slack) as pixel art in the house palette, not brand logos; the destination's name is the label.
8. **What opens a destination icon?** Default: **Settings → Destinations at that row** (the one place he edits it; no new window).

## 5. Unknown (not verified here)

- A deep link that opens the Room at the Update posture with one update open (F8): not found in `shell.ts` or `ProjectRoomCore.tsx`; not proven absent.
- The drag on a real touch screen at 393: the code arms a touch drag (`engine.ts:853-883`); my rig used a mouse and hit a persona on the crowded Floor.
- How the palette (⌘K) should list `Send to …` per destination: not grounded.
- Everything about the data: what a destination icon's position is stored as, the artifact source kind, the brief as a Floor object (Astra's half).
