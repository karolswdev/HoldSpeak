# The Surface Inventory — 2026-09-20

**What this is.** Every face HoldSpeak has, under the magnifying glass, on
`main` at `93f9524f`, the day the owner said: *"a proper, all surface
inventory and analysis, to ensure that we have an interface that doesn't
overflow and hide data, to ensure that the interface is coherent and in
agreement with our development philosophy… a comprehensive one. Everything's
going to be put under the magnifying glass."* Four lanes, one rulebook
([00-rulebook.md](surface-inventory-2026-09-20/00-rulebook.md): the Seven
Tenets and the Constitution first, UX-CANON and the design system second,
the UI/UX review checklist third). The lanes' full reports are the appendices;
this document is the synthesis and the plan.

**The one-paragraph answer.** The product's faces are honest on the wire
(zero console errors and zero failed requests on all 287 measured legs;
motion clean; focus rings on every tab stop; every window a proper sheet at
phone width) and dishonest on the screen: **the phone width has no doors**
(the dock is laid out at desktop width and sits 410 px off the screen at 393;
three of the four menus never open there), **eleven groups of verbs leave the machine with no badge (two confirmed live) and four categories of badge say "this device" and are false**, **the
faces are built from raw HTML more often than from the library** (2,082 rendered raw-button observations across the legs against 869 library Button renders, which is 157 raw-button SOURCE sites; the menu items, the wing tabs and the dock itself are raw), **type is too small and too faint by the thousands**
(4,358 text elements under 12 px; 560 below AA contrast; 1,350 verbs under
44 px at 393), and **things are cut, empty or said twice** (124 clipped texts, some with a reveal; two empty sections and 88 label wrappers the rig misread as empty; 155 duplicated facts; 11 zero counters). A stranger with no lore scored two jobs done, two partly, one failed (the microphone), and got lost because the button called "Write a thought" opens the dictation router; saving a note gave no confirmation and the microphone failure offered a retry that cannot help. The fix is not a hundred face patches: most of the numbers fall at
the species and the tokens, and the rest is doors, names and honesty. One phase, six stories, sized to the owner's first-use path with a small deterministic fence first; the broad census numbers stay diagnostic and are re-run at phase close.

---

## 1. What was measured

| | |
|---|---|
| Surfaces in the inventory | 100 (22 registered applications, 34 cores, 19 pullout kinds, settings modules, wings, states) |
| Legs walked (surface × desk × width) | 344: cold desk and rich desk, 1440×900 and 393×852 |
| Legs measured / unopened | 287 / 57 (each unopened with its reason; never scored) |
| Shots | 287 (census) + 55 (interaction) + 37 (sober eye) |
| Verbs pressed one by one | 46 menu entries, 11 dock buttons, 32 ⌘K rows, 14 surfaces, both widths |
| Rigs checked in | `scripts/surface_census_walk.py` + `surface_census_measure.js`; `scripts/surface_interaction_walk.py` (re-runnable; the phase's exit fence) |
| Read-and-count planes (Astra) | species, tokens and type, words (noun and verb maps), doors and states, Philo SRS parity; 17 tables |
| The sober eye | a fresh mind, no docs, the five owner jobs cold |

Every measure a rig could not take is NOT ASSESSED, never zero: spacing
rhythm (M11), motion timing in the census (M12; the interaction walk measured
it), contrast over wallpaper (48 leaves), microphone verbs (12), People
(the encrypted sidecar needs a keychain the isolated HOME does not have).

## 2. The numbers

| Rule | Count | Where it falls |
|---|---|---|
| U1 raw-button renders vs library Button renders across 287 legs (rendered observations, not sites) | **2,082 vs 869**; **157 raw-button source sites** in consumer code (appendix 02) | the species: menu items (`DeskMenu.tsx:155`), wing tabs (`wings.tsx:88`), the dock (7), DeskEditor (11), WorkbenchWindow (23), inspector (10), ThreadPullout (9), SessionPullout (7), CoderPullout (6) |
| M7 text under 12 px | **4,358** (smallest 6 px) | the interior type scale has no floor |
| M7 verbs under 44 px at 393 | **1,350** on 140 legs | the dense Button has no hit-area floor |
| M8 text below AA contrast | **560** of 8,647 (worst 2.97:1) | the muted tokens |
| M10 legs with more than two font stacks | **63** | display + body + mono mixed on one face |
| M1 legs with horizontal overflow | **47** | the dock at 393 (410 px past the viewport); Components; the Floor; the window switcher |
| M2 clipped text | **124** | clipped; whether a reveal exists was NOT ASSESSED by the rig |
| M5 empty sections | **2**; the rig's other 88 are checkbox label wrappers with accessibly named inputs (misread, not defects); 12 observations were on the cold desk |
| M6 the same fact twice on one screen | **155** on 54 legs | "Nothing needs you" ×2; context receipts |
| U3 visible zero counters | **11** (+ one in an aria-label: "…zone, 0 items") | |
| U4 legs with more than one filled primary | **16** | |
| A7 prose sentences | **1** distinct sentence (a dictation-install line) rendered four times; the first-run card carries another | |
| C3 surfaces with no Go/dock door | **8** by the census's Go/dock rule; People and New Project have Desk-menu doors, Calendar snapshot a Settings door, Live the orb, Runtime docs has the Settings Guide wing (`SettingsCore.tsx:738`), so truly doorless: Components, /presence, /welcome, plus the `assignments` settings module | recalculated per appendix 03 |
| A3 egress verb groups with no badge and no receipt | **11 source-table groups** (one holds the three PR writes); two fired live and confirmed bare (`Run now`, `Generate`); the rest are source findings | |
| A3 false-badge categories | **4** (`THIS DEVICE` beside an internet download; hardcoded on the dictation face; a hardcoded `⌂` on Live; a category of five prop-less `<EgressChip/>` that print "This device" by default, `gadgets.tsx:745-747`) | source findings; two seen on one 393 shot |
| Menu entries that are ghosts on load | **18 of 46** (all of Object, all of Window) | |
| Menus that never open at 393 | **3 of 4** (Desk, Object, Window; still announced to screen readers) | |
| M13 open → settled | median 3.6 s, p90 6.5 s, max 17.2 s | |
| M9 console errors, 4xx/5xx | **0** on 287 legs | a real pass |
| Motion, focus rings, icon names, window grammar at 393 | **pass within coverage**: 0 transitions over 400 ms (the reduced-motion pass ran at 1440 only); 0 of 69 SAMPLED tab stops without a ring; 0 anonymous icon buttons; all 14 pressed windows become sheets with one scroll owner; Agents was recorded MEASURED while its shot shows only the loading state; the Thought window at 393 was UNOPENED | |

## 3. Where the four lanes converge

### 3.1 The phone width has no doors (T3, T6)

The dock is the only persistent door at 393 and it is off the screen; the
`Record a meeting` orb lives in it. Three menus are dead there. Three surfaces and one settings module have no door at any width (the other five the census flagged have contextual doors: a Desk-menu entry, a Settings row or wing, the orb). ⌘K's Enter commits the highlighted row,
not the typed match (`Notes` opened `Telegram control`; `Thoughts` opened
`Intelligence`), so two of the five owner jobs cannot be started from the
keyboard. ⌘K's `Ask AI` row is permanently disabled while the Go menu's
works. The button called **"Write a thought" opens the Speak dictation
router** (`LANDS IN · Codex CLI`, `NOT SET`, no keep); the real door is Desk
→ New Note, nine moves away for a stranger. Four of nine `New …` verbs mint an object but open no editor. Nine call sites `openSurfaceOr` an unregistered key and
silently land on the bare desk. Dev surfaces ship ungated: Components has
zero callers and no door; RAILS/Delivery/story objects reach ⌘K and the
Floor wearing the raw token `STORY`; there is no build gate anywhere in the
web app.

### 3.2 The screen is not honest about egress and state (A3, A6)

Eleven source-table groups of verbs leave the machine with nothing beside them, two of them fired live and confirmed bare. Four categories of badge say "this device" and are false; the chip species prints "This device" when
given no props, so every forgotten prop is a lie. The Trust window says
"All data stays on this device" after its status read fails while the same
window shows external scope (F01). The Room turns a degraded needs-you
section into "Nothing needs you" and hides it (F02). Desk memory shows an
empty body on a desk that has a meeting, decisions and a brief. The summary
needs two browser reloads to appear after the engine is set and after the
run, though the hub finished in two seconds. Two printed URLs lack the
tab-scoped token, so a bookmark or a second tab lands on a black page saying
`principal_right_required`.

### 3.3 The faces are not built from the framework (T5, U1, D1, D2)

Raw buttons outnumber library Buttons more than two to one, and the worst
sites are the shared species themselves: every menu item, every wing tab,
the dock, the editor's controls. Thread CSS repeats 54 hex and 38 rgb
literals; shared surface CSS carries 88 off-scale and 31 off-interior
records; 474 dimension records fall outside the token set. The design system
names display/body/mono while the census caps a face at two stacks: the
rule and the system disagree (F28) and the faces show it (63 legs).

### 3.4 Type is too small and too faint (T6, M7, M8)

Thousands of text elements under 12 px, the smallest 6 px; hundreds below
AA; over a thousand verbs under 44 px at phone width. These are token and
species floors, not per-face bugs.

### 3.5 Things are hidden, empty, or said twice (M2, M4, M5, M6, U3)

Clipped text whose reveal the rig did not assess; two empty sections (the 88 other flags were label wrappers with named inputs);
the all-clear printed twice on one screen; receipts that restate the row
above them; zero counters in text and in accessible names.

### 3.6 One thing, many names (T4, U6, C2, C1)

A meeting result is **Summary** on the record and **Intelligence** on Live
(F06). A failed summary offers **Retry** and **Retry intelligence** (F07).
The Sequence object's edit verb calls it a **chain** (F08). The Project Room
has **six names** across the faces. `Sequence` is a canon term that renders on no face; `Runs on` renders once, as a Rhythm row. `SEG` and `MTG` stand where segment and meeting
would do. Thirty-eight distinct labels meet a stranger in the first two
minutes; five did anything for the five jobs.

## 4. Defects the audit found by accident

| Defect | Evidence |
|---|---|
| `POST /api/decisions` is a hard 500 for every caller: `build_desk_decisions_router` deletes `ctx` at `decisions.py:20` and its closure reads it at `:28`; GET works only because a second router owns it | census seeding, verified live |
| The `assignments` settings module has no door: `PREF_MODULES` declares nine, the ledger renders eight | census |
| The owner's private LAN address is hardcoded as the shipped Server-address placeholder (`ConciergeCore.tsx:522`) | sober eye |
| Two startup URLs are printed without the tab-scoped token (`web_runtime.py:430`, `:438`) and land on `principal_right_required` | sober eye, verified in a fresh context |
| The ＋Create face is unreachable on any real desk: it lives only in `EmptyDesk`, and first boot furnishes zones | census |
| An empty zone announces "…zone, 0 items" (`DeskListView.tsx:214`) | source evidence; the rig does not scan accessible names |
| Four or five of nine `Favorite` toggles in Change places showed no observed effect; the probe did not read aria-pressed, SVG fill or localStorage, and the nine requests were polling GETs: UNVERIFIED, not a defect yet | interaction |
| The meeting record does not refresh after the engine is assigned or the run completes (two reloads to see a summary) | sober eye |

## 5. What passes, and stays

Zero console errors and zero failed requests on every measured leg. Motion
clean at both widths and reduced-motion honoured. Every SAMPLED tab stop (69) has a focus ring; no icon button is anonymous. Every PRESSED window (14) becomes a full-width sheet at 393 with one scroll owner; the reduced-motion pass ran at 1440 only. The import path (four moves), the Concierge (five
moves from `Choose an engine` to a working LAN engine), ⌘K search across a
restart, and provenance after a run (the host named four ways on one screen)
were the sober eye's good moments. `docs/WHAT_IS_HOLDSPEAK.md` predicted the
gaps honestly; `README.md` promises faces that never appeared.

## 6. The plan — Phase 202: The Coherent Face (re-cut after Astra's check)

**Principle.** The owner's first-use path first (Phase 201 story 07, the
sitting, stays the exit that selects the next scope); fix at the shared
species and the tokens where the first-use flows touch them; a small,
deterministic fence before repairs; the broad census numbers stay
diagnostic and are re-run at phase close, never as gates. Every story ends
on a face the owner uses on a Tuesday.

| # | Story | Exit |
|---|---|---|
| 01 | **The first-use fence.** One deterministic, isolated smoke at 1440 and 393 with fixture audio and a stub engine: the doors to the five jobs, visible completion of each, the truthful host before and after a run, save and refind, restart; it requires the expected content to load (no green on a loading ellipsis). Fixture coverage only: the owner's real recording and real dictation are the sitting's exits (story 06), never this fence's. Reuses the existing source-button ratchet; adds no census gates | the smoke is red on main today at the doors it names, then green as the stories land |
| 02 | **First-use doors and truthful state.** Each item names the job it unblocks. Job 1 (speak): the microphone failure names the microphone and offers a recovery that can work. Job 2 (meeting → summary): the meeting record refreshes on assignment and on run without a reload; `<EgressChip/>` with no props renders NOT SET, never "This device"; the false badges on that path fixed; the startup URLs carry the token so the desk opens. Job 3 (write a thought): `Write a thought` opens a note and saving a note confirms. Job 4 (find it again): ⌘K commits the typed match; Desk memory shows the desk's memory. Job 5 (set up an engine): the `assignments` module has a door; the owner's LAN address removed from the placeholder. All jobs at 393: the dock fits; the four menus open. On the arrival: `Generate` badged and receipted; one Ask AI door. LEDGERED (no first-use step needs them): decisions POST (no job writes a decision yet), the Room's degraded all-clear, `Run now` and the steward's `Run once`, the Trust window's failed-read state, the disposition of Components, /presence and /welcome | each item with a fence red first; the first-use smoke green at both widths |
| 03 | **Shared controls on the first-use path become library species.** Menu items, wing tabs, the dock, DeskEditor's controls, and the consumers those flows touch (bounded by the 157-site source census, migrated in this order; the rest ledgered) | the source-button ratchet moves down by the migrated sites; no raw control on the five jobs' screens |
| 04 | **Names and repeats on the touched flows.** Summary not Intelligence on Live; one Retry; one all-clear per screen; receipts never restate the row; zero counters gone from text and accessible names on those flows; `SEG`/`MTG` in words | the touched flows' shots; the noun and verb maps collapse on those rows |
| 05 | **The type-scale ruling, then the tokens.** A design beat first: settle the 11 px caption allowance, the 12 px floor, and the three type roles (display/body/mono) between canon and the census rule, with counsel; then apply at the tokens (floor, muted-token contrast, the dense Button's hit ownership at 393 verified by hit testing, not rectangles); the broad M7/M8/M10 numbers re-measured as diagnostics | the ruling recorded in UX-CANON and DESIGN_SYSTEM; the first-use screens pass AA and the hit test |
| 06 | **The sitting selects the next scope.** The owner sits (Phase 201 story 07's script) on the merged phase; the sober eye re-runs on the rich desk; the census re-runs as a diagnostic; the phase closes on his words, and the next phase is chartered from what he hit | the second sober-eye scorecard beside the first; the owner's line |

**Order.** 01 → 02 → 03 and 04 together → 05 → 06.

**Ledger (recorded, not scheduled).** The broad census residue outside the
first-use flows: the remaining raw-control sites, the 474 dimension
records, cut text and duplicated facts on faces the five jobs do not
touch, the 11 zero counters off-path, Components and the RAILS objects
(gated, kept), the Favorite toggles (unverified), decisions POST, the Room's degraded all-clear, `Run now` and `Run once`, the Trust window's failed-read state, the disposition of Components, /presence and /welcome, real voice delivery (the sitting's, never the fence's),
populated People, full failure and recovery transitions, zoom and
assistive-technology behaviour, the Philo SRS's seven no-face requirements
and 26 partly-matched rows.

## 7. Appendices

| File | Contents |
|---|---|
| [00-rulebook.md](surface-inventory-2026-09-20/00-rulebook.md) | the rules every lane measured against |
| [01-measured-walk.md](surface-inventory-2026-09-20/01-measured-walk.md) | 100 surfaces × cold/rich × 1440/393, every measure; `census.json` |
| [02-coherence-astra.md](surface-inventory-2026-09-20/02-coherence-astra.md) | species, tokens and type, the noun and verb maps, doors and states, SRS parity; top 30 (Astra, PR #593) |
| [03-interaction-walk.md](surface-inventory-2026-09-20/03-interaction-walk.md) | every verb pressed, keyboard, touch, motion, the menus and ⌘K, egress per verb, window grammar; `interaction.json` |
| [04-sober-eye.md](surface-inventory-2026-09-20/04-sober-eye.md) | the five jobs cold, no lore: scorecard, noun count, promise gap, delete list |
| [05-first-use-fence.md](surface-inventory-2026-09-20/05-first-use-fence.md) | the fixture fence: what it proves, its named failures, and the real voice boundary |
