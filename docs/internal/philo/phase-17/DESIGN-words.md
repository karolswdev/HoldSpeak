# Phase 17 design: words

Cluster: **words**. R3 (chips and phase words), R7 (demo chrome and seed
clutter), and the recon's whole cut list. Source: `RECON-2026-10-13.md`
(main @ b50b13a0b). Every path below is relative to the repo root and was
read on that head.

Seams, named where they occur: **verbs** (`DESIGN-verbs.md`: every AI run,
its reason, the one engine chip), **attention** (`DESIGN-attention.md`: one
attention source, one review, a thought's machinery), **windows**
(`DESIGN-windows.md`: Runs on as a wing, the phone, the dock at 393).
This design gives those faces their WORDS; it does not design their
mechanics.

## 1. The problem

The desk speaks in state-machine labels. One thought window shows
`ONE QUESTION · NO ENGINE YET`, `EVERYDAY CONTEXT · 2 NOTES`,
`READS · NOTHING`, `KEPT · 1:52 PM · IN INBOX`, and `THIS DEVICE` three times
(shot 018). One meeting row shows seven chips: `MTG 10-13 · 13:53 · PROPOSAL ·
○ LINKED · ○ UNREVIEWED · ⚠ DUE · UNKNOWN · OWNER · TOMAS` (shot 030). Ask AI
opens on `SESSION · NO TRAFFIC`, `GROUND THIS ASK`, `CTX 0.0K/16.4K · USES
ASSIGNMENT` (shot 039). Search prints raw JSON under a `MEANING` chip (shot
020). The recon counted 31 words not understood on first read.

The desk is also not his. His copy holds one note of his and eight seed
objects, 8 to 1 (shots 001, 078). The dock holds 13 buttons, five of them
apps (`Missed`, `Delivery`, `Terminals`, `Hide the menus`, `Places`, a `SENT
23:55` badge; shot 059). "Change places" shows eight scenes with a line of
prose each (shot 058). A fresh Mac has an empty desktop and a Dock of apps
that open.

## 2. The cause in the code

### 2.1 Chips are enum projections, not words

Every chip is drawn from a field by a small `token` function, one per face,
and the token is the field's enum name in uppercase. There is no shared
word table and no chip species: a plain chip is the raw markup
`<span className="surface-token" data-chip>` (no `Chip` component exists;
`web/src/desk/surface/kit.tsx` has `KindPlate` :154, `StatusStrip` :42).

| Chip | Where | Data |
|---|---|---|
| `ONE QUESTION` | `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:513` | static caption while `!completed` |
| `NO ENGINE YET` + `Choose an engine` | same, :390-422 (the `askRow` ternary), :514, :518 | `projection.inference.availability !== "ready"` and `placement.readiness !== "ready"` |
| `THIS DEVICE` (engine) | same, `engineEgress()` :81-90 | `placement.boundary === "same_device"` |
| `READS · NOTHING` | same, `readsToken` :424-430, foot :567 | `attachments[]` empty → the literal `"NOTHING"` |
| `EVERYDAY CONTEXT · 2 NOTES` | same `readsToken`; title from the hub | the seeded kb `hs-seed-everyday-context` (`holdspeak/seeds/fresh-desk.yaml:100`) |
| `KEPT · 1:52 PM` | `web/src/desk/thought-workspace/thoughtReceipt.ts:30-36` | `writer.keptAt`, uppercased `keptReceipt()` |
| `IN INBOX` / `NOT IN A DRAWER` / `· FINISHED` | `thoughtReceipt.ts:38-41` | `filing_status`, `directory_name`, `completed` |
| `PROPOSAL` | `web/src/pages/cores/history/MeetingReview.tsx:498`; `web/src/desk/surface/patterns/ClaimAxes.tsx:19` | static, every review row |
| `LINKED` / `SUPPORTED` / `UNSUPPORTED` / `DISPUTED` | `reviewModel.ts:215-224` `supportToken` | `p.support` enum |
| `UNREVIEWED` / `ACCEPTED` / `REJECTED` / `SUPERSEDED` | `reviewModel.ts:227-232` `acceptanceToken` | `p.acceptance` enum |
| `DUE · UNKNOWN`, `OWNER · UNKNOWN` | `reviewModel.ts:235` `unknownToken` | `${u.type} · ${u.value}` uppercased |
| `MTG 10-13 · 13:53` | `MeetingReview.tsx:492` `spanLabel` | the proposal's transcript span |
| `MTG` / `DEC` / `ACT` plates | `kit.tsx:154` `KindPlate`; used in `MeetingDetail.tsx:98-151`, `needsFace.ts:123-125`, `ChairHome.tsx:332`, `HandSheet.tsx:164`, `BriefView.tsx:72`, `CoverageRow.tsx:47`, `ProjectRoomCore.tsx:157`, `PreparePosture.tsx:315` | `kind` |
| `TO CONFIRM` / `TO DECIDE` | `MeetingDetail.tsx:119`, `needsFace.ts:415` | `state === "proposed"` |
| `GOVERNING` | gone; `DecisionsView.tsx:54` renders `CURRENT` now | `lifecycle === "active"` |
| `RANKED` | `NeedsDrawer.tsx:610`; `ChairHome.tsx:1092` (the empty filter) | `computedAt`; the default filter |
| `SESSION` / `NO TRAFFIC` | `web/src/desk/components/AskPanel.tsx:309,313`; `Surface.tsx:557` `SurfaceTraffic` default `empty` | `turnCount === 0` |
| `GROUNDING`, `Ground this ask` | `AskPanel.tsx:503`; `GroundingSection.tsx:171` | static; `groundingIsEmpty(selection)` |
| `CTX 0.0K/16.4K · USES ASSIGNMENT` | `AskPanel.tsx:275-276` (foot), :321 (per turn), :494, :541 (meter) | `groundTokens`, `limitTokens` |
| `Uses group · 192.168.1.43:8080` + `Change` | `ContextualAssignment.tsx:16` `namedChain`; `AssignmentSummary.tsx:15` | `editor.effective.inherited_from` + the endpoint host |
| default ask text | `web/src/desk/ask.ts:22` `ASK_LENSES[0]`, seeded into the draft at `AskPanel.tsx:89` | the iPad's lens list, verbatim |
| `NOT ANSWERED · THE HUB REFUSED IT · ASK KEPT · EDIT THE ASK` | `AskPanel.tsx:44-50` `askFailureLabel` | a regex over the hub's output text; the fallback branch |
| `HOLD NONE ANYWHERE` | `web/src/pages/cores/dictation/SpeakFace.tsx:330`; CSS uppercases (`speak.css:650`) | config `hotkey.display`, echoed raw (`holdspeak/web/routes/dictation/_helpers.py:930`) |
| `LANDS IN · FOCUSED APP`, `DRY RUN` | `SpeakFace.tsx:529-556`; `shared.ts:56` | the aim and the rehearse switch |
| `LISTENER FAILED` | hub `holdspeak/desktop_permissions.py:296` `hotkey_failure_token()` → `custody.reason`, rendered `SpeakFace.tsx:903-905` | the hub's token, verbatim |
| `Question did not complete`, `not set up: Set up local AI downloads this model` | hub `holdspeak/services/monday_brief_service.py:342`; `holdspeak/inference_targets.py:245` `NOT_SET_UP_REASON`; drawn by `ChairHome.tsx:2362-2398` | hub sentences, written for another face |
| `BRIEF · 5 THINGS WAITING` | `ChairHome.tsx:2381-2385` | `desk.needs_you`, not the brief's rows |
| `Ack` / `Defer` | `ChairHome.tsx:2409,2418` | `onShelf(id, "acknowledged" \| "deferred")` |
| raw JSON in a MEMORY hit | `DeskToolShelf.tsx:783-830` → `paletteHit.tsx:127` prints `hit.snippet` as served | a JSON-bodied memory chunk; no guard |
| `MEANING` | `FoundBy.tsx:16,39` | `retrieval_origin === "vector"` |
| `NOT SET · WRITTEN 13:47` | `settingsPrefs.tsx:782` renders a bare `<EgressChip />` whose default label is `NOT SET` (`gadgets.tsx:780`); `:765` | no route data at all; `receipt.writtenAt` |
| `✕ NO LIVE SOURCE · N SOURCES · N WORK · READ hh:mm` | `DeliveryBoard.tsx:197,500,565` | no live source; counts incl. zero |
| `No coder ready · 3 CODERS`, the prose line | `ConductorWindow.tsx:227,592`; "Hooks: see the coder's work…" | none `canRun`; a sentence |
| `THIS DEVICE` everywhere | `web/src/desk/surface/egress.ts:148` `egressFor` returns the label for a local scope; `turnRoute.tsx:65`; `briefEgress.tsx:21` | `scope === "local"` |

Three structural facts explain the rest:

1. **The hub writes sentences for faces.** `NOT_SET_UP_REASON`, `_breakage_words`,
   `hotkey_failure_token` reach the face verbatim. Only Send has a code→word
   table (`web/src/features/channels/channels.ts` REFUSED/FAILED/UNKNOWN, fenced by
   `tests/unit/test_philo10_face_words.py`).
2. **Egress is decorative.** `EgressChip` (`gadgets.tsx:774`) draws `THIS DEVICE`
   whenever the scope is local. UX-CANON A.9 asks for the host chip only where
   bytes leave the machine.
3. **The guards do not know these words.** `docs/product-language.json`
   `copy_contract.prohibited_operational_patterns` (five rules, enforced by
   `tests/unit/test_product_copy.py` over `web/src/**/*.tsx`, with a debt ledger
   `tests/fixtures/product_copy_debt.json` that only shrinks) bans legacy nouns
   and promotional words, not phase words. `tests/unit/test_web_vocabulary_guard.py`
   `_BANNED` bans `intel`, `persona`, absolute paths.

### 2.2 The desk shows seeds, threads and side products as his objects

`composeScreen()` (`web/src/desk/screen/compose.ts:137`) draws every object of
`LOOSE_KINDS` (`meeting, note, decision, artifact, repository, thread`, :79) that
no Project holds (:210-225), plus every unfiled person (:226-238). Nothing marks
a seed: `holdspeak/db/seed.py:10-16` makes seeded objects "indistinguishable from
a user-made one"; the only mark is the `hs-seed-*` id. So:

- The five seeded notes (`fresh-desk.yaml:35-77`) lie loose. Their seeded
  directories (Inbox, Personal, Work; :18-33) do not hide them: `filed` means
  Project membership.
- `First dictation` is POSTed by first run (`FirstWords.tsx:272,300`,
  `firstrun/useFirstTake.ts:220`).
- `Thread` and `New thread` are empty thread objects
  (`web/src/desk/api.ts:426` `fromWireThread`; `desk/threads.ts:342`).
- `Ledger st… actions` is a meeting artifact: `fromWireArtifact` titles it from
  `artifact_type` when the hub sends no title (`api.ts:559`), and compose.ts
  draws it loose because an artifact with a `meetingId` is not "filed".
- `Mira` is a person; every unfiled relationship is a loose icon (:226-238),
  even though the People drawer is the ledger (:165).

### 2.3 The dock is three apps plus whatever announces itself

`DOCK_APPLICATIONS` (`web/src/desk/applications.ts:508`) holds three apps:
Today, Speak, Meetings (the only rows with `dock`). The rest of the dock is
`Dock.tsx:550-681`: seated windows, then launchers that announce themselves
(`launcherRegistry.ts:17-21`: `attention` = Missed from `AttentionDrawer.tsx:108`,
`delivery-board` from `DeliveryBoard.tsx:390`, `panes` = Terminals from
`SessionPullout.tsx:259`), then `<RoomActions/>` (`RoomActions.tsx:30-49`:
"Hide the menus" = verb `desk.settle`, "Places" = verb `go.change-places`), the
orb, Overview, Reset. The `SENT 23:55` badge is `dockStateLabel()`
(`dockState.ts:210-218`), drawn on the Today tile (`Dock.tsx:530-541`). At 393
nothing is removed: `dock.css:510-592` hides labels and `Dock.tsx:685-699` adds
a More pager.

### 2.4 Places is an app; the GL it was built for is parked

`change-places` is a manifest row with `⌘⇧P` (`applications.ts:56-70`). Its
window is `ChangePlacesCore.tsx` → `<WallpaperModule showFavorites favoritesOnly/>`
(`settingsWallpaper.tsx:12`), which renders each entry's `description`
(:85) from `web/src/desk/gl/atmosphereRegistry.ts:19-107`. The live desk paints
only the still: `Screen.tsx:131-145` sets `--desk-place-still` to
`resolveAtmosphere(id).previewUrl`; `gl/Atmosphere.tsx` is mounted by the
design preview and tests only (`web/src/desk/_parked/floor/README.md:22-24`).
A Settings `wallpaper` row already exists (`settingsPrefs.tsx:50`, row :669-675,
`SettingsCore.tsx:1895`). Choice persists in localStorage (`hs.desk.atmosphere`,
`atmospherePreference.ts:8`).

### 2.5 Go ▸ Tools lists six tools with no day-one job

`go: { section: "tools" }` on Workbenches, Activity, Processes, Rhythm,
Commands, Context (`applications.ts:218-429`); Memory is a Go `app` row
(:347). ⌘K finds any row with a `group` (`tools.ts:4-21`, `verbRegistry.ts:632-666`),
independent of `go`. Calendar snapshot and Components are already in neither.
The pinned orders live in `web/src/desk/__tests__/applicationManifest.test.ts:41,68,77-81`.

## 3. The target behavior

### 3.1 Three word rules (the whole design in three lines)

1. **Would he say it out loud?** A chip is a fact he would say: a name, a
   time, a count, a host. Never an enum (`PROPOSAL`, `LINKED`), never an
   abbreviation (`MTG`, `CTX`), never a phase (`UNREVIEWED`).
2. **State goes in the verb.** A row that shows `Confirm` is unconfirmed. A
   window that shows `Finish` is open. The chip that said so is cut.
3. **A row carries at most two chips: when, and who.** Everything else is a
   section caption said once, or nothing.

Plus one egress rule (UX-CANON A.9): a host chip is drawn only where bytes
leave the machine. `THIS DEVICE` is never drawn.

### 3.2 What he sees, press by press

**Job 2, the thought window (1440 and 393).** Desk ▸ Write a thought, type,
Finish. The window shows: the title bar (the first line), the text, the foot
`Saved 1:52 PM`, and the verbs `Add a note · Copy · Send · Finish`. No engine
line (the engine is assigned; the verbs doc draws the one chip only where a
run is offered). No `READS`, no `KEPT`, no `IN INBOX`, no `THIS DEVICE`. Send
unfolds one block: `HoldSpeak/Sent` and the `Send` button. Words on the face:
7, was 23.

**Job 3, the meeting rows (1440 and 393).** Outcomes ▸ Who owes what:

```
Complete the reconcile step          Tomas · no date        Confirm  Decline
Send the data retention doc          Karol · Wed            Confirm  Decline
```

Two chips: who, when. No plate, no `PROPOSAL`, no `TO CONFIRM`, no span. A row
whose claim is not in the transcript carries one warning chip instead of the
when-chip: `Not in the transcript`. At 393 the same row wraps the verbs under
the title (`SurfaceLedgerRow wrap`). (The attention doc decides that Outcomes
owns Confirm; these are its words either way.)

**Job 6, Ask AI (1440 and 393).** The window opens on the ask box with the
placeholder `Ask about your desk`, the mic, the `Ask` button, and under it one
fold `Add notes` and one chip `Qwen3.8 27B · LAN` (the verbs doc's one engine
chip). No `SESSION`, no `NO TRAFFIC`, no `CTX`, no lens checkboxes, no
`Uses group`. A failure reads `Not answered · <the hub's reason in words> ·
Ask again` (the verbs doc supplies the reason; the shape is here).

**Job 7 / the desk itself.** The bare desk at 1440 holds his things and two
drawers (People, Conductor) and one note, `Start here`. The dock holds five
apps: Today, Speak, Meetings, People, Conductor, then the orb and Overview.
Wallpaper is Settings ▸ Wallpaper. Go is six rows and Projects.

### 3.3 The new cost

| Measure (recon §7) | Before | After this design |
|---|---|---|
| Words not understood on first read | 31 | ≤ 5 (the glossary leaves: Prep, Outcomes, Conductor, Coder, Brief) |
| Chips on one meeting row | 7 | 2 |
| Chips on the thought window | 9 | 1 (`Saved h:mm`) |
| `THIS DEVICE` on one thought window / brief | 3 / 4 | 0 / 0 |
| Seed objects on his desk vs his own | 8 : 1 | 1 : n (`Start here` only) |
| Dock buttons at 1440 | 13 | 5 apps + orb + Overview |
| Go rows (+ Tools submenu) | 7 + 6 | 6, no submenu |
| Apps with a window the sweep opens | 24 manifest rows | 24 (parked rows stay; `MANIFEST_FLOOR` 22 holds) |
| Presses, Job 7 "change the wallpaper" | 3 (dock Places, scroll, Choose) | 3 (HoldSpeak ▸ Settings, Wallpaper, pick); no app, no window |

Job presses in §7 of the recon do not change from words alone; the dead ends
and the window counts belong to the other three designs.

## 4. The design

### 4.1 The glossary: every old term → the new word, or the cut

The table is the law for the word pass. Case: a chip is CSS-uppercased mono
(caption step); the source literal is written in sentence case. "Cut" means
the element leaves the face; the data stays.

**Objects and places (the nouns)**

| Old | New | Why |
|---|---|---|
| Thought, thought window, `THOUGHTS 3`, "Write a thought" | **Note**, "Write a note" | one noun for what he writes; `Thought` was the workspace's name (`ThoughtWorkspaceWindow`), not his word. OWNER CALL 1 below |
| Thread, "New thread", "Continue in thread" | **Thread** stays, only for a conversation with an agent (POSITIONING: Threads). An empty thread has no icon | |
| Everyday context (the seeded kb) | cut from the seed; the thought's well says **Notes this note reads** with plain titles | the owner's first question was "what is that?" |
| Runs on | **Engines** (Settings ▸ Engines); the windows doc makes it a wing | `Runs on` is a phrase, not a name |
| Connections | **Accounts** (Settings already shows an ACCOUNTS card, shot 038) | one name per thing |
| Change places / Places / Environments | **Wallpaper** (Settings row, exists) | it paints a still (`Screen.tsx:131-145`) |
| Settle in / "Hide the menus" (dock) | stays a Desk-menu verb `Hide the menus` ⌘⇧F; cut from the dock | |
| Missed (dock), `NEEDS ATTENTION · 8` | cut; **Needs you** is the one list (attention doc) | |
| Brief chair window | cut; **Today ▸ Brief** (attention doc) | |
| Review (meeting wing) | **Outcomes** owns Confirm (attention doc); the words below apply to whichever face stays | |
| Delivery, Terminals (dock) | cut from the dock; reachable by ⌘K (`group: "tool"` stays) | they open on nothing he can do (shots 053, 057) |
| Go ▸ Tools (Workbenches, Activity, Processes, Rhythm, Commands, Context) and Go ▸ Memory | cut from Go; ⌘K only, until each has a job | recon §3 |
| Agents (parked), Calendar snapshot, Components | unchanged (already out of Go and the dock) | |

**Chips and captions (the phase words)**

| Old | New | Where it is said instead |
|---|---|---|
| `PROPOSAL` | cut | the `Confirm` verb |
| `UNREVIEWED` | cut | the `Confirm` verb |
| `ACCEPTED` / `REJECTED` / `SUPERSEDED` | `Confirmed` / `Declined` / `Replaced`, only in the kept list (`renderKept`) | |
| `LINKED`, `SUPPORTED`, `LINKED · EDITED` | cut | a claim from the transcript needs no badge |
| `UNSUPPORTED`, `DISPUTED` | `Not in the transcript` (warning tone), the row's one chip | the only support state he must know |
| `TO CONFIRM`, `TO DECIDE` | cut | the verb |
| `DUE · UNKNOWN` | `no date` | |
| `OWNER · UNKNOWN`, `UNASSIGNED` | `no owner` | |
| `OWNER · TOMAS` | `Tomas` | a name is a chip |
| `DUE · WEDNESDAY · SUPPLIED` | `Wed` (he typed it: no `SUPPLIED`) | |
| `DONE · FRI` | `Done · Fri` | kept |
| `MTG 10-13 · 13:53` (span) | cut from the row | the meeting is the window; the transcript opens with `Open transcript` |
| `MTG` / `DEC` / `ACT` / `CMT` plates | `Meeting` / `Decision` / `Action` as the plate's word, on mixed lists only (Needs you, Today, Prep); cut on a list of one kind (Outcomes) | ASD-STE100 has no undefined abbreviations (the `SEG` precedent in `product-language.json`) |
| `RANKED hh:mm`, `RANKED` filter | `Checked hh:mm`; the filter's empty label is `All` | |
| `GOVERNING` / `CURRENT` | `Current` stays (it is a word) | |
| `ONE QUESTION` | cut | |
| `NO ENGINE YET` / `Choose an engine` | drawn only when the assignment is empty: `No engine · Set up` (verbs doc) | |
| `READS · NOTHING` | cut when empty; `Reads: About me, Current priorities` when not | |
| `KEPT · 1:52 PM` | `Saved 1:52 PM` | the keep list's honest `SAVED 14:09` |
| `IN INBOX`, `NOT IN A DRAWER`, `· FINISHED` | cut | `Finish` / `Resume` say it; the icon's drawer says where |
| `SAVING… · SEND WAITS`, `NOT SAVED · SEND WAITS` | `Saving…`, `Not saved · try again` | |
| `CHANGED ELSEWHERE`, `DID NOT SAVE · …` | `Changed on another device · Reload`, `Not saved · <cause>` | the four failure facts (`test_product_copy.py:138`) |
| `FILE · HoldSpeak/Sent · THIS DEVICE` + `FOLDER HoldSpeak/Sent` + `Send · THIS DEVICE` | one line: `HoldSpeak/Sent` and the `Send` button | the name is said once (A.7) |
| `THIS DEVICE` (every face) | never drawn | A.9 |
| `LAN · 192.168.1.43` on a row that leaves the machine | stays, as the EgressChip | A.9 |
| `SESSION`, `NO TRAFFIC`, `N TURNS` | cut; the answers list has no head until there is an answer | A.3 one true line |
| `GROUNDING`, `GROUND THIS ASK`, `Grounded on …` | `Add notes` / `With: <titles>` | |
| `CTX 0.0K/16.4K`, `CTX n`, `CTX · n CARDS`, the meter | cut; one warning only when over budget: `Too long for the engine · remove a note` | |
| `USES ASSIGNMENT`, `Uses group · host:port`, `ASSIGNMENT` | cut; the one engine chip `Qwen3.8 27B · LAN` (verbs doc) | |
| `NOT ANSWERED · THE HUB REFUSED IT · ASK KEPT · EDIT THE ASK` | `Not answered · <reason> · Ask again` | reason from the verbs doc |
| the lens checkboxes `SUMMARIZE · ACTION ITEMS · RISKS · DECISIONS · DRAFT EMAIL` | cut from the desk Ask; the draft starts empty with placeholder `Ask about your desk` | OWNER CALL 3 |
| `HOLD NONE ANYWHERE` | `Hold ⌥Space anywhere` when set; `No hotkey · Set one` when not | the config echo |
| `LANDS IN · FOCUSED APP · n MS` | `Types into the front app` (`n ms` stays) | |
| `DRY RUN` | `Practice` (no typing) | |
| `LISTENER FAILED` | `Hotkey not working · Allow HoldSpeak in System Settings` | a word table over `hotkey_failure_token()` |
| `Question did not complete` / `not set up: Set up local AI downloads this model` | `Ask AI did not run · No engine` with the verb `Set up` | a word table over the brief's breakage codes |
| `NOT READ · People (locked) · Generate for the full brief` | `People not read · Unlock` | |
| `BRIEF · 5 THINGS WAITING` | `Brief · Tuesday 13 Oct` | the count is the bell's (attention doc) |
| `Ack` / `Defer` | `OK` / `Later` | |
| `OCT 12-13 · GENERATED OCT 13 06:00 · PARTIAL` | `Made 06:00` (`Partial` only when a source was not read) | |
| `NO CALENDAR · Connect` | stays (honest, one line) | |
| raw JSON in a MEMORY hit | the `text` (or `fact.text`) field; else the title only | |
| `MEANING` / `KEYWORD` / `TIME` / `NAME` / `LINK` (`FoundBy`) | cut in the palette | retrieval internals |
| palette captions `VERBS` / `OBJECTS` / `MEMORY` | `Do` / `Open` / `Remembered` | |
| `NOT SET` (settings foot) | cut | it named nothing |
| `WRITTEN 13:47` | `Saved 13:47` | |
| `Summaries: 192.168.1.43:8080 · THIS DEVICE · 3 ENGINES · 2 CONNECTED` | cut; the two cards are the face | |
| `✕ NO LIVE SOURCE`, `Companion repo · owner/repo` | `No repo yet · Add a repo` | |
| `N SOURCES · N WORK · READ hh:mm` | `Read hh:mm` (counts only when > 0, A.8) | |
| `No coder ready · 3 CODERS`, "Hooks: see the coder's work, hand it work" | `No coder ready`; the prose line cut; the three rows are the count | |
| `SENT 23:55` / `SEND FAILED` on the Today tile; `READY 1` on Meetings | cut; `REC` stays while recording | the bell is the one count |
| `HUGGINGFACE.CO`, `Set up speech · 144 MB` | stay | bytes leave; honest |
| `SUMMARY RUNNING`, `SUMMARISED · 14 S`, `SAVED 14:09 /path` | stay | the keep list |

### 4.2 Component, store and route changes

**A. The egress chip draws nothing for a local scope.**
`EgressChip` (`web/src/desk/surface/gadgets.tsx:774`): when `scope === "local"`
and no `onClick`, return `null`. `egressFor` (`egress.ts:148`) returns `null`
for same-device; `turnRoute.tsx:65` and `briefEgress.tsx:21` follow. The
default label `"NOT SET"` goes; a chip with no label renders nothing. The
canon scanner's A9 rule is static (it looks for `<EgressChip` beside a
provider call, `ux_canon_scan.py:770-773`), so the hard zero holds.
`settingsPrefs.tsx:782` drops the bare `<EgressChip />`.

**B. A review row is title + who + when + verbs.**
`reviewModel.ts`: `supportToken` returns `null` for `supported` and
`source_linked`, and `{label: "Not in the transcript", state: "warning"}`
otherwise; `acceptanceToken` returns `null` for `proposed`; `unknownToken`
returns `no date` / `no owner`. `MeetingReview.tsx:484-525` `renderAxes`
draws: who (`p.owner` or `no owner`), when (`p.due` or `no date`), and the
support chip only when present; no `PROPOSAL`, no span. `ClaimAxes.tsx`
(the library twin) gets the same table, so Needs you and the Room say the
same words. `MeetingDetail.tsx:98-151` drops the `KindPlate` and `TO CONFIRM`;
`DONE · X` becomes `Done · X`.

**C. `KindPlate` speaks words.**
`kit.tsx:154`: the word table becomes `meeting → Meeting`, `decision →
Decision`, `action → Action`, `commitment → Action`. One change, nine faces.
Width: the plate's `min-width` grows from 3ch to 8ch; at 393 the plate sits
above the title (`SurfaceLedgerRow wrap`).

**D. The thought foot and head.**
`ThoughtWorkspaceWindow.tsx`: remove :513 (`ONE QUESTION`); draw the `askRow`
(:390-422) only when the verbs doc's engine state is "empty"; `readsToken`
(:424-430) returns `null` when empty and `Reads: <titles>` otherwise;
`thoughtReceipt.ts` `thoughtWriteLine` returns `Saved h:mm` (sentence case; the
foot's CSS stops uppercasing receipts) and `thoughtFilingLine` is removed with
its render at :573. The Send well (:551-563) keeps `NoteSendWells` but the
destination row says the path once. The `Change` verb (:580) is relabelled
`Add a note` (the attention doc replaces the verb row later; the word is
ready for it).

**E. Ask AI words.**
`AskPanel.tsx`: `SurfaceTraffic` (:309-313) is mounted only when
`turnCount > 0`; the `GadgetGroup` label (:503) and the fold title
(`GroundingSection.tsx:171`) become `Add notes` / `With: …`; the four `CTX`
sites (:275, :321, :494, :541) collapse to one over-budget warning;
`askFailureLabel` (:44-50) returns `{label: "Not answered", reason, verb:
"Ask again"}` and the face draws reason as body text, verb as the library
Button. `useDurableDraft("desk-ask", "")` (:89): the draft starts empty;
`ASK_LENSES` stays in `ask.ts` for the meeting-scoped Ask (OWNER CALL 3).

**F. Hub words get a table, not a sentence.**
Two small code→word tables in the web, built like `channels.ts` REFUSED
words:
- `web/src/pages/cores/dictation/hotkeyWords.ts`: `hotkey_failure_token()`
  values → `Hotkey not working · Allow HoldSpeak in System Settings`,
  `No hotkey · Set one`. `SpeakFace.tsx:903-905` reads it; :330 reads
  `custody.display` only when it is a real chord.
- `web/src/desk/chair/briefWords.ts`: the brief's `broke` rows carry a
  `code` (the hub adds one additive field, `holdspeak/services/monday_brief_service.py:342`:
  `code: "ask_not_run" | "source_not_read" | …`); the web prints the word
  table's line and keeps the hub sentence as `title` on hover only. The
  hub's text is unchanged (additive).
  Fence: `tests/unit/test_philo10_face_words.py` pattern, one new file per
  table, deriving the codes from the Python source.

**G. Search never prints JSON.**
`paletteHit.tsx:75` `snippetParts`: if the snippet starts with `{` and parses,
take `text`, `fact.text` or `summary`; else return the title only. `FoundBy` is
not mounted in `DeskToolShelf.tsx` MEMORY rows (:783-830); the date stays.
Section captions at `DeskToolShelf.tsx:58` read `Do`, `Open`, `Remembered`.

**H. The desk shows his things.**
`compose.ts`:
- :215: skip `o.kind === "artifact" && o.meetingId` (an artifact lives in its
  meeting; the meeting window's Artifacts wing already lists it).
- :215: skip `o.kind === "thread"` when the thread has no user turn (the store
  knows `turns`; `fromWireThread` `api.ts:426`).
- :226-238: persons are not loose; the People drawer is the ledger. The
  drawer's caption already carries the next 1:1 (`peopleCaption`, :73).
- A note tagged `prompt` is not loose (it is a Thread starter, `fresh-desk.yaml:60`).
- A seed note is loose only if it is `hs-seed-start-here` (see 4.3; the id
  prefix is the only mark and `compose.ts` already receives ids).
No DB change. `Start here` stays the one seeded icon.

**I. The seed carries one desk note.**
`holdspeak/seeds/fresh-desk.yaml`: notes keep `Start here` and the `prompt`
starter `Weekly update`. `About me`, `Current priorities`, `1:1 prep` and the kb
`Everyday context` leave the seed and go to `docs/internal/PARKED-SEED-NOTES.md`
(the existing park, with a dated section as U18 did). Desks seeded before keep
theirs (the seed never removes; `seed.py:231`). The first-run `First dictation`
note (`FirstWords.tsx:272`, `useFirstTake.ts:220`) is titled by its first six
words, not `First dictation`: it is his.

**J. The dock is apps.**
`applications.ts`: add `dock: { order: 3, launch: "surface" }` to People (:439)
and `dock: { order: 4, … }` to Conductor (:141). `AttentionDrawer.tsx:108`,
`DeliveryBoard.tsx:390`, `SessionPullout.tsx:259` stop calling
`announceLauncher` (the windows stay reachable by ⌘K and Go/the Window menu;
the attention doc owns the Missed drawer's fate). `RoomActions` is not mounted
in `Dock.tsx:606` (the two verbs keep their menu rows and keys). `Dock.tsx:410-416,
530-541` (SENT/SEND FAILED) and :521-529 `READY n` are removed; `REC` stays.
`LAUNCHER_SEAT` stays (nothing announces; parked by non-use, with a
`// PARKED (PHILO-17 words)` comment at each announce site). The dock at 393
is the windows doc's.

**K. Wallpaper is a Settings row.**
`applications.ts:56-70` `change-places`: drop `shortcut` and `group`, add the
`// PARKED (PHILO-17 words): Settings ▸ Wallpaper` comment; the row stays so
`MANIFEST_FLOOR` (22) and the sweep's case list hold (the sweep still opens it;
a parked window must still pass the fences, which it does today).
`settingsWallpaper.tsx:85` stops rendering `description`; the `GadgetGroup`
label (:27) reads `Wallpaper`; favorites stay (one star, one press). Sound and
motion controls are not rendered while the GL is parked (A.11: a switch that
changes nothing). `atmosphereRegistry.ts` is untouched (the names are names;
the descriptions stay in the registry for the day the GL returns).

**L. Go is six rows.**
`applications.ts`: remove `go` from Rhythm, Context, Workbenches, Activity,
Memory, Processes, Commands (their `group: "tool"` stays, so ⌘K finds each).
`DeskMenuBar.tsx:139` renders no Tools submenu when `GO_TOOL_APPLICATIONS` is
empty. `applicationManifest.test.ts:41,68,77-81` pins the new orders:
Go = Speak, Meetings, Today, Ask AI, People, Conductor.

**M. Names: Engines and Accounts.**
`applications.ts:474-492`: `configure-runs-on` label `Engines`,
`configure-integrations` label `Accounts`; `SettingsCore` card captions follow
(`RUNS ON` → `ENGINES`). Aliases keep the old `action` ids (no route change).
The windows doc turns Engines into a wing; the label is ready for it.

### 4.3 Data and API

Additive only:
- `monday_brief_service.py:342`: a `code` field on each `broke` row (string).
- Nothing else. No migration. The seed manifest shrinks; `seed.py` is unchanged.

### 4.4 What is parked, and where

| Thing | Park |
|---|---|
| `About me`, `Current priorities`, `1:1 prep`, kb `Everyday context` | `docs/internal/PARKED-SEED-NOTES.md`, a dated PHILO-17 section with the YAML |
| `change-places` app placement (`⌘⇧P`, `group`) | the manifest row stays with a `// PARKED` comment; the window stays (sweep) |
| `RoomActions` (dock Places + Hide the menus) | `web/src/desk/components/window/_parked/RoomActions.tsx` (`_parked` is excluded by `tsconfig.json:21`, `vite.config.ts:113`) |
| the three `announceLauncher` calls | left in place behind a `DOCK_LAUNCHERS = false` constant in `launcherRegistry.ts` with the `// PARKED` comment; the drawer code is untouched |
| `dockStateLabel` (SENT badge) | `dockState.ts` keeps the function; `Dock.tsx` stops calling it; its vitest moves to `web/src/desk/components/window/__tests__/_parked/` |
| the `description` lines of the eight places | stay in `atmosphereRegistry.ts`, not rendered |
| `ASK_LENSES` | stay in `ask.ts` for the meeting-scoped Ask |
| the review axes tokens (`SUPPORTED`, `LINKED`, …) | `reviewModel.ts` keeps the enums; only the words change. Nothing to park |
| Go ▸ Tools entries | the `go` field is removed; the rows stay, ⌘K finds them |

### 4.5 The guard: the glossary is enforced

`docs/product-language.json` `copy_contract.prohibited_operational_patterns`
gains one rule:

```json
{
  "id": "phase-words",
  "pattern": "\\b(?:PROPOSAL|UNREVIEWED|SUPPORTED|GOVERNING|KEPT|IN INBOX|READS|EVERYDAY CONTEXT|GROUNDING|GROUND THIS ASK|CTX|NO TRAFFIC|USES ASSIGNMENT|LANDS IN|DRY RUN|LISTENER|HOLD NONE|THIS DEVICE|RANKED|MTG|DEC|ACT|MEANING|NOT SET)\\b",
  "reason": "PHILO-17 words: a chip is a name, a time, a count or a host; state lives in the verb (docs/internal/philo/phase-17/DESIGN-words.md)."
}
```

`tests/unit/test_product_copy.py` already scans `web/src/**/*.tsx` and keeps
the debt ledger `tests/fixtures/product_copy_debt.json`, which only shrinks
(:80). Slice 1 records today's offenders in the ledger; every later slice
deletes its lines. `test_each_prohibited_product_copy_rule_is_exercised` (:94)
gets the example `"PROPOSAL"`. Case: the rule matches the source literal, so
literals are written in sentence case from now on and CSS uppercases captions;
a sentence-case `Proposal` in a sentence of docs prose is outside `web/src` and
not scanned. (The `_BANNED` list in `test_web_vocabulary_guard.py` is left
alone: it has no debt ledger, and a frozen allowlist would be a second
ratchet for the same words.)

`docs/GLOSSARY.md` and `POSITIONING.md` "Canonical feature names" get the four
renamed rows (Note, Engines, Accounts, Wallpaper) in the same PR as the rename.

### 4.6 OWNER CALLs

1. **One noun for what he writes.** Recommendation: **Note** everywhere a user
   reads (`Write a note`, the window title, `NOTES 3` in The week); `Thread`
   stays for a conversation with an agent; `Thought` disappears as a word.
   The data model is untouched (the attention doc merges the machinery). The
   other option: keep `Thought` as the name of a note that is being worked on
   and `Note` for the rest. Two nouns for one object is what the recon calls
   out.
2. **Persons on the desk.** Recommendation: a person is never a loose icon;
   People is the ledger and its drawer caption carries the next 1:1. The other
   option: a loose icon only for a person with a 1:1 today, with a lamp.
3. **The Ask lenses.** Recommendation: the desk Ask opens empty with
   `Ask about your desk`; the five lens checkboxes leave the desk Ask and stay
   on the meeting-scoped Ask where "Summarize the following" makes sense. The
   other option: keep the lenses as five ghost Buttons under the box that fill
   the draft on press.
4. **Seeds.** Recommendation: one seeded desk note (`Start here`) and the
   `prompt` starter; the three prompt notes and the kb go to the park. The
   other option: keep all five inside a `Start here` drawer icon. A drawer
   is a Project in this desk (`compose.ts`), so that option costs a new
   drawer kind; the recon's own first ask was "or are cut".

## 5. The slices

Each slice is one PR on the fast cycle: `scripts/quick_check.sh`, merge,
the watcher runs the suite, Astra after. The word tables in 4.1 are the spec
for every slice; no slice invents a word.

**Slice 1, the egress rule and the guard (the foundation).**
Files: `gadgets.tsx` (EgressChip), `egress.ts`, `turnRoute.tsx`,
`briefEgress.tsx`, `settingsPrefs.tsx:782`, `docs/product-language.json`,
`tests/fixtures/product_copy_debt.json` (today's offenders recorded),
`tests/unit/test_product_copy.py:94` (the example).
Tests: T2 `web/src/desk/surface/__tests__/egress.test.ts` (local scope renders
nothing; LAN renders the host); T1 none; T3 the sweep's `egress` fence already
asserts a host chip where a fetch leaves (reads unchanged). The canon ratchet
(`test_ux_canon_ratchet.py`) stays green: A9 is static.
Risk: a face that used `THIS DEVICE` as its only foot content shows an empty
slot; `SurfaceFooter` keeps the slot geometry ("empty slots never move their
neighbours", UX-CANON D).
He judges: open a thought and the Brief; no `THIS DEVICE` anywhere; the
Speak face still shows `HUGGINGFACE.CO` on the download row.

**Slice 2, the meeting row and the kind plate.**
Files: `reviewModel.ts`, `MeetingReview.tsx:484-525,679-719`, `ClaimAxes.tsx`,
`MeetingDetail.tsx:98-151`, `kit.tsx:154` (KindPlate words), `needsFace.ts:123-125,
415`, the debt ledger (lines removed).
Tests: T2 `web/src/pages/cores/history/__tests__/meetings.app.test.tsx` (a
proposed action row renders exactly `Tomas` and `no date` and two verbs; a
disputed row renders `Not in the transcript`; the kept list says `Confirmed`);
T2 `kit.test.tsx` (KindPlate words); T3 the sweep's `readable` and `12 px`
fences on the meeting case at 393 (the wider plate must not clip).
Risk: `KNOWN_REDS` entries keyed on the meeting case that named a chip text
heal and must be removed in the same PR (strict xfail).
He judges: import the standup; Outcomes rows read `Complete the reconcile
step · Tomas · no date · Confirm · Decline`.

**Slice 3, the thought window words.**
Files: `ThoughtWorkspaceWindow.tsx` (:513, :390-422, :424-430, :567-585),
`thoughtReceipt.ts`, `thought-workspace` CSS for the foot's case,
`NoteSendWells` destination row, the debt ledger.
Tests: T2 `web/src/desk/thought-workspace/__tests__/note.app.test.tsx` against
the recorded hub answer (`web/src/test/recordedHub.ts`): foot = `Saved h:mm`
only; no `READS`; the send well names the path once. T3 sweep `thought` case.
Risk: the attention doc rewrites this window's verbs next; this slice
touches only tokens and the foot, so the two merge cleanly.
He judges: Write a thought → Finish; count the words on the face.

**Slice 4, Ask AI and Speak words.**
Files: `AskPanel.tsx` (:89, :275-321, :309-313, :494-541, :44-50 shape),
`GroundingSection.tsx:171`, `AssignmentSummary.tsx` (not mounted on the desk
Ask; the verbs doc's chip takes its slot), `SpeakFace.tsx:330,529-556,903`,
new `hotkeyWords.ts`, `tests/unit/test_hotkey_face_words.py` (derives tokens
from `desktop_permissions.py`), the debt ledger.
Tests: T2 `ask.app.test.tsx` (opens empty; no SESSION; the failure shape),
T2 `speak.app.test.tsx` (NONE hotkey → `No hotkey · Set one`), T1 the new
code-derivation test. Seam: the verbs doc delivers the reason text; this
slice draws `Not answered · <reason> · Ask again` with the hub's current
text as the reason until then.
Risk: the lens cut is OWNER CALL 3; build the recommendation, keep
`ASK_LENSES` so the other option is one import away.
He judges: ⌘I; the box is empty; ask "What do I owe Mira this week?".

**Slice 5, the desk shows his things.**
Files: `compose.ts:210-238`, `fresh-desk.yaml`, `PARKED-SEED-NOTES.md`,
`FirstWords.tsx:272,300`, `useFirstTake.ts:220`, `api.ts:559` (an artifact
without a title says `Actions` not `action_items`).
Tests: T1 `tests/unit/test_desk_seed.py` extended (the seed makes one desk note and
one prompt note; the park doc lists the rest by id); T2 `compose.test.ts`
(an artifact with a meetingId is not loose; an empty thread is not loose; a
person is not loose; a `prompt` note is not loose); T3 the sweep's bare desk
at 393 (`chair:*`).
Risk: his real desk was seeded on 2026-10-08 and keeps its five notes (the
seed never removes). He can delete four notes himself, or `Reset to seed`
(`seed.py:322`) on a copy first. Say so in the PR body.
He judges: a fresh HOME boots to People, Conductor, `Start here`; after a
meeting the desk gains the meeting icon only.

**Slice 6, the dock and Go.**
Files: `applications.ts` (People and Conductor `dock`; seven `go` removals;
`change-places` parked; the two renames), `Dock.tsx:410-416,521-541,606`,
`launcherRegistry.ts` (`DOCK_LAUNCHERS`), `RoomActions.tsx` → `_parked/`,
`DeskMenuBar.tsx:139`, `applicationManifest.test.ts`, `settingsWallpaper.tsx`
(:27 label, :85 description, sound/motion), `SettingsCore` captions,
`docs/GLOSSARY.md`, `POSITIONING.md` names table.
Tests: T2 `applicationManifest.test.ts` (new orders; `DOCK_APPLICATIONS` is
five; `GO_TOOL_APPLICATIONS` is empty); T2 `dock.app.test.tsx` (no launcher
tiles, no SENT badge, REC while recording); T3 the sweep (`palette` case still
lists Rhythm, Workbenches… under `Do`; the `change-places` case still opens).
Risk: `test_dock_pager_waiver_is_the_ratified_geometry`
(`test_desk_sweep.py:1217`) pins the dock pager's geometry at 393; with five
tiles the pager may not appear and the waiver test must be re-read with the
windows doc's 393 dock. Name it in the PR; the windows doc owns 393.
He judges: the dock is five apps; HoldSpeak ▸ Settings ▸ Wallpaper picks a
still in three presses; Go has six rows.

**Slice 7, the brief and the search words.**
Files: `monday_brief_service.py:342` (`code`), new `briefWords.ts`,
`ChairHome.tsx:2362-2418`, `paletteHit.tsx:75`, `DeskToolShelf.tsx:58,783-830`,
`NeedsDrawer.tsx:610`, `ChairHome.tsx:1092`, `DeliveryBoard.tsx:197,500,565`,
`ConductorWindow.tsx:227,592` and the prose line, the debt ledger (empty for
`phase-words` at the end of this slice).
Tests: T1 `tests/unit/test_monday_brief_outcome_words.py` extended (every
`broke` row carries a code the web table knows); T2 `today.app.test.tsx` (a
`broke` row reads `Ask AI did not run · No engine · Set up`); T2
`palette.app.test.tsx` (a JSON snippet renders its `text`); T3 the sweep's
`today` and `palette` cases.
Risk: the attention doc may cut the Brief chair window first; these words
apply to Today ▸ Brief, which stays.
He judges: ⌘K "ledger": no braces on the face; Today ▸ Brief reads in words.

First slice to build: **Slice 1**. It is one library change and the guard;
every other slice deletes its lines from the ledger it creates.

## 6. What not to do

- **No `Chip` species, no i18n layer, no word service.** The recon's words
  are forty literals in twelve files. A new `Chip` component with a word
  registry would be a Phase of its own and would not change one word he sees.
  The guard rule in `product-language.json` is the registry; it already
  exists and already ratchets.
- **No hub-side rewording.** The hub's sentences (`NOT_SET_UP_REASON`,
  `hotkey_failure_token`) are also the CLI's and the MCP's words. One additive
  `code` on the brief row and two web word tables (the `channels.ts` pattern,
  with a derivation test) is the whole bridge.
- **No seed flag column.** `hs-seed-*` ids are the mark; `compose.ts` already
  has the ids. A `seeded` column is a migration for a filter.
- **No deletion of manifest rows.** Parking by placement keeps the sweep's
  cases, `MANIFEST_FLOOR` and the ⌘K reach. A deleted row is a verb that
  disappears without a park, against the never-delete rule.
- **No drawer for the seeds.** A drawer is a Project in this desk; building
  a non-project drawer kind to hold four notes the recon says to cut is the
  stage set again.
- **No merge of Note, Thought and Thread in the data model here.** It is a
  words design. One noun on the face now; the machinery is the attention
  doc's, and the storage merge (`/api/notes`, thought workspaces, `/api/threads`)
  is not worth a migration until that machinery exists.
- **No new atmosphere work.** The GL is parked; the places are stills; the
  Settings row exists. Rendering eight prose lines less is the whole change.
- **No 393 dock design here.** The four-button phone dock is the windows
  doc's; this design only makes the 1440 dock five apps so that the 393 cut
  is a subset, not a second list.
