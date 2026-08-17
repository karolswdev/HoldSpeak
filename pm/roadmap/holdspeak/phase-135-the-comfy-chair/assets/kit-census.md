Now I have comprehensive data. Here is the full report.

---

## HOLDSPEAK WEB DESIGN SYSTEM / COMPONENT KIT -- STRUCTURAL CENSUS

HEAD `d4acbbe7` (main, clean). React+Vite desk-first. Dark-only "Signal Workbench" material model (Phase 110).

---

### 1. KIT INVENTORY

**Where the design system lives:**

| Directory | Role |
|---|---|
| `web/design-tokens.json` (1185 lines) | Source of truth for all tokens |
| `web/scripts/generate-tokens.cjs` (240 lines) | Token generator: JSON to CSS |
| `web/src/styles/tokens.css` (331 lines, GENERATED) | Three-layer CSS custom properties |
| `web/src/styles/global.css` (635 lines) | Reset, base controls, button `.btn`, `.desk-chip`, `.hs-field`, scrollbars, materialize animation, empty-state `.empty-well` |
| `web/src/styles/react-app.css` (414 lines) | Legacy route shell styles (`.signal-panel`, `.welcome-*`, `.presence-*`) -- 29 legacy class selectors |
| `web/src/desk/desk-tokens.css` (6 lines) | Convenience re-export of tokens.css |
| `web/src/lib/tokens.gen.ts` (43 lines, GENERATED) | TS mirror of z-indexes, window physics, glow pool |
| `web/src/components/signal/Signal.tsx` (132 lines) | Base controls: Button, Field, TextInput, TextArea, Select, Panel |
| `web/src/desk/surface/` (11 files, ~6900 lines) | **The surface kit** -- the ONE way to build window content |
| `web/src/desk/components/` (~60 files, ~22600 lines) | DeskWindow, DeskMenu, Pullout, MicButton, chrome, window subsystem |

**Token layer (272 CSS custom properties on `:root`):**

| Category | Count | Examples |
|---|---|---|
| Color | ~60 primitives + ~50 semantic + ~30 component | `--p-color-ink-0` through `--glow-directory`, full accent/ok/warn/danger/info families |
| Spacing | ~16 | `--space-1` through `--space-8`, desk window/surface padding tokens |
| Typography | ~20 | 3 font families (display/ui/mono), 7 size steps, 3 line heights, 5 letter-spacings, display/primary type tokens |
| Depth | ~25 | `--elev-0` through `--elev-4`, `--desk-z-canvas` through `--desk-z-popover`, bevels, etches |
| Border/Radius | ~10 | `--border`, `--border-strong`, `--radius-xs` through `--radius-pill` (all 2px -- the Workbench contract) |
| Motion | ~10 | `--duration-micro` through `--duration-slow`, `--ease-standard/emphasized/decelerate/quart/expo/back` |
| Focus | ~3 | `--focus-ring`, `--focus-outline-width`, `--focus-outline-offset` |
| Sound | **0** | No sound tokens exist anywhere. |
| Reduced-motion | 1 media query block | `tokens.css:314-331` -- zeroes all durations and kills all animations |

**Component inventory (reusable primitives):**

| Component | Path | ~Lines | Job |
|---|---|---|---|
| **Button** | `components/signal/Signal.tsx:21` | 25 | Verb button (4 variants: primary/secondary/ghost/danger) |
| **Field** | `components/signal/Signal.tsx:47` | 37 | Label+input+hint+error wrapper |
| **TextInput/TextArea/Select** | `components/signal/Signal.tsx:85-105` | 20 | Legacy native inputs (kept for InlineEditor cluster) |
| **Panel** | `components/signal/Signal.tsx:107` | 25 | Document-shell card (non-desk routes) |
| **DeskWindow** | `desk/components/DeskWindow.tsx` | 936 | THE window: drag, resize, snap, minimize, close, bevel, spring animation (motion/react) |
| **DeskMenu** | `desk/components/DeskMenu.tsx` | 463 | Context menus (Work menu, floor menu) |
| **DeskMenuBar** | `desk/components/DeskMenuBar.tsx` | 116 | System menu bar |
| **DeskToolShelf** | `desk/components/DeskToolShelf.tsx` | 557 | Cmd-K command deck |
| **DeskSortableTable** | `desk/components/DeskSortableTable.tsx` | 212 | Dense table with sort, selection, groups, row actions, roving |
| **DeskListView** | `desk/components/DeskListView.tsx` | 327 | Semantic list mode for the desk floor |
| **DeskEditor** | `desk/components/DeskEditor.tsx` | 389 | CodeMirror rich-text editor |
| **DeskComposer** | `desk/components/DeskComposer.tsx` | 64 | Chat/input composer bar |
| **DeskChrome** | `desk/components/DeskChrome.tsx` | 253 | System chrome band (menus, launchers) |
| **DeskFilingStrip** | `desk/components/DeskFilingStrip.tsx` | 224 | Tab strip for filing/navigating primitives |
| **Pullout** | `desk/components/Pullout.tsx` | 93 | Side panel container (spatial origin) |
| **MicButton** | `desk/components/MicButton.tsx` | 430 | Voice mic (click-to-toggle, speak-to-fill) |
| **RecordOrb** | `desk/components/RecordOrb.tsx` | 89 | Recording orb indicator |
| **InlineEditor** | `desk/components/InlineEditor.tsx` | 54 | In-place rename editor |
| **InletAutocomplete** | `desk/components/InletAutocomplete.tsx` | 350 | @-reference autocomplete for inlet |
| **AttentionDrawer** | `desk/components/AttentionDrawer.tsx` | 309 | Attention/admission drawer |
| **SystemShade** | `desk/components/SystemShade.tsx` | 285 | System shade overlay (ask, recording) |
| **AgentAvatar** | `desk/components/AgentAvatar.tsx` | 51 | Agent/persona avatar (sprite-based) |
| **EmptyDesk** | `desk/components/EmptyDesk.tsx` | 77 | Empty desk state |
| **GlassDropLayer** | `desk/components/GlassDropLayer.tsx` | 150 | Drag-and-drop feedback layer |
| **TrustWindow** | `desk/components/TrustWindow.tsx` | 148 | Trust/consent surface |
| **WhyControl** | `desk/components/WhyControl.tsx` | 42 | Explain-why toggle |
| **ReceiptLine** | `desk/components/ReceiptLine.tsx` | 28 | Session receipt display |
| **EditorAIBar** | `desk/components/EditorAIBar.tsx` | 213 | AI proposal accept/reject bar |
| **PersonaChat** | `desk/components/PersonaChat.tsx` | 379 | Agent chat conversation |
| **AskPanel** | `desk/components/AskPanel.tsx` | 601 | Ask/query panel with grounding |
| **Dock** | `desk/components/window/Dock.tsx` | 287 | Window dock (minimized chips) |
| **Expose** | `desk/components/window/Expose.tsx` | 151 | Window expose/overview |
| **Switcher** | `desk/components/window/Switcher.tsx` | 57 | Window switcher |
| **SnapGhost** | `desk/components/window/SnapGhost.tsx` | 42 | Snap target preview |
| **ShortcutSheet** | `desk/components/window/ShortcutSheet.tsx` | 63 | Keyboard shortcut help |
| **Surface sub-kit:** | | | |
| SurfaceVerbs | `desk/surface/Surface.tsx:26` | 14 | Sticky verb bar |
| SurfaceSection | `desk/surface/Surface.tsx:44` | 24 | Group with hairline + label |
| SurfaceRow | `desk/surface/Surface.tsx:76` | 65 | Dense row (title, detail, meta, verbs) |
| SurfaceState | `desk/surface/Surface.tsx:141` | 80 | Loading/empty/error state |
| SurfaceColumns | `desk/surface/Surface.tsx:223` | 18 | Two-column layout |
| SurfaceSplit | `desk/surface/Surface.tsx:242` | 24 | Master-detail pane |
| MetricStrip | `desk/surface/Surface.tsx:267` | 20 | Labeled figures strip |
| SurfaceFacts | `desk/surface/Surface.tsx:288` | 42 | Key-value facts |
| SurfaceCode | `desk/surface/Surface.tsx:331` | 8 | Code block |
| SurfaceWell | `desk/surface/Surface.tsx:340` | 44 | Sunken content well |
| PaneWell | `desk/surface/Surface.tsx:385` | 72 | Terminal/xterm pane well |
| SurfaceTraffic | `desk/surface/Surface.tsx:458` | 26 | Traffic/conversation thread |
| SurfaceTrafficTurn | `desk/surface/Surface.tsx:485` | 36 | Individual turn in thread |
| SurfaceGroup | `desk/surface/Surface.tsx:522` | 17 | Grouping wrapper |
| SurfaceSettingRow | `desk/surface/Surface.tsx:540` | 27 | Settings row |
| SurfaceToggle | `desk/surface/Surface.tsx:568` | 24 | Toggle switch row |
| SurfaceStream | `desk/surface/Surface.tsx:593` | 26 | Timeline stream |
| SurfaceStreamDay | `desk/surface/Surface.tsx:620` | 14 | Day header in stream |
| SurfaceStreamEntry | `desk/surface/Surface.tsx:635` | 41 | Entry in stream |
| SurfaceLedger | `desk/surface/Surface.tsx:677` | 30 | Tabular ledger with roving |
| SurfaceLedgerRow | `desk/surface/Surface.tsx:708` | 64 | Ledger row |
| SurfaceLibrary | `desk/surface/Surface.tsx:773` | 36 | Tile grid library |
| SurfaceLibraryTile | `desk/surface/Surface.tsx:810` | 37 | Individual tile |
| SurfaceBay | `desk/surface/Surface.tsx:878` | 84 | Labeled bay with rail/actions |
| EditInPlace | `desk/surface/Surface.tsx:963` | 124 | In-place text editor |
| ConfirmVerb | `desk/surface/Surface.tsx:1088` | 40 | Two-press confirm button (no modal) |
| **Gadget sub-kit:** | | | |
| GadgetGroup | `desk/surface/gadgets.tsx:26` | 13 | Engraved settings group |
| GadgetRow | `desk/surface/gadgets.tsx:44` | 34 | Label+control row |
| CheckGadget | `desk/surface/gadgets.tsx:79` | 30 | Checkbox gadget |
| CycleGadget | `desk/surface/gadgets.tsx:117` | 43 | Cycle-through-options |
| MxRadio | `desk/surface/gadgets.tsx:168` | 48 | Mutually-exclusive radio |
| StringGadget | `desk/surface/gadgets.tsx:217` | 56 | Text input gadget |
| PadGadget | `desk/surface/gadgets.tsx:274` | 64 | Multi-line text gadget |
| FoldGadget | `desk/surface/gadgets.tsx:339` | 49 | Collapsible section |
| StepperGadget | `desk/surface/gadgets.tsx:389` | 57 | Numeric stepper |
| PropGadget | `desk/surface/gadgets.tsx:447` | 35 | Read-only property display |
| GadgetTable | `desk/surface/gadgets.tsx:483` | 86 | Editable data table |
| LedMeter | `desk/surface/gadgets.tsx:570` | 44 | Segmented level meter |
| LampGadget | `desk/surface/gadgets.tsx:615` | 21 | Status lamp indicator |
| TransportKey | `desk/surface/gadgets.tsx:637` | 49 | Instrument key (play/stop/record) |
| TransportRow | `desk/surface/gadgets.tsx:687` | 5 | Transport controls row |
| EgressChip | `desk/surface/gadgets.tsx:693` | 45 | Egress badge (privacy) |
| SecretRow | `desk/surface/gadgets.tsx:739` | ~40 | Secret/password row |
| **Other surface kit:** | | | |
| Material | `desk/surface/Material.tsx` | 112 | Markdown-to-React document renderer |
| SurfaceFooter | `desk/surface/SurfaceFooter.tsx` | 28 | Footer with foot slot |
| foot | `desk/surface/foot.tsx` | 5 | Foot slot component |
| wings | `desk/surface/wings.tsx` | 124 | Wing annotations |
| citations | `desk/surface/citations.tsx` | 55 | Citation links |
| XtermPane | `desk/surface/XtermPane.tsx` | 190 | xterm.js terminal pane |
| LedgerFilter | `desk/surface/LedgerFilter.tsx` | 153 | Search/filter for ledgers |
| roving | `desk/surface/roving.ts` | 174 | Roving tabindex focus hook |
| format | `desk/surface/format.ts` | 100 | Time/value formatting |
| **Error surface:** | | | |
| ErrorBoundary | `components/ErrorBoundary.tsx` | 42 | Route-level error boundary (uses SurfaceState) |

---

### 2. COVERAGE MAP

Method: counted imports from `desk/surface/`, `desk/components/`, and `components/signal/` per room file vs total imports. Pullouts were separately checked.

| Room / Surface | Kit imports | Total imports | Kit fraction | Notes |
|---|---|---|---|---|
| **Desk floor** (DeskApp, world, GL) | N/A -- IS the kit | N/A | ~100% | The kit defines the desk |
| **WorkbenchWindow** | heaviest consumer | 1979 lines | ~85% | Imports surface, gadgets, Signal; some bespoke workbench-config.css (584 lines) |
| **MissionControl** | embedded | 689+738 lines | ~70% | Has 738 lines of bespoke `mission-control.css` |
| **Settings** (SettingsCore) | 3 kit / 13 total | 927 lines | ~60% | Large, but gadgets imported via settingsPrefs/settingsModels which heavy-use the kit |
| **settingsPrefs** | 3/6 | 456 lines | ~80% | Almost entirely GadgetRow/GadgetGroup |
| **settingsModels** | 2/7 | 584 lines | ~70% | GadgetTable + GadgetRow |
| **LiveCore** (meetings live) | 6/15 | 717 lines | ~70% | SurfaceState, SurfaceSection; imports from multiple kit layers |
| **HistoryCore** (meeting history) | 4/13 | 354 lines | ~75% | Heavy kit use in sub-files (ArtifactsLibrary, CatalogRail etc.) |
| **History sub-files** (14 files) | avg 2/file surface | ~3000 lines | ~80% | Nearly all import from surface; SurfaceRow/Section/State/Ledger/etc |
| **DictationCore** (speak) | 0/8 | 137 lines | ~50% | Thin wrapper; sub-files (14 files in dictation/) heavy-use surface |
| **Dictation sub-files** | avg 2/file surface | ~2200 lines | ~75% | SurfaceSection/Row/State/FoldGadget |
| **CompanionCore** | 7/13 | 201 lines | ~85% | Kit-heavy |
| **ProjectMemoryCore** | 8/16 | 754 lines | ~85% | Heaviest core kit consumer |
| **ActivityCore** | 4/11 | 257 lines | ~80% | |
| **CadenceCore** | 4/12 | 206 lines | ~80% | |
| **CommandsCore** | 3/11 | 314 lines | ~70% | |
| **ProcessCore** | 4/9 | 182 lines | ~80% | |
| **WorkbenchesHome** | 5/12 | 178 lines | ~80% | |
| **SetupCore** | 4/11 | 173 lines | ~80% | |
| **ConstitutionalContext** | 3/7 | 193 lines | ~75% | Has own 30-line CSS |
| **Pullouts** (12 pullout files) | ALL import from surface | ~2000 lines | **~95%** | Every pullout uses SurfaceFooter, most use SurfaceRow/State/Material; also DeskFilingStrip, MicButton, AgentAvatar from components |
| **Pullout editors** (4 files) | surface+components | ~645 lines | ~85% | NoteEditor/KbEditor/RecipeEditor/WorkflowEditor |
| **Intelligence views** (3 files) | surface | ~815 lines | ~85% | BriefView/DecisionsView/FollowThroughView |
| **Meetings recovery** (2 files) | Signal+surface+gadgets | 376 lines | ~90% | |
| **Delivery windows** | surface+components | ~1000 lines | ~80% | DeliveryBoard, DeliveryDossierWindow, DeliveryTerminalWindow |
| **WelcomePage** | 0/3 | thin | 0% (legacy) | Uses react-app.css `.welcome-*` classes |
| **PresencePage** | 0/2 | thin | 0% (legacy) | Uses react-app.css `.presence-*` classes |

**Worst bespoke offenders:**

1. `desk/components/workbench-config.css` -- 584 lines of bespoke CSS for workbench configuration panel
2. `desk/components/mission-control.css` -- 738 lines bespoke for MissionControl
3. `desk/surface/surface.css` -- 2392 lines (this IS the kit's CSS, but includes much layout-specific px work)
4. `desk/components/chrome-menus.css` -- 775 lines (chrome/chip/menu styling -- partially kit, partially one-off)
5. `desk/components/attention.css` -- 539 lines for the attention drawer
6. `styles/react-app.css` -- 414 lines of legacy pre-desk route styles (29 legacy selectors still alive)

---

### 3. GAP ANALYSIS: CAN IT BUILD NEARLY ANYTHING?

| Capability | Status | Evidence / What is missing |
|---|---|---|
| **Layout: split panes** | EXISTS | `SurfaceSplit` at `Surface.tsx:242` -- master-detail that collapses on narrow containers |
| **Layout: two-column** | EXISTS | `SurfaceColumns` at `Surface.tsx:223` -- main+side |
| **Layout: resizable regions** | PARTIAL | DeskWindow resizing exists (`DeskWindow.tsx:34`, `window-chrome.css:40-64`); no generic resizable-panel primitive for split-pane drag handles within a window |
| **Layout: grid** | PARTIAL | `SurfaceLibrary` tile grid exists (`Surface.tsx:773`); no generic CSS grid layout primitive |
| **Data: virtualized lists** | ABSENT | `DeskListView.tsx:27` explicitly says "no virtualization dep" -- uses plain "show more" pagination at 100 rows |
| **Data: sortable tables** | EXISTS | `DeskSortableTable.tsx` -- sort, selection, groups, row actions, roving focus, accessible row labels |
| **Data: meters/charts** | PARTIAL | `LedMeter` (segmented level meter, `gadgets.tsx:570`); no general charting/sparkline/dataviz |
| **Input: full form kit** | EXISTS | GadgetGroup/GadgetRow + CheckGadget/CycleGadget/MxRadio/StringGadget/PadGadget/StepperGadget/PropGadget/SecretRow -- comprehensive |
| **Input: validation display** | EXISTS | `Field` in `Signal.tsx:47` has error + description slots; `StringGadget` has inline feedback |
| **Input: combobox/pickers** | PARTIAL | `InletAutocomplete` (`desk/components/InletAutocomplete.tsx`, 350 lines) for @-references; `RailsPicker` (182 lines), `RunsOnPicker` (94 lines), `WorkbenchTemplatePicker` (148 lines) -- but no generic combobox/select primitive |
| **Input: date/time** | ABSENT | No date picker or time picker exists. Native `<input type="date">` would inherit the control styling at `global.css:83` but no kit component wraps it |
| **Feedback: progress** | PARTIAL | `WorkbenchWindow.tsx:928` has ad-hoc `runProgress` state; no reusable progress bar component |
| **Feedback: skeletons** | ABSENT | `Signal.tsx:2` explicitly says Skeleton was retired in the gadget-kit sweep |
| **Feedback: empty states** | EXISTS | `SurfaceState` at `Surface.tsx:141` handles loading, empty (with label), and error; `global.css:468` has `.empty-well` |
| **Feedback: error surfaces** | EXISTS | ErrorBoundary (`ErrorBoundary.tsx`), SurfaceState error mode, `.hs-field-error` -- errors render in-flow per the standing rule |
| **Overlay: menus** | EXISTS | `DeskMenu.tsx` (463 lines) with ghosted items, dismiss on outside click/Escape |
| **Overlay: palettes** | EXISTS | `DeskToolShelf.tsx` (557 lines) -- cmd-K palette with ranked search |
| **Overlay: NO modals** | CORRECT | No `<dialog>` or modal usage anywhere in production code. Every modal reference is a comment saying "never a modal" -- the rule is strictly observed |
| **In-world editing** | EXISTS | `EditInPlace` (`Surface.tsx:963`), `InlineEditor.tsx`, editors in pullouts/windows |
| **Motion/animation** | EXISTS | motion/react (framer-motion) for DeskWindow springs; CSS @keyframes for chip-in/shade-drop/materialize; duration+easing tokens; prefers-reduced-motion respected everywhere |
| **Density modes** | PARTIAL | `@container surface` queries (32 total) adapt to window width; no explicit user-toggled density mode |
| **Keyboard/focus: roving** | EXISTS | `roving.ts` (174 lines) -- ArrowUp/Down/Home/End/PageUp/PageDown, type-ahead, re-anchoring on click. Used in SurfaceLedger, GadgetTable |
| **Keyboard/focus: rings** | EXISTS | `global.css:62-66` -- `:focus-visible` with `--focus-outline-width` solid `--accent` everywhere; `tokens.css:203` defines `--focus-ring` |
| **Keyboard: keymap** | EXISTS | `keymap.ts` -- single document-level keydown binder, reads from verb registry |
| **Scrollbars** | EXISTS | `global.css:577-610` -- always-visible styled scrollbars using tokens |

---

### 4. CONSISTENCY DEBT

**Same visual job, two+ implementations:**

| Job | Pattern A | Pattern B | Evidence |
|---|---|---|---|
| **Buttons** | `.btn` class (Signal `Button`, 4 variants) -- `global.css:128` | `.desk-chip` class (205 uses) -- `chrome-menus.css:175` | Two complete button systems. `Button` uses `.btn--primary/secondary/ghost/danger`. `.desk-chip` is the desk-era chip with bevels. Signal.tsx:1-7 documents the split: "Button = verb, TransportKey = momentary instrument." |
| **Buttons (third)** | `.gadget-transport-key` -- `gadgets.css:669` | (above two) | Three distinct button faces total. TransportKey is documented as deliberate: instrument control vs verb |
| **List rows** | `SurfaceRow` (`Surface.tsx:76`) with class `.surface-row` (69 uses) | `SurfaceLedgerRow` (`Surface.tsx:708`) with class `.surface-ledger-row` (117 uses) | Two row systems. Justified: SurfaceRow is for single-line rows; SurfaceLedgerRow is for tabular ledger rows. But the CSS is not shared |
| **Panels/cards** | `.signal-panel` (`react-app.css:70`) | `SurfaceSection` (`Surface.tsx:44`) | Legacy Panel vs desk SurfaceSection. Panel is documented as "non-desk routes" only |
| **Tables** | `DeskSortableTable` (`DeskSortableTable.tsx`) | `GadgetTable` (`gadgets.tsx:483`) | Two table components. Justified: DeskSortableTable for data display; GadgetTable for editable settings |
| **Input fields** | `StringGadget` / `PadGadget` (new gadget kit) | `TextInput` / `TextArea` (legacy Signal) | Signal.tsx:8-9 documents this: legacy kept "ONLY for the InlineEditor native cluster" |

**Hardcoded px values bypassing spacing tokens (worst files):**

| File | px instances | var(--) instances | Ratio |
|---|---|---|---|
| `surface.css` | 304 | 354 | 0.86:1 -- many px values for specific layout geometry (padding, margins, widths) |
| `gadgets.css` | 181 | (embedded in 973-line file) | High px density for precise gadget dimensions |
| `chrome-menus.css` | 142 | 148 | ~1:1 |
| `attention.css` | 110 | (in 539 lines) | Bespoke attention geometry |
| `mission-control.css` | 108 | (in 738 lines) | MissionControl-specific layout |
| `workbench-config.css` | 98 | (in 584 lines) | Workbench config panel |
| `window-chrome.css` | 87 | 140 | 0.62:1 |

Note: the token layer defines `--space-1` through `--space-8` plus desk-specific spacing (`--desk-window-pad-x/y`, `--desk-surface-row-h`, etc.), but most layout CSS uses raw px for geometry that is not repeated (column widths, specific padding, icon positions). There are no sizing tokens between `--space-8` (4rem) and `--desk-window-pad-x` (14px) -- the gap makes raw px the practical choice for mid-range values.

**Hex literals bypassing color tokens:**

Color discipline is strong. Only two CSS files have any raw hex: `attention.css` (1 occurrence) and `RepoWindow.css` (1 occurrence). In TSX, `XtermPane.tsx:60-78` has ~10 raw hex values for xterm ANSI colors that have no token equivalent (magenta, cyan, brightRed, etc.) -- these are the xterm-specific palette, not general UI. The glow pool in `tokens.gen.ts` duplicates hex values from tokens for JS consumption -- necessary for the GL layer.

---

### 5. THE VERDICT INPUTS (top 10 findings, ranked)

1. **[STRENGTH]** The three-layer token architecture (primitive/semantic/component) is mature, generated from a single JSON source of truth (`design-tokens.json`, 1185 lines), with TS mirrors for the GL world -- tokens.css:1-312, tokens.gen.ts.

2. **[STRENGTH]** The surface kit (`Surface.tsx` + `gadgets.tsx`, ~2000 lines, 50+ exported components) is genuinely comprehensive and heavily adopted: 214 import references across the codebase; pullouts are ~95% kit-composed; most cores are 70-85% kit.

3. **[STRENGTH]** The no-modal law is perfectly observed -- zero `<dialog>` elements in production; every modal reference in the codebase is a comment saying "never a modal." In-world alternatives exist: `ConfirmVerb` (Surface.tsx:1088, two-press confirm), `EditInPlace` (Surface.tsx:963), pullouts, and windows.

4. **[STRENGTH]** Roving focus (`roving.ts`, 174 lines) and the unified keymap (`keymap.ts`) form a real keyboard/a11y foundation: ArrowUp/Down/Home/End/PageUp/PageDown navigation, type-ahead, one document-level binder feeding from the verb registry.

5. **[GAP]** No virtualized list exists anywhere -- `DeskListView.tsx:27` explicitly rejects it ("no virtualization dep"). At 100-row pagination this works for today's data volumes but blocks any room with 500+ items (artifact archives, meeting history, large zones).

6. **[GAP]** No date/time picker, no general combobox/select primitive, and no reusable progress bar exist in the kit. Pickers are domain-specific one-offs (`RailsPicker`, `RunsOnPicker`, `WorkbenchTemplatePicker`). Progress is ad-hoc state in WorkbenchWindow.

7. **[GAP]** Skeleton loading was explicitly killed in the gadget-kit sweep (Signal.tsx:2). `SurfaceState` handles loading with a spinner, but there is no content-shape skeleton for perceived-performance optimization.

8. **[DEBT]** ~1100 raw px values across the six heaviest component CSS files (`surface.css:304`, `gadgets.css:181`, `chrome-menus.css:142`, `attention.css:110`, `mission-control.css:108`, `workbench-config.css:98`) represent layout geometry that bypasses spacing tokens. The token layer provides 8 spacing steps but no layout-specific sizing tokens, making raw px the practical default.

9. **[DEBT]** `react-app.css` (414 lines, 29 legacy class selectors: `.signal-panel`, `.welcome-*`, `.presence-*`, `.dialog-form`) serves only WelcomePage and PresencePage -- two routes that predate the desk era and use zero kit components. This is dead-weight CSS loaded globally via `main.tsx:8`.

10. **[GAP]** Sound tokens are entirely absent -- no `--sfx-*` or audio design tokens exist anywhere. Motion tokens are thorough (6 durations, 6 easings, prefers-reduced-motion sweep), but there is no parallel system for audio feedback, despite voice being a core product surface (MicButton, RecordOrb, dictation).