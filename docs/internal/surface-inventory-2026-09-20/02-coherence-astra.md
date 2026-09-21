# Coherence census — 2026-09-20

**LANE:** Astra, coherence (§A and §C). **WORKTREE:** `/Users/karol/dev/tools/wt-202-astra`. **BRANCH:** `audit/surface-coherence-astra`. **PRODUCT REVISION:** `93f9524f682aacf2fdb6138fa259506a338a1e2f`.

This audit found two ways to show an all-clear over an unknown or failed read, a large residue of raw controls, and several names for the same saved result. Those cost the owner more than the number of CSS literals. No product code, rulebook, roadmap story, or acceptance criterion is changed by this report.

The Tuesday answer is **not yet established**. The source gives the owner inconsistent names and false reassurance on failure. The Trust failure was reproduced with a local fixture hub at both widths. A complete first-use walk belongs to the sibling measured lane, not to this census.

| Inventory | Brief expected | Count at the pinned revision | Counting rule |
|---|---:|---:|---|
| Application manifest entries | 25 | 22 | AST objects in `DESK_APPLICATIONS`, `web/src/desk/applications.ts:48`; aliases do not add applications |
| Pullout registry kinds | 19 | 20 | Keys in `PULLOUT_CONTENT`, `web/src/desk/pullouts/registry.ts:26`; includes redirected/fallback kinds and `layout` |
| Direct core-directory TSX files | 34 | 33 | Non-test `.tsx` directly in `web/src/pages/cores`; 20 end in `Core.tsx`, others are helpers/settings/compositions |
| POSITIONING canonical-name rows | 73 | 71 | Table starting `docs/internal/POSITIONING.md:153`; rows, not unique names |
| Product-language terms | — | 22 | `docs/product-language.json:4` |
| Philo requirements / catalogue components | — | 63 / 73 | `docs/internal/philo/data/requirements.json:3`; `components-catalogue.json` |
| TypeScript source files | — | 427 | Non-test TS/TSX, including parked source |
| TSX files / files containing JSX | — | 229 / 224 | 207 active TSX, 22 parked JSX files; five active TSX modules contain no JSX |
| Active TSX breakdown | — | 177 consumer/support, 28 library, 2 preview | Source roles, not 207 distinct windows |
| CSS files | — | 64 | 63 nongenerated files plus generated `web/src/styles/tokens.css` |

These differences correct the census inputs. They do not silently omit the missing three applications or add three invented ones. The source inventories and door tables are the measured denominators.

## How to read the evidence

- A **source finding** is a named rule with a concrete source location and a checked interpretation. An **automated candidate** needs context or a rendered state. Neither an empty cell nor a clean scanner result means that a face passes every rule.
- The full [surface × rules matrix](02-surface-rules.csv) has every TSX source unit, including library, preview, helper and parked rows. It counts each file's own written controls and direct CSS imports. Shared children and global CSS have their own rows; these are not flattened runtime window totals.
- Counts are occurrences, not independent defects or percentages of compliance. A row, component wrapper and nested button are different species sites; adding them does not produce a meaningful “percent library” score.
- Parked source remains in the language and CSS inventory with a scope label. It is excluded from the active raw-control census and from the owner-cost ranking unless a live import/door is proved.
- The existing canon scanner was reused unchanged. Its raw-button matcher was reused by the species census; an independent TypeScript AST check found **zero differences across all 233 raw-control locations**. A second PostCSS count independently checked the CSS file, family, size, hex and standalone-z totals.
- Token review follows primitive → semantic → component. Repository law takes precedence over the skill's example values. The requested ignored skill was absent in this worktree; its local reference copy and `references/token-architecture.md` were read without changing the main checkout. The governing source remains `docs/internal/DESIGN_SYSTEM.md:10` and `web/design-tokens.json`.
- Static matching is not ASD-STE100 certification. A long word is not automatically wrong; registered terms and the first user's technical meanings matter. Runtime values, arbitrary component children and server-authored copy remain unresolved where the AST cannot establish text.

## Executive surface matrix

The compact table below selects the main core files, pullout renderers and shared faces. The linked CSV is the exhaustive source table. “Review” includes direct CSS and language candidates, not confirmed failures. Door reachability and SRS parity are reported separately, so a source file is not confused with a reachable application.


| Source surface (`web/src/` prefix omitted) | Source failures | Review candidates | Library sites / raw sites |
| --- | --- | --- | --- |
| desk/chair/ChairHome.tsx | — | — | 68 / 0 |
| desk/components/AskPanel.tsx | T5 | A7 D1 D2 U3 | 21 / 1 |
| desk/components/DeskEditor.tsx | T5 U1 | A7 D1 D2 | 0 / 11 |
| desk/components/DeskMenu.tsx | T5 U1 | A7 | 0 / 4 |
| desk/components/DeskToolInspector.tsx | T5 U1 | A7 D1 D2 T4 U6 | 3 / 10 |
| desk/components/DeskWindow.tsx | T5 U1 | — | 0 / 3 |
| desk/components/InfoWindow.tsx | T5 U1 | — | 3 / 4 |
| desk/components/ThreadComposer.tsx | T5 | A7 | 7 / 2 |
| desk/components/TrustWindow.tsx | A6 C4 T3 T5 U1 | A7 | 8 / 1 |
| desk/components/WorkbenchWindow.tsx | T5 U1 | A7 D1 D2 T4 U3 | 34 / 24 |
| desk/components/window/Dock.tsx | T5 U1 | — | 0 / 7 |
| desk/pullouts/ArtifactPullout.tsx | T5 U1 | — | 2 / 3 |
| desk/pullouts/ChainPullout.tsx | C2 T4 T5 U1 | — | 4 / 2 |
| desk/pullouts/CoderPullout.tsx | T5 U1 | A7 | 5 / 6 |
| desk/pullouts/DecisionPullout.tsx | — | — | 16 / 0 |
| desk/pullouts/DirectoryPullout.tsx | T5 U1 | — | 5 / 1 |
| desk/pullouts/FallbackPullout.tsx | — | — | 2 / 0 |
| desk/pullouts/IntelligencePullout.tsx | T5 U1 | D1 D2 M10 T4 | 4 / 1 |
| desk/pullouts/KbPullout.tsx | — | — | 10 / 0 |
| desk/pullouts/MeetingPullout.tsx | T5 U1 | A7 U3 | 4 / 2 |
| desk/pullouts/NotePullout.tsx | — | T4 | 48 / 0 |
| desk/pullouts/PeoplePullout.tsx | — | — | 3 / 0 |
| desk/pullouts/RecipePullout.tsx | — | — | 8 / 0 |
| desk/pullouts/ThoughtContextPicker.tsx | T5 U1 | A7 T4 | 7 / 2 |
| desk/pullouts/ThreadPullout.tsx | T5 U1 | D1 D2 U3 | 32 / 9 |
| desk/pullouts/WorkflowPullout.tsx | — | — | 5 / 0 |
| features/concierge/ConciergeCore.tsx | — | A7 D1 D2 U3 | 40 / 0 |
| features/project-room/ProjectRoomCore.tsx | A6 C4 T3 T5 | A7 D1 T4 U3 | 97 / 2 |
| features/project-room/door/DoorCore.tsx | T5 | A7 D1 D2 | 24 / 1 |
| pages/cores/ActivityCore.tsx | C2 T4 U6 | A7 | 15 / 0 |
| pages/cores/AssignmentEditor.tsx | — | A7 T4 | 14 / 0 |
| pages/cores/AssignmentModelChooser.tsx | T5 U1 | A7 | 3 / 1 |
| pages/cores/AssignmentSummary.tsx | — | — | 1 / 0 |
| pages/cores/CadenceCore.tsx | — | A7 D1 D2 T4 | 33 / 0 |
| pages/cores/CalendarSnapshotReviewCore.tsx | — | A7 | 16 / 0 |
| pages/cores/CapabilityAssignmentsCore.tsx | — | U6 | 7 / 0 |
| pages/cores/ChangePlacesCore.tsx | — | — | 5 / 0 |
| pages/cores/CommandsCore.tsx | — | A7 | 23 / 0 |
| pages/cores/CompanionCore.tsx | — | — | 13 / 0 |
| pages/cores/ComponentsCore.tsx | T5 U1 | A7 T4 | 94 / 1 |
| pages/cores/ConstitutionalContextCore.tsx | — | A7 D1 | 15 / 0 |
| pages/cores/ContextualAssignment.tsx | — | T4 | 0 / 0 |
| pages/cores/DictationCore.tsx | — | D1 D2 | 4 / 0 |
| pages/cores/HistoryCore.tsx | — | A7 | 13 / 0 |
| pages/cores/LiveCore.tsx | C2 T4 T5 U1 | U3 | 47 / 1 |
| pages/cores/ModelLibraryCore.tsx | — | A7 T5 | 35 / 4 |
| pages/cores/PeopleCore.tsx | — | A7 D1 D2 T4 U6 | 99 / 0 |
| pages/cores/ProcessCore.tsx | — | — | 6 / 0 |
| pages/cores/ProjectMemoryCore.tsx | — | — | 0 / 0 |
| pages/cores/RuntimeDocsCore.tsx | — | A7 | 29 / 0 |
| pages/cores/SettingsCore.tsx | A3 A6 C4 T3 | A7 T4 U3 | 127 / 0 |
| pages/cores/SetupCore.tsx | — | A7 | 14 / 0 |
| pages/cores/TopologyMapView.tsx | — | A7 D1 D2 T5 | 27 / 2 |
| pages/cores/WorkbenchesHomeCore.tsx | T5 U1 | — | 6 / 1 |
| pages/cores/core-hooks.tsx | — | — | 2 / 0 |
| pages/cores/core-layout.tsx | — | — | 3 / 0 |
| pages/cores/frontDoor.tsx | — | D1 | 15 / 0 |
| pages/cores/settingsBespoke.tsx | T5 U1 | — | 2 / 1 |
| pages/cores/settingsModels.tsx | — | — | 0 / 0 |
| pages/cores/settingsPrefs.tsx | C2 T4 U6 | A7 T4 | 22 / 0 |
| pages/cores/settingsTts.tsx | — | A7 | 7 / 0 |
| pages/cores/settingsWallpaper.tsx | — | A7 | 7 / 0 |


| desk/thought-workspace/ThoughtWorkspaceWindow.tsx | — | A7 D1 D2 | 14 / 0 |

## Top 30 by cost to the owner

This order favors a wrong work decision, a blocked move, and relearning a name over cosmetic debt. **S** means a checked source failure, **G** adds the controlled glass reproduction, **R** means review is still needed, and **K** means a conflict or stale claim in the rulebook/SRS. These ranks are an architectural judgment for the first user, not measured frequency or 30 proven runtime defects. Each row is an audit reference (`F01`–`F30`) in this report; the existing A1 ceiling remains the prior home for raw-button debt.

| Rank / home | Status | Owner cost and finding | Rule; Seven Tenet | Evidence |
|---|---|---|---|---|
| F01 | S/G | Trust says all data stays on the device after its status read fails; the same window shows external scope. The owner cannot use this to decide where work goes. A failed reopen also retains the last successful value because trust is not reset (`TrustWindow.tsx:57`). | A6, C4, T3; **3 — help, with a clear move** | `web/src/desk/components/TrustWindow.tsx:61`, `:65`, `:86`; controlled 503 at 1440 and 393, verification below |
| F02 | S | Room turns a degraded needs-you section into zero and “Nothing needs you,” then hides the section. Unread work can look finished. | A6, C4, T3; **3 — help, not vague reassurance** | `web/src/features/project-room/ProjectRoomCore.tsx:264`, `:282`, `:732`, `:2011`; decoder `web/src/features/project-room/model.ts:554` preserves the degraded state |
| F03 | S, conditional object | Generic Open is enabled for selected game/story/layout objects, whose declared surface is none. The move silently does nothing when such an object exists. | C3, C4, T3; **3 — one useful move** | `web/src/desk/verbRegistry.ts:381`; `web/src/lib/primitives.ts:563`, `:585`, `:641`; `web/src/desk/store/compositorSlice.ts:163` |
| F04 | S | Calendar source stats, auto-record state and the snapshot egress chip fall back silently; the source list itself comes from the settings payload. Snapshot remains enabled without a resolved badge, so a configured remote extraction can be offered without its before-click boundary. | A3, A6, C4, T3; **3 — useful state and boundary** | `web/src/pages/cores/SettingsCore.tsx:156`, `:795`, `:813`, `:1416`, `:1611` |
| F05 | S | Remote access removes its whole module while loading. Working is invisible at a boundary the owner must inspect. | C4, T3; **3 — useful state** | `web/src/pages/cores/SettingsCore.tsx:478`, `:485`, `:580` |
| F06 | S | A meeting result is Summary in the record and Intelligence in Live. The owner must learn that they refer to the same result. | U6, C2, T4; **4 — one plain meaning** | `web/src/pages/cores/LiveCore.tsx:340`; `web/src/meetings/MeetingSummarySlab.tsx:52`; `docs/product-language.json:23` |
| F07 | S | Failed Summary recovery has Retry and Retry intelligence. It makes one repair look like two jobs. | C1, U6, T3/T4; **3/4 — one move, one name** | `web/src/pages/cores/history/NeedsYouTable.tsx:92`; `web/src/pages/cores/history/DoorSection.tsx:114` |
| F08 | S | The saved Sequence object's own edit verb calls it a chain. | C2, U6, T4; **4 — one name** | `web/src/desk/pullouts/ChainPullout.tsx:42`; `web/src/lib/primitives.ts:529`; `docs/product-language.json:89` |
| F09 | R | Five direct manifest entries lack a Go/dock/mark projection; Models has a Go alias. Contextual doors exist for others; first-use discovery and their prerequisites need the sibling walk, especially Components and calendar review. | C3, T2/T3; **2/3 — first real use** | `web/src/desk/applications.ts:48`; `web/src/desk/tools.ts:4`; full reachability table below |
| F10 | K | POSITIONING calls Home/Studio canonical at lines 155/157 while its own line 110 says there is no Studio, and the Constitution replaced that page architecture with Desk. This can direct the next build toward the wrong door. | C2, U6, T3; **3 — no extra interface** | `docs/internal/POSITIONING.md:155`, `:157`, `:110`; `docs/internal/CONSTITUTION.md:62`; `web/src/routes.tsx:20`, `:70` |
| F11 | K | Universal state/error SRS rows say implemented, yet the Trust counterexample violates them. The parity ledger gives false confidence. | C5, A6, T3; **3 — honest help** | FR-STATE-001 and NFR-ERR-001 in [parity table](02-srs-parity.csv); `web/src/desk/components/TrustWindow.tsx:61` |
| F12 | S | WorkbenchWindow has 23 raw buttons and one raw textarea. Core work verbs bypass the common species in the owner's main work container. | T5, U1; **5 — component framework** | `web/src/desk/components/WorkbenchWindow.tsx:178`, `:319`, `:422`; all 24 rows in [raw table](02-raw-controls.csv) |
| F13 | S | DeskEditor has 11 raw controls. Editing uses a local control vocabulary instead of the common library. | T5, U1; **5 — component framework** | `web/src/desk/components/DeskEditor.tsx:330`, `:340`, `:350` |
| F14 | S | DeskToolInspector has ten raw controls at tool setup seams. | T5, U1; **5 — component framework** | `web/src/desk/components/DeskToolInspector.tsx:274`, `:293`, `:329` |
| F15 | S | Dock has seven raw buttons. The same bypass appears in the shared launcher, so it is encountered across jobs. | T5, U1; **5/6 — common Workbench controls** | `web/src/desk/components/window/Dock.tsx:124`, `:177`, `:197` |
| F16 | S + R | ThreadPullout has seven source raw-control findings and two native-input review sites; the running-work face is partly local control code. | T5, U1; **5 — component framework** | `web/src/desk/pullouts/ThreadPullout.tsx:110`, `:122`, `:1671`; nine sites total |
| F17 | S | SessionPullout has seven raw controls in captured work. | T5, U1; **5 — component framework** | `web/src/desk/components/SessionPullout.tsx:308`, `:581`, `:593` |
| F18 | S | CoderPullout has six raw controls around the delegated coding session. | T5, U1; **5/7 — common controls for the architect's work** | `web/src/desk/pullouts/CoderPullout.tsx:78`, `:117`, `:147` |
| F19 | S | GroundingSection has five raw controls at the context-selection seam. | T5, U1; **5 — component framework** | `web/src/desk/components/GroundingSection.tsx:205`, `:225`, `:259` |
| F20 | S | BriefView and the meeting catalog implement button roles on ordinary elements. Those verbs bypass the library too. | T5, U1; **5 — component framework** | `web/src/desk/pullouts/views/BriefView.tsx:386`; `web/src/pages/cores/history/CatalogRail.tsx:211` |
| F21 | S, language review | SEG and MTG make provenance harder to read than segment/meeting. The abbreviation is present; no rendered first-use definition was established. | T4, U6; **4 — plain words** | `web/src/pages/cores/LiveCore.tsx:662`; `web/src/features/project-room/RoomPeopleSection.tsx:151` |
| F22 | R | Arrival recovery and placeholders include sentences. This is the first face to simplify if state and next move can be preserved. | A7, T4; **2/4 — first use in plain words** | `web/src/desk/components/FirstWords.tsx:409`, `:423` |
| F23 | R | A 20-word Resourceful warning and command warning narrate the tool. Review them as compact state plus verb, while retaining the consequence. | A7, T4; **3/4 — useful, short text** | `web/src/desk/components/WorkbenchResourceful.tsx:185`; `web/src/pages/cores/CommandsCore.tsx:284` |
| F24 | R | Thought workspace deserves an explicit owner-facing review: A7/D1/D2 candidates and 62 direct CSS literal records occur in this face. Content hiding belongs to the sibling M2/M4 walk; no hidden-content failure is proved here. | A7, D1, D2, T2/T7; **2/7 — the architect’s actual thought work** | `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx`; [source matrix](02-surface-rules.csv) and occurrence tables |
| F25 | R | Thread CSS repeats 54 hex and 38 RGB literals in token fallbacks. This duplicates theme decisions in a heavily used work face. | D1, T5; **5 — common design system** | `web/src/desk/pullouts/thread-pullout.css`; occurrence anchors in [CSS table](02-css-occurrences.csv) |
| F26 | R | Shared surface CSS leads the static CSS ranking: 88 off-scale and 31 off-interior records. Shared roles deserve review before per-face patches. | D1, D2, T5; **5 — reusable framework** | `web/src/desk/surface/surface.css:62`; full exact line records in [CSS table](02-css-occurrences.csv) |
| F27 | R | 474 dimension/spacing records fall outside the scalar token set. Layout intent, role and active scope must be read before converting them. | D1, T5; **5 — shared dimensions** | [CSS file totals](02-css-files.csv), [all occurrence lines](02-css-occurrences.csv); 255 dimensions + 219 spacing |
| F28 | K/R | The design system offers display/body/mono while M10 caps a face at body/mono. A renderer can use the named roles and still fail the census rule. | D2, M10, T5; **5 — coherent framework** | `docs/internal/DESIGN_SYSTEM.md:325`; rulebook M10; four static CSS owners listed in Plane 2 |
| F29 | K | FR-SEL-002 says there is no selection model although lasso and multi-select exist. This understates the built component and invites duplicate work. | C5, T5; **5 — reuse what exists** | `web/src/desk/gl/WorldStage.tsx:65`, `:116`, `:375`; `web/src/desk/gl/sceneModel.ts:334`; parity table |
| F30 | R | The SRS has seven no-face requirements and 26 partly matched rows. Many honestly describe future/measurement work; they are a scope map, not seven release blockers or 26 proven bugs. | C5, T1/T2; **1/2 — no premature machinery** | [All 63 requirements](02-srs-parity.csv); native host, locale/theme and drag-equivalence rows remain explicitly scoped |

No fix is authorized by this ranking alone. This lane records debt under the user's no-product-code instruction; a later charter can choose the small set that changes Tuesday's work.


## Plane 1 — species (T5, U1, U2)

The active JSX census contains **233 raw-control sites**: 187 `<button>`, 32 `<input>`, eight `<textarea>`, three `<select>`, and three elements with `role="button"`. There are no native `<dialog>` sites in this scope. This is broader than the existing scanner's 175 A1 candidates: that scanner covers 247 files and deliberately uses a different scope.

| Source role | Files | Imported library symbols | Library JSX sites | Raw-control sites |
|---|---:|---:|---:|---:|
| Consumer / support | 177 | 900 | 1,983 | 187 |
| Library implementations | 28 | 7 | 9 | 40 |
| Development previews | 2 | 0 | 0 | 6 |
| Total active TSX | 207 | 907 | 1,992 | 233 |

Of the raw sites, **176 are source findings**, 40 implement the library itself, seven have a scoped exception (including six preview controls), and ten need reading. There are **157 consumer raw buttons**. The exact reconciliation is **187 = 157 consumer + 24 library + six preview**; the scanner's **175 = 187 minus Signal's one implementation button, five gadget implementation buttons, and six AtmospherePreview buttons**. The pre-existing home is the down-only A1 ratchet in `tests/ux_canon_ceiling.json`, described by `docs/internal/UX-CANON.md:136`; these are inherited species debts, not 176 newly introduced defects. Chrome is included as a deliberate source category; ranking Dock/DeskMenu/window chrome beside job faces is the lane owner's judgment, not a claim that each is a separate product face. Native file/secret inputs are retained for review; a microphone allowlist or native input type does not by itself exempt a face from T5. The two consumer `role="button"` findings are `web/src/desk/pullouts/views/BriefView.tsx:386` and `web/src/pages/cores/history/CatalogRail.tsx:211`; the third is library code, `web/src/desk/surface/Surface.tsx:853`.

[Every raw site, with line and classification](02-raw-controls.csv), [all 207 source files and library species](02-species-files.csv), and [41 menu/portal candidates](02-menu-portals.csv) are the complete tables. “Library JSX sites” counts syntactic use, not runtime instances.

| Consumer/support file | Library sites | Raw sites | Source failures / review |
| --- | --- | --- | --- |
| web/src/desk/components/WorkbenchWindow.tsx | 34 | 24 | 24 / 0 |
| web/src/desk/components/DeskEditor.tsx | 0 | 11 | 11 / 0 |
| web/src/desk/components/DeskToolInspector.tsx | 3 | 10 | 10 / 0 |
| web/src/desk/pullouts/ThreadPullout.tsx | 32 | 9 | 7 / 2 |
| web/src/desk/components/SessionPullout.tsx | 27 | 7 | 7 / 0 |
| web/src/desk/components/window/Dock.tsx | 0 | 7 | 7 / 0 |
| web/src/desk/pullouts/CoderPullout.tsx | 5 | 6 | 6 / 0 |
| web/src/desk/components/GroundingSection.tsx | 7 | 5 | 5 / 0 |
| web/src/desk/components/DeskFilingStrip.tsx | 5 | 4 | 4 / 0 |
| web/src/desk/components/DeskMenu.tsx | 0 | 4 | 4 / 0 |
| web/src/desk/components/InfoWindow.tsx | 3 | 4 | 4 / 0 |
| web/src/desk/components/MissionControlConveyor.tsx | 20 | 4 | 4 / 0 |
| web/src/desk/gl/WorldStage.tsx | 0 | 4 | 4 / 0 |
| web/src/desk/pullouts/shared/CapabilitySection.tsx | 2 | 4 | 4 / 0 |
| web/src/pages/cores/ModelLibraryCore.tsx | 35 | 4 | 0 / 3 |


There are **41 menu/portal candidates**: 31 are the shared DeskMenu chrome; ten need contextual reading. These include InletAutocomplete, DeskToolShelf, ThreadComposer, WorldStage rename, NotePullout's more menu, ThoughtContextPicker's portal, and ReviewPosture's listbox. A portal or a dropdown is not a modal. A final direct-call search adds [eight imperative/portal sites](02-dom-portals.csv): one `document.createElement("input")` file picker at `web/src/pages/cores/SettingsCore.tsx:1620`, plus all seven active `createPortal(...)` calls. These are separate from the 233 JSX controls and the 41 marker candidates; overlapping portal records must not be added as unique defects. ContextualAssignment at `web/src/pages/cores/ContextualAssignment.tsx:85` is an additional overlay-ownership review seam missed by the marker heuristic. No active native dialog, `role="dialog"`, `aria-modal`, or `Modal`/`Dialog` component was found by the bounded JSX scan. U2 is **not globally certified** by that absence; overlay focus and dismissal still need the measured walk.

The reused canon scanner also reports A3-prose 43, B 30, A8 25, emoji 21, raw IDs 17, C four, and A3-sentence two, for **317 candidates** in total. Its zero A9 count is a file-level `EgressChip` heuristic, not proof of an honest badge at every egress decision. [Scanner rows](02-canon-candidates.csv) retain the scanner's own rule vocabulary; it must not be confused with the rulebook's A3 egress rule.

## Plane 2 — tokens and type (D1, D2; M10 candidates)

There are **64 CSS files**, including generated `styles/tokens.css`; the 63 nongenerated files contain 12,877 declarations. Excluding three parked stylesheets and one preview leaves 59 active nongenerated files, 12,206 declarations. The full [CSS file table](02-css-files.csv) keeps both scopes. The [occurrence table](02-css-occurrences.csv) has 4,191 categorized records, each with a path, line, property, value, scope and audit status. Several categories can describe the same declaration; its automated `finding` flag is not a count of confirmed defects.

| Measure, 63 nongenerated files | Count | Interpretation |
|---|---:|---|
| Raw hex occurrences | 161 | Source literal occurrences; all are in active consumer CSS |
| RGB/RGBA occurrences | 57 | Eight allowlisted, 49 remaining; hex plus nonallowlisted RGB gives 210 color candidates |
| Raw dimension occurrences, excluding type and spacing | 756 | 255 outside the scalar token set, 501 numerically on it |
| Raw spacing occurrences | 1,813 | 219 outside the scalar token set, 1,594 numerically on it |
| Off-scale dimension + spacing occurrences | 474 | Source arithmetic, not 474 measured layout failures |
| `font-family` declarations | 317 | Declaration count, not simultaneous computed families |
| `font-size` declarations | 643 | All property values, including inherited/token forms |
| Font-shorthand size records | 227 | With the prior row, 870 size records |
| Interior size classification | 349 token / 184 raw on scale / 257 off scale / 79 unresolved / 1 zero | Off scale includes display/icon roles that still need context |
| Numeric z-index fallback values | 7 | All inside token `var(...)` fallbacks; **zero standalone numeric z-index declarations** |
| Static CSS owners that can reference three family roles | 4 | Potential M10 cases, no computed violation asserted |

The scalar token set is the union of numerical token values, not a permission to use any number in any role. A raw `12px` may match a scalar while still bypassing a semantic token. The type comparison uses the repository's interior set **11, 12, 13, 15, 26 px** and a stated 16px baseline for rem arithmetic. Media breakpoints are excluded, as permitted by the canon. The 257 off-interior records comprise 177 raw `font-size`, four raw shorthand sizes, ten token `font-size`, and 66 token shorthand sizes. Icon and display sizes remain **type review**, not automatically body-text failures.

All 210 nonallowlisted color candidates are token fallbacks. They are duplication risks at the primitive → semantic boundary, not proof that the current rendered theme ignores the token. A clean token gate and a broader literal census answer different questions. Both `npm run tokens:check` and `npm run tokens:gate` pass; the gate reports 11 allowlisted exceptions, all in use.

The worst 15 files below are ordered by the worker's weighted static flag count, which favors color/type/scale candidates. This is a triage order, not a measured owner-cost score. Exact categories are retained so the weighting cannot turn uncertain type roles into proven defects.

| CSS file (`web/src/` prefix omitted) | Hex / RGB | Raw dimension / spacing records | Off scale / off type | Families | Anchor |
| --- | --- | --- | --- | --- | --- |
| desk/surface/surface.css | 2 / 1 | 129 / 352 | 88 / 31 | 48 | web/src/desk/surface/surface.css:62 |
| desk/pullouts/thread-pullout.css | 54 / 38 | 57 / 127 | 20 / 12 | 38 | web/src/desk/pullouts/thread-pullout.css:270 |
| desk/components/chrome-menus.css | 1 / 0 | 55 / 78 | 31 / 10 | 7 | web/src/desk/components/chrome-menus.css:155 |
| desk/surface/gadgets.css | 5 / 0 | 46 / 67 | 21 / 16 | 12 | web/src/desk/surface/gadgets.css:26 |
| features/concierge/concierge.css | 39 / 1 | 12 / 56 | 5 / 3 | 0 | web/src/features/concierge/concierge.css:166 |
| desk/components/attention.css | 1 / 0 | 30 / 90 | 22 / 3 | 1 | web/src/desk/components/attention.css:56 |
| desk/components/pullout.css | 0 / 0 | 25 / 84 | 26 / 5 | 5 | web/src/desk/components/pullout.css:340 |
| desk/components/workbench-config.css | 0 / 0 | 13 / 78 | 10 / 15 | 29 | web/src/desk/components/workbench-config.css:51 |
| features/project-room/project-room.css | 17 / 0 | 14 / 77 | 6 / 0 | 17 | web/src/features/project-room/project-room.css:38 |
| desk/components/mission-control.css | 0 / 0 | 22 / 63 | 8 / 12 | 20 | web/src/desk/components/mission-control.css:83 |
| features/project-room/door/door.css | 21 / 1 | 10 / 36 | 5 / 1 | 0 | web/src/features/project-room/door/door.css:281 |
| desk/pullouts/intelligence.css | 0 / 0 | 20 / 27 | 14 / 13 | 26 | web/src/desk/pullouts/intelligence.css:27 |
| desk/components/window-chrome.css | 0 / 0 | 26 / 43 | 19 / 3 | 5 | web/src/desk/components/window-chrome.css:178 |
| desk/chair/chair.css | 5 / 0 | 13 / 26 | 7 / 13 | 23 | web/src/desk/chair/chair.css:44 |
| desk/surface/surface-footer.css | 0 / 0 | 31 / 23 | 6 / 12 | 11 | web/src/desk/surface/surface-footer.css:25 |


**M10 has a canon seam.** `docs/internal/DESIGN_SYSTEM.md:325` explicitly gives display text Space Grotesk, body text Inter, and data JetBrains Mono. The rulebook's M10 allows only body plus mono per surface. The four CSS owners with a static three-role potential are `web/src/desk/chair/chair.css`, `web/src/desk/pullouts/intelligence.css`, `web/src/desk/surface/surface.css`, and `web/src/styles/global.css`. A file does not establish a computed family census. Resolve the permitted display role against D2/M10 before assigning a defect to a face which obeys the named design tokens. No canon was amended here.

## Plane 3 — words (T4, U6, C1, C2, A7)

The AST harvest has **6,670 rows from 427 non-test TS/TSX files**. Of these, 3,986 are static or candidate literals: 1,365 JSX text, 1,145 selected copy attributes, 602 JSX expression strings, and 874 map/vocabulary strings. Another **2,684 are unresolved expressions** (795 attributes and 1,889 children). Those expressions include arbitrary component children; they are not 2,684 unique missing strings. Static confidence is recorded separately: 3,112 direct, 357 maps, 517 candidates.

[Every harvested string/expression](02-language-strings.csv), [noun rows](02-nouns.csv), [verb rows](02-verbs.csv), [language findings](02-language-findings.csv), and [252 bounded copy-review candidates](02-copy-candidates.csv) preserve the evidence. The noun table covers all 22 product terms and all 71 POSITIONING canonical-name rows; variant expansion plus checked Connections/Connectors evidence yields 129 CSV rows. The verb inventory has 11 job groups and 24 label rows.

### Noun map

This is the registry vocabulary. Legacy aliases are search inputs, not blanket proof that two observed strings have the same meaning. The CSV’s “observed” status means found in the source harvest and can include registry mirrors; it is not proof that a canonical noun renders on a face. The checked collision table below uses actual face properties/text.

| Canonical noun | Registry meaning | Legacy aliases to inspect | Source |
| --- | --- | --- | --- |
| Desk | The primary world where work, capabilities, presence, attention, and results live. | — | docs/product-language.json:5 |
| Meeting | A captured or imported conversation with stable identity. | — | docs/product-language.json:11 |
| Transcript | Speaker and time material owned by a Meeting. | — | docs/product-language.json:17 |
| Summary | What a Meeting produced for a person to read. The wire calls it meeting intelligence. Every face says Summary (HS-201-06, Constitution tenet 4). | — | docs/product-language.json:23 |
| Action item | Work a person should complete; never an external effect. | — | docs/product-language.json:29 |
| Result | Transient output produced by a run before it is kept or discarded. | — | docs/product-language.json:35 |
| Artifact | A kept generated result with stable identity and lineage. | — | docs/product-language.json:41 |
| Note | Durable text authored by a person. | — | docs/product-language.json:47 |
| Zone | A findable Desk placement for items. | directory, folder | docs/product-language.json:53 |
| Knowledge | A named collection of material used to ground answers. | kb, knowledge_base | docs/product-language.json:59 |
| Project | An ongoing endeavor or work scope, distinct from placement and grounding. | — | docs/product-language.json:65 |
| Agent | Saved reusable behavior made from instructions, tools, and knowledge. | agent, recipe | docs/product-language.json:71 |
| Coder session | A live Claude or Codex process, never a saved agent. | coder | docs/product-language.json:77 |
| Workflow | Saved reusable multi-step behavior. | — | docs/product-language.json:83 |
| Sequence | An advanced linear Workflow whose output flows through ordered steps. | chain | docs/product-language.json:89 |
| Integration | A named connection to a service or system. | connector, plugin | docs/product-language.json:95 |
| Runs on | The user-facing answer to where intelligence executes. | profile | docs/product-language.json:101 |
| Proposed action | A request to produce a named effect on a named destination. | — | docs/product-language.json:107 |
| Review | A judgment about content that does not authorize an external effect. | — | docs/product-language.json:113 |
| Approval | Authority for one exact effect, payload, and destination. | — | docs/product-language.json:119 |
| Grant | Bounded authority for repeated effects within an explicit scope. | — | docs/product-language.json:125 |
| Receipt | A durable account of what ran, where, why, and with what outcome. | — | docs/product-language.json:131 |


The checked collisions are narrower than a word search:

| Thing | Names on faces | Finding and seam |
|---|---|---|
| Meeting result | Summary / Intelligence | C2, U6, T4: `web/src/pages/cores/LiveCore.tsx:340` labels the result Intelligence; `web/src/meetings/MeetingSummarySlab.tsx:52` uses SUMMARY. `docs/product-language.json:23` requires Summary for the result. Intelligence remains a legitimate system primitive. |
| Saved sequence | Sequence / chain | C2, U6: `web/src/lib/primitives.ts:529` names Sequence; `web/src/desk/pullouts/ChainPullout.tsx:42` says Edit chain. Assignment model fallback chains are a different concept and are excluded. |
| Primary operating surface | Desk / Home / Studio | Stale lower canon: POSITIONING's rows at `docs/internal/POSITIONING.md:155` and `:157` retain Home/Studio although `:110` says there is no Studio; `docs/internal/CONSTITUTION.md:62` supersedes that page architecture. `web/src/routes.tsx:20` is correctly Desk. |
| Intent routing versus deployment | Routing profile / Runs on | No checked collision: `web/src/pages/cores/SettingsCore.tsx:1715` edits `meeting.routing_profile`; `web/src/pages/cores/settingsPrefs.tsx:162` supplies intent-routing choices. This is different from deployment placement. Narrow the registry alias if it conflates them. |
| Named service connection | Integration / Connections / Connectors | C2/U6/T4 source naming mismatch: the registry names Integration (`docs/product-language.json:95`), `web/src/desk/components/DeliveryBoard.tsx:329` renders Integration, `web/src/desk/applications.ts:421` and `web/src/pages/cores/settingsPrefs.tsx:57` render Connections, and `web/src/pages/cores/ActivityCore.tsx:230` renders Connectors. Registry-mirror strings are not proof of a face using the canonical name. |
| Meeting analysis extension | plugin / Integration legacy alias | Separate scope review: `web/src/pages/cores/LiveCore.tsx:453` says Deferred plugin jobs; POSITIONING explicitly names meeting plugins at `docs/internal/POSITIONING.md:167`. Do not apply the connection rename to meeting plugins. |

### Verb map

| Job | Observed labels | Interpretation | Example seam |
| --- | --- | --- | --- |
| open an existing record, row, or window | Open | coherent | web/src/desk/chair/ChairHome.tsx:1475 |
| start or repeat a meeting Summary run | Run summary / Retry | state-specific-coherent | web/src/pages/cores/history/helpers.ts:265-270 |
| commit a proposed effect or extracted proposal | Confirm / Approve | candidate-conflict | docs/internal/POSITIONING.md:201-202 |
| create a new Desk object | New Note / New Decision / New Knowledge / New Agent / New Workflow / New Workbench | coherent | web/src/desk/verbRegistry.ts:137-198 |
| edit an existing record in place | Edit / Edit Workflow / Edit working note | coherent-with-context | web/src/desk/pullouts/ChainPullout.tsx:72 |
| persist an edited record | Save | coherent | web/src/desk/chair/ChairHome.tsx:1413 |
| leave an edit without saving | Cancel | coherent | web/src/desk/chair/ChairHome.tsx:934 |
| remove an attention item from the active list | Dismiss | coherent | web/src/components/AmbientLayer.tsx:189 |
| repeat a failed operation | Retry / Try again | candidate-contextual | web/src/meetings/MeetingIntelRecovery.tsx:246-253 |
| keep a generated result versus persist an edit | Keep / Keep as artifact / Save | intentionally-distinct | docs/internal/DOCS_STYLE.md:31-35 |
| recover a failed meeting Summary | Retry / Retry intelligence | verified-conflict | web/src/pages/cores/history/NeedsYouTable.tsx:92-110 |


The verified same-job mismatch is **Retry / Retry intelligence**: `web/src/pages/cores/history/NeedsYouTable.tsx:92` and `web/src/pages/cores/history/DoorSection.tsx:114` both recover a failed meeting Summary. `Run summary` for a first run is a legitimate state distinction (`web/src/pages/cores/history/helpers.ts:265`), not a third conflicting retry verb. Ask, generate a new result, run a workflow, save an edit, and apply a proposal are different jobs; their labels are not collapsed because all trigger work.

### Short words and no prose

There are **192 sentence/long-copy candidates**, defined as a known static row with at least five words or sentence punctuation. Forty-two rows contain a word of at least 13 letters; 15 were curated for a greater-than-three-syllable review. These are bounded heuristics with false positives, not dictionary validation. The 252-row candidate CSV is their union with selected technical-word and abbreviation checks, not an additional 252 violations.

| Source | Static copy issue | Interpretation |
|---|---|---|
| `web/src/desk/components/WorkbenchResourceful.tsx:185` | 20-word warning | A7/T4 review: replace narration with a state, consequence and direct verb if the face can retain the required meaning. |
| `web/src/desk/components/FirstWords.tsx:409` | Recovered-draft sentences | First-value recovery deserves priority, but shortening must keep the true state and next move. |
| `web/src/pages/cores/CommandsCore.tsx:284` | Nine-word warning | Source presence verified; whether warning context justifies the text needs the face. |
| `web/src/pages/cores/LiveCore.tsx:662` | SEG | Unexplained source abbreviation; spell segment when that is the meaning. |
| `web/src/features/project-room/RoomPeopleSection.tsx:151` | MTG and SEG | Same abbreviation problem in a provenance token. `MeetingIntelRecovery.tsx:68` already uses SEGMENT; its old comment is not a third active SEG instance. |
| `web/src/desk/voice/ProposalStrip.tsx:75` | classification | Review “intent label” in this context; preserve the architect's technical meaning. |
| `web/src/features/project-room/prepare/PreparePosture.tsx:626` | deterministic | Review “fixed” only if that preserves the scheduling meaning. |
| `web/src/pages/cores/CadenceCore.tsx:511` | notification | Review “alert.” No syllable count alone establishes an STE violation. |

No pluralized lifecycle state was verified. RUNS and PROPOSALS are section nouns, not plural Ready/Failed states. No complete verdict covers backend-authored values, localized text or unknown runtime copy.


## Plane 4 — doors and states (C3, C4)

The complete [reachability CSV](02-reachability.csv) and [JSON](02-reachability.json) contain 22 applications and 20 primitive kinds, including aliases and silent no-op dispatch. The nine Settings modules and Trust are below. There are 18 lazy surface-backed applications, two special desks and two aliases. The pullout registry has 13 concrete components and seven fallbacks; primitive dispatch can redirect a kind before that fallback is painted.

“One move” in C3 is a named door choice, as its Go example implies. The table also gives raw pointer activations: Go then item costs two; a visible dock/row costs one. **Zero pointer clicks is not zero work**: a shortcut is one chord, search requires chord → query → Enter, and a direct URL is not an in-product door. Object rows require a visible object of that kind; select → Object → Open costs three pointer activations. These are source lower bounds, not timed walks.

First arrival is a separate state. `web/src/desk/DeskApp.tsx:110` holds normal chrome while setup is pending/failed; `:174` renders ChairHome alone while first value is required. `web/src/desk/components/SurfaceWindows.tsx:58` registers the recovery setup surface only then. Dock, Go, Search and normal shortcuts are unavailable until that gate is cleared. FirstWords at `web/src/desk/components/FirstWords.tsx:390` is the visible route; the report does not invent normal-launcher reachability on that face.

Five apps are absent from Go/dock/mark: Live, Models/Concierge, New Project, Components and Calendar snapshot. The Models alias does put the same Concierge face in Go, so its absent direct manifest projection is not an absent face door. Contextual paths can satisfy C3, so absence from a primary launcher alone is a review risk. Components is a design/development face with a deep route; calendar review requires snapshot context. Neither gets a cold-discovery pass from a URL. The three `none` kinds do have a checked generic Open/no-op mismatch (F03), conditional on an actual object being present.

State entries are **source presence**, not proof of all transitions. A read-only/static face may have no meaningful write-done state; that is N/A. Unknown child states remain unknown. The positive word “all” means the worker identified empty/loading/error plus settled/read or write-result paths at the stated layer; it does not override listed submodule counterexamples.

### Applications

`door` names the first normal Chair choice. `state` uses `read/N/A` where the
face is read-only and a domain “done” state has no meaning; it does not claim
that every surface needs a writable completion state. `all` means the cited
core has an explicit loading/empty/error or failure path and a success or
written/settled receipt where it performs work.

| stable app ID | label / core | door and raw clicks | prerequisites / keyboard | registry → dispatch → render | state and honesty |
|---|---|---|---|---|---|
| `app:change-places` | Change places / `ChangePlacesCore` | Go 2; Search 0; shortcut 0 | normal Chair; `⌘⇧P` | `web/src/desk/applications.ts:49-63` → `web/src/desk/tools.ts:4-21` → `web/src/desk/verbRegistry.ts:581-608` → `web/src/desk/shell.ts:94-118` → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/ChangePlacesCore.tsx:13-61` | read/local picker; working/failed/done N/A for local choice, shared wallpaper owns its own preference state |
| `app:open-intelligence` | Intelligence / pullout | Dock 1; HoldSpeak mark 2; Search 0 | normal Chair; no manifest shortcut; Search uses `desk.open-intelligence` | `web/src/desk/applications.ts:65-73` → `web/src/desk/components/window/Dock.tsx:110-143` → `web/src/desk/intelligenceNavigation.ts:18-23` → `web/src/desk/store/compositorSlice.ts:137-154` → `web/src/desk/components/Pullout.tsx:54-104` → `web/src/desk/pullouts/IntelligencePullout.tsx:79-` | read/navigation; child views own their reads; no write-done state claimed |
| `app:dictate` | Speak / `DictationCore` | Dock 1; Go 2; `⌘1` 0; Search 0 clicks after `⌘K` | mic permission for capture; first-value gate first | `web/src/desk/applications.ts:75-93` → `web/src/desk/components/window/Dock.tsx:110-143` or `web/src/desk/verbRegistry.ts:581-608` → `web/src/desk/shell.ts:94-118` → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/DictationCore.tsx:63-190` | all: readiness/resource, capture phases and refusal/receipt are explicit (`web/src/pages/cores/DictationCore.tsx:63-190`, `web/src/desk/components/FirstWords.tsx:32-137`) |
| `app:ask` | Ask AI / AskPanel | Go 2; Search 0 clicks after `⌘K`; `⌘I` 0 | normal Chair; selected context improves grounding | `web/src/desk/applications.ts:96-103` → `web/src/desk/verbRegistry.ts:581-603` → `web/src/desk/store/deskSlice.ts:143-150` → `web/src/desk/components/AskPanel.tsx:64-95` | all: compose/routing/printed plus action error (`web/src/desk/components/AskPanel.tsx:64-95` and action handlers); done is the printed result |
| `app:review-meetings` | Meetings / `HistoryCore` | Dock 1; Go 2; `⌘2` 0; Search 0 clicks after `⌘K` | normal Chair; meeting scope optional | `web/src/desk/applications.ts:105-123` → `web/src/desk/components/window/Dock.tsx:110-143` or `web/src/desk/verbRegistry.ts:581-608` → `web/src/desk/shell.ts:94-118` → `web/src/pages/cores/HistoryCore.tsx:33-111` | all: resource, no-model, action refusal and written receipts (`web/src/pages/cores/HistoryCore.tsx:270-285,491-530`) |
| `app:inspect-personas-and-coders` | Agents / `CompanionCore` | Dock 1; Go 2; `⌘3` 0; Search 0 clicks after `⌘K` | normal Chair; sessions/agents may be empty | `web/src/desk/applications.ts:125-144` → `web/src/desk/components/window/Dock.tsx:110-143` or Go spine → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/CompanionCore.tsx:30-46,138-177` | all for resource loads: empty sessions/agents and recipe error are named; write-done N/A for inspect face |
| `app:configure-settings` | Settings / `SettingsCore` | Dock 1; Go 2; `⌘4` 0; Search 0 clicks after `⌘K` | normal Chair; module choice is a second row choice | `web/src/desk/applications.ts:146-172` → dock/Go spine → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/SettingsCore.tsx:737-780,1882-1944` | all at outer resource/write layer; module-specific gaps are F04/F05 |
| `app:record-live` | Live meeting / `LiveCore` | Start/Record row 1; Search 0 clicks after `⌘K`; no Go/dock/shortcut | normal Chair; mic/device permission | `web/src/desk/applications.ts:174-188` → `web/src/desk/components/DeskStartActions.tsx:5-45` or `web/src/desk/components/RecordOrb.tsx:69` → `web/src/desk/shell.ts:94-118` → `web/src/pages/cores/LiveCore.tsx:67-96,454-534` | all: devices/plugins loading/error/empty, capture recovery, saved receipt |
| `app:configure-cadence` | Rhythm / `CadenceCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair; normal settings state | `web/src/desk/applications.ts:190-212` → Go spine → `web/src/pages/cores/CadenceCore.tsx:170-197,348-434,556-645` | all: running/held/generating, action error and written receipt |
| `app:open-constitutional-context` | Context / `ConstitutionalContextCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair | `web/src/desk/applications.ts:214-229` → Go spine → `web/src/pages/cores/ConstitutionalContextCore.tsx:19-28,104-165` | all: loading/error, dirty/saving/saved; save error is named |
| `app:open-workbenches` | Workbenches / `WorkbenchesHomeCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair; workbench data may be empty | `web/src/desk/applications.ts:231-246` → Go spine → `web/src/pages/cores/WorkbenchesHomeCore.tsx:36-40,73-159` | all: loading/empty/error, run status completed/failed |
| `app:design-components` | Components / `ComponentsCore` | deep route only; 0 URL clicks; no normal Search row | normal Chair; route `/design/components` is a demoted deep link | `web/src/desk/applications.ts:248-262` → `web/src/routes.tsx:31-76` → `SurfaceRedirect` → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/ComponentsCore.tsx:87-102,269-304` | read/demo; explicit state catalog and error/empty samples; domain done N/A |
| `app:inspect-activity` | Activity / `ActivityCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair | `web/src/desk/applications.ts:264-280` → Go spine → `web/src/pages/cores/ActivityCore.tsx:46-63,87-127,220-255` | all: resource empty, action busy/error, retry path |
| `app:open-project-memory` | Desk memory / `ProjectMemoryCore` → Room | Go 2; Search 0 clicks after `⌘K`; project row Search 0 clicks after `⌘K` | project scope for Room; unscoped is recall face | `web/src/desk/applications.ts:282-299` → Go spine → `web/src/pages/cores/ProjectMemoryCore.tsx:1-14` → `web/src/features/project-room/ProjectRoomCore.tsx:2010-2038` | **failed needs-you honesty gap**, F02; decoder itself is sound |
| `app:open-concierge` | Models / `ConciergeCore` | Go → Models alias 2; contextual Choose model 1; Search 0 pointer clicks; no direct Go/dock/shortcut projection | model assignment or a face that offers Choose model | `web/src/desk/applications.ts:301-322` → contextual callers or `web/src/desk/components/DeskToolShelf.tsx:361-373` → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/features/concierge/ConciergeCore.tsx:404-431,604-622` | all: loading/empty, ready/not set/unreachable/waiting/checking, applying/error receipt |
| `app:project-setup` | New Project / `DoorCore` | Desk New menu 3 (Desk→New→New Project); first-value Setup 1; Start action 1; Search 0; no Go/dock | first-value recovery or normal empty/start face; outcome needed to Create | `web/src/desk/applications.ts:324-339` → `web/src/desk/verbRegistry.ts:230-240` or `web/src/desk/components/FirstWords.tsx:457-467` → `web/src/desk/shell.ts:94-118` → `web/src/features/project-room/door/DoorCore.tsx:378-473` | all: source unpicked/checking/live/can't check, create busy/error, blank-project receipt |
| `app:inspect-processes` | Processes / `ProcessCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair; kernel rows may be empty | `web/src/desk/applications.ts:341-356` → Go spine → `web/src/pages/cores/ProcessCore.tsx:115-177` | rows expose running/waiting/failed/refused/unknown; initial poll has no explicit loading token (static risk) |
| `app:configure-commands` | Commands / `CommandsCore` | Go 2; Search 0 clicks after `⌘K` | normal Chair; settings write may be refused | `web/src/desk/applications.ts:358-373` → Go spine → `web/src/pages/cores/CommandsCore.tsx:42-55,141-160,149-306` | all: resource loading/error/empty, busy and success/refusal |
| `app:open-people` | People / `PeopleCore` | HoldSpeak mark 2; Search 0 clicks after `⌘K` if query row; no Go/dock/shortcut | normal Chair; protected data may be unavailable | `web/src/desk/applications.ts:375-390` → `web/src/desk/components/DeskChrome.tsx:27-30,142-180` or Search → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/PeopleCore.tsx:130-147,224-238,353-375` | all: loading/error/empty, protected failure and busy; read-done N/A |
| `app:review-calendar-snapshot` | Calendar snapshot / `CalendarSnapshotReviewCore` | contextual/deep route only; 0 pointer clicks for direct URL; no Go/dock/shortcut | snapshot evidence must be supplied; Settings → Meetings → Snapshot posts the file then opens this review | `web/src/desk/applications.ts:392-406` → `web/src/routes.tsx:31-76`/context caller → `web/src/desk/components/SurfaceWindows.tsx:46-203` → `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:27-29,37-118` | all: read error, saving/error, done receipt |
| `app:configure-runs-on` | Models alias / Concierge | Go 2; Search 0; `/profiles` deep route 0 URL clicks | normal Chair; alias targets Concierge | `web/src/desk/applications.ts:408-416` → `DESK_APPLICATION_ALIASES:455-461` → `web/src/desk/components/SurfaceWindows.tsx:97-105` → `web/src/features/concierge/ConciergeCore.tsx:404-431` | same as Concierge; alias is a door target, not a second core |
| `app:configure-integrations` | Connections alias / Settings | Go 2; Search 0 clicks after `⌘K`; Settings row 2 (Search + module) | normal Chair; `integration:destinations` scope | `web/src/desk/applications.ts:418-428` → `web/src/desk/tools.ts:4-21` → Go spine → `web/src/pages/cores/SettingsCore.tsx:1809-1859,1914-1944` | all at Connections pane/secrets; `NOT CHECKED` is honest until checked (`web/src/pages/cores/SettingsCore.tsx:1914-1926`) |

### Pullout kinds

All object rows below use the direct list/accessibility-row door: **1 click**
from a normal list or world accessibility face, with a selected-object Object
menu alternative of **3 clicks** (select row, Object, Open). Search is **0
pointer clicks after ⌘K + query + Enter**. A kind's registry row is not a claim
that the current Desk has an object of that kind.

| stable kind ID | kind / declaration | door and raw clicks | exact dispatch → render | state truth / gap |
|---|---|---|---|---|
| `kind:meeting` | Meeting / pullout | row 1; Object menu 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:428-437` → `web/src/desk/store/compositorSlice.ts:137-154` → `web/src/desk/pullouts/registry.ts:27` → `web/src/desk/components/Pullout.tsx:54-104` → `web/src/desk/pullouts/MeetingPullout.tsx:43-130` | explicit intel pending/complete/partial/failed/running and empty; fetch catch becomes null with no separate loading token (`web/src/desk/pullouts/MeetingPullout.tsx:43-67,125-130`) |
| `kind:artifact` | Artifact / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:439-449` → pullout spine → `web/src/desk/pullouts/ArtifactPullout.tsx:13-70` | read-only material/lineage; working/failed/done N/A, copy receipt is the only action result |
| `kind:note` | Note / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:451-460` → pullout spine → `web/src/desk/components/Pullout.tsx:108-130` → `web/src/desk/pullouts/NotePullout.tsx:48-105,430-470` | all: ownership pending/error, working/refining, failure messages, completed/finish receipts |
| `kind:decision` | Decision / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:462-471` → pullout spine → `web/src/desk/pullouts/DecisionPullout.tsx:20-` | content is read immediately; edit/status writes use local close/refresh but no visible write refusal was verified in the source slice; mark unknown |
| `kind:directory` | Zone / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:473-483` → pullout spine → `web/src/desk/pullouts/DirectoryPullout.tsx:19-90` | read/empty members; working/failed/done N/A for local membership view |
| `kind:kb` | Knowledge / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:485-494` → pullout spine → `web/src/desk/pullouts/KbPullout.tsx:22-120` | empty is explicit; editor Save has no visible refusal in this component; read loading/failed N/A because members are already in store |
| `kind:project` | Project / surface redirect | row 1; Object 3; Search project row 0 after ⌘K | `web/src/lib/primitives.ts:496-505` → `web/src/desk/store/compositorSlice.ts:154-163` → `openSurfaceWhenReady` → `web/src/pages/cores/ProjectMemoryCore.tsx:1-14` / Room | Room uses outer resource states but F02 collapses degraded needs-you |
| `kind:repository` | Repository / window | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:507-516` → `web/src/desk/store/compositorSlice.ts:154-158` → `openRepositoryWindow` → `components/RepoWindow.tsx` | window routing exists; repository face state was not inspected deeply in this bounded pass, unknown |
| `kind:recipe` | Agent / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:518-527` → pullout spine → `web/src/desk/pullouts/RecipePullout.tsx:21-90` | thread action busy + write receipt; read content immediate, done is thread-open receipt |
| `kind:chain` | Sequence / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:529-539` → pullout spine → `web/src/desk/pullouts/ChainPullout.tsx:12-77` | explicit empty steps; edit action; no async read state needed for local object |
| `kind:workflow` | Workflow / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:541-550` → pullout spine → `web/src/desk/pullouts/WorkflowPullout.tsx:13-82` | edit Save closes locally with no visible refusal in this component; working/failed/done unknown for persistence |
| `kind:coder` | Coder session / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:552-561` → pullout spine → `web/src/desk/pullouts/CoderPullout.tsx:22-154` | send/select phases include failed and retry; done is selected/sent receipt |
| `kind:game` | Game / none | row 1 if an object row exists; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:563-572` → `web/src/desk/store/compositorSlice.ts:163-169` → no render | **C3 no-op**; no empty/working/failed/done truth is painted |
| `kind:roadmap` | Roadmap / window | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:574-583` → `openRoadmapWindow` → `components/RoadmapWindow.tsx:52-` | window state not deeply inspected; unknown |
| `kind:story` | Story / none | row 1 if an object row exists; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:585-594` → `web/src/desk/store/compositorSlice.ts:163-169` → no render | **C3 no-op**; no state truth |
| `kind:workbench` | Workbench / window | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:596-605` → `openWorkbenchWindow` → `components/WorkbenchWindow.tsx:932-` | window has run/item states; home core explicitly shows loading/empty/error |
| `kind:intelligence` | Intelligence / pullout | row 1; Dock/mark app path also opens it | `web/src/lib/primitives.ts:607-616` → pullout spine → `web/src/desk/pullouts/IntelligencePullout.tsx:79-` | navigation/read views; child data states not exhaustively verified, no write-done claim |
| `kind:people` | People / surface redirect | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:618-627` → `openSurfaceWhenReady` → `web/src/pages/cores/PeopleCore.tsx:130-147` | all for People face; pullout registry entry is bypassed by surface declaration |
| `kind:thread` | Thread / pullout | row 1; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:629-639` → pullout spine → `web/src/desk/pullouts/ThreadPullout.tsx:1192-1210,1608-1735` | all: loading/no turns, streaming/running, failed/denied, turn done/receipt |
| `kind:layout` | Layout / none | row 1 if an object row exists; Object 3; Search 0 after ⌘K | `web/src/lib/primitives.ts:641-650` → `web/src/desk/store/compositorSlice.ts:163-169` → no render | **C3 no-op**; local-only does not explain a silent Open |

### Settings modules

All nine are module rows in the Settings hub (`web/src/pages/cores/settingsPrefs.tsx:40-60`),
reachable from the normal Settings hub in **2 clicks** (Search then module)
or from a direct `⌘K` row in **0 pointer clicks**. These are second-level
doors, so they do not make the Settings application itself a one-click Dock
door into a module.

| stable settings ID | module / keys | render and state audit |
|---|---|---|
| `setting:voice` | Voice / `hotkey,model,dictation,wake_word` | `web/src/pages/cores/SettingsCore.tsx:1183-1347` plus outer `SurfaceState` and write receipt; TTS/readiness children show working/refused states; done is written receipt |
| `setting:sounds` | Sounds & Presence / `ui,presence` | `web/src/pages/cores/SettingsCore.tsx:1350-1376`; toggle writes use shared saving/refusal; read/local controls have no domain done |
| `setting:wallpaper` | Wallpaper / no API keys | `web/src/pages/cores/settingsWallpaper.tsx:12-` local picker; empty favorites is a valid empty state; async working/failed/done N/A except local preference |
| `setting:meetings` | Meetings / `meeting,calendar` | `web/src/pages/cores/SettingsCore.tsx:1377-1759`; outer save states and calendar edit refusal exist, but `/api/calendar/sources` lacks loading/catch (`:795-817`), F04 |
| `setting:rhythm` | Rhythm / `cadence,cadence_telegram` | `web/src/pages/cores/SettingsCore.tsx:1760-1801`; shared saving/refusal and write receipt; module has no separate async done beyond written |
| `setting:models` | Models / `rails_observer` | `web/src/pages/cores/SettingsCore.tsx:1803-1811` immediately opens Concierge and returns null; state belongs to Concierge, so this module has no independent face state |
| `setting:assignments` | Assignments / no keys | same redirect at `web/src/pages/cores/SettingsCore.tsx:1803-1811`; no independent face state; state belongs to Concierge |
| `setting:integrations` | Connections / no API keys | `web/src/pages/cores/SettingsCore.tsx:1812-1859,1914-1944`; Connections pane checks/secrets and explicit `NOT CHECKED` until receipt; states are comparatively honest |
| `setting:system` | System / `device,mesh` | `web/src/pages/cores/SettingsCore.tsx:1860-1876`; RuntimeIdentity/Desk reset states are present; `RemoteAccessModule` loading returns null at `:478-580`, so its working state is hidden (F05) |


### Trust

| Surface | Normal arrival door | Empty / working / failed / done | Honesty |
|---|---|---|---|
| Data boundaries (`TrustWindow`) | Privacy-and-trust status control, one click; `web/src/desk/components/TrustWindow.tsx:49` is the window | Empty list is rendered; initial/failed status is converted to null; no explicit failed state; read-only done N/A | **F01 reproduced:** after a controlled 503 it says “All data stays on this device,” enabled destinations None, while scope says “this device + external.” |

For Calendar, the list comes from settings (`web/src/pages/cores/SettingsCore.tsx:1400`); per-source facts use `data._calendar_sources` (`:1414`). The auxiliary read supplies stats, auto-record details and snapshot egress. At `:1611` a missing resolution yields no badge, while Snapshot at `:1618` remains enabled and posts to `/api/calendar/snapshot`. `snapshotEgressChip` at `:156` also omits a nonlocal scope with no host. No remote upload was executed by this audit; the missing before-click badge is source-backed.

Trust and Room are actual contradictions, not missing generic state labels. Local pickers do not need a fabricated asynchronous success receipt simply to make a four-column checklist look complete.


## Plane 5 — Philo SRS parity (C5)

All **63 requirement IDs** in `docs/internal/philo/data/requirements.json` are represented once in [the parity CSV](02-srs-parity.csv). The current face classification is **17 yes, 26 partly, seven no, 13 N/A**. The pinned shard instead records 23 IMPLEMENTED, ten PARTIAL, 13 SPEC-DEBT and 17 UNIMPLEMENTED. These are different axes: implementation status is not proof of owner observation, and lack of a measurement in this audit is not proof that source is absent.

The registries were built against anchor `675401a857b85336d4acaa8c65383dfc9636e4c8`; this census reads product revision `93f9524f`. The component catalogue has 73 entries; Desk has eight capability rows, voice 41, runtime 11 and integrations 17. A capability row is not automatically another face or another Desk SRS requirement.

Three source-contradicted corrections are proposed, with no registry edit in this lane:

- **FR-SEL-002 → PARTIAL:** lasso/multi-select already exists (`web/src/desk/gl/WorldStage.tsx:65`, `:116`, `:375`; `web/src/desk/gl/sceneModel.ts:334`). Range/select-all/ordering remain separate gaps.
- **FR-STATE-001 → PARTIAL:** the universal freshness/state claim is contradicted by Trust's unknown-to-empty path (`web/src/desk/components/TrustWindow.tsx:61`). Transport connection state is implemented; universal honest domain state is not established.
- **NFR-ERR-001 → PARTIAL:** a typed API error and a reusable retry component do not make the Trust failure disappear. The controlled 503 is a concrete counterexample to universal face error mapping.

NFR-TEST-001 remains IMPLEMENTED after checking the existing UX scanner/ratchet, copy/language guards and token gates. The first bounded SRS read missed those guards; root review corrected it. Animation, forced colours, whole-Desk focus, runtime backoff and import refusal are kept as measured/coverage limits where source alone cannot contradict the shard. They are not downgraded merely because this lane did not run a trace.

YES below means a source-backed shape at the named seam, not an accepted owner walk. PARTLY can mean implementation scope or missing whole-face evidence; each row states which. NO is a missing face for that requirement; N/A covers host/CI/test/measurement/process contracts without a product face. Many NO rows are honest future contracts, not a reason to build release machinery before first use.

### Every SRS requirement

| ID | Face seam (current symbol) | Face | SRS status | Correction / exact seam finding | Unknown or inspected proof |
|---|---|---:|---|---|---|
| FR-DESK-001 | `web/src/routes.tsx:20-76`; `web/src/App.tsx:46-68` | YES | IMPLEMENTED | retain | `web/src/routes.test.ts` was named by the shard; route behavior was source-inspected. |
| FR-DESK-002 | `web/src/desk/components/DeskListView.tsx:81-91`; `web/src/desk/gl/WorldStage.tsx:364-386` | PARTLY | PARTIAL | retain PARTIAL; no all-object projection assertion | Spatial and list paths consume the same store/world helpers, but parity is not exhaustively asserted. |
| FR-OBJ-001 | `web/src/desk/world.ts:18-201`; `web/src/desk/gl/sceneModel.ts:163-207` | YES | IMPLEMENTED | retain | `web/src/desk/gl/__tests__/sceneModel.test.ts:146-164` asserts stable state projection; receipts/selection persistence are outside this row. |
| FR-OBJ-002 | `web/src/desk/gl/WorldStage.tsx:364-383`; `web/src/desk/components/DeskListView.tsx:220-229` | PARTLY | PARTIAL | retain PARTIAL | Marks, labels and `[x]` cues exist; the whole Pixi state set is not parity-tested. |
| FR-OBJ-003 | `web/src/desk/gl/WorldStage.tsx:364-386`; `web/src/desk/components/DeskListView.tsx:292-305` | PARTLY | PARTIAL | retain PARTIAL; touch-specific proof is absent | Pointer/list keyboard paths exist; no inspected touch activation assertion. |
| FR-WIN-001 | `web/src/desk/components/DeskWindow.tsx:815-873` | YES | IMPLEMENTED | retain | `web/src/desk/__tests__/windows.test.tsx:38-52` asserts shared title and three controls; move/resize source is in the same frame hook. |
| FR-WIN-002 | `web/src/desk/store/workspaceStorage.ts:79-149` | YES | IMPLEMENTED | retain | `web/src/desk/__tests__/windows.test.tsx:187-216` inspects round-trip/order/max/min behavior; no future v2 migration registry. |
| FR-WIN-003 | `web/src/desk/components/DeskWindow.tsx:719-736`; `web/src/desk/store/compositorSlice.ts:300-316` | YES | IMPLEMENTED | retain | Source returns focus to opener and MRU order is asserted at `windows.test.tsx:211-216`; reload focus is unknown. |
| FR-WIN-004 | `web/src/desk/components/window/windowGeometry.ts:95-119` | YES | IMPLEMENTED | retain | The shard names numerical shell assertions; native multi-monitor areas are out of Web scope. |
| FR-WIN-005 | Proposed `DesktopHost`; no native adapter in current Desk census | N/A | UNIMPLEMENTED | honest future host contract | No native host face exists; do not convert a proposed ADR into implementation. |
| FR-SEL-001 | `web/src/desk/keymap.ts:66-87`; `web/src/desk/store/deskSlice.ts:131-143` | YES | IMPLEMENTED | retain | One key context reads selected IDs and dispatches registry verbs; cross-window selection persistence remains unknown. |
| FR-SEL-002 | `web/src/desk/gl/WorldStage.tsx:65-70,116-125`; `web/src/desk/gl/sceneModel.ts:334-348` | PARTLY | SPEC-DEBT | **SRS WRONG → PARTIAL**; lasso/multi-select already exist, range/select-all/order remain debt | `sceneModel.test.ts:288-296` and `DeskListView.test.tsx:128-144` are assertion-bearing. |
| FR-MENU-001 | `web/src/desk/verbRegistry.ts:133-145`; `web/src/desk/components/DeskMenu.tsx:313-337` | YES | IMPLEMENTED | retain | `web/src/desk/__tests__/verbRegistry.test.ts:16-26` asserts unique IDs, labels and scopes; runner matrix is not exhaustive. |
| FR-MENU-002 | `web/src/desk/verbRegistry.ts:41-47`; `web/src/desk/__tests__/verbRegistry.test.ts:28-34` | YES | IMPLEMENTED | retain | Ghost reason and no-run behavior are asserted; localization is separate debt. |
| FR-MENU-003 | `web/src/desk/verbRegistry.ts:692-760`; `web/src/desk/components/ThreadComposer.tsx:603-640` | PARTLY | SPEC-DEBT | retain SPEC-DEBT; execution ownership needs a complete callback matrix | Slash ID parity is asserted at `verbRegistry.test.ts:118-124`; this does not prove every executor. |
| FR-KEY-001 | `web/src/desk/keymap.ts:19-89,112-127` | YES | IMPLEMENTED | retain | `web/src/desk/__tests__/keymap.test.ts:34-81` asserts modifier, typing guard and dispatch. |
| FR-KEY-002 | `web/src/desk/keymap.ts:21-64`; `web/src/desk/verbRegistry.ts:89-110` | PARTLY | SPEC-DEBT | retain SPEC-DEBT; no browser/AT/OS conflict matrix | The parser reserves primary modifiers but no conflict oracle or alternate label catalogue exists. |
| FR-DND-001 | `web/src/desk/dropMatrix.ts:9-47`; `web/src/desk/gl/WorldStage.tsx:300-311` | YES | IMPLEMENTED | retain | `web/src/desk/__tests__/dropMatrix.test.ts:21-32` asserts inert unlisted pairs and named actions. |
| FR-DND-002 | `web/src/desk/dropMatrix.ts:22-39`; `web/src/desk/verbRegistry.ts:133-145` | NO | UNIMPLEMENTED | honest future contract | Matrix effects exist, but no matrix-to-verb coverage seam exists. |
| FR-DND-003 | `web/src/desk/components/GlassDropLayer.tsx:41-95`; `web/src/desk/gl/WorldStage.tsx:300-311` | YES | IMPLEMENTED | retain; the row does not require a durable importer receipt | `GlassDropLayer.tsx:111-150` shows the named armed/import/refusal face; no owner observation is claimed. |
| FR-DND-004 | `web/src/desk/gl/WorldStage.tsx:65-70`; `web/src/desk/dropMatrix.ts:22-39` | NO | UNIMPLEMENTED | honest future design contract | Current lasso is selection, not a settled cross-window/orb drag contract. |
| FR-INFO-001 | `web/src/desk/surface/contract.md:1-34`; `web/src/desk/components/InfoWindow.tsx:119-257` | PARTLY | IMPLEMENTED | retain; object Info exposes identity/lineage and handoff verbs, while broader window provenance remains outside this row | `InfoWindow.tsx:142-207,228-250` is source evidence; no claim that every Desk window is an object inspection surface. |
| FR-INFO-002 | `web/src/desk/surface/patterns/ProvenanceChip.tsx:35-65`; `web/src/desk/verbRegistry.ts:133-145` | PARTLY | SPEC-DEBT | retain SPEC-DEBT; presentational receipt is not durable receipt storage | `Receipt` has status/label/time props, but no verb-to-persistence contract. |
| FR-STATE-001 | `web/src/runtime/RuntimeBus.tsx:48-83`; `web/src/desk/components/TrustWindow.tsx:59-89` | PARTLY | IMPLEMENTED | **SRS WRONG → PARTIAL**; transport state is real, universal freshness and unknown trust state are not | `RuntimeBus.test.tsx:51-75` proves one socket/frame/cleanup, not all surface freshness. |
| FR-STATE-002 | `web/src/runtime/RuntimeBus.tsx:52-83`; `web/src/lib/api.ts:26-68` | PARTLY | PARTIAL | retain PARTIAL | No common subscriber/refetch protocol; this gap is correctly stated by the shard. |
| FR-HOST-001 | Proposed `docs/internal/philo/adr/desktop-host.md:1`; no native adapter | N/A | UNIMPLEMENTED | honest future host contract | No host face or capability adapter exists. |
| FR-HOST-002 | `web/src/main.tsx:1-26`; `web/src/App.tsx:46-74` | YES | IMPLEMENTED | retain | Browser boot and Desk route do not require a native host; owner observation is not claimed. |
| NFR-A11Y-001 | `web/src/desk/keymap.ts:112-127`; `web/src/desk/gl/WorldStage.tsx:352-386` | PARTLY | PARTIAL | retain PARTIAL | Named controls and focusable list/world proxies exist; complete Desk keyboard walk/axe evidence is absent. |
| NFR-A11Y-002 | `web/src/desk/components/DeskWindow.tsx:719-736,780-816` | PARTLY | SPEC-DEBT | retain SPEC-DEBT | Opening/closing focus behavior exists; no focus-obscuration or virtual-keyboard oracle. |
| NFR-A11Y-003 | `web/src/desk/dropMatrix.ts:22-47`; `web/src/desk/verbRegistry.ts:133-145` | NO | UNIMPLEMENTED | honest future contract | No equivalent keyboard/non-drag action for every matrix effect. |
| NFR-A11Y-004 | `web/src/desk/surface/Surface.tsx:287-327`; `web/src/desk/components/DeskWindow.tsx:751-767` | PARTLY | SPEC-DEBT | retain SPEC-DEBT | Container/window responsive seams exist; no complete 393px action/state/source/egress parity evidence. |
| NFR-A11Y-005 | `web/src/desk/surface/gadgets.tsx:609-684`; `web/src/desk/gl/WorldStage.tsx:370-374` | YES | IMPLEMENTED | retain; the requirement asks for non-colour cues, not a forced-colours fixture | LedMeter/Lamp text and object ARIA cues are source evidence; whole-Desk forced-colour testing belongs to NFR-TEST-004. |
| NFR-A11Y-006 | `web/src/desk/DeskApp.tsx:186-201`; `web/src/desk/components/DeskListView.tsx:268-330` | PARTLY | PARTIAL | retain PARTIAL | List parity consumes shared records and actions; no exhaustive census parity assertion. |
| NFR-PERF-001 | `web/src/desk/DeskApp.tsx:184-201`; `web/src/desk/gl/sceneModel.ts:157-161` | PARTLY | SPEC-DEBT | retain SPEC-DEBT | Object cap exists, but no reference scale/frame trace. |
| NFR-PERF-002 | `web/src/desk/components/DeskWindow.tsx:349-386,628-646` | YES | IMPLEMENTED | retain; source implements the compositor animation and bounded window update contract | No performance run in this lane; lack of a trace is an evidence limit, not a source contradiction. |
| NFR-PERF-003 | `web/src/desk/surface/Surface.tsx:438-449`; `web/src/desk/DeskApp.tsx:44-63` | PARTLY | SPEC-DEBT | retain SPEC-DEBT; lazy terminal exists, measured first paint does not | Lazy import is source evidence; no first-usable mark or bundle budget. |
| NFR-PERF-004 | `web/src/desk/gl/sceneModel.ts:157-161`; `web/src/runtime/RuntimeBus.tsx:41-83` | N/A | SPEC-DEBT | retain SPEC-DEBT; this is a capacity contract, not a face | No documented degradation face or event/window ceilings. |
| NFR-REL-001 | `web/src/runtime/RuntimeBus.tsx:48-83` | YES | IMPLEMENTED | retain; source has bounded attempts/delay and truthful state transitions | `RuntimeBus.test.tsx:51-75` inspects one socket/frame/cleanup; this lane did not rerun reconnect cases. |
| NFR-REL-002 | `web/src/desk/store/workspaceStorage.ts:79-117` | YES | IMPLEMENTED | retain, with malformed-input test gap | Catch/version/filter behavior is source-backed; tests named by the shard do not cover every malformed shape. |
| NFR-REL-003 | `web/src/lib/api.ts:14-23,62-68`; `web/src/desk/surface/Surface.tsx:201-253` | PARTLY | PARTIAL | retain PARTIAL | API and retry faces exist; host failures and durable domain receipts do not share one recovery contract. |
| NFR-I18N-001 | `web/src/desk/surface/Surface.tsx:201-253`; `web/src/desk/verbRegistry.ts:133-145` | NO | UNIMPLEMENTED | honest future catalogue | Visible strings are still literals; no message catalogue/extractor. |
| NFR-I18N-002 | `web/src/desk/surface/Surface.tsx:287-327`; `web/src/desk/components/DeskWindow.tsx:751-767` | PARTLY | UNIMPLEMENTED | honest future expansion fixture; responsive face exists | No 30/50 percent expansion fixture or measured width budget. |
| NFR-I18N-003 | `web/src/desk/surface/format.ts:7-35,74-95` | PARTLY | UNIMPLEMENTED | retain UNIMPLEMENTED; default locale formatters cover only part of the contract | `toLocaleDateString`/`toLocaleTimeString` are source evidence; number/byte formatting and locale injection are unknown. |
| NFR-I18N-004 | `web/src/desk/surface/Surface.tsx:47-55`; proposed localization brief | NO | UNIMPLEMENTED | honest future RTL/bidi contract | No RTL layout or keyboard fixture. |
| NFR-THEME-001 | `web/src/styles/tokens.css:240-300`; `web/src/lib/tokens.gen.ts:6-30` | PARTLY | PARTIAL | retain PARTIAL | Semantic roles exist; legacy overlays and direct color seams remain. |
| NFR-THEME-002 | `web/src/styles/tokens.css:240-300` | NO | UNIMPLEMENTED | honest future high-contrast layer | No high-contrast token layer or snapshot face. |
| NFR-THEME-003 | `web/src/styles/tokens.css:240-300` | NO | UNIMPLEMENTED | honest future light/system layer | Signal dark exists; light/system role parity is not implemented. |
| NFR-ERR-001 | `web/src/lib/api.ts:14-23,57-68`; `web/src/desk/surface/Surface.tsx:201-253`; `web/src/desk/components/TrustWindow.tsx:59-89` | PARTLY | IMPLEMENTED | **SRS WRONG → PARTIAL**; TrustWindow masks 503 and displays a false empty-destination state | `web/src/lib/api.test.ts:26-41` proves typed 503 only; no universal recovery assertion. |
| NFR-ERR-002 | `web/src/desk/verbRegistry.ts:41-47`; `web/src/desk/gl/WorldStage.tsx:300-311`; `web/src/desk/components/GlassDropLayer.tsx:111-150` | PARTLY | IMPLEMENTED | retain; source supplies ghost reasons, drop hints and refusal alerts; UI run evidence is outside this audit | `WorkMenu` consumes the ghost reason; no owner observation is claimed. |
| NFR-ERR-003 | `web/src/desk/store/workspaceStorage.ts:131-153`; `web/src/desk/store/compositorSlice.ts:290-307` | PARTLY | PARTIAL | retain PARTIAL | Save catches storage failures and live store remains authoritative; no retry receipt or user-facing save-failure face. |
| NFR-TEST-001 | `scripts/check_docs.py:101-142`; `scripts/ux_canon_scan.py:953-1029`; `tests/unit/test_ux_canon_scan.py:466-527`; `tests/unit/test_ux_canon_ratchet.py:61-188`; `tests/unit/test_product_copy.py:67-94,257-264`; `tests/unit/test_product_language.py:30-105,121-151`; `web/package.json:17-20` | N/A | IMPLEMENTED | retain; the full guard set covers links, canon rules/ratchet, product copy/language and token check/gate | Root reported 38 scanner tests green and clean npm token check/gate; this lane did not rerun them. |
| NFR-TEST-002 | `web/src/desk/__tests__/shell.test.tsx:125-285`; `web/src/desk/__tests__/dropMatrix.test.ts:6-32`; `web/src/desk/__tests__/verbRegistry.test.ts:16-124` | N/A | IMPLEMENTED | retain for the named focused behaviors | Assertions were inspected; no test execution is claimed. |
| NFR-TEST-003 | `docs/internal/TWO-BRAINS.md:1`; phase story acceptance | N/A | SPEC-DEBT | retain SPEC-DEBT; evidence artifact contract | This is a merge/evidence requirement, not a product face; current root has glass proof for Trust only. |
| NFR-TEST-004 | proposed quality fixture in `docs/internal/philo/briefs/workbench-design-srs.txt:302` | N/A | SPEC-DEBT | retain SPEC-DEBT | No reduced-motion/high-contrast/keyboard/RTL/pseudo-locale matrix run in this lane. |
| NFR-TEST-005 | proposed `docs/internal/philo/adr/desktop-host.md:1` | N/A | UNIMPLEMENTED | honest future host test contract | No native host adapter exists to test. |
| NFR-CI-001 | `.github/workflows/test.yml:28-29,86-119`; `CLAUDE.md:83-103` | N/A | PARTIAL | retain PARTIAL | CI has docs, npm and isolated-HOME jobs; Desk shard drift is not wired as a separate gate. |
| NFR-CI-002 | `scripts/check_docs.py:101-142`; `docs/internal/philo/data/README.md:1-82` | N/A | SPEC-DEBT | retain SPEC-DEBT | No source-anchor validator for SRS/catalogue rows. |
| ROAD-001 | `pm/roadmap/holdspeak-philo/phase-1-audit-and-specification/story-05-desk.md:1`; proposed host ADR | N/A | SPEC-DEBT | retain SPEC-DEBT | Delivery order is process documentation, not a product face or implementation claim. |
| NFR-PERF-005 | proposed `docs/internal/philo/DELIVERY_ROADMAP.md:1` | N/A | UNIMPLEMENTED | honest benchmark contract | No CPU fixture was run; no face exists for this metric. |
| NFR-PERF-006 | proposed `docs/internal/philo/DELIVERY_ROADMAP.md:1` | N/A | UNIMPLEMENTED | honest benchmark contract | No heap/GC fixture was run; no face exists for this metric. |
| NFR-REL-004 | `web/src/runtime/RuntimeBus.tsx:73-83`; `web/src/desk/DeskApp.tsx:95-121` | PARTLY | UNIMPLEMENTED | honest future reliability contract; current refresh failure face preserves visible Desk | No 30-second disconnect or duplicate-dispatch assertion. |
| NFR-A11Y-007 | `web/src/desk/components/DeskWindow.tsx:838-861`; `web/src/desk/components/DeskListView.tsx:214-229` | PARTLY | UNIMPLEMENTED | honest future measured target contract | Buttons/rows have a face, but 44 CSS px/spacing is unmeasured. |
| NFR-A11Y-008 | `web/src/desk/DeskApp.tsx:186-201`; `web/src/desk/components/DeskWindow.tsx:751-767` | PARTLY | UNIMPLEMENTED | honest future zoom/reflow contract | Compact branching exists; no 200% zoom/enlarged-text assertion. |

### Registry-to-face coverage

The narrow Desk registry has eight capability rows. The following mapping is
the useful coverage check; it does not imply that the 41 voice, 11 runtime, or
17 integration capabilities are all Desk requirements.

| Registry capability | Registry status | Requirement seams | Face result |
|---|---|---|---|
| `desk.open` | built_unreleased | FR-DESK-001, FR-HOST-002 | YES/PARTLY: shell and browser fallback exist; owner release/use is unknown |
| `desk.arrange` | built_unreleased | FR-WIN-001, FR-WIN-004, NFR-PERF-002 | YES/PARTLY: geometry exists; performance proof is missing |
| `desk.inspect` | partial | FR-OBJ-001, FR-INFO-001/002 | PARTLY: inspection exists; provenance/receipt durability is incomplete |
| `desk.execute` | partial | FR-SEL-001, FR-MENU-001/003, NFR-ERR-002 | PARTLY: registry and context seams exist; callback/error matrix is incomplete |
| `desk.drop` | partial | FR-DND-001/002/003/004, NFR-A11Y-003 | PARTLY/NO: matrix and glass face exist; alternatives and multi-drop contract do not |
| `desk.persist` | built_unreleased | FR-WIN-002, NFR-REL-002/003 | YES/PARTLY: v1 load/save exists; save-failure recovery is incomplete |
| `desk.runtime` | partial | FR-STATE-001/002, NFR-REL-001/004 | PARTLY: transport state exists; stale reconciliation and disconnect guarantee do not |
| `desk.native_host` | planned | FR-WIN-005, FR-HOST-001, NFR-TEST-005 | N/A: proposed host contract only |

### SRS evidence boundary

The SRS worker inspected assertion sources and ran no tests. Root's actual Python and web runs are recorded below. No SRS row claims owner observation, measured performance or accessibility merely because a source seam exists. Registry anchors stay pinned to `675401a`; current face anchors refer to `93f9524f`.


## Proof and reproducibility

The count data, source denominators, command outputs and controlled Trust observation are recorded in [verification JSON](02-verification.json). Product source is pinned to `93f9524f`; all five workers used `gpt-5.6-luna` at `xhigh`, with disjoint scratch ownership. They did not stage, commit, flip stories, capture roadmap evidence or change product code. Root checked the material claims before reporting them.

| Check | Actual result | Retained local output |
|---|---|---|
| Reused canon scanner | 247 files, 317 candidates; no changes to scanner | `.tmp/coherence/canon.json`, `canon.md`, `canon-ranking.md` |
| Scanner/ratchet collection | 38 tests collected | `.tmp/coherence/canon-collect.log` |
| Scanner/ratchet execution | 38 passed in 1.70s | `.tmp/coherence/canon-tests.log` |
| Independent raw-control AST comparison | 233 locations; zero set differences | `.tmp/coherence/species-crosscheck.json` |
| Independent PostCSS census | 64 files; nongenerated totals reconcile for hex/family/size/z | `.tmp/coherence/css-crosscheck.json` |
| Token generated-source check | Pass | `.tmp/coherence/tokens-check.log` |
| Token gate | Pass; 11 scoped exceptions, all in use | `.tmp/coherence/tokens-gate.log` |
| Full Python suite collection | 11,417 tests collected; metal excluded | `.tmp/coherence/full-collect.log` |
| Full Python execution | 3 failed, 11,302 passed, 116 skipped, four xfailed in 1,905.13s; exit 1 | `.tmp/coherence/full-suite.log` |
| Web inherited-baseline check | 2,645 passed, zero failed/skipped; baseline-subset, zero branch-new (exit 0) | `.tmp/coherence/web-baseline.log` |
| Controlled Trust failure on glass | Same false local claim at 1440×900 and 393×852 after status 503 | `.tmp/coherence/trust-glass/proof.json` and shots below |

Commands actually used (environment isolation is described next):

```text
python3 scripts/ux_canon_scan.py --json .tmp/coherence/canon.json --md .tmp/coherence/canon.md --ranking .tmp/coherence/canon-ranking.md
uv run --extra test pytest --collect-only -q tests/unit/test_ux_canon_scan.py tests/unit/test_ux_canon_ratchet.py
uv run --extra test pytest -q tests/unit/test_ux_canon_scan.py tests/unit/test_ux_canon_ratchet.py
npm run tokens:check
npm run tokens:gate
uv run --extra test pytest --collect-only -q --ignore=tests/e2e/test_metal.py
uv run --extra test pytest -q -n auto --ignore=tests/e2e/test_metal.py
uv run python scripts/check_web_baseline.py --run
```

Every test subprocess had a new temporary HOME under this worktree, a null keyring backend and a private GitHub config path. Python dependencies, npm and Chromium caches were isolated under `.tmp/coherence`; the owner DB and microphone were not used. The controlled hub was a fresh fixture using the existing glass test harness. It loaded normal arrival before the browser intercepted `/api/setup/status` with 503; then root opened Data boundaries from its real status control. No provider call or microphone capture was needed.

Root inspected both images: `.tmp/coherence/trust-glass/trust-failed-1440.png` and `.tmp/coherence/trust-glass/trust-failed-393.png`. Both show **“All data stays on this device”**, **“Current scope / this device + external”**, and **“Enabled destinations / None.”** Image SHA-256 values and captured text are in the verification JSON. These are local, controlled corroboration shots; they are not the sibling lane's full measured acceptance walk and are not claimed as a row in the owner's real DB. The user's one-report-plus-JSON/CSV scope is preserved, so PNGs remain in scratch.

The full suite's generated evidence images are restored from a pre-run byte archive before staging, and newly generated images are parked in scratch. No moving/cleaning git verb is used. Only the report and its named tables are part of this audit change.

## Ledger

F01–F30 and the complete source tables are the homes for this census's findings. They are **inherited at the pinned base**, with class **(b)** used for checked real source defects and explicit review/K qualifiers for uncertain candidates and canon debt. In the test fallout taxonomy, **(a)** means an old-posture assertion, **(b)** a real defect, and **(c)** an unrelated failure with two serial-green runs. This documentation lane introduces no product change. The three test failures are classified separately below.

The pre-work `dw doctor` was healthy. `dw check holdspeak` returned six inherited structural errors, recorded in `.tmp/coherence/dw-check.txt`:

| Existing home | Error |
|---|---|
| `pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md` | Evidence exists while matching story is not done |
| `pm/roadmap/holdspeak/phase-152-the-hands/` | Missing final-summary.md although all stories are done |
| `pm/roadmap/holdspeak/phase-153-the-practice/` | Same missing summary |
| `pm/roadmap/holdspeak/phase-154-the-call/` | Same missing summary |
| `pm/roadmap/holdspeak/phase-156-the-front-door/` | Same missing summary |
| `pm/roadmap/holdspeak/phase-200-the-working-practice/` | Same missing summary |

The full Python suite is **not green**. Its three failures have these homes and classifications under ORCHESTRATION's fallout rule:

| Failure home | Class and evidence | Disposition in this audit |
|---|---|---|
| `tests/e2e/test_hs170_meetings_glass.py:317` | **(a), old posture assertion.** It demands a facet panel even with no open actions. `web/src/pages/cores/HistoryCore.tsx:460` intentionally hides that panel under HS-201-11; `web/src/pages/cores/history/__tests__/openActionsFacet.test.tsx:65` asserts the new empty posture, and the full web run passes. | Ledger inherited test debt; a later test-only correction must retain the case with open actions. No test changed here. |
| `tests/unit/test_phase200_canon_guard.py:353` | **(c), serial-green twice:** the parallel run observed a change in `git status --porcelain`; the same test passes in both quiet reruns. The full suite generated tracked evidence while this whole-tree fingerprint test ran. That is a likely interference mechanism, not a proved scanner write. | Preserve original failure; isolate this guard from concurrent evidence writes in a later test charter. |
| `tests/unit/test_sequence_workflow_runner_migration.py:297` | **(c), serial-green twice:** parallel run returned 502 instead of 409 after cancellation; both quiet reruns pass. The exact timing/cause was not established. | Preserve original failure and keep the cancellation seam **open with a race watch**: serial passes do not exclude a product race under load. No product fix or claim of a diagnosed cause. |

The two quiet targets were collected explicitly (**two tests**) and run serially twice in fresh isolated HOMEs: **two passed in 2.10s**, then **two passed in 1.96s**. Logs are `.tmp/coherence/quiet-collect.log`, `quiet-run.log` and `quiet-run-2.log`; the second run also used the full run's blocked external-workbench URL. These focused results do not turn the full-suite result green.

Cleanup restored **475 tracked PNGs** from the byte archive and six test-generated tracked records from their unchanged pre-audit HEAD, and parked nine new PNGs. `git diff --name-only` was empty afterward. The record is in the verification JSON.

No roadmap story is flipped and no unrelated roadmap repair is bundled. This is an atomic census document, using the gate's mechanically selected contract tier. The two supplied untracked rulebook copies are inputs, not authored outputs, and are excluded from staging.

## Amendments and unknowns

**Amendments:** the report corrects stale expected inventory counts and proposes three SRS status corrections. It changes no acceptance criterion, rulebook, product-language registry, SRS shard, token, face or product test. POSITIONING's old Home/Studio rows and the display-font/M10 conflict are recorded for resolution, not silently waived.

**Not assessed to completion:**

- **Not assessed exhaustively in §A:** U4 (one filled primary), U5 (overlap/mixed-era rooms), and A3 at every egress decision. F04 is a checked A3 counterexample; the clean file-level A9 scan is no comprehensive egress-point audit. No pass is implied for those rules.
- Full measured §B: M1–M9, M11 and M12 belong to the sibling live-walk lane. M10 here is static potential only; no computed family maximum is certified.
- A complete cold-start or populated-owner Tuesday walk; all app/pullout states on glass; viewport action bounds, contrast, touch targets, focus, reduced motion, and runtime egress receipts. The Trust fixture proves only its named failure.
- Exact runtime text for 2,684 unresolved expressions, backend-authored copy, dictionary-level ASD-STE100 conformance, or every technical term's intended meaning. Long-word and sentence records are candidates.
- Final role classification for 79 unresolved font-size records and off-interior display/icon sizes; imported/global styles do not yield a runtime per-window family count from a file total.
- Whether every possible primitive kind currently has a visible object on the owner's Desk. The no-op Open finding is conditional on such an object existing.
- Complete SRS behavior/measurement coverage where a row says PARTLY or N/A. Honest future locale/host/theme contracts are not treated as new first-use requirements.

## Check — Muad'Dib, 2026-09-20

Initial check session: `5428bdbd-d77b-48de-b66d-4ac62bff164e`. Requested model: `claude-fable-5-1`. Read-only counsel; exit 0.

### Astra response to conditions

C1 corrected F04 and the Settings narrative: settings supplies the source rows; the auxiliary read supplies stats and the snapshot boundary. A3 and the live Snapshot/no-chip seam are now explicit. C2 splits the Settings references into F04 for Meetings and F05 for System. C4 gives POSITIONING 155/157 and its contradictory line 110. C5 adds Integration/Connections/Connectors with actual face evidence and excludes the registry mirror as proof of rendering; meeting plugins remain separate. C6 names U4/U5 and exhaustive A3 checks as not assessed. C7 reconciles all three raw-button counts exactly and names the existing A1 ceiling, with chrome scope explicit.

C3 is resolved by the full non-green tail and the three named failures above. Two follow-up isolated serial runs were completed after the first check: the tree guard and cancellation test both passed twice. Their class (c) labels now meet ORCHESTRATION's explicit serial-green-twice criterion; neither cause is claimed as proved and the original full-suite failure remains visible. The Meetings failure is class (a), corroborated by the changed HS-201-11 source and the passing new-posture web assertions.

The Thought workspace is now in the executive table and F24. The checker mentioned an owner complaint from context not supplied as a primary record in this lane; this report does not repeat that complaint as verified evidence. Its hidden-content behavior remains a sibling-walk question. Models' Go alias is made explicit. The Calendar review door is now traced to Settings' Snapshot callback (`SettingsCore.tsx:1630`). Trust's stale-reopen variant is recorded in F01. The shared chrome null-egress default remains a candidate: DeskApp has explicit setup pending/failure guards, so no reachable false chrome state is claimed without tracing a counterexample.

All corrections remain report/table edits. No law, source, test, SRS status or roadmap criterion changed. The initial check below is retained verbatim, including the then-pending test state; the later evidence above supersedes only that pending state.

### Initial check, verbatim

VERDICT: RATIFY-WITH-CONDITIONS

Read-only check of `docs/internal/surface-inventory-2026-09-20/02-coherence-astra.md` and its `02-*` tables at `93f9524f`. I ran no tests, no browser and no git mutations. The Claude session id is in the caller's `.tmp/coherence/muad-check.json`.

FINDINGS

1. **F01 holds.** Tenet 3; A6, C4.
   - `web/src/desk/components/TrustWindow.tsx:61-64` swallows the failed read with `.catch(() => null)`.
   - `:66-67` turns a null trust into an empty destination list.
   - `:86-88` then prints "All data stays on this device". `:68-71` prints "this device + external", because null is not `"none"`.
   - The two lines contradict each other inside one window. The interpretation is correct.
   - One addition: `trust` is never reset on reopen. A failure after one good read shows stale data as current. This is the same class, so it needs no new row.

2. **F02 holds.** Tenet 3; A6, C4.
   - `ProjectRoomCore.tsx:282` sets the count to 0 when the state is not `ok`.
   - `:264` prints "Nothing needs you". `:732` returns null for the section.
   - Every `state !== "ok"` branch in the file returns null (`:732`, `:923`, `:1131`, `:1175`, `:1920`). None paints the degraded state.
   - The decoder at `model.ts:554` keeps the degraded state. The fault is in the face only.

3. **F03 holds as a conditional finding.** Tenet 3.
   - `verbRegistry.ts:381-393` gates Open on selection only.
   - `compositorSlice.ts:163` has `case "none": break`.
   - `primitives.ts:572`, `:594` and `:650` declare `none` for game, story and layout.
   - The "conditional object" label is the right level of caution.

4. **F04 has the right anchor and the wrong wording.** A3, A6; Tenet 3.
   - The source list renders from `data._calendar_sources` (`SettingsCore.tsx:1414`), not from the failed fetch.
   - The `/api/calendar/sources` read at `:814-816` has no catch and no loading state.
   - When that read is missing, three things fall back:
     - the per-source stats (`:1416`, `:1537`);
     - `auto_record` and the lead minutes (`:1654-1663`);
     - the snapshot egress chip (`:1611`).
   - The list itself does not fall back to empty. See MISSED 1.

5. **F05 holds.** `SettingsCore.tsx:580` is `if (loading) return null`. Tenet 3.

6. **F06, F07, F08 and F21 hold.** Tenet 4.
   - F06: `LiveCore.tsx:340` has `label="Intelligence"`. `MeetingSummarySlab.tsx:52` has `SUMMARY`.
   - F07: `NeedsYouTable.tsx:101-110` has "Run summary" and "Retry". `DoorSection.tsx:127-129` has "Retry intelligence" and "Retry background work".
   - F07 also breaks the registry's own rule that every face says Summary (`product-language.json:23`). That strengthens the row.
   - F08: `ChainPullout.tsx:45` has `actionLabel="Edit chain"`.
   - F21: `LiveCore.tsx:662` and `RoomPeopleSection.tsx:150-152` hold SEG and MTG.

7. **F10 holds, with a loose anchor.**
   - `POSITIONING.md:153` is the table head. The rows are `:155` (Home) and `:157` (Studio).
   - `POSITIONING.md:110` already says "there is no Studio". The document contradicts itself, which is stronger than "stale".

8. **The counts reconcile with the tables.** Tenet 5.
   - `02-raw-controls.csv` has 233 rows: 187 button, 32 input, 8 textarea, 3 select, 3 role=button.
   - Its classes are 176 face violation, 40 library, 7 sanctioned and 10 needs-reading.
   - `02-srs-parity.csv` has 63 rows: 17 YES, 26 PARTLY, 7 NO, 13 N/A.
   - Its SRS statuses are 23 IMPLEMENTED, 10 PARTIAL, 13 SPEC-DEBT and 17 UNIMPLEMENTED.
   - `02-surface-rules.csv` has 229 rows, which matches the TSX count.

9. **The raw-button debt already has a home in canon, and the report does not say so.**
   - `UX-CANON.md:136-142` holds A1 to a dated, down-only ratchet of 175 (HS-200-44).
   - The report gives 187, 175 and 157 and says "different scope". It does not reconcile the three numbers, and it calls F12–F20 "their own ledger home".
   - A reader could take this as 176 new debts.
   - Dock, DeskWindow and DeskMenu are the Workbench chrome (F15, 14 sites in total), not a face in the sense of `UX-CANON.md:19-21`. Classing them as species bugs is lawful. Ranking them with job faces is a judgement, so label it as one.

10. **The report's caution is sound.**
    - It keeps the static-versus-glass distinction, the "blank is not a pass" note, and the scanner's A9 caveat.
    - It states the M10 seam against `DESIGN_SYSTEM.md:325` and refuses to downgrade SRS rows for lack of a trace.
    - No tenet fails in the method. No fix is authorized, which is lawful for an audit.

CONDITIONS (smallest corrections; none changes the verdict's direction)

- **C1 — F04 text.**
  - Replace "an unread source list falls back to empty" with "source stats, auto-record state and the snapshot egress chip fall back silently; the source list itself comes from the settings payload".
  - Add rule A3 to the row.
- **C2 — Settings table.**
  - `setting:meetings` cites "F04/F05". Make it F04.
  - `setting:system` cites "F04/F05". Make it F05.
- **C3 — Full-suite accounting.**
  - The "Full Python execution" row and the ledger's pending sentence must carry the final tail and the named failures before staging.
  - Make no green claim and no flake class. Once that is recorded, I do not need a second look.
- **C4 — F10 anchor.** Cite `POSITIONING.md:155` and `:157`, and add `:110`.
- **C5 — Noun collision table.** Add the Integration row from MISSED 3. This plane is the lane's core mandate, and one face name is absent.
- **C6 — "Not assessed" list.**
  - Rulebook §A rules U4, U5 and A3 have no plane in the report, and neither does any per-egress-point check. Name them as not assessed.
  - Without that line, a reader takes silence as a pass.
- **C7 — Species reconciliation.** Add one sentence to Plane 1 that reconciles 187, 175 and 157 and names the existing A1 ratchet (`tests/ux_canon_ceiling.json`) as the prior home.

MISSED (ranked by cost to the owner)

1. **The egress badge disappears beside an egress verb.** A3; the owner's hard boundary; Tenet 3.
   - `SettingsCore.tsx:1611` paints the snapshot egress chip only when `calSources?.snapshot_egress` resolves.
   - `snapshotEgressChip` at `:156-166` also returns null for a non-local scope with an empty host.
   - The upload button at `:1618` stays live in every case.
   - A pending or failed read, or a missing host, gives a cloud upload with no badge before the click.
   - The report's A9 caveat predicted this class. This is the concrete instance.
2. **The owner's only real-use datum is not in the executive view.**
   - On 2026-09-20 he said of the Thought window: "hides things; doesn't look good".
   - `thought-workspace/ThoughtWorkspaceWindow.tsx` is in the CSV: A7, D1, D2, and 62 direct CSS literal records. That is the largest per-face literal count I saw.
   - It is absent from the executive matrix and from the Top 30.
   - The hiding belongs to the sibling lane (M2, M4). This lane should still list the row and point to it.
   - A top 30 "by owner cost" that omits the one face he bounced is ranked on judgement alone. Tenets 2 and 7.
3. **Integration has three face names.**
   - The registry noun is Integration (`product-language.json:95`).
   - Faces say "Connections" at `applications.ts:421`, `settingsPrefs.tsx:57` and `:464`.
   - `ActivityCore.tsx:230` says "Connectors".
   - In the noun CSV, the "observed" evidence for Integration includes `lib/productLanguage.ts:31`. That file is the registry mirror, not a face.
   - The canonical word renders on about one face (`DeliveryBoard.tsx:329`). The report marks this "scope review only". C2, U6; Tenet 4.
4. **The chrome egress badge has the same default as F01.**
   - `web/src/desk/setup.ts:99-135`: `egressBadge(null)` returns "⌂ This device".
   - That feeds the always-visible chip at `DeskChrome.tsx:150` and `:254`.
   - If the chrome can render with `setup === null`, the false all-clear is on every screen, not in one window.
   - The report's own note on `DeskApp.tsx:110` suggests chrome is held while setup is pending. I did not trace that, so this is a candidate. A6.
5. **Four doors open one face, and one door has the wrong name.** Tenet 3; C2, C3.
   - "Models" is an application label twice (`applications.ts:304`, `:412`).
   - The Settings modules Models and Assignments both redirect to Concierge (`SettingsCore.tsx:1803-1811`).
   - "Desk memory" (`applications.ts:285`) opens the Project Room.
   - The reachability table has the facts. No finding draws the conclusion.
6. **One unhandled rejection and one swallowed failure for the sibling lane (M9).**
   - `SettingsCore.tsx:815` has a `.then` with no catch, which gives an unhandled rejection on failure.
   - `TrustWindow.tsx:64` swallows the failure silently.

TUESDAY: Not yet. A tired owner would get two false all-clears (Trust and the Room's needs-you section) and one upload with no egress badge, and he would have to learn four names for two things. The report says this honestly, and its verdict of "not yet established" is correct.

UNKNOWN

- I did not open the glass shots or `02-verification.json`. The Trust 503 reproduction is accepted on root's word together with my source reading.
- I did not re-derive the CSS and token counts (4,191 records; 474 off-scale) or the 6,670 language rows.
- I sampled the reachability rows against `applications.ts` labels only. I did not trace all 42 dispatch chains.
- I did not verify whether `setup` can be null while the chrome is painted (MISSED 4).
- I did not check whether any game, story or layout object exists on the owner's Desk.
- I did not verify the five Luna workers' rollouts (model and effort).
- The full Python suite result is pending. C3 governs it.

### Checker reply

VERDICT: RATIFY

This verdict covers committing the report and its `02-*` tables only. It does not cover merging, accepting any product work, or authorizing any fix. This is round two of the read-only check of `docs/internal/surface-inventory-2026-09-20/02-coherence-astra.md` at `93f9524f`, continuing session `5428bdbd-d77b-48de-b66d-4ac62bff164e`. I ran no tests and made no edits.

FINDINGS

1. **C1 is closed.** Tenet 3; A3, A6.
   - F04 (report line 116) now says that stats, auto-record state and the snapshot egress chip fall back silently, and that the source list comes from the settings payload.
   - A3 is on the row and `SettingsCore.tsx:156` is added as an anchor. This matches the source I read.

2. **C2 is closed.**
   - `setting:meetings` cites F04 (line 403) and `setting:system` cites F05 (line 408).
   - The application row at line 342 keeps "F04/F05". That is correct, because both modules are gaps inside Settings.

3. **C4 is closed.** F10 (line 122) and the collision table (line 272) cite `POSITIONING.md:155`, `:157` and the contradiction at `:110`.

4. **C5 is closed.** Tenet 4; C2, U6.
   - Line 274 adds Integration, Connections and Connectors with the face anchors: `DeliveryBoard.tsx:329`, `applications.ts:421`, `settingsPrefs.tsx:57` and `ActivityCore.tsx:230`.
   - It says that a registry-mirror string is not proof of rendering. Meeting plugins stay a separate concept, which is correct.
   - `02-nouns.csv` now has 129 data rows, as the report says.

5. **C6 is closed.**
   - Line 600 names U4, U5 and A3 at every egress decision as not assessed exhaustively.
   - It gives F04 as the checked counterexample and says no pass is implied.

6. **C7 is closed.** Tenet 5.
   - The arithmetic holds: 187 = 157 consumer + 24 library + 6 preview, and 175 = 187 − 1 − 5 − 6.
   - The A1 ceiling is named as the existing home. Line 109 now calls F-rows "audit references", not new ledger homes.

7. **C3 is closed.**
   - Line 542 has the real tail: 3 failed, 11,302 passed, 116 skipped, 4 xfailed, exit 1.
   - The report says "not green" in plain words.

8. **The class (a) failure is verified at source.**
   - `tests/e2e/test_hs170_meetings_glass.py:317` demands that `meetings-facets` is visible without condition.
   - `HistoryCore.tsx:460-465` draws it only when `openActionsFacetDrawn` is true (HS-201-11).
   - `openActionsFacet.test.tsx:67` asserts the new empty posture. The classification is correct.
   - The failure was introduced on my side of the house: HS-201-11 is one of the Phase 201 stories I recorded in session memory as merged with main green, and its e2e test was not updated. I take it as debt. See MISSED 1.

9. **The flake class is accepted.**
   - My first-round condition said "no flake class" because at that time no repeated evidence existed. It was not meant to override the law.
   - Two fresh-HOME serial runs were green (2 passed in 2.10s, then 2 passed in 1.96s). That meets the ORCHESTRATION criterion, so class (c) is lawful.
   - The report leaves both causes unproven and keeps the full-suite result red. That is the honest reading.
   - One reservation is in MISSED 2.

10. **The owner-quote handling is accepted.**
    - My first-round evidence for that point was memory, not a record in the tree. Astra was right not to repeat it as verified.
    - ThoughtWorkspaceWindow is now in the executive matrix (line 105) and in F24, and the hiding question is sent to the sibling M2/M4 lane. That is enough.
    - The chrome null-egress default remains a candidate behind the `DeskApp` guards. That position is sound, because I did not trace a counterexample either.

11. **Staging scope is clean.**
    - The tracked diff is empty.
    - Only `docs/internal/surface-inventory-2026-09-20/` and the stray `docs/internal/00-rulebook.md` are untracked under `docs/`.
    - The new `02-dom-portals.csv` has 8 data rows (1 imperative file input and 7 portal calls). It is a separate supplement and is not mixed into the 233 count.

CONDITIONS: none. There is one staging instruction. It does not change the verdict.
- Use explicit paths only.
- Leave `docs/internal/00-rulebook.md` (the duplicate) and the 9 parked PNGs out.
- Whoever owns the rulebook decides separately whether `00-rulebook.md` inside the folder ships.

MISSED (ranked by cost to the owner)

1. **Main is red on `test_hs170_meetings_glass.py`, and it has been since the HS-201-11 merge.**
   - The audit found this and classified it correctly, but it has no fix story yet.
   - It needs a test-only correction that keeps the open-actions case. This is my lane's debt to pay.
2. **The cancellation 502-versus-409 failure is the (c) most likely to be a real defect.**
   - The test is `test_sequence_workflow_runner_migration.py:297`.
   - Two serial-green runs cannot rule out a product race that appears only under load.
   - Record it as (c) with a watch, and do not close it. The owner cancels runs.
3. **The tree guard at `test_phase200_canon_guard.py:353` will keep failing under parallel runs.**
   - The suite rewrites hundreds of tracked PNGs while the guard fingerprints the tree.
   - Every future `-n auto` run is likely to show this red, and that teaches people to ignore red.
   - The report names the mechanism as likely. It deserves a small test charter soon.
4. **MISSED 4 to 6 from round one stand as candidates.**
   - They are the chrome badge default, the four doors into Concierge together with "Desk memory" opening the Room, and the unhandled rejection at `SettingsCore.tsx:815`.
   - Astra's response addresses the first two. No further correction is needed for an audit.

TUESDAY: Still not yet, and the report still says so. Nothing in the corrections changes the product. The corrections make the record of the product's state accurate.

UNKNOWN

- I did not open `quiet-run.log`, `quiet-run-2.log`, `full-suite.log` or the restored-PNG byte archive. I accept the run results and the "475 tracked PNGs and 6 test records restored" claim on the strength of the empty tracked diff I observed and on root's word.
- I did not re-derive the CSS and language counts or all reachability chains. That is unchanged from round one.
- I did not verify the Luna rollouts.
- I did not check whether the link to `02-dom-portals.csv` renders in the report. I confirmed the file and its row count, not the link text.
