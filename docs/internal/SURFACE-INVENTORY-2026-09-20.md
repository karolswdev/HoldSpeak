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
three of the four menus never open there), **eleven verbs leave the machine
with no badge and four badges say "this device" and are false**, **the
faces are built from raw HTML more often than from the library** (2,082 raw
buttons against 869 library Buttons; the menu items, the wing tabs and the
dock itself are raw), **type is too small and too faint by the thousands**
(4,358 text elements under 12 px; 560 below AA contrast; 1,350 verbs under
44 px at 393), and **things are hidden, empty or said twice** (124 cut texts,
90 empty headings with data present, 155 duplicated facts, 11 zero
counters). A stranger with no lore reached four of five jobs and got lost on
the fifth because the button called "Write a thought" opens the dictation
router. The fix is not a hundred face patches: most of the numbers fall at
the species and the tokens, and the rest is doors, names and honesty. One
phase, eight stories, and the walk itself becomes the fence so the numbers
cannot climb back.

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
| U1 raw buttons vs library Buttons | **2,082 vs 869** | the species: menu items (`DeskMenu.tsx:155`), wing tabs (`wings.tsx:88`), the dock (7), DeskEditor (11), WorkbenchWindow (23), inspector (10), ThreadPullout (9), SessionPullout (7), CoderPullout (6) |
| M7 text under 12 px | **4,358** (smallest 6 px) | the interior type scale has no floor |
| M7 verbs under 44 px at 393 | **1,350** on 140 legs | the dense Button has no hit-area floor |
| M8 text below AA contrast | **560** of 8,647 (worst 2.97:1) | the muted tokens |
| M10 legs with more than two font stacks | **63** | display + body + mono mixed on one face |
| M1 legs with horizontal overflow | **47** | the dock at 393 (410 px past the viewport); Components; the Floor; the window switcher |
| M2 cut text | **124** | ellipsis with no reveal |
| M5 empty headings or labels with no value | **90** (78 on the RICH desk) | they appear with data |
| M6 the same fact twice on one screen | **155** on 54 legs | "Nothing needs you" ×2; context receipts |
| U3 visible zero counters | **11** (+ one in an aria-label: "…zone, 0 items") | |
| U4 legs with more than one filled primary | **16** | |
| A7 prose sentences | **4** visible; the first-run card carries one | |
| C3 surfaces with no door | **8** (Calendar snapshot, Components, Live meeting, New Project, People, Runtime docs, /presence, /welcome) + the `assignments` settings module | |
| A3 egress verbs with no badge and no receipt | **11** (`Run once`, `Run now`, `Generate`, `Send reply`, `Process pending`, `Preview route`, two `Download`s, `Draft review`, the PR writes, `Talk`) | |
| A3 badges present and false | **4** (`THIS DEVICE` beside an internet download; hardcoded on the dictation face; a hardcoded `⌂` on Live; five prop-less `<EgressChip/>` that print "This device" by default, `gadgets.tsx:745-747`) | |
| Menu entries that are ghosts on load | **18 of 46** (all of Object, all of Window) | |
| Menus that never open at 393 | **3 of 4** (Desk, Object, Window; still announced to screen readers) | |
| M13 open → settled | median 3.6 s, p90 6.5 s, max 17.2 s | |
| M9 console errors, 4xx/5xx | **0** on 287 legs | a real pass |
| Motion, focus rings, icon names, window grammar at 393 | **pass** (0 transitions over 400 ms; 0 of 69 tab stops without a ring; 0 anonymous icon buttons; all 14 windows become sheets, single scroll owner) | |

## 3. Where the four lanes converge

### 3.1 The phone width has no doors (T3, T6)

The dock is the only persistent door at 393 and it is off the screen; the
`Record a meeting` orb lives in it. Three menus are dead there. Eight
surfaces have no door at any width. ⌘K's Enter commits the highlighted row,
not the typed match (`Notes` opened `Telegram control`; `Thoughts` opened
`Intelligence`), so two of the five owner jobs cannot be started from the
keyboard. ⌘K's `Ask AI` row is permanently disabled while the Go menu's
works. The button called **"Write a thought" opens the Speak dictation
router** (`LANDS IN · Codex CLI`, `NOT SET`, no keep); the real door is Desk
→ New Note, nine moves away for a stranger. Four of nine `New …` verbs mint
and open nothing. Nine call sites `openSurfaceOr` an unregistered key and
silently land on the bare desk. Dev surfaces ship ungated: Components has
zero callers and no door; RAILS/Delivery/story objects reach ⌘K and the
Floor wearing the raw token `STORY`; there is no build gate anywhere in the
web app.

### 3.2 The screen is not honest about egress and state (A3, A6)

Eleven verbs leave the machine with nothing beside them. Four badges say
"this device" and are false; the chip species prints "This device" when
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

Cut text with no reveal; empty headings that appear only when data exists;
the all-clear printed twice on one screen; receipts that restate the row
above them; zero counters in text and in accessible names.

### 3.6 One thing, many names (T4, U6, C2, C1)

A meeting result is **Summary** on the record and **Intelligence** on Live
(F06). A failed summary offers **Retry** and **Retry intelligence** (F07).
The Sequence object's edit verb calls it a **chain** (F08). The Project Room
has **six names** across the faces. `Runs on` and `Sequence` are canon terms
that render on no face. `SEG` and `MTG` stand where segment and meeting
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
| An empty zone announces "…zone, 0 items" (`DeskListView.tsx:214`) | census |
| Four or five of nine `Favorite` toggles in Change places do nothing while one fires nine requests | interaction |
| The meeting record does not refresh after the engine is assigned or the run completes (two reloads to see a summary) | sober eye |

## 5. What passes, and stays

Zero console errors and zero failed requests on every measured leg. Motion
clean at both widths and reduced-motion honoured. Every tab stop has a focus
ring; no icon button is anonymous. Every window becomes a full-width sheet at
393 with one scroll owner. The import path (four moves), the Concierge (five
moves from `Choose an engine` to a working LAN engine), ⌘K search across a
restart, and provenance after a run (the host named four ways on one screen)
were the sober eye's good moments. `docs/WHAT_IS_HOLDSPEAK.md` predicted the
gaps honestly; `README.md` promises faces that never appeared.

## 6. The plan — Phase 202: The Coherent Face

**Principle.** Fix at the species and the tokens, not per face; the census
numbers are the exit criteria and the walk is the fence, so they cannot
climb back. Every story ends with the rig re-run and the number moved.
Nothing new ships that does not shorten one of the owner's jobs.

| # | Story | Exit (the census re-run) |
|---|---|---|
| 01 | **Doors at every width.** The dock fits at 393; the four menus open there; ⌘K commits the typed match; one Ask AI door; every application has one door (the eight without, and the `assignments` module); `Write a thought` opens a note; `New …` verbs that mint nothing leave; the nine unrouted `openSurfaceOr` calls fixed or removed; dev surfaces gated out of the product build | C3 = 0; dock M1 = 0 at 393; menus 4/4 at 393; ghost entries only when truly inapplicable |
| 02 | **Honest egress on every verb.** The eleven bare verbs get the badge before and the receipt after; the four false badges fixed; `<EgressChip/>` with no props renders NOT SET, never "This device"; the Trust window tells the truth after a failed read; the Room never hides degraded work under an all-clear; Desk memory shows the desk's memory | A3 table: 0 bare, 0 false; F01, F02 closed |
| 03 | **The species pay the raw-button debt.** Menu items, wing tabs, the dock, DeskEditor's controls, WorkbenchWindow, the inspector, Thread/Session/Coder pullouts, GroundingSection, BriefView: library species | U1 raw buttons: 2,082 → 0 in product faces (dev surfaces gated) |
| 04 | **Type, size and contrast at the tokens.** A 12 px floor on the interior scale; a 44 px hit area on every verb at 393 (the dense Button extends its hit area, not its ink); AA for the muted tokens; two stacks per face by role, and the design system says so | M7 < 12 px: 4,358 → 0; verbs < 44 px at 393: 1,350 → 0; M8 below AA: 560 → 0; M10 > 2 stacks: 63 → 0 |
| 05 | **Nothing hidden, nothing empty, nothing twice.** Cut text wraps or reveals; empty headings render nothing; one all-clear per screen; receipts never restate the row; zero counters gone from text and aria | M2: 124 → 0; M5: 90 → 0; M6: 155 → 0; U3: 11 → 0; U4: 16 → 0; A7: 4 → 0 |
| 06 | **One name per thing.** Summary, not Intelligence, on Live; one Retry; Sequence; the Project Room's one name; SEG/MTG in words; canon terms render or leave POSITIONING; `product-language.json` enforced across every face | noun map: one row per thing; verb map: one verb per job; C2 = 0 |
| 07 | **The eight defects.** Decisions POST; the assignments door; the LAN placeholder removed; tokened startup URLs; the Create face reachable or parked; the zone aria; the Favorite toggles; the meeting record refreshes on assignment and on run without a reload | each with a fence red first |
| 08 | **The walk is the fence.** Both rigs in CI as down-only ratchets on every census number; the sober eye re-run at phase close on the rich desk; the phase closes on the owner's sitting, not on the numbers | the ratchet file committed; the second sober eye scorecard beside the first |

**Order.** 07 first (defects, small, on the owner's path), then 04 and 03
together (tokens and species, the two lanes that move most numbers), then
01 and 02 (doors and honesty), then 05 and 06 (the residue, mostly
mechanical after 03/04), then 08.

**What parks (never deleted).** The Philo SRS's seven no-face requirements
and 26 partly-matched rows (a scope map, not blockers). Per-face CSS
literal cleanups beyond the shared species (474 dimension records) until
04 has moved the shared ones. The Components catalog and the RAILS objects
(gated, kept).

## 7. Appendices

| File | Contents |
|---|---|
| [00-rulebook.md](surface-inventory-2026-09-20/00-rulebook.md) | the rules every lane measured against |
| [01-measured-walk.md](surface-inventory-2026-09-20/01-measured-walk.md) | 100 surfaces × cold/rich × 1440/393, every measure; `census.json` |
| [02-coherence-astra.md](surface-inventory-2026-09-20/02-coherence-astra.md) | species, tokens and type, the noun and verb maps, doors and states, SRS parity; top 30 (Astra, PR #593) |
| [03-interaction-walk.md](surface-inventory-2026-09-20/03-interaction-walk.md) | every verb pressed, keyboard, touch, motion, the menus and ⌘K, egress per verb, window grammar; `interaction.json` |
| [04-sober-eye.md](surface-inventory-2026-09-20/04-sober-eye.md) | the five jobs cold, no lore: scorecard, noun count, promise gap, delete list |
