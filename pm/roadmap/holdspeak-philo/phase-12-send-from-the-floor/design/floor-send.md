# Send from the Floor (PHILO-12 design)

**Status:** CHECKED by Astra (r1 RATIFY-WITH-CONDITIONS, paid) — awaiting the owner's ratification. Written 2026-09-30 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib; round two pays `../checks/charter-astra-r1.md` conditions 1–7 here (§§1–7, 10). It binds stories 01–04 and gives the canvases (story 02) their wire.

**Inputs:** the faces grounding (`docs/internal/philo/phase-12/grounding/faces.md`, findings F1–F11, boards F–J, questions 1–8); the backend grounding (`docs/internal/philo/phase-12/grounding/backend.md`, findings 1–4, forks 1–2); Muad'Dib's check of the backend half (`docs/internal/philo/phase-12/grounding/checks/backend-muaddib.md`, RATIFY, no conditions). Where this design states a default, the charter's ratification question names it (`../current-phase-status.md`, "The one question").

**What does not change.** The Phase 10 send lifecycle (`../../phase-10-the-channels/design/send-lifecycle.md`) and the Phase 11 document sources (`../../phase-11-more-documents-on-the-channels/design/document-sources.md`) stay binding. The SEND well species (`web/src/desk/surface/send/SendWell.tsx`; contract `web/src/desk/surface/contract.md`) stays the one place where a preview shows and Send is pressed. This design adds one document kind, one Floor layer, one menu entry and one drop rule. It adds no operation, no authority class, no table and no migration.

## 1. Destinations on the Floor: a world layer, not a primitive

- **A new layer, like zones.** Zones are already a non-object layer: built apart from objects (`web/src/desk/gl/sceneModel.ts:210-252`), hit-tested before objects (`:285-327`), with their own menu target (`web/src/desk/gl/engine.ts:133-136`) and their own drop (`engine.ts:1129-1132`). Destinations follow that precedent. They are **not** a `PrimitiveKind`: a new kind drags the pullout registry, the descriptor table and `ORDER` with it (`web/src/desk/world.ts:50-56`; `web/src/desk/pullouts/registry.ts:26-47`; faces F11; backend finding 2).
- **The data.** The existing `channel.destinations` read, active rows only (`holdspeak/db/channels.py:100`; `include_parked` stays off). One icon per active saved destination. A parked destination disappears on the next read; its send history stays. Refresh on the existing destination-change hook (`DEST_CHANGED`, `web/src/desk/surface/send/SendWell.tsx:130-137`). Drawing the icons is a read: no admission, no receipt (`holdspeak/channel_operations.py:35`, `:55`).
- **The place.** A column at the right edge of the Floor, like Workbench's disk icons. He can drag an icon anywhere. Its position saves in the existing per-browser position map (`hs.diorama.pos`, `web/src/desk/store/dataSlice.ts:32`, `:825`) under the key `destination:<saved id>`. A parked icon's old key stays harmless; a replacement destination has a new id (backend §3). No table.
- **The art.** One 64 × 64 pixel-art silhouette per channel (folder, GitHub, Jira, Confluence, email, Slack), in the house palette. No brand logos. Each ships as rest, `_sel` and `_stale`, as every sprite does (`web/ICON-DISCIPLINE.md`, "The cell", "States are images"; `scripts/gen-sprite-states.py`). The destination's saved name is the label.
- **Open.** Opening a destination icon opens Settings → Destinations **at that destination's row** (the one place he edits a destination). No new window. Today the Destinations arrival opens the **add form**, not a named row (`web/src/pages/cores/connections/Destinations.tsx:360-366`, B2); story 04 extends the arrival to carry a destination id and focus its row (Astra r1 finding 6). The icon's menu has `Open` only. Park and Remove stay in Settings, where they are today (one place, Tenet 3). **`Open` only supersedes grounding board F2** (`faces.md` §3 drew `Open`, `Park`; ratified by Astra r1 finding 6).
- **Narrow widths.** Not drawn when the Desk is compact (`window.innerWidth <= 720`, the line `web/src/desk/world.ts:172` already uses), and not in the list. At 393 the phone opens the list (`web/src/desk/store/types.ts:75-85`; faces §1g), and the spatial Floor is already over-full (faces F6). The phone sends through `Send to ▸` (section 3).
- **No destinations.** No icons and nothing in their place (UX-CANON A.8).

## 2. The document binding per icon

A generic icon id does not name a document (backend finding 1). Each sendable icon binds one exact `document_ref`:

| Icon | `document_ref` | Rule |
|---|---|---|
| Decision (`decision`, a desk decision) | `desk_decision:<decision id>` | its own record kind (`web/src/desk/documentSends.tsx:32`) |
| Meeting | `meeting_summary:<meeting id>` first; `meeting_digest:` and `meeting_followup:` by the picker | the preview opens on **Summary** with the Summary / Digest / Follow-up picker visible (`web/src/meetings/MeetingSendWell.tsx:31-54`); a change of form loads that form's preview for the same destination. Never the transcript. A meeting with no summary cannot send (`no_summary`) |
| Project | `project_update:<update id>` of its **latest published** update | a project id is not an update id. A project with no published update cannot send (the renderer's `not_published`, `holdspeak/services/channel_contract.py:221`) |
| Brief (section 5) | `monday_brief:<stored brief id>` | the id of the brief the view shows, never the string `latest` and never the icon's layout key |
| Artifact (section 4) | `artifact:<artifact id>` | the new source |

- **Nothing else on the Floor sends.** Notes, knowledge, personas, zones and the rest stay out (the owner did not pick notes). No document prefix is guessed for them.
- **The gate.** A `send` capability joins `primitiveCan` (`web/src/lib/primitives.ts:704-711`) for `decision`, `meeting`, `project` and `artifact`. The brief projection (section 5) carries it in its own variant.
- **Per object, not per kind.** A meeting with no summary and a project with no published update cannot send **this** object. The resolver answers per object (faces F5). The menu (section 3) and the drop (section 6) use the same resolver, so the two paths never disagree.
- **The binding lives in one pure module** (story 01). A pure function cannot discover facts the Floor does not hold: a Floor project carries no published-update id (`web/src/lib/primitives.ts:213`), and the meeting list carries a status but no summary (`holdspeak/services/meeting_service.py:868`). So the module takes **resolved inputs** and never reads (Astra r1 finding 3):

```text
resolve(input) -> { ref } | { refusal: code } | { pending: "unread" | "loading" | "failed" }

input (one of):
  { kind: "decision", id }
  { kind: "artifact", id }
  { kind: "meeting",  id, summary: Fact<boolean> }                    form: summary | digest | followup
  { kind: "project",  id, latestPublishedUpdateId: Fact<string|null> }
  { kind: "brief",    briefId }                                        the stored id the projection holds
  destination: { id, state: "active" | "parked" }

Fact<T> = { state: "unread" } | { state: "loading" } | { state: "failed" }
        | { state: "known", value: T }
```

  Only a **known** absence refuses (`no_summary`, `not_published`, `destination_parked`). `unread`, `loading` and `failed` answer `pending`, never a refusal.
- **The reads belong to story 03**, in one small shared module that both the menu and the later drop (story 04) consume: a meeting's summary presence from `GET /api/meetings/{meeting_id}` (`holdspeak/web/routes/meetings/crud.py:100`), and a project's latest published-update id from `GET /api/projects/{project_id}/updates` (`holdspeak/web/routes/project_updates.py:61`). The read starts when the menu opens or the drag starts, and its answer is kept for the session view.
- **No lost Send while a read is not done.** A `pending` object keeps `Send to ▸` and stays a drop target. A pick or a release on a `pending` object waits for the read: `known` → the normal path; known absence → the refusal word on that row or tag, nothing opens; `failed` → the row says `CAN'T CHECK` and the pick still opens the document's own window, whose well tells the truth (UX-CANON A.10).

## 3. `Send to ▸` — the menu path (ships with or before the drag)

- **Where.** One `sub` entry, `Send to ▸`. The menu species already nests (`WorkMenuEntry` `type: "sub"`, `web/src/desk/components/DeskMenu.tsx:182-201`, `:322-360`). `objectMenuEntries` (`web/src/desk/floorMenu.ts:59-71`) reaches the spatial Floor (`web/src/desk/gl/WorldStage.tsx:303-313`) and the list (`web/src/desk/components/DeskListView.tsx:405`). **The menu bar does not read that list:** it builds flat entries from `menuVerbs` on its own (`web/src/desk/components/DeskMenuBar.tsx:78-82`), and at compact width it shows only the `Go` menu (`DeskMenuBar.tsx:101-108`). (Round one claimed otherwise; Astra r1 finding 2.) Story 03 owns **one shared composition** of the object's menu entries, `Send to ▸` included, and all three rendered entry points: the spatial Floor, the list, and the menu bar (its Object menu and, at compact width, the `Go` menu).
- **The rows.** His active saved destinations by name, each with its channel word. No destinations: one row, `Add destination`, that opens Settings → Destinations at the form (Phase 10 B2).
- **Withheld where it cannot run.** On a kind that cannot send (a note, a persona, knowledge), and on an object that cannot send now (a meeting with no summary, a project with no published update), `Send to ▸` is not in the menu (UX-CANON A.11; the menu already carries four ghost rows on a decision, faces F3). The verb registry's "ghosting over hiding" comment (`web/src/desk/verbRegistry.ts:8-12`) is amended: UX-CANON A.11 governs, and a verb that cannot run for this object is withheld (Astra r1 finding 6).
- **Release of a pick.** Picking a destination opens the document's own window (section 6, "Open") with that destination picked and its preview loaded. He presses Send. A pick never sends and never prepares.
- **At 393.** The list's row menu carries it; the submenu replaces the panel with a back row first (`DeskMenu.tsx:592`). This is the phone's whole path (faces F1). The list row exposes `onContextMenu` only (`web/src/desk/components/DeskSortableTable.tsx:247`); the long-press in `engine.ts:790-830` belongs to the GL engine, not the list. Story 03 makes a **touch** long-press open the list row menu (or proves the platform already does), and its fence uses a touch gesture. A mouse right-click at phone width does not count (Astra r1 finding 5).
- **The brief in the list.** The brief projection (section 5) is a row in the list at every width, so the phone sends the brief through `Send to ▸` too. Destinations stay absent from the list.
- **The project's open path (moved from story 04 to story 03; Astra r1 finding 1).** A pick on a project opens the existing Room at the Update posture on that exact update with the destination picked. Today the opener carries only a project scope (`web/src/desk/store/compositorSlice.ts:158-168`; `openSurfaceWhenReady(key, scope)`, `web/src/desk/shell.ts:34-36`). Story 03 adds one link with the shape `{ projectId, updateId, destinationId }` (`updateId` = the exact published update). It opens that update when the Room's data is ready, **also when the Room is already open** (the open Room switches to that update and posture; it does not stay on what it showed).
- **Out:** `Send to …` rows in the ⌘K palette (not grounded; BACKLOG).

## 4. The artifact source: `artifact:<id>`

- **One renderer and one registry row.** `_ArtifactSource.render(db, source_id)` in `holdspeak/services/document_sources.py`, and its row in `DOCUMENT_SOURCES` (`:435-444`, eight rows today; this is the ninth). It reads the stored row with `db.plugins.get_artifact(source_id)` (`holdspeak/db/plugins.py:828`) and returns the existing `Document(ref, title, body_md, slug, label)` (`holdspeak/services/channel_contract.py:80`, `:93`). The channel descriptor text that lists the kinds changes in the same commit (`holdspeak/channel_operations.py:24`), and the registry fence pins nine (`tests/unit/test_philo11_document_sources.py:34`).
- **The body is the stored `body_markdown`.** No model runs. No regeneration from `structured_json`. No rendered HTML. No attachment. A Mermaid or code block in the body is text.
- **No internal id leaves the machine.** Meeting synthesis appends a source footer of raw window and plugin-run ids (`holdspeak/plugins/synthesis.py:680-683`). The renderer removes **only that synthesis-owned footer**, and only when its lines match the artifact's stored lineage (`artifact_sources` rows of type `intent_window` and `plugin_run`, `holdspeak/db/schema.py:371`; written at `synthesis.py:673-676`). Authored text and code blocks stay as stored. No general text scrubber (Astra r1 finding 6). The Phase 11 fence that no internal id appears in a sent document (`6dc9a76c0`, `tests/unit/test_philo11_document_sources.py`) runs over the ninth kind, through real synthesis output.
- **The label.** A short word from `artifact_type`, for example `ARTIFACT · REQUIREMENTS`. No id in the label or the file name (the Phase 11 ruling, `6dc9a76c0`).
- **Named refusals.**

| Case | Refusal | Where |
|---|---|---|
| No row with that id | `document_not_found` (exists) | the source |
| An empty or whitespace body | `artifact_body_missing` (new) | the source |
| A stored body that is not text | `artifact_not_text` (new) | the source, on the raw stored value before the DTO coerces it (`holdspeak/db/plugins.py:708`, `:862`; backend §1) |
| Too large for the channel | `payload_too_large:<channel>` (exists) | the channel limits, before dispatch (`holdspeak/services/channel_service.py:393`); no new artifact cap |

  The two new codes join the descriptor refusal list and the shared face words in the same commit. No upload, no OCR, no binary decoding, no truncation.
- **Which artifacts show.** The Floor shows the artifacts it shows today. Run listings hide `pending-review` and `rejected` (`holdspeak/db/plugins.py:931`); that stays. No new review gate: his preview and his Send are the approval.
- **Change.** If the body changes, the well shows the new preview, and he presses Send again (Phase 11 R9). No revision store.

## 5. The brief icon: a world-only projection

- **One icon for the latest stored brief.** It reads `GET /api/brief/latest` (`holdspeak/web/routes/monday_brief.py:112`). Its layout key is the stable `intelligence:brief`; its send identity is `monday_brief:<the stored id it shows>` (backend §2). Label: `BRIEF <day>`, for example `BRIEF SEP 29`.
- **Not a primitive.** `WorldObject.kind` and `.ref` require a primitive today (`web/src/desk/world.ts:11`). The Floor gains one explicit projection variant for non-primitive icons (the brief and the destinations), which delegates to existing surfaces. No 21st `PrimitiveKind`, no cast (backend §2, the table's first row).
- **Place.** Beside the destinations column. He can drag it; its position saves under `intelligence:brief`. No Dock change.
- **Open.** Opens Intelligence → BRIEF (`openIntelligence({ view: "brief" })`, `web/src/desk/intelligenceNavigation.ts:3`, `:18`). That view already composes the SEND well (`web/src/desk/pullouts/views/BriefView.tsx:461-463`).
- **The exact-id handoff (Astra r1 finding 4).** Today the navigation carries no brief id (`intelligenceNavigation.ts:5`), and the view fetches `/api/brief/latest` on its own (`BriefView.tsx:174`). A send from the brief icon or row passes `{ view: "brief", briefId, destinationId }`. The view shows that stored brief and keeps it; if `latest` answers another id, the view still shows the handed id. One read by id, `GET /api/brief/{brief_id}`, does not exist today (`holdspeak/web/routes/monday_brief.py:112-132` has `latest`, `generate`, `shelf`); story 01 adds it as a plain authenticated read (the renderer already loads by id, `holdspeak/services/document_sources.py:247`).
- **No brief yet:** no icon and no list row. Generate stays where it is (the Chair and Intelligence). A drop never generates a brief.
- **A refresh never switches the document in an open preview.** The well keeps the id it opened with.
- **Narrow widths:** at compact width the brief is a row in the list (section 3) with `Send to ▸`; no destination icons there.

## 6. Drag a document onto a destination

- **One rule in the drop matrix.** The drop matrix is kind × kind today (`web/src/desk/dropMatrix.ts:17-48`); the send rule asks the section 2 resolver per object (faces F5). No second drag engine (backend §4).
- **The tag while held.** `Preview for <destination name>`, for example `Preview for Slack #leads`. Never `Send`: release opens a preview; it does not send (`dropMatrix.ts:13-14`; UX-CANON A.11; faces F4). The target lights with its `_sel` image (`engine.ts:554-560`). The egress chip stays in the well, where the send happens (A.9).
- **A refusal on the tag.** When the resolver refuses, the tag says why and release does nothing (the glass-drop precedent: never a silent no-op, `web/src/desk/glassDrop.ts:41-47`): `NO SUMMARY` (a meeting with no summary), `NO PUBLISHED UPDATE` (a project), `PARKED` (a destination parked since the last read). The exact words are drawn on canvas G and ratified with it.
- **Release (Open).** The **dragged document's** window opens at the drop point, with the destination picked and its preview loaded (the mirror of `ground-into`, `engine.ts:1110-1118`; `openPullout(id, origin)`, `web/src/desk/store/compositorSlice.ts:137-152`). The dragged icon goes back to its place (`engine.ts:1123`); a drop never moves or files the document into a destination. Per icon, through the same open paths story 03 builds for the menu:
  - decision → the decision window (`DecisionPullout`);
  - meeting → the meeting window, form `Summary`, the picker visible;
  - project → the Room link `{ projectId, updateId, destinationId }` (section 3; built in story 03);
  - brief → Intelligence → BRIEF on the exact id (section 5);
  - artifact → the artifact window, the destination picked.
- **The selection pushed into a well (story 03; Astra r1 finding 4).** Round one said "export one setter; nothing else changes". That understates it. The pick is a module map keyed by the whole `document_ref` (`picked`, `web/src/desk/surface/send/SendWell.tsx:63-64`, read at `:459`), and the meeting form is read once into component state (`formPick`, `web/src/meetings/MeetingSendWell.tsx:28`, `:34`). The species gains:
  - **one push seam per well** (pick for a `document_ref`; form for a meeting), named in `web/src/desk/surface/contract.md`;
  - **an already-open well reacts** to a pushed selection: the open window changes its pick and loads the new preview, without a remount (a second drop on the same document with another destination changes the pick in place);
  - **the destination is kept across meeting forms:** Summary → Digest → Follow-up keeps the picked destination and loads each form's preview for it (today the pick is keyed by the form's ref and is lost);
  - **the brief's exact id** (section 5).
  Each is a rendered-transition fence at both widths, and the receipt after Send names the expected `document_ref` and destination.
- **No auto-prepare.** Release calls `channel.preview` only (XI.5-exempt; `holdspeak/channel_operations.py:180`, `:200`). No `channel_sends` row and no kernel operation exist until he presses Send (backend finding 4).
- **Narrow widths:** no destination icons, so no drop. The menu is the path (section 3).

## 7. The artifact window

- **The SEND well** composes in `ArtifactPullout` on `artifact:<id>`, as on every other document window (Phase 11 R4).
- **Its three raw `<button>`s become library Buttons** (`web/src/desk/pullouts/ArtifactPullout.tsx:38`, `:57`, `:64`; UX-CANON A.1; faces F10), in the same story.

## 8. The decision sprite

The decision wears the note sprite today (`web/src/desk/sprites.ts:28`; faces F2). Dragging "a decision onto Slack" needs a decision he can find by shape. One new sprite family with its own silhouette, rest, `_sel` and `_stale` (`web/ICON-DISCIPLINE.md`). The pool entry in `sprites.ts` changes; nothing else.

## 9. Authority (no new authority)

| Action | Class | Receipt |
|---|---|---|
| Draw destination and brief icons | authenticated read | none |
| Drop or `Send to ▸` pick → `channel.preview` | WORK; XI.5-exempt computation | none |
| Send | EGRESS, `owner_press=True` (`holdspeak/channel_operations.py:250`, `:292`; `holdspeak/mcp/tool_authority.py:272`) | the existing terminal receipt and send row |
| Save, park, remove a destination | AUTHORITY, in Settings only (unchanged) | unchanged |

An agent may prepare an artifact send over MCP or from a thread (Phase 11 D2); only he sends. The `artifact` kind reaches MCP through the existing descriptors with no new tool.

## 10. What this design does not decide

- The exact tag and refusal words, the icon art and the column's spacing: canvases F–J (story 02), ratified by the owner.
- The Room link's code shape beyond `{ projectId, updateId, destinationId }` (section 3): story 03's first commit, checked by Astra.
- Floor icons for the decision record and the meeting decision (faces F7): they keep their Phase 11 wells. BACKLOG if he asks.
