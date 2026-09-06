# The mic census (Phase 176, story 01 recon)

Recomputed on `feat/the-speak-loop` @ `7a47904e` (= main, 2026-09-06),
after 170--175 merged. Supersedes the 2026-09-05 numbers in the design
draft (which were taken on `feat/the-great-pass` and counted tests and
`_parked/`).

**Scope.** Every `<input` and `<textarea` occurrence in
`web/src/**/*.tsx`, excluding `*.test.*` and any `_parked/` directory.
Script: `scratchpad/census2.py` (element text collected across the
JSX tag's lines; enclosing component from the nearest preceding
top-level `function`/`const`; `type=` read off the element).

**Coverage rule.** An input is COVERED when it is the internal element
of a mic-bearing library species (StringGadget / PadGadget /
EditInPlace, mic default true) **or** an explicit `<MicButton>` binds
it in the same component within ~20 lines.

---

## 1. The mic-bearing species and their defaults

| Species | Defined at | mic default | Mic rendered at | Render sites (`<Species`) |
|---|---|---|---|---|
| StringGadget | `web/src/desk/surface/gadgets.tsx:243` | `mic = true` | `gadgets.tsx:298-299` (suppressed for `type="password"`, `gadgets.tsx:298`) | 97 |
| PadGadget | `web/src/desk/surface/gadgets.tsx:315` | `mic = true` | `gadgets.tsx:356-357` | 16 |
| EditInPlace | `web/src/desk/surface/Surface.tsx:1070` | `mic = true` | `Surface.tsx:1169-1174` (`if (!mic) return editor;`) | 6 |

Standalone `<MicButton>` placements: **33 across 29 files**; 3 of those
are the species' own (`gadgets.tsx:299`, `gadgets.tsx:357`,
`Surface.tsx:1174`), so **30 standalone placements across 26 faces**.

`web/src/desk/components/MicButton.tsx` contains **no** `<input>` or
`<textarea>` of its own (grep, 0 hits) -- the draft's "the MicButton's
own internal input" allowlist entry does not exist.
`web/src/desk/surface/controls/MicButton.tsx` is a 4-line re-export.

---

## 2. Every raw `<input>` / `<textarea>` (44)

### 2a. COVERED (17)

| # | file:line | Component | Type | Covered by |
|---|---|---|---|---|
| 1 | `web/src/desk/surface/gadgets.tsx:281` | StringGadget | text | own mic, `gadgets.tsx:299` |
| 2 | `web/src/desk/surface/gadgets.tsx:345` | PadGadget | textarea | own mic, `gadgets.tsx:357` |
| 3 | `web/src/desk/surface/Surface.tsx:1152` | EditInPlace | textarea | own mic, `Surface.tsx:1174` |
| 4 | `web/src/desk/surface/Surface.tsx:1161` | EditInPlace | text | own mic, `Surface.tsx:1174` |
| 5 | `web/src/desk/components/AskPanel.tsx:432` | AskPanel | textarea | MicButton `:428` |
| 6 | `web/src/desk/components/SessionPullout.tsx:470` | SteerComposer | textarea | MicButton `:464` |
| 7 | `web/src/desk/components/ThreadComposer.tsx:968` | ThreadComposer | textarea | MicButton `:981` |
| 8 | `web/src/desk/components/WorkbenchWindow.tsx:1705` | WorkbenchWindow inlet | text | MicButton `:1686` |
| 9 | `web/src/desk/gl/WorldStage.tsx:444` | ZoneRenameOverlay | text | MicButton `:458` |
| 10 | `web/src/desk/pullouts/CoderPullout.tsx:109` | CoderPullout draft | textarea | MicButton `:100` |
| 11 | `web/src/desk/pullouts/shared/CapabilitySection.tsx:129` | CapabilitySection | text | MicButton `:120` |
| 12 | `web/src/desk/pullouts/ThreadPullout.tsx:737` | AnnotationPopover | text | MicButton `:752` |
| 13 | `web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:65` | ThoughtDocumentPane title | text | MicButton `:72` |
| 14 | `web/src/features/project-room/ProjectRoomCore.tsx:1428` | RoomAskWell | text | MicButton `:1442` |
| 15 | `web/src/features/project-room/ProjectRoomCore.tsx:1568` | HistoryWing search | search | MicButton `:1575` |
| 16 | `web/src/features/project-room/door/DoorCore.tsx:408` | DoorCore outcome | text | MicButton `:417` |
| 17 | `web/src/features/project-room/review/ReviewPosture.tsx:108` | EditFields | text | MicButton `:114` |

Rows 14--16 are the walk's beats 6 and 7 (the Room's ask well, the
Door's name field): **already covered on main**.

### 2b. UNCOVERED, dictatable -- THE GAP (8)

| # | file:line | Component | Type | Disposition | Note |
|---|---|---|---|---|---|
| 1 | `web/src/desk/surface/LedgerFilter.tsx:112` | LedgerFilterBar | text (`"Filter..."`) | ADD-MICBUTTON | A library species; one fix covers every ledger filter on the desk |
| 2 | `web/src/desk/components/ThreadComposer.tsx:1060` | InlineEditor | textarea | ADD-MICBUTTON | Nearest MicButton (`:981`) belongs to ThreadComposer, not this editor |
| 3 | `web/src/desk/pullouts/ThreadPullout.tsx:211` | ElicitationForm | text | ADD-MICBUTTON | Free-text elicitation answer |
| 4 | `web/src/desk/pullouts/ThreadPullout.tsx:1634` | ThreadPulloutInner | text (title) | ADD-MICBUTTON | Thread title edit |
| 5 | `web/src/desk/pullouts/ThoughtContextPicker.tsx:191` | ThoughtContextPicker | search (`"Find a note…"`) | ADD-MICBUTTON | |
| 6 | `web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:90` | ThoughtDocumentPane tags | text | ADD-MICBUTTON | The mic at `:72` is bound to `title`, not `tags` |
| 7 | `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:415` | WorkspaceReady answer | textarea | MIGRATE-TO-GADGET (PadGadget) | Already carries a `// UX-CANON: needs redesign (HS-170-04)` marker |
| 8 | `web/src/desk/pullouts/NotePullout.tsx:409` | NotePullout answer | textarea | MIGRATE-TO-GADGET (PadGadget) | Refinement-question answer |

### 2c. ALLOWLIST, raw elements -- non-dictatable or library primitive (19 of 23)

| # | file:line | Type | Reason |
|---|---|---|---|
| 1 | `web/src/components/signal/Signal.tsx:86` | text | Library primitive `TextInput`; **zero call sites** in `web/src` (dead export) |
| 2 | `web/src/components/signal/Signal.tsx:91` | textarea | Library primitive `TextArea`; zero call sites |
| 3 | `web/src/desk/surface/gadgets.tsx:97` | checkbox | CheckGadget |
| 4 | `web/src/desk/surface/gadgets.tsx:112` | checkbox | CheckGadget (token variant) |
| 5 | `web/src/desk/surface/gadgets.tsx:211` | radio | MxRadio |
| 6 | `web/src/desk/surface/gadgets.tsx:450` | number | StepperGadget |
| 7 | `web/src/desk/surface/gadgets.tsx:500` | range | PropGadget slider |
| 8 | `web/src/desk/surface/patterns/ChoiceCardGroup.tsx:135` | radio | ChoiceCard |
| 9 | `web/src/desk/pullouts/ThreadPullout.tsx:194` | checkbox | Elicitation boolean |
| 10 | `web/src/desk/pullouts/ThreadPullout.tsx:203` | number | Elicitation numeric |
| 11 | `web/src/desk/components/ScheduleCreateWindow.tsx:160` | datetime-local | Date/time picker |
| 12 | `web/src/features/project-room/review/ReviewPosture.tsx:278` | date | Defer-until date picker |
| 13 | `web/src/pages/cores/ModelLibraryCore.tsx:383` | password | Provider key |
| 14 | `web/src/pages/cores/ModelLibraryCore.tsx:396` | password | Provider key |
| 15 | `web/src/pages/cores/ModelLibraryCore.tsx:404` | file | Model file chooser |
| 16 | `web/src/pages/cores/ModelLibraryCore.tsx:434` | radio | Row selection |
| 17 | `web/src/pages/cores/TopologyMapView.tsx:441` | password | Provider key |
| 18 | `web/src/pages/cores/TopologyMapView.tsx:456` | password | Provider key |
| 19 | `web/src/pages/cores/history/ImportSection.tsx:76` | file | Audio/transcript import |

---

## 3. The second gap the draft never named: `mic={false}` opt-outs (14)

A gadget instance that opts out of its default mic is a voice-law hole
the raw-element count cannot see. Fourteen occurrences on main:

| file:line | Species | Label | Disposition |
|---|---|---|---|
| `web/src/desk/components/FirstWords.tsx:413` | PadGadget | `Your dictated text` | RESTORE-MIC (the onboarding dictation well, mic off) |
| `web/src/desk/components/WorkbenchWindow.tsx:350` | StringGadget | `Search agents` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:242` | StringGadget | `New relationship` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:568` | StringGadget | `Owner alias` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:585` | StringGadget | `Topic` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:585` | PadGadget | `Grounding note` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:677` | StringGadget | `Request` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:696` | StringGadget | `Satisfaction note` | RESTORE-MIC |
| `web/src/pages/cores/PeopleCore.tsx:713` | PadGadget | `Agenda item` | RESTORE-MIC |
| `web/src/desk/components/ScheduleCreateWindow.tsx:176` | StringGadget | `Cron expression` | ALLOWLIST (syntax field) |
| `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:224` | StringGadget | `Event N start` (`HH:MM`) | ALLOWLIST (time field) |
| `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:232` | StringGadget | `Event N end` (`HH:MM`) | ALLOWLIST (time field) |
| `web/src/pages/cores/SettingsCore.tsx:1108` | StringGadget | `Symbol N` (`→`) | ALLOWLIST (glyph field) |
| `web/src/pages/cores/dictation/UtteranceWell.tsx:38` | PadGadget | `Utterance` | PARK -- dead component (below) |

**9 RESTORE-MIC · 4 ALLOWLIST (4 of 23) · 1 PARK.**

**The allowlist is 23 everywhere: 19 raw elements (section 2c) + 4
`mic={false}` opt-outs (cron, `HH:MM` x2, glyph).** A 24th entry lands
with story 05: `SpeakFace.tsx:296-308`, the Speak face's utterance well,
takes `mic={false}` by ruling R13 with the reason "the `Talk` transport
is this face's mic authority (Article IV.3)" -- it is a 170 drift, not a
census finding, so the design's number stays 23 until it lands.

---

## 4. 170's orphans in `pages/cores/dictation/`

Four files there are not in the barrel (`pages/cores/dictation/index.ts`)
and have zero importers in `web/src`: `UtteranceWell.tsx`,
`InstrumentStrip.tsx`, `AimRow.tsx`, `ResultPanel.tsx`. `UtteranceWell`
is nonetheless one of the six faces holding the scanner's current `mic`
ceiling. Owner ruling "never delete -- park instead" applies: move to a
`_parked/` directory (which the census and the scanner both skip).

---

## 5. The scanner ALREADY has a voice-law rule -- it is `mic`, not `A14`

`scripts/ux_canon_scan.py` carries rule id **`mic`** ("Missing MicButton
on text input"), weight 1:

- registered: `scripts/ux_canon_scan.py:100`
- coverage flag computed once per FILE: `scripts/ux_canon_scan.py:178-180`
  (`("MicButton" in content) or ("StringGadget" in content and "mic={false}" not in content)`)
- text-input flag: `scripts/ux_canon_scan.py:360-363`
- emitted (once per file, gated on `classify_face`):
  `scripts/ux_canon_scan.py:409-414`

Current ceiling `mic: 6` (`tests/ux_canon_ceiling.json`), held by
`CalendarSnapshotReviewCore`, `ChoiceCardGroup`, `LedgerFilter`,
`PeopleCore`, `SettingsCore`, `UtteranceWell`. Rule `B` (raw
`<input>`/`<select>`/`<textarea>`, `ux_canon_scan.py:306-316`) has
ceiling 34.

The rule's **four** weaknesses 176 must fix (ruling R9):

1. The text-input flag matches `<(?:input|StringGadget|TextInput)\b`
   (`ux_canon_scan.py:361`) and **never `<textarea`** -- three of the
   eight gap sites (`ThreadComposer.tsx:1060`,
   `ThoughtWorkspaceWindow.tsx:415`, `NotePullout.tsx:409`) are
   invisible to the rule today and would stay invisible after a naive
   per-element port.
2. It counts `<StringGadget` as an uncovered input, when a StringGadget
   is covered by definition -- per-element counting must target raw
   `<input` / `<textarea` plus `mic={false}` gadget instances only.
3. It is **file-scoped**: one violation per file however many inputs
   are bare.
4. It is **gated on `classify_face`**, so non-face files are never
   checked; dropping the gate widens the scan to this census's scope.

Also: one `mic={false}` anywhere in a file voids that whole file's
coverage flag (`:178-180`).

176 extends `mic` to per-element with a named `path:line` allowlist; it
does not add `A14`. **The census's own numbers do not move** -- this
census matched `<input` and `<textarea` directly, independent of the
scanner. What moves is the scanner's view. The honest ceiling claim is
"`mic: 0` with a 23-entry reasoned allowlist", not "0 because every
input has a mic".

---

## 6. Summary

| Measure | Count |
|---|---|
| Raw `<input>` + `<textarea>` in `web/src/**/*.tsx` (excl. `*.test.*`, `_parked/`) | **44** |
| -- covered (library species internal, or an explicit MicButton in the component) | **17** |
| -- uncovered dictatable (**the gap**) | **8** |
| -- allowlisted, raw (password 4, file 2, radio 3, checkbox 3, number 2, range 1, date/time 2, dead primitive 2) | **19** |
| `mic={false}` opt-outs on mic-bearing gadgets | **14** |
| -- to restore | **9** |
| -- allowlisted (cron, HH:MM x2, glyph) | **4** |
| **The allowlist, stated as one number everywhere (19 raw + 4 opt-outs)** | **23** |
| -- to park (dead component) | **1** |
| **176-04's real work: 8 raw + 9 opt-outs** | **17 sites** |
| StringGadget render sites | 97 |
| PadGadget render sites | 16 |
| EditInPlace render sites | 6 |
| Standalone `<MicButton>` placements (excl. the 3 library-internal) | 30 across 26 faces |

The draft's "22 raw `<input>` + 9 raw `<textarea>` = 31 GAP" counted
library internals, allowlist-class controls, tests and `_parked/`. The
true gap is 8 raw elements plus 9 opt-outs.
