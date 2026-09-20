# 03 — The Interaction Walk (2026-09-20)

Every verb pressed, every keyboard path, every menu, on every surface the
web desk has, at **1440x900** and **393x852**.

The census lane (`01-measured-walk.md`) measures what a surface LOOKS
like. This lane measures what it DOES. Rule ids are the rulebook's
(`00-rulebook.md`); where a UI/UX review-skill rule is the sharper
statement it is named as `skill §N/<rule-id>`.

## How this was measured

| Fact | Value |
|---|---|
| Harness | `scripts/surface_interaction_walk.py` (this lane; no product code changed) |
| Machine data | `docs/internal/surface-inventory-2026-09-20/interaction.json` |
| Shots | `docs/internal/surface-inventory-2026-09-20/assets/interaction/` |
| Hub | one real `MeetingWebServer` per run, isolated `HOME=$(mktemp -d)`, seeded by `scripts/walk_working_desk.py serve` (`DeskService.seed` + the `_populate` meeting/decisions/brief/agent-session block) plus two projects and two notes over HTTP |
| Browser | Chromium, `--use-fake-device-for-media-stream` (a FAKE device; the real microphone is never opened) |
| Refused on purpose | the mic species (`.desk-mic`, `.desk-orb`, `.desk-first-talk`, `.gadget-transport-key`), and the desk-wide reset/wipe verbs (they would eat the walk's own seed). Every one is reported **NOT ASSESSED**, never a pass. |
| Honest gaps | People was **not seeded**: `POST /api/people/setup` is the one gesture that builds the encrypted sidecar and it goes through the macOS Keychain — a walk must never raise a Keychain prompt on the owner's machine. The People surface is measured EMPTY; its populated states are NOT ASSESSED. A LAN engine could not be defined either: `POST /api/inference/model-library/define-endpoint` needs a profile head to bind to and the seeded library has none (`interaction.json.seed.engine`). |

## 1. The executive table — surface × the seven lanes

`pass` = measured and clean. `fail` = measured and broken. `NOT ASSESSED`
is never a pass. One row per surface the walk opened, both widths.

| Surface | 1 verbs | 2 keyboard | 3 touch @393 | 4 motion | 5 IA door | 6 egress | 7 window grammar |
|---|---|---|---|---|---|---|---|
| First Words (cold arrival) | **fail** — 5 verbs, 2 disabled, the primary is the mic, the only way out is a ghost | **fail** — reachable, but the way out is the ghost verb | **fail** — the mic gadget on the field is 20×20 | pass | **fail** — it is the ONLY face a cold desk has; the surface registry behind it reads `recovery-only` | n/a | n/a — no window, no dock, no menu bar |
| Menu bar | pass @1440 (46 entries enumerated) | pass @1440 | **fail** — 22-26px tall titles, 2-4px apart | pass | **fail @393** — the bar renders only `Go`; `Desk`, `Object` and `Window` are still in the DOM and still in the accessibility tree, but no menu opens from them | n/a | n/a |
| Dock | **fail** — 3 of 11 app buttons unpressable @1440 behind an open window; **11 of 11 @393** | pass (all 11 are still tab stops @393 — they are focusable while unreachable by pointer) | **fail** — the dock is laid out at desktop width inside a 393 viewport: `Overview` measures x=1313, `Reset layout` x=1343. Each dock chip's close X measures **0×11 px** | pass | **fail @393** | n/a | n/a |
| ⌘K tool shelf | **fail** — the `Ask AI` row is a permanent ghost (`aria-disabled="true"`, `desk-deck-row is-ghost`) | pass — opens on ⌘K, Escape closes, Enter opens the highlighted row | NOT ASSESSED | pass | pass — 32 rows at both widths | n/a | n/a |
| Intelligence | pass @393; NOT ASSESSED @1440 (6 of 11 verbs never became clickable) | pass | **fail** | pass | pass | pass (read-only) | pass |
| Speak | **fail** — `SPEAK` tab dead | pass | **fail** | pass | pass | **fail** — `Talk` has no badge beside it (B.1) | pass |
| Meetings | **fail** — `ARTIFACTS` tab dead at both widths | pass | **fail** | pass | pass | pass — `Open` fires the intel routes and the surface carries `RouteDisclosure` | pass |
| Agents | **fail** — `ROSTER` and `How it connects` dead at both widths | pass | **fail** | pass | pass | NOT ASSESSED | pass |
| Settings | **fail** — `SETTINGS` tab and the `Meetings … Open` row verb dead; 8 of 20 verbs never became clickable @393 | pass | **fail** | pass | pass | **fail** — a prop-less `<EgressChip/>` at `SettingsCore.tsx:1846` | pass (the only 1392-wide window; 1 scroller) |
| Change places | **fail** — `All places` plus **4-5 of the 9 `Favorite X` toggles** produce no change | pass | **fail** | pass | pass | n/a | pass |
| Rhythm | **fail** — `Run now` and `Generate` fire, but both are egress with no badge | pass | **fail** | pass | pass | **fail** — `Run now` → `POST /api/settings/heartbeat/run-now`, `Generate` → `POST /api/brief/generate`, neither badged nor receipted | pass |
| Context | NOT ASSESSED — 5 verbs, `Save` disabled, the only live verb is the mic | pass | **fail** | pass | pass | n/a | pass |
| Workbenches | pass — `+ Create` opens `New Workbench` | pass | **fail** | pass | pass | n/a | pass |
| Activity | pass — `Refresh now` fires the connector read | pass | **fail** | pass | pass | NOT ASSESSED — the connector read is egress-shaped and unbadged | pass |
| Desk memory | **fail** — the body is EMPTY on a populated desk; all five filter chips change nothing; `Search` is disabled | pass | **fail** | pass | pass | n/a | pass |
| Processes | NOT ASSESSED — 3 verbs @1440 / 2 @393, none changed anything observable | pass | **fail** | pass | pass | n/a | pass |
| Commands | pass — `Enable in Settings` opens Settings | pass | **fail** | pass | pass | n/a | pass |
| Models | NOT ASSESSED — `Adjust` and the first assignment row never became clickable at either width | pass | **fail** | pass | pass | **fail** — the catalog `Download` (B.1) | pass (1 scroller) |
| Ask AI | **NOT ASSESSED** — could not be opened from ⌘K at either width: its row is disabled | pass by the Go menu (⌘I opens it) | NOT ASSESSED | pass | **fail** — two doors, one of them dead | NOT ASSESSED | NOT ASSESSED |

## 2. The verbs (T3, A6, UX-CANON A.11)

### 2.1 — the dead-verb list

A verb is called dead when it was pressed, the press succeeded, and
nothing observable followed: no request, no window, no pullout, no
change to the page text, no change to any window's geometry or class.
Measured at both widths unless a width is named.

| Surface | Verb | Widths | What a press produced |
|---|---|---|---|
| Change places | `Favorite Rainy City` | 1440 + 393 | nothing |
| Change places | `Favorite Lantern Garden` | 1440 + 393 | nothing |
| Change places | `Favorite After-Hours Radio` | 1440 + 393 | nothing |
| Change places | `Favorite Midnight Archive` | 1440 + 393 | nothing |
| Change places | `Favorite Deep-Sea Station` | 393 | nothing |
| Change places | `All places` | 1440 + 393 | nothing (it is the active filter on open, so this may be honest; `Favorites` beside it did change state) |
| Desk memory | `Filter: All` | 1440 + 393 | nothing — **but the window's body is empty**, so this is not proof the filter is broken (see finding 7) |
| Desk memory | `Filter: Decisions` | 1440 + 393 | nothing (same caveat) |
| Desk memory | `Filter: Commitments` | 1440 + 393 | nothing (same caveat) |
| Desk memory | `Filter: Briefs` | 1440 + 393 | nothing (same caveat) |
| Desk memory | `Filter: Meetings` | 1440 + 393 | nothing (same caveat) |
| Meetings | `ARTIFACTS` (tab) | 1440 + 393 | nothing — and it was NOT the active tab: `REVIEW` had just been pressed and did change state |
| Agents | `ROSTER` (tab) | 1440 + 393 | nothing |
| Agents | `How it connects` | 1440 + 393 | nothing |
| Settings | `Meetings ✓ INTELLIGENCE ON · AFTER ROOM MEETINGS Open` | 1440 + 393 | nothing — the sibling rows (`Models`, `Connections`, `Voice`) all did something |
| Models | `⚠ github Connections ✗ CREDENTIAL EXPIRED GITHUB authentication_required` | 1440 + 393 | nothing — a warning that reads like a verb and is not one |
| Speak | `SPEAK` (tab) | 1440 + 393 | nothing (the active tab on open — honest) |
| Settings | `SETTINGS` (tab) | 1440 + 393 | nothing (the active tab on open — honest) |
| Activity | `RECORDS` (tab) | 1440 + 393 | nothing (the active tab on open — honest) |

**Six verbs are dead on any reading** (five `Favorite X` toggles and
`ARTIFACTS`); the five Desk-memory filters answer with nothing but sit
over an empty body, so they are reported with that caveat; four more (`ROSTER`, `How it connects`, the
Settings `Meetings` row, the Models warning row) are dead with no
"active tab" excuse. The five active-tab rows are listed for honesty and
are not counted as defects.

### 2.2 — verbs whose effect is invisible (T3)

`Rhythm` holds four ledger rows whose whole row is a `[role=button]`
(`Sweep ↻ …`, `Runs on ↻ THIS DEVICE`, `Monday brief … Generate`,
`Notify ↻ …`). Pressing the ROW does nothing; the verb inside it
(`Run now`, `Generate`) does. A row that takes the pointer and answers
with nothing teaches the user that the surface is broken.

### 2.3 — verbs that could not be pressed (NOT ASSESSED, never a pass)

| Where | Count | Why |
|---|---|---|
| Dock @1440 | 3 of 11 (`Intelligence`, `Speak`, `Meetings`) | the button never became clickable within 4s — an open window covers that end of the dock |
| Dock @393 | **11 of 11** | no dock button was clickable at any point in the run |
| Settings @1440 | 6 of 21 | never became clickable |
| Settings @393 | 8 of 20 | never became clickable |
| Intelligence @1440 | 6 of 11 (`BRIEF`, `FOLLOW-THROUGH`, `DECISIONS`, and three rows) | never became clickable; the same six ARE pressable at 393 |
| Models | 2 of 23-24 (`Adjust`, the first assignment row) | never became clickable at either width |
| Ask AI | the whole surface | its ⌘K row is `aria-disabled="true"` |
| Every mic species | 12 verbs | the walk never presses the microphone |

### 2.4 — verbs that need a second gesture nobody signals (T3)

* The Object menu's `Move to Zone` does not move anything: it opens the pullout and leaves the user to find the Filing disclosure inside (`web/src/desk/verbRegistry.ts:539-544`, comment in place).
* The Object menu's `Duplicate` returns silently for any kind `duplicateOverrides` has no case for (`verbRegistry.ts:88-116`, `:519-521`).
* Every dock chip carries a **0×11 px** close X (measured). It is a verb, it is in the accessibility tree with the name `Close <window>`, and it has no hit area at all until the chip is hovered.

## 3. The keyboard scorecard (skill §1)

| Measure | 1440×900 | 393×852 |
|---|---|---|
| Tab stops before the ring repeats | 32 | 37 |
| Stops with **no** visible focus ring (outline < 1px AND no box-shadow) | **0** | **0** |
| Stops that are off-screen | 0 | 0 |
| Tab-order inversions vs visual order (pairs) | 35 / 496 = **7%** | **183 / 666 = 27%** |
| ⌘K opens by keyboard | yes | yes |
| Escape closes the shelf | yes | yes |
| Escape closes the window Enter opened | yes | yes |
| Icon-only buttons with no accessible name | **0** | **0** |
| Menus openable by keyboard | Desk, Object, Go, Window all open | **only `Go`** — the other three titles enumerate (they are in the accessibility tree) but never render a menu |

Focus rings and accessible names are a genuine pass: every one of the 69
measured tab stops across both widths carried a ring, and not one
icon-only button was anonymous. Tab order at 393 is the failure: better
than one pair in four is out of reading order.

### 3.1 — the five owner jobs, no mouse

| Job | ⌘K query | Reached by keyboard alone | What actually opened | Completable with no mouse |
|---|---|---|---|---|
| Dictate | `Speak` | yes, both widths | `Speak` | **NOT ASSESSED** — the walk never presses the microphone |
| Record → summary | `Meetings` | yes, both widths | `Meetings` | **NOT ASSESSED** — needs a real recording |
| Write a thought | `Thoughts` | the shelf answered, but with **`Intelligence`** at both widths | `Intelligence` | **fail** — there is no surface named Thoughts to reach; the typed word lands somewhere else |
| Find a note later | `Notes` | the shelf answered, but with **`Change places`** @1440 and **`Telegram control`** @393 | wrong window at both widths | **fail** — typing the name of the thing and pressing Enter opens something unrelated |
| Set up an engine | `Models` | yes, both widths | `Models` | **fail beyond the door** — `Adjust` and the first assignment row never became clickable at either width |

Two of the five jobs cannot be *started* by keyboard: ⌘K's Enter commits
the highlighted row, not the typed match, so `Notes` opens `Telegram
control` and `Thoughts` opens `Intelligence`.

## 4. Touch at 393 (skill §2)

Measured on the desk and again inside an open `Meetings` window.

| Measure | Desk @393 | Meetings window @393 | Desk @1440 (reference) |
|---|---|---|---|
| Interactive targets in view | 61 | 59 | 74 |
| Targets under 44×44 | **48 (79%)** | **49 (83%)** | 64 |
| Neighbour pairs closer than 8px | **30** | 27 | 28 |
| Hover-only disclosure (a `title` and no visible text) | 4 | 5 | 4 |
| Icon buttons with no accessible name | 0 | 0 | 0 |
| Document horizontal overflow | **0 px** | 0 px | 0 px |

Worst offenders, measured: window traffic lights at **16×14**; the mic
gadget on a search field at **20×20**; `Overview` and `Reset layout` at
**26×22**; the dock chip close X at **0×11**. Three follow-through rows
sit **1px** apart.

Two verbs are outside the 393 viewport entirely (M3):
`Overview` at **x=1313** and `Reset layout` at **x=1343** in a 393-wide
window, and the `Desk memory` bell at **y=-20**, above the top edge.

No horizontal-swipe conflict was found: `document.scrollWidth` equals
`clientWidth` at 393 on every surface measured, and no surface owns a
horizontal scroller.

## 5. Motion (skill §7, M12)

| Measure | 1440 | 393 |
|---|---|---|
| CSS transitions or animations longer than 400ms | **0** | **0** |
| Transitions on `width` / `height` / `top` / `left` | **0** | **0** |
| Animations running at rest | 5 | 5 |
| `prefers-reduced-motion` honoured in a second pass | **yes** — the reduced pass reports `reducedMotionMatches: true` and the same zero counts | yes |

Motion is the cleanest lane in this walk. The window entrance is a
framer-motion spring that is skipped outright under reduced motion
(`web/src/desk/components/DeskWindow.tsx`, the `initial={reducedMotion ||
!entrance ? false : …}` guard).

## 6. Window grammar (T6)

| Measure | 1440 | 393 |
|---|---|---|
| Windows that carry a title bar | all 14 opened | all 14 |
| Title-bar gadgets | **3** (`Close`, `Minimize`, `Maximize`) | **2** — maximize is withdrawn |
| Footer present | all 14 | all 14 |
| Becomes a sheet at 393 | — | **all 14** (`is-sheet`, x=0, full width, bottom-anchored) |
| Windows with horizontal overflow inside | 14 × **3 px** | **0 px** |
| Windows outside the viewport | 0 | 0 |
| Nested scrollers | 0 or 1 per window (Settings, Change places, Rhythm@1440, Models) — never 2 | same |

The 393 story is good: every window becomes a full-width sheet, nothing
overflows, scroll ownership is single. The 3px horizontal overflow
inside every window at 1440 is uniform enough to be one shared rule, not
fourteen bugs.

## 7. The IA table — entry → what it opens

Measured by pressing every entry, not read from source.

### Desk menu (13 entries, all live)

| Entry | Measured effect |
|---|---|
| New Note ⌘N | opens window + pullout `Edit New note` (39 requests) |
| New Decision ⌘⇧N | state change only, 20 requests — **no window** where its six siblings all open one |
| New Knowledge | state change only, 38 requests — **no window** |
| New Agent | opens `Edit New Agent` |
| New Workflow | state change only, 38 requests — **no window** |
| New Workbench | opens `New Workbench` |
| New Zone | state change only, 38 requests — **no window** |
| New Thread | opens `th_…` |
| New Project | opens `New Project` |
| Hide the menus ⌘⇧F | state change |
| List view | state change |
| Open Intelligence | opens `Intelligence` |
| Open People | opens `People` |

Four of the nine `New …` verbs mint the object and open nothing, while
five open an editor. Same menu, same verb family, two outcomes.

### Object menu (10 entries)

**All ten are ghosts on arrival** (`aria-disabled`), because nothing on
the desk is selected. 100% of the menu is unusable at the moment a user
first opens it.

### Go menu (15 entries)

Every one opened its surface: `Ask AI`, `Meetings`, `Settings`, `Change
places`, `Agents`, `Rhythm`, `Context`, `Workbenches`, `Activity`, `Desk
memory`, `Processes`, `Commands`, `Models` each opened a window named for
the entry. Two exceptions: `Speak` was NOT ASSESSED (mic guard), and
`Connections` fired one request and changed state **without opening a
window named Connections** — it is an alias that re-scopes the already-open
Settings window.

### Window menu (8 entries)

**All eight are ghosts on arrival** ("No window open"). With windows
open they work.

**Menu-bar arithmetic: of 46 entries, 18 (39%) are disabled the moment
the desk finishes loading.**

### Dock (11 buttons + 2 tail verbs + the orb)

`Intelligence`, `Speak`, `Meetings`, `Agents`, `Settings`, `Floor`,
`Desk memory`, `Delivery`, `Panes`, `Hide the menus`, `Change places`,
then one chip per open window (`Focus X` + a 0×11 `Close X`), then
`Overview` and `Reset layout`, with the `Record a meeting` orb in the
centre. The dock label for the Agents application is **`Agents`** while
the Go menu calls the same thing **`Agents and coder sessions`** (C2).

### ⌘K (32 rows, identical at both widths)

2 PROJECT rows · 6 VERB rows (`New Note` … `New Workbench`) · 14 PROGRAM
rows · 2 DRAWER rows (`Delivery`, `Panes`) · 6 SETTINGS rows (`Voice`,
`Sounds & Presence`, `Wallpaper`, `Meetings`, `Rhythm`, `Models`).

The catalog carries **no** row for `Components`, `Live meeting` or
`Calendar snapshot` — the three applications with no door (A.1) — and its
`Ask AI` row is permanently disabled.

## 8. The ranked findings — top 20 by owner cost

Cost is what it takes from the first user on a Tuesday, not how hard it
is to fix.

| # | Finding | Rule | Where | Evidence |
|---|---|---|---|---|
| 1 | **The dock is off the screen at 393.** It is still laid out at desktop width inside a 393px viewport — `Overview` measures x=1313 and `Reset layout` x=1343 — so all eleven buttons refused a press for the whole run, and `dock-393.png` shows no dock at all. The dock is the only persistent door at the phone width, and it is also where the `Record a meeting` orb lives. | M3, T3, skill §9/`persistent-nav` | `web/src/desk/components/window/Dock.tsx:105-301` | `interaction-393.json` dock.presses (11 × CLICK-FAILED); `dock-393.png` |
| 2 | **Three of the four menus never open at 393.** The bar renders only `Go` (`dock-393.png`); `Desk`, `Object` and `Window` remain in the DOM and in the accessibility tree — the walk reads their labels — but activating any of them renders no menu. Every "New …" verb and every window verb is gone at the phone width while a screen reader still announces them. | T3, C3, A6 | `web/src/desk/components/DeskMenuBar.tsx:86-119` | `interaction-393.json` menus.menus[0..1,3].error |
| 3 | **A cold desk has exactly one face, and its way out is a ghost.** First Words fills the screen, the surface registry behind it reads `recovery-only`, its two content verbs (`Copy`, `Keep as Note`) are disabled, its primary verb is the microphone, and the only escape is a `btn--ghost` reading "Continue later". It also carries a sentence of prose — "Speak. Then edit and keep your text." (A7). | T3, U4, A7, UX-CANON A.12 | `web/src/desk/components/FirstWords.tsx` | `first-words-gate-1440.png`, `first-words-gate-393.png`; gate block in both JSONs |
| 4 | **Eleven egress verbs carry neither a badge before nor a receipt after** — the steward's `Run once`, the sweep's `Run now`, the brief's `Generate`, `Send reply`, `Process pending`, `Preview route`, two `Download`s, `Draft review`, the PR write verbs, and dictation's `Talk`. Two of them were fired in this walk and confirmed on the wire. | **A3** | see Appendix B.1 | `POST /api/settings/heartbeat/run-now` and `POST /api/brief/generate` recorded with no badge on the row (`surface-rhythm-1440.png`) |
| 5 | **Four badges are present and false** — a `THIS DEVICE` chip beside an internet download, a hardcoded `THIS DEVICE` on the dictation face, a hardcoded `⌂` glyph in front of any host on Live, and five prop-less `<EgressChip/>` that print "This device" unconditionally. | **A3, A6** | see Appendix B.2 | source; `gadgets.tsx:745-747` defaults |
| 6 | **Two of the five owner jobs cannot be started by keyboard.** ⌘K's Enter commits the highlighted row, not the typed match: `Notes` opens `Telegram control` @393 and `Change places` @1440; `Thoughts` opens `Intelligence`. | T3, skill §1/`keyboard-nav` | `web/src/desk/components/DeskToolShelf.tsx:529-607` | owner_jobs block in both JSONs; `job-notes-1440.png` |
| 7 | **Desk memory shows nothing on a desk that has memory.** The window's body is empty (`surface-desk-memory-1440.png`) while the same desk holds a meeting, two decision records and a generated brief — all of them visible on the Floor behind the window. Its five filter chips change nothing and its `Search` verb is disabled. **Honest reading:** the filters cannot be judged separately while the result set is empty; the empty body is the defect to chase first. | A6, C4, T3 | Desk memory surface | `interaction-*.json` surfaces["Desk memory"] (both widths); `surface-desk-memory-1440.png` |
| 8 | **⌘K's `Ask AI` row is permanently disabled** (`aria-disabled="true"`, `desk-deck-row is-ghost`) while the Go menu's `Ask AI` opens it. Two doors to the same thing, one dead. | UX-CANON A.11, C3 | `DeskToolShelf.tsx` VERBS section over `object.ask` | both JSONs' `notes[]` (the 30s timeout naming `desk-palette-option-object.ask`) |
| 9 | **18 of 46 menu entries (39%) are ghosts the moment the desk loads** — the whole Object menu and the whole Window menu. | T3 | `verbRegistry.ts:130-131`, `:381-547`, `:611-667` | menu press block, both JSONs |
| 10 | **Four or five of the nine `Favorite X` toggles in Change places do nothing**, while one fires nine requests. A toggle that sometimes works is worse than one that never does. | A6, UX-CANON A.11 | Change places surface | surfaces["Change places"].dead_verbs, both widths |
| 11 | **Tab order at 393 is out of reading order in 27% of pairs** (183/666), against 7% at 1440. | skill §1/`keyboard-nav` | desk shell | keyboard block, `interaction-393.json` |
| 12 | **79% of touch targets at 393 are under 44×44**, and 30 neighbour pairs sit closer than 8px — three follow-through rows are 1px apart. Window lights are 16×14; a dock chip's close X is **0×11**. | M7, skill §2/`touch-target-size`, `touch-spacing` | `DeskWindow.tsx:837-864`, `Dock.tsx:271` | touch block, `interaction-393.json`; `touch-meetings-393.png` |
| 13 | **Nine call sites open nothing and say nothing** — `openSurfaceOr("project-room", "/projects")` ×7, `("people", "/people")`, `("open-intelligence", "/")`. None of those keys is registered and none of those hrefs is a route, so the user is returned to the bare desk. | C3, A6 | Appendix A.2 | source, cited per site |
| 14 | **Dev surfaces ship ungated in the product build.** Delivery announces its dock launcher before its own `if (!open) return null`, Panes the same, and roadmap/story/repository objects land in ⌘K and on the Floor wearing the raw token `STORY`. There is no `import.meta.env` gate anywhere in the web app. | T3 | Appendix A.3 | source, cited per surface |
| 15 | **Three registered applications have no door**: `Components` (nothing at all — not in Go, not in ⌘K, zero callers), `Live meeting` (the orb only) and `Calendar snapshot` (a file drop only). | C3 | Appendix A.1 | source |
| 16 | **`ARTIFACTS` in Meetings, `ROSTER` and `How it connects` in Agents, and the Settings `Meetings … Open` row are dead at both widths** — four verbs that are not the active tab and still answer with nothing. | UX-CANON A.11 | those surfaces | dead_verbs, both JSONs |
| 17 | **Four of the nine `New …` verbs mint and open nothing** (`New Decision`, `New Knowledge`, `New Workflow`, `New Zone`) while five open an editor. Same family, two outcomes, no signal which is which. | C1, T3 | `verbRegistry.ts:136-232` | menu press block, `interaction-1440.json` |
| 18 | **One thing, six names**: the Project Room is `Desk memory` / `Long memory` / the project's own name / `Open <name>` / `/project-memory` / `project-room`, and the canon word is `Project`. `Runs on` and `Sequence` are canon terms that render on no face. | C2, U6 | Appendix A.4 | source + `docs/product-language.json` |
| 19 | **Rhythm's ledger rows take the pointer and answer with nothing** — the whole row is a `[role=button]`, the verb inside it is what works. Four such rows. | T3, A6 | Rhythm surface | surfaces["Rhythm"], both widths |
| 20 | **The whole window layout lives in one browser key.** `localStorage["hs.desk.workspace.v1"]` alone holds every open window; clearing it empties the desk, and the hub knows nothing about it. A desk opened on a second browser is a different desk. | A6 | measured by this harness | `scripts/surface_interaction_walk.py` `close_all_windows` (the reset that works) |

### What this walk could NOT assess

* Every microphone verb (12 across the desk) — by law.
* The `Ask AI` surface — its ⌘K door is disabled and the walk opens surfaces from ⌘K.
* Populated **People** — seeding it needs the Keychain.
* A LAN engine defined through the product — `define-endpoint` needs a profile head the seeded library does not have.
* 6 of 11 Intelligence verbs and 6-8 of ~20 Settings verbs at one width or the other — they never became clickable inside 4s.
* Five applications outside this run's list (`People`, `New Project`, `Connections`, `Delivery`, `Panes` as surfaces of their own).


## Appendix A — the information architecture, read from source

Counts verified against the registry, and confirmed live by this walk's
menu enumeration (Desk 13 / Object 10 / Go 15 / Window 8).

**The brief says 25 applications. The registry holds 22**
(`web/src/desk/applications.ts:48-428`; `DESK_APPLICATIONS`), of which 18
are hosted surfaces, 5 ride the dock, 15 reach the Go menu, and one
(`configure-setup`) is commented out at `applications.ts:208-213`.

### A.1 — applications with no door

| Application | Registration | Reachable how |
|---|---|---|
| `design-components` "Components" | `applications.ts:249` | **Nothing.** No `group`, so not in Go and not in ⌘K; zero `openSurface("design-components")` callers repo-wide. Only by typing `/design/components` (`web/src/routes.tsx:75`) |
| `record-live` "Live meeting" | `applications.ts:175` | the RecordOrb only (`web/src/desk/components/RecordOrb.tsx:69`) — no menu, no ⌘K entry |
| `review-calendar-snapshot` "Calendar snapshot" | `applications.ts:393` | a drag-drop of a calendar file (`GlassDropLayer.tsx:68`) and one Settings row (`SettingsCore.tsx:1631`) — no menu, no dock, no ⌘K |

### A.2 — entries whose handler cannot do the job (C3, UX-CANON A.11)

`openSurfaceOr(key, href)` falls back to `shellNavigate(href)`; an
unrouted href hits `<Route path="*" element={<Navigate to="/" replace/>}>`
and drops the user on the bare desk with nothing opened and no error.

| Key used | Registered? | Fallback href | Routed? | Call sites |
|---|---|---|---|---|
| `"project-room"` | **no such action or alias** (`applications.ts:48-428`) | `/projects` | **no** (`routes.tsx:20-76`) | `chair/ChairHome.tsx:649`, `:662`, `:1484`; `components/SystemShade.tsx:450`, `:586`; `features/project-room/recall/RecallFace.tsx:84`; `pages/cores/history/MeetingReview.tsx:273` — **7 sites** |
| `"people"` | no (the action is `open-people`) | `/people` | **no** | `desk/pullouts/views/BriefView.tsx:477` |
| `"open-intelligence"` | has no `surface:`, so `SurfaceWindows` never registers it (`applications.ts:66-74`, `SurfaceWindows.tsx:46-56`) | `/` | yes, but `/` is the desk — the pullout never opens | `components/SystemShade.tsx:643` |

Nine call sites that silently return the user to the desk floor.

### A.3 — dev surfaces in the product build (T3)

There is **no build-time or runtime gate anywhere in the web app**: a
grep for `import.meta.env` finds only asset-base URLs. "RAW" is a fold
inside a surface (`SettingsCore.tsx:411`), not a mode.

| Surface | Gate | Evidence |
|---|---|---|
| Delivery board | **none** — its `announceLauncher` effect runs before the `if (!open) return null` at `:396`, so the "Delivery" chip is always in the dock and always in ⌘K PROGRAMS | `components/DeliveryBoard.tsx:349-394` |
| Panes (coder steering) | none | `components/SessionPullout.tsx:236,255-263` |
| RAILS (MissionControlConveyor) | data-gated only (`repos.length === 0` returns null); with any repo on the hub a floating "RAILS" button sits over the desk | `components/MissionControlConveyor.tsx:598,603-605`; mounted `DeskApp.tsx:220` |
| Story / Repository objects | ungated **and unfiltered** — `story` is in `ORDER` and not in `WORLD_ONLY_EXCLUDE`, so stories land on the Floor, in the List and in ⌘K OBJECTS wearing the raw token `STORY` (no `KIND_LABEL` entry) | `desk/world.ts:19-46`; `desk/tools.ts:38-50` |
| Roadmap objects | fetched on every desk refresh, filtered off Floor and List but still in `allObjects`, so they surface in ⌘K on any query | `desk/api.ts:700-705`; `world.ts:107-109`; `DeskToolShelf.tsx:348` |
| Processes, Activity | ungated first-class Go entries that are kernel/debug panes | `applications.ts:265`, `:342` |

### A.4 — one thing, many names (C2 / U6)

The full table is fourteen rows; these are the ones that cost the owner a
guess. Canon terms come from `docs/product-language.json`.

| The thing | The names it wears |
|---|---|
| The Project Room | registry label **Desk memory** (`applications.ts:285`) · eyebrow **Long memory** (`:291`) · window title becomes **the project name** (`ProjectRoomCore.tsx:1899-1901`) · ⌘K row **Open &lt;name&gt;** (`DeskToolShelf.tsx:251`) · href **/project-memory** · feature dir `features/project-room/` · canon says only **Project** (`product-language.json:65-70`). Six names. |
| "Desk memory" itself | the application above **and** the dock launcher that opens the SystemShade (`AttentionDrawer.tsx:76`). One string, two surfaces. |
| Engine placement | app label **Models** ×2 (`applications.ts:304`, `:412`) · a *different* Settings pane also labelled **Models** (`settingsPrefs.tsx:53`) · **Assignments** (`:55`) · route `/profiles` · href `/models` · dir `concierge` · canon term is **Runs on** (`product-language.json:101-106`) — **which appears on no face**. |
| Connections | Go menu **Connections** (`applications.ts:421`) · window title **Settings** · scope token `integration:destinations` · canon noun is **Integration**, with `connector` listed as a *legacy alias* (`product-language.json:95-100,147`). The face uses the legacy alias; the canon noun renders nowhere. |
| Rhythm | app **Rhythm** (`applications.ts:193`) with eyebrow **Follow-through** · a Settings module also **Rhythm** (`settingsPrefs.tsx:51`). Two doors, same name, different surfaces. |
| Agents | dock/window **Agents** · Go menu **Agents and coder sessions** · eyebrow **Companion** · create verb **New Agent** minting kind `recipe` (`verbRegistry.ts:173`) · canon key is `persona` (`product-language.json:71-76`). |
| Workflow / Sequence | `KIND_LABEL` gives **Workflow** to both `chain` and `workflow` (`tools.ts:40,48`); canon says `chain` is a legacy alias of **Sequence** (`product-language.json:89-94`) — a word on no face. |
| Change places | title **Change places** · dock button text **Places** (`RoomActions.tsx:46-49`) · eyebrow **Places to think**. |
| Activity | Go menu renders `≋`, dock/window render `⊙` for the same application (`applications.ts:268,270`). Same thing, two icons. |
| Speak | app **Speak**, action `dictate`, href `/dictation`, eyebrow **Daily cockpit**, the Settings module covering the same keys is **Voice** (`settingsPrefs.tsx:44`); canon has **no term at all** for the feature. |

## Appendix B — the egress table (A3)

Article III: the badge before the click, the receipt after. Read from
source across the whole web tree. "Badge beside" means inside the verb's
own visual group — a chip in the window head or the chrome bar is not
beside anything.

### B.1 — the eleven verbs with NEITHER

| Verb | File:line | What leaves the machine |
|---|---|---|
| `Run once` (project steward) | `features/project-room/steward/StewardPosture.tsx:635-645` | GitHub comments + a model draft. The effect chips exist — on the *Policy* face (`:516-528`), behind a second verb. |
| `Run now` (Cadence sweep) | `pages/cores/CadenceCore.tsx:326-334` | every configured connector read. Its chip renders only when `runs_on !== "local"` and lives in another section (`:412-432`). |
| `Generate` (weekly / Monday brief) | `CadenceCore.tsx:456-465` | the whole week's material to the brief model. |
| `Send reply` (agent-question loop) | `CadenceCore.tsx:587-595` | the typed reply to an agent pane. |
| `Process pending` (deferred plugin jobs) | `pages/cores/LiveCore.tsx:461-471` | queued intel jobs to the model host. |
| `Preview route` (intent router) | `LiveCore.tsx:412-418` | the typed text to the router model. |
| `Download` (Concierge preset) | `features/concierge/ConciergeCore.tsx:115` | model weights from the internet. |
| `Download` (Model Library catalog row) | `pages/cores/ModelLibraryCore.tsx:340-346` | model weights; `providerBoundary()` (`:81-83`) withholds the chip from catalog rows, and the receipt (`:415`) is a fixed sentence with no host. |
| `Draft review` (PR) | `components/PrReceiptsSection.tsx:114` | the diff to a model. |
| `Send agent` / `Post comment` / `Post status` (PR) | `PrReceiptsSection.tsx:114`, composer `:136-155` | writes to github.com. |
| `Talk` (dictation delivery) | `pages/cores/dictation/SpeakFace.tsx:368-371` | the utterance to the dictation engine, which may be LAN or cloud. |

### B.2 — four places where the badge is present and FALSE

A wrong badge is worse than a missing one: it is a reassurance.

| Site | File:line | The lie |
|---|---|---|
| Concierge preset row | `ConciergeCore.tsx:133` ← `useConciergeController.ts:82-91` | `THIS DEVICE` beside a `Download` that fetches from the internet (`engineHostLabel` returns `THIS DEVICE` for anything not cloud and not LAN). |
| Dictation footer | `pages/cores/DictationCore.tsx:154` | a hardcoded `<EgressChip label="THIS DEVICE" />` on a face whose own engine row (`SpeakFace.tsx:753`) can read a LAN IP or `CLOUD`. |
| LiveCore Intelligence chip | `LiveCore.tsx:450` | `label={"⌂ " + egressLabel}` — the home glyph is hardcoded in front of whatever host comes back, and no `scope` is passed, so a cloud host renders in the local tone carrying the default title "Transcript processing stays on this device." |
| Five prop-less `<EgressChip />` footers | `CadenceCore.tsx:641`, `LiveCore.tsx:658`, `SettingsCore.tsx:1846`, `settingsPrefs.tsx:634`, `ComponentsCore.tsx:197` | the component's defaults (`desk/surface/gadgets.tsx:745-747`) make a bare tag print `⌂ This device` unconditionally — on faces whose verbs demonstrably reach GitHub, Jira and remote models. The fix already exists in two places (`HistoryCore.tsx:262-267`, `MeetingReview.tsx:761-765`): with no route read, say nothing. |

### B.3 — why the one global chip does not pay Article III

The desk chrome carries a single clickable `EgressChip`
(`components/DeskChrome.tsx:253-260`) fed by `egressBadge(setup)`
(`desk/setup.ts:99-136`). It cannot be the badge at the point of decision:

1. its input is a configuration snapshot from `/api/setup/status`, so it cannot know which verb the cursor is over;
2. its best case is `→ <last_egress.name>` — *the last* receipted egress, never this click's destination (`setup.ts:101-107`);
3. it lives in `desk-chrome-tl`, the one place on the screen that is by construction beside nothing;
4. it returns `⌂ This device` whenever zero *destinations* are enabled (`setup.ts:113-114`) — while the steward's `Run once`, the sweep's `Run now`, `Generate` and a catalog `Download` all reach the network by paths that are not "destinations".

The pattern that does pay Article III is already in this tree, proven in
five places: `RouteDisclosure` + `RunAttempts`
(`web/src/meetings/RouteDisclosure.tsx:52-123`), the nudge card
(`ProjectRoomCore.tsx:541` / `:496`), the Prepare well
(`PreparePosture.tsx:168` / `:707`), the Concierge add-engine row
(`ConciergeCore.tsx:527-541`) and the TTS weights row
(`settingsTts.tsx:110-117`). The eleven verbs above have never been given it.

### B.4 — two badge species for one fact (T5)

`EgressChip` (`gadgets.tsx:745`) and the `LampGadget` lamps of
`desk/inferenceEgress.ts:9-50` (`LOCAL/LAN/PAIRED/MESH/CLOUD/NO MODEL`)
both state egress: AskPanel (`:325-334`), ThreadPullout (`:1070`, `:1702`)
and WorkbenchRunsWing (`:72`) use the lamp, everything else uses the chip.
Two further sites bypass the library with a hand-rolled
`<span className="egress-badge is-cloud">` (`PrReceiptsSection.tsx:73`,
`:161`; `Pullout.tsx:72-74`) — a U1 bounce as well as a T5 one.

### B.5 — NOT ASSESSED in the egress lane

* the calendar `Snapshot` receipt: the review surface it hands off to (`SettingsCore.tsx:1632`) was not opened by this walk.
* the Thought-workspace one-question receipt (the before-badge at `ThoughtWorkspaceWindow.tsx:447` is confirmed; the after half was not traced).
* `Delivery` launch: the composer's own button line was not isolated; only the frame-level `Hub` chip (`DeliveryBoard.tsx:409`) is confirmed.


## Appendix C — the shot index

Every shot is in `assets/interaction/`; `-1440` and `-393` are the two
widths. 55 shots from the two final runs.

| Finding | Shot |
|---|---|
| 1 — the dock off-screen at 393 | `dock-393.png` (no dock in frame), `dock-1440.png` (the dock, for contrast) |
| 2 — three menus gone at 393 | `dock-393.png` (the bar shows only `Go`), `menu-go-393.png`; `menu-desk-1440.png`, `menu-object-1440.png`, `menu-go-1440.png`, `menu-window-1440.png` |
| 3 — the First Words gate | `first-words-gate-1440.png`, `first-words-gate-393.png` |
| 4, 5 — egress | `surface-rhythm-1440.png`, `surface-rhythm-393.png` (`Run now` and `Generate` with no badge on the row); `dock-393.png` (two `THIS DEVICE` chips on one screen) |
| 6 — the owner jobs by keyboard | `job-notes-1440.png`, `job-notes-393.png`, `job-thoughts-1440.png`, `job-thoughts-393.png`, `job-speak-*.png`, `job-meetings-*.png`, `job-models-*.png` |
| 7 — Desk memory empty | `surface-desk-memory-1440.png`, `surface-desk-memory-393.png` |
| 8 — the ⌘K catalog | `shelf-open-1440.png`, `shelf-open-393.png`, `shelf-enter-*.png` |
| 9 — ghosted menus | `menu-object-1440.png`, `menu-window-1440.png` |
| 10 — Change places | `surface-change-places-1440.png`, `surface-change-places-393.png` |
| 11 — focus and tab order | `keyboard-focus-1440.png`, `keyboard-focus-393.png` |
| 12 — touch at 393 | `touch-meetings-393.png`, `touch-meetings-1440.png` |
| 16, 17, 19 and the per-surface rows | `surface-<name>-1440.png` / `-393.png` for Intelligence, Speak, Meetings, Agents, Settings, Change places, Rhythm, Context, Workbenches, Activity, Desk memory, Processes, Commands, Models |
