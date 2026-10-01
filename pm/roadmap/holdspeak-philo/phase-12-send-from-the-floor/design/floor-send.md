# Send from the Floor (PHILO-12 design)

**Status:** DRAFT — UNCHECKED — awaiting Astra's check, then the owner's ratification. Written 2026-09-30 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. It binds stories 01–04 and gives the canvases (story 02) their wire.

**Inputs:** the faces grounding (`docs/internal/philo/phase-12/grounding/faces.md`, findings F1–F11, boards F–J, questions 1–8); the backend grounding (`docs/internal/philo/phase-12/grounding/backend.md`, findings 1–4, forks 1–2); Muad'Dib's check of the backend half (`docs/internal/philo/phase-12/grounding/checks/backend-muaddib.md`, RATIFY, no conditions). Where this design states a default, the charter's ratification question names it (`../current-phase-status.md`, "The one question").

**What does not change.** The Phase 10 send lifecycle (`../../phase-10-the-channels/design/send-lifecycle.md`) and the Phase 11 document sources (`../../phase-11-more-documents-on-the-channels/design/document-sources.md`) stay binding. The SEND well species (`web/src/desk/surface/send/SendWell.tsx`; contract `web/src/desk/surface/contract.md`) stays the one place where a preview shows and Send is pressed. This design adds one document kind, one Floor layer, one menu entry and one drop rule. It adds no operation, no authority class, no table and no migration.

## 1. Destinations on the Floor: a world layer, not a primitive

- **A new layer, like zones.** Zones are already a non-object layer: built apart from objects (`web/src/desk/gl/sceneModel.ts:210-252`), hit-tested before objects (`:285-327`), with their own menu target (`web/src/desk/gl/engine.ts:133-136`) and their own drop (`engine.ts:1129-1132`). Destinations follow that precedent. They are **not** a `PrimitiveKind`: a new kind drags the pullout registry, the descriptor table and `ORDER` with it (`web/src/desk/world.ts:50-56`; `web/src/desk/pullouts/registry.ts:26-47`; faces F11; backend finding 2).
- **The data.** The existing `channel.destinations` read, active rows only (`holdspeak/db/channels.py:100`; `include_parked` stays off). One icon per active saved destination. A parked destination disappears on the next read; its send history stays. Refresh on the existing destination-change hook (`DEST_CHANGED`, `web/src/desk/surface/send/SendWell.tsx:130-137`). Drawing the icons is a read: no admission, no receipt (`holdspeak/channel_operations.py:35`, `:55`).
- **The place.** A column at the right edge of the Floor, like Workbench's disk icons. He can drag an icon anywhere. Its position saves in the existing per-browser position map (`hs.diorama.pos`, `web/src/desk/store/dataSlice.ts:32`, `:825`) under the key `destination:<saved id>`. A parked icon's old key stays harmless; a replacement destination has a new id (backend §3). No table.
- **The art.** One 64 × 64 pixel-art silhouette per channel (folder, GitHub, Jira, Confluence, email, Slack), in the house palette. No brand logos. Each ships as rest, `_sel` and `_stale`, as every sprite does (`web/ICON-DISCIPLINE.md`, "The cell", "States are images"; `scripts/gen-sprite-states.py`). The destination's saved name is the label.
- **Open.** Opening a destination icon opens Settings → Destinations at that row (the one place he edits a destination; Phase 10 B2). No new window. The icon's menu has `Open` only. Park and Remove stay in Settings, where they are today (one place, Tenet 3).
- **Narrow widths.** Not drawn when the Desk is compact (`window.innerWidth <= 720`, the line `web/src/desk/world.ts:172` already uses). At 393 the phone opens the list (`web/src/desk/store/types.ts:75-85`; faces §1g), and the spatial Floor is already over-full (faces F6). The phone sends through `Send to ▸` (section 3).
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
- **Per object, not per kind.** A meeting with no summary and a project with no published update cannot send **this** object. The resolver answers `accepts(dragged, target) → verb | refusal` per object (faces F5). The menu (section 3) and the drop (section 6) use the same resolver, so the two paths never disagree.
- **The binding lives in one module** (story 01): a pure function from a Floor object (or a projection) to its `document_ref` or a named refusal. The menu, the drop and the atlas read that one function.

## 3. `Send to ▸` — the menu path (ships with or before the drag)

- **Where.** One `sub` entry in `objectMenuEntries` (`web/src/desk/floorMenu.ts:59-71`). The menu species already nests (`WorkMenuEntry` `type: "sub"`, `web/src/desk/components/DeskMenu.tsx:182-201`, `:322-360`). One entry reaches the three faces that read that list: the spatial Floor (`web/src/desk/gl/WorldStage.tsx:303-313`), the list (`web/src/desk/components/DeskListView.tsx:405`) and the menu bar's Object menu (`web/src/desk/components/DeskMenuBar.tsx:80`, `:139-145`).
- **The rows.** His active saved destinations by name, each with its channel word. No destinations: one row, `Add destination`, that opens Settings → Destinations at the form (Phase 10 B2).
- **Withheld where it cannot run.** On a kind that cannot send (a note, a persona, knowledge), and on an object that cannot send now (a meeting with no summary, a project with no published update), `Send to ▸` is not in the menu (UX-CANON A.11; the menu already carries four ghost rows on a decision, faces F3). The verb registry's "ghosting over hiding" comment (`web/src/desk/verbRegistry.ts:8-12`) gets one line that names this exception.
- **Release of a pick.** Picking a destination opens the document's own window (section 6, "Open") with that destination picked and its preview loaded. He presses Send. A pick never sends and never prepares.
- **At 393.** The list's row menu carries it; the submenu replaces the panel with a back row first (`DeskMenu.tsx:592`). This is the phone's whole path (faces F1).
- **Out:** `Send to …` rows in the ⌘K palette (not grounded; BACKLOG).

## 4. The artifact source: `artifact:<id>`

- **One renderer and one registry row.** `_ArtifactSource.render(db, source_id)` in `holdspeak/services/document_sources.py`, and its row in `DOCUMENT_SOURCES` (`:435-444`, eight rows today; this is the ninth). It reads the stored row with `db.plugins.get_artifact(source_id)` (`holdspeak/db/plugins.py:828`) and returns the existing `Document(ref, title, body_md, slug, label)` (`holdspeak/services/channel_contract.py:80`, `:93`). The channel descriptor text that lists the kinds changes in the same commit (`holdspeak/channel_operations.py:24`), and the registry fence pins nine (`tests/unit/test_philo11_document_sources.py:34`).
- **The body is the stored `body_markdown`.** No model runs. No regeneration from `structured_json`. No rendered HTML. No attachment. A Mermaid or code block in the body is text.
- **No internal id leaves the machine.** Meeting synthesis appends a source footer of raw window and plugin-run ids (`holdspeak/plugins/synthesis.py:680-683`). The renderer leaves out that known producer footer and nothing else. The Phase 11 fence that no internal id appears in a sent document (`6dc9a76c0`, `tests/unit/test_philo11_document_sources.py`) runs over the ninth kind, through real synthesis output.
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
- **No brief yet:** no icon. Generate stays where it is (the Chair and Intelligence). A drop never generates a brief.
- **A refresh never switches the document in an open preview.** The well keeps the id it opened with.
- **Narrow widths:** drawn on the spatial Floor only; at 393 the brief has its Chair and Intelligence wells (Phase 11).

## 6. Drag a document onto a destination

- **One rule in the drop matrix.** The drop matrix is kind × kind today (`web/src/desk/dropMatrix.ts:17-48`); the send rule asks the section 2 resolver per object (faces F5). No second drag engine (backend §4).
- **The tag while held.** `Preview for <destination name>`, for example `Preview for Slack #leads`. Never `Send`: release opens a preview; it does not send (`dropMatrix.ts:13-14`; UX-CANON A.11; faces F4). The target lights with its `_sel` image (`engine.ts:554-560`). The egress chip stays in the well, where the send happens (A.9).
- **A refusal on the tag.** When the resolver refuses, the tag says why and release does nothing (the glass-drop precedent: never a silent no-op, `web/src/desk/glassDrop.ts:41-47`): `NO SUMMARY` (a meeting with no summary), `NO PUBLISHED UPDATE` (a project), `PARKED` (a destination parked since the last read). The exact words are drawn on canvas G and ratified with it.
- **Release (Open).** The **dragged document's** window opens at the drop point, with the destination picked and its preview loaded (the mirror of `ground-into`, `engine.ts:1110-1118`; `openPullout(id, origin)`, `web/src/desk/store/compositorSlice.ts:137-152`). The dragged icon goes back to its place (`engine.ts:1123`); a drop never moves or files the document into a destination. Per icon:
  - decision → the decision window (`DecisionPullout`);
  - meeting → the meeting window, form `Summary`, the picker visible;
  - project → the Room at the Update posture with the latest published update, its well picked (`web/src/features/project-room/ProjectRoomCore.tsx:2167-2174`). A deep link to that posture with one update open was not found (faces §5); story 04 adds it if it does not exist;
  - brief → Intelligence → BRIEF, the destination picked;
  - artifact → the artifact window, the destination picked.
- **The pre-pick seam.** The pick is a private map today (`picked`, `web/src/desk/surface/send/SendWell.tsx:63-64`), and so is the meeting form (`formPick`, `web/src/meetings/MeetingSendWell.tsx:28`). Each well exports **one setter** (faces F9). `contract.md` gains one line for it. Nothing else in the species changes.
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
- The Room deep link's shape, if it must be built (section 6; story 04's first commit, checked by Astra).
- Floor icons for the decision record and the meeting decision (faces F7): they keep their Phase 11 wells. BACKLOG if he asks.
