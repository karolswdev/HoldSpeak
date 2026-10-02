# The Workbench look (PHILO-13-11, C1) — the settled design for build

**Status: DRAFT, round 3c (Astra canvas r2 paid: the 393 footer collision and a rendered-overlap fence; every measured count now lives in the canvas README's generated block, not here), for Astra's re-check and the owner's ratification.** The canvas is `../assets/story-11-canvas/` (README, `index.html`, `shots/`). Nothing is built in product code. When the owner ratifies, his word goes here verbatim, and the build matches the boards, board beside shot (UX-CANON §A.2).

The owner, 2026-10-01: "The whoe Workbench 2.0+ on steroids needs to really lean on steroids." Fork 1: "All the way".

## 1. The direction: Workbench Steel

Workbench 2.0 drew everything with four pens. HoldSpeak keeps the four pens as roles:

| Workbench 2.0 pen | Role here | Token |
|---|---|---|
| 0 grey | the frame: window borders, title bars, gadgets, the AppIcon shelf | `--wb-steel` |
| 1 black | every line and every word on the frame | `--wb-ink` |
| 2 white | the screen title bar, the menus, the state tags, the shine | `--wb-paper` |
| 3 blue | the ONE front window: its frame and its title bar | `--wb-blue` (#6688bb, 2.0's own blue) |

"On steroids": the body of every window stays the dark Signal well (`--surface-1`). The 19 `DeskWindowFrame` hosts keep their bodies and wear the frame. Ember (`--accent-ink`) stays the colour of a verb and of attention. A hard 4 px drop replaces the blur. The Chair becomes a Workbench screen with a dithered backdrop (WBPattern).

The alternative on board C1-7, **Honest 2.0**, puts the four pens on every body too. Round two's Honest headline at 1.56:1 came from that alternative's own `--accent` override (blue on grey), not from grey bodies; round three completes its palette, and both directions now measure 0 texts under the threshold on the Chair, two windows and People (`shots/facts.json`, `_cmp_*`). **Recommended: Steel, for coherence and preference** — the hosts keep their dark material and their ember and state colours. Its limits, stated: under the inherited `--accent`, the large `8 need you` reads 4.26:1 (large text, passes 3:1) and round two's `Add` primary read 3.79:1 (small text, fails); the build draws ember text on `--accent-text` and filled verbs on `--accent-ink` (§2).

## 2. The tokens (→ `web/design-tokens.json` → `tokens.css`, COMPONENT layer)

| Token | Value | Use |
|---|---|---|
| `--wb-steel` | `#9ea4b0` | frame plate, bars, gadgets |
| `--wb-steel-2` | `#b3b8c2` | a plate under the pointer |
| `--wb-ink` | `#0b0c10` | lines and words on the frame |
| `--wb-paper` | `#eef0f3` | screen bar, menus, tags |
| `--wb-blue` | `#6688bb` | the front window |
| `--wb-hi` | `rgba(255,255,255,.72)` | the shine (top and left edges) |
| `--wb-lo` | `rgba(0,0,0,.5)` | the shade (bottom and right edges) |
| `--wb-backdrop` / `--wb-dither` | `#3c4454` / `#363e4d` | the Chair screen, a 4 px checker |
| `--wb-rec` | `#b3261e` | REC on paper |
| `--wb-frame` | `4px` | window border |
| `--wb-bar-h` | `26px` (393: `44px`) | window title bar |
| `--wb-screen-h` | `28px` (393: `44px`) | screen title bar |
| `--wb-gadget-w` | `26px` (393: `44px`) | one gadget |
| `--wb-raised` | `inset 1px 1px 0 --wb-hi, inset -1px -1px 0 --wb-lo` | a raised plate |
| `--wb-sunken` | the same, reversed | a pressed plate, an open wing, a running icon |
| `--wb-drop` | `4px 4px 0 rgba(0,0,0,.32)` | window and menu drop, no blur |
| `--wb-stipple` | 1 px lines every 4 px, 16 % ink | the drag bar |

Re-pointed existing tokens: `--desk-window-keyline` → ink; the work band: `--desk-work-top` = the screen bar, `--desk-work-bottom` = the shelf (84 px; 393: 56 px). **NOT re-pointed (R5):** `--desk-window-head-fill`, `--desk-window-head-front`, `--gadget-fill`, `--gadget-fill-hover` — body strips wear them (People's `.surface-verbs` read `--text-muted` on steel at 1.02:1). The frame names `--wb-*` directly.

New semantic tokens (R5): `--accent-text: #bc8058` (ember TEXT on the dark well, 5.43:1 on `--surface-1`; `--accent` text read 4.26:1); filled verbs stay on `--accent-ink` (5.24:1). Every word in a title bar is `--wb-ink`, whatever the host puts there.

Contrast: ink on steel 7.81:1, ink on blue 5.40:1, ink on paper 17.12:1, REC on paper 5.73:1, text on the ember ink 5.24:1. Every word on the frame is 12 px or more.

The full rule set, each section naming its product file, is `../assets/story-11-canvas/harness/canvas.css` §1–§8.

## 3. The gadget set (→ `DeskWindow.tsx`, `pullout.css`, `window-chrome.css`)

One composition for every `DeskWindowFrame` host and every Chair window (board C1-2a):

- **Left, flush to the corner:** close. Glyph: a small white square in the middle (2.0).
- **Right, flush to the corner, in this order:** iconify (the window falls to its Dock chip; 3.9's gadget for today's minimize), zoom (a small black rect in a big rect), depth (two overlapping rects, the front one white).
- **Bottom right, on the frame:** the sizing gadget (two nested corners). It replaces the grip.
- Each gadget is a library `Button variant="chrome"`, an SVG glyph, 1 px ink divider, raised bevel on the bar's own fill; pressed = sunken. Accessible names: `Close <window>`, `Iconify <window>`, `Zoom <window>`, `To back <window>`.
- **393:** a window fills the work area (§5b). Its head is ONE 44 px row: close · the wings (or the title, for a window without wings) · the head verbs · depth; the screen bar already names the window. Wings that do not fit become the strip menu Button (§3a).

### 3a. Strips of choices: nothing clips, nothing scrolls sideways (Muad'Dib's ruling, round 3b; HS-200-12 stands)

Applies to every strip of choices: the window tabs (wings) and the Chair's ranking filters (`FilterTokens`).

- **At 1440 a strip must fit.** The Chair's ranking strip has its own line in the Needs-you window; the availability chip, `CHECKED …` and the calendar state wrap to the next line, off the strip (C1-1).
- **At 393 a strip that does not fit becomes ONE library menu Button in its row**, showing the current choice and ▾ (`RANKED ▾`, `OUTCOMES ▾`), 44 px tall. It opens the existing DeskMenu species with every choice and a check mark on the current one; a window's gear door joins the menu after a separator (C1-2e, C1-6a). A strip that fits stays a strip (the Room's ROOM · HISTORY). The build measures "does not fit"; the canvas draws the rule as "more than two choices at 393".
- **Seats in the build:** `web/src/desk/surface/FilterTokens.tsx` and `web/src/desk/surface/wings.tsx` render the menu form (library species; contract.md gains the form).
- **Fenced** on every board: no horizontally scrolling element, and no text node whose box runs past its clipping ancestor or spills out of its control. Ellipsis truncation of a single line (`text-overflow: ellipsis`, A.6 "titles shrink first") is recorded, not failed. The Dock is outside this rule by name: it is the AppIcon shelf, paged by its More gadget at 393.
- The traffic lights (`.desk-traffic`, red/amber/green) are removed.
- **The title bar is the drag bar:** steel (front: blue), stipple, the title on a solid plate in 12 px bold mono ink, never shrinking (max 45 % of the bar). Wing tabs are raised steel; the open one is sunken paper (a cycle gadget). Whatever a host puts in its actions slot wears the steel plate and the 12 px floor.
- **One front window (R4, a build instruction).** Today two windows can wear `is-front` at once (grounding `faces-surfaces.md:219`), and the inherited rule `.desk-next .desk-window-shell.is-front .desk-pullout-head` (`web/src/desk/components/window-chrome.css:337`, four classes) paints every such head. The build derives `is-front` from the one `panelOrder` for every window family, Chair windows included, and replaces that rule; until then the canvas neutralises a stale `is-front` with `.desk-window-shell.is-front:not([data-p13-front]) > .desk-pullout-head` (five classes + an attribute). Exactly one title bar is blue on every board (fenced).
- **The resize edges sit under the title bar** (`.desk-pullout-head { position: relative; z-index: 3 }`): round two's edge handles took the outer column of the close and depth gadgets (6 of 9 points).
- **The right button** on the title bar opens the window's menu at the pointer, beside the title so the name stays readable (board C1-2b): Iconify ⌘M, Zoom ⌃M, To back ⌃B, Close window ⌘W, then `Desk ▸` and `Go ▸` from the verb registry, every row with its Amiga-key column (⌘ is the Amiga key). The key wells are raised steel caps. ⌃M and ⌃B are proposals for C2's fence (no verb shows a key that does not run).

What C2 builds behind these gadgets: depth (send to back; the canvas stands in by reordering `panelOrder`), zoom between two remembered rects, the right button anywhere in a window, the shortcuts.

## 4. The screen title bar (→ `DeskChrome.tsx`, `chrome-menus.css`, `attention.css`)

Board C1-1. One line, 28 px, paper with an ink rule:

`[mark] HoldSpeak · Desk Object Go Window │ <front window name> ······ [hub lamp] [egress chip] [bell n] [Search ⌘K] [day · time]`

- The front window's name is the screen's title, in 13 px bold display ink, ellipsized. With no desk window open, it names the front Chair window (`Needs you`). It reads the same mark as the blue frame, so the bar never disagrees with the glass.
- Menu titles hover inverted (ink plate, paper text), as Workbench did.
- The status controls (egress, bell, search) are raised steel plates; the clock sits in a steel plate at the right edge.
- The bell's count is THE needs-you number (§5a) on the ember ink plate (5.24:1; today `--accent` at 3.79:1).
- **393:** one 44 px row of 44 px targets: the mark (picture only), `Go` (it carries every menu's verbs, Search and `Chair ▸` among them), the front window's name, the egress chip at its scope's mark (its words stay in its accessible name), the needs-you bell, the time.

## 5. The Chair composed of windows (→ `web/src/desk/chair/**`, `chair.css`)

Boards C1-1, C1-4a–e. The Chair is a Workbench screen. The Arrival's existing sections move, unchanged, into four windows:

| Window | Sections (by their test ids) | 1440 place |
|---|---|---|
| Needs you | headline, SETUP blocker, coverage, needs-you, muted | left, top → above Capture |
| Capture | the capture bar (Talk, Write a thought, Record meeting, Schedule), the aftercare slot | left, bottom, 100 px |
| Brief | the brief section, its date, its receipt, its SEND well | right, top half |
| The week | week strip, calendar events, armed recordings, meetings, thoughts, agents | right, bottom half |

- Each is a `DeskWindowFrame` host (ids `chair:needs`, `chair:capture`, `chair:brief`, `chair:week`) with the full gadget set; its body scrolls by itself; the Chair as a whole never scrolls at 1440.
- Zoom fills the screen (C1-4b); depth sends it back; **close closes** (§5b).
- The capture bar is no longer a bar over content: it lives in its window.
- **The work first (R3):** the Needs-you window leads with `8 need you`, the ranking strip on its own line (393: `RANKED ▾`, §3a), the availability and calendar line, then `ACTIONS 5 OF 7`; SETUP drops below the actions as one compact row. The Brief window is 64 % of the right column so SEND and its destination are on the first screen at 1440.
- **393:** one window at a time (§5b).

## 5a. One meaning of "needs you" on every face (story 03, A2; drawn fixed)

The canvas draws the Desk after A2, not today's contradictions:

- **One number:** `needsYou = R1 ranked rows + R2 meeting-path blockers + R3 failed summaries` (story 03). On the seeded week it is 8 (7 actions + 1 blocker). The Chair head (`8 need you`), the bell, the Dock's Intelligence icon and the Desk memory icon carry the same 8 on every board. The build reads H-A2's `needsYou.ts`; the canvas publishes the Chair's count.
- **A narrower count says what it counts:** the Chair's capped list is `ACTIONS 5 OF 7` (its `2 MORE · Show all` stays); Meetings' head says `All summaries done` or `N meetings need summaries`; the Room says `N open here` / `Clear here`, its section `OPEN HERE`, its empty line `Nothing open`. Only the one number is ever called "needs you". The Chair window's name, `Needs you`, is the window's title.
- No counter of zero: an empty narrower count says the true thing in words.

## 5b. One window lifecycle and the phone (R1, R2)

**Close closes, on every window, the Chair's included. Depth sends to back.** Two gadgets, two functions (C1-4c).

- A closed Chair window comes back from **`Window ▸ Chair`** (393: `Go ▸ Chair`): Needs you / Brief / The week / Capture (393: without Capture), a check on each open one; picking one opens it in front (C1-4d, C1-4e).
- At 1440 the Chair's screen holds **one compact reopen Button** (library Button, dense, the window's name) where a closed window was (C1-4c). At 393 a closed window gives the work area to the next open Chair window; with none open, the Chair shows a reopen Button for each.
- **Handoff to B2 (story 07):** B2's persisted document carries the four Chair window ids `chair:needs`, `chair:brief`, `chair:week`, `chair:capture` — each one's open/closed state, rect, zoom and place in the order — so a reload brings the Chair back as he left it.

**The phone is one window at a time** (C1-6a, every 393 board):

- One window fills the work area: 852 − 44 (screen bar) − 44 (window head) − 56 (shelf) − 4 (frame) = 704 px of content by design (C7: ≥ 700; the measured value is in the canvas README's generated block). No stack of collapsed bars.
- Switch windows from the Dock (the daily seats: Intelligence, Meetings, People, Speak) or `Go ▸ Chair`. Opening a Chair window from `Go` iconifies the window in front to its Dock chip; it never closes it.
- Capture is on demand: the Speak AppIcon (a daily seat) or the pop-key (C6); no permanent strip.
- Every target owns a 44 × 44 box at 393 (fenced by nine points): screen-bar controls, gadgets, the strip menu Buttons, shelf icons, menu rows, body controls. The first `Done` is whole on the first screen. Nothing scrolls sideways except the Dock (§3a).
- The footer at 393 is two rows by explicit grid areas (`"egress egress" "receipt verbs"`): the egress chip, then the receipt and the verbs, so a warning never runs under `MD`/`SRT` (round 3c; fenced by the rendered-overlap fence).
- **No rendered overlap** (round 3c): no two visible interactive or text elements of one window, bar, shelf or menu intersect; named exceptions: content scrolling under a sticky bar of its own window, the in-well MicButton, an icon scrolled under the Dock's More gadget. On the shelf, a state tag and a count never share a box: at 1440 the tag takes the icon's top-left and the count its top-right (an icon with both is at least 128 px); at 393 the tag rides the foot and reads short (`FAILED` for `SEND FAILED`).

## 6. The AppIcon shelf and live state (→ `window/Dock.tsx` logic by H-C3; `dock.css` by C3-W)

Boards C1-1, C1-3 (the states).

- The Dock is a steel shelf across the full width, 76 px (393: 56 px). It never leaves the viewport: the shelf scrolls inside itself when it is full; an icon never shrinks (1440: 66 px at least).
- **393:** the shelf shows the daily seats first (Intelligence, Meetings, People, Speak), each 85 px, and ends on a whole icon; a 48 px `More AppIcons` gadget (▸, library Button) stays at the right edge and moves one page; the shelf snaps to whole icons. The projects follow behind More.
- An AppIcon is the 32 px sprite over its name (12 px bold mono ink). At 393 the name goes to the accessible name; the picture and the state stay.
- **States drawn ON the icon:**
  - rest: no plate;
  - running: a sunken steel plate, the name inverted (ink plate, paper text);
  - front: the name on the blue plate;
  - a count: an ember-ink notch at the top right (`7`, `3`), never a zero (A.8);
  - a state tag on the icon that owns the thing (the window a send left from): `● REC 12:04` (REC red; only when the hub confirms, A3), `READY 1` (a meeting's summary is ready), `SENT 14:02` (a send settled), `SEND FAILED` (REC red), `UNKNOWN` (a send whose result is not known), `1:1 14:30` on People (C1-8a, C1-8b);
  - **disconnected:** one `OFFLINE · AS OF hh:mm` tag heads the shelf; no tag and no count is drawn, so nothing claims to be fresh (C1-8c);
  - **one AppIcon per active project**, always: the drawer sprite, the project's name, its needs-you count only when it is not zero (Staff hiring: no badge; never hidden, never a zero).
- No status window.
- Open windows that are not applications keep their chips: raised steel tabs (front: blue), 200 px at most, ellipsized.

## 7. Parked and Restore (A1-F → `HistoryCore.tsx`, `WorkbenchWindow.tsx`)

Boards C1-5a–j. Every outcome is a compact receipt in the footer's receipt slot (the existing `surface-footer-receipt-line` species).

- **Meetings:** the selected record's footer verb is `Park` (library Button, ghost, dense). No confirm: Restore undoes it (Tenet 1). Park removes the row from the list and writes the receipt `PARKED <hh:mm>` + `Restore` in the footer's receipt slot.
- **The Parked filter:** a `CheckGadget variant="token"` reading `PARKED <n>` under the facets. It is absent while nothing is parked (A.8). On: the list gives way to the parked rows: `SurfaceLedgerRow` with the park time, the primary title, a `PARKED` chip and `Restore`.
- **Restore:** the row returns to the list, comes into view and is marked; the receipt reads `RESTORED hh:mm` (C1-5d, C1-5h). The token goes when nothing is parked.
- **Restore refused:** `NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE` + `Retry` (danger tone; C1-5e).
- **Claimed by a run:** a run claims an item between the read and the press: `NOT PARKED · CLAIMED BY A RUN` (danger tone; no Restore: nothing changed; C1-5i). A claimed item shows no Remove (today's rule stays).
- **Bulk:** the voice intent `Clear done` is also a visible library Button while done items exist; it parks them all: `PARKED 2 · hh:mm` + `Restore` (restores all; C1-5j).
- **The Workbench window:** `Remove` on an item parks it; the same receipt, the same token above the items, the same parked rows with Restore (C1-5f–h).
- The words: `Park`, `PARKED`, `Restore`. Never `Delete` or `DELETED` on these two faces.
- H-A1 supplies the routes and the client functions; the canvas keeps the parked set in the harness.

## 8. The seven criteria: where to check each

| # | Criterion | Board | What to check |
|---|---|---|---|
| 1 | Every window carries one gadget set — close, depth, zoom — in one place | C1-2a–d, C1-4b–e, C1-6b | close at the left; iconify, zoom, depth at the right of every title bar; the sizing gadget bottom right. **At 393 the set is close + depth** (a window fills the work area, so zoom has nothing to do; the Chair windows follow the same rule). Close closes and depth sends back on every window (§5b). Fenced: every window's set and every frame control's nine points (the counts are in the canvas README's generated block) |
| 2 | A screen title bar names the front window and the time | C1-1, C1-2a, C1-2c | the name equals the ONE blue window (fenced: one blue bar per board; the intended front window matches the recorded one) |
| 3 | One material as tokens, worn by every DeskWindowFrame host | C1-3, C1-2a, C1-5f, C1-6b | the frame, bar and gadgets on Meetings, the Room, People, the Workbench window, the Chair windows; the host tokens no longer re-pointed (People reads on its own well). Not shown: all 19 hosts one by one |
| 4 | The Chair is composed of windows (brief, needs you, the week), not one scrolling page | C1-1, C1-4a–e | four windows with their own gadgets and scroll; one lifecycle; at 393 one at a time |
| 5 | The 12 px floor and library Buttons throughout | all | fenced on the WHOLE board: 0 texts under 12 px, 0 texts under 4.5:1 (3:1 large) in place; inherited raw buttons assigned in the canvas README |
| 6 | Both widths | every board; C1-6a, C1-6b | 393: ≥ 700 px of content and every target owns 44 × 44 (fenced; values in the README's generated block) |
| 7 | Live state on the AppIcons, not in a status window | C1-1, C1-8a–c | REC, READY, SENT, SEND FAILED, UNKNOWN, OFFLINE · AS OF, 1:1, project counts (no zero, no project hidden), the one needs-you number |
| A2 | One meaning of needs you (drawn fixed) | every board | Chair head = bell = Dock = 8; narrower counts named; fenced |

## 9. What each later story inherits (the handoffs)

- **C1 build (11):** the strip rule of §3a (FilterTokens and wings render their menu form; contract.md); the tokens (§2: `--wb-*`, `--accent-text`; the host tokens NOT re-pointed), the frame, bar and gadget set (§3) in `DeskWindow.tsx`, `pullout.css`, `window-chrome.css`; ONE `is-front` from the one `panelOrder` and the replacement of `window-chrome.css:337` (§3); the edges under the bar; the screen title (§4); the Chair as four `DeskWindowFrame` hosts with the lifecycle of §5b; the work-first Needs-you window and the taller Brief (§5). Fences that assert the traffic lights or the Chair's one-page structure change in the same commit.
- **B2 (07):** persists the four Chair window ids `chair:needs`, `chair:brief`, `chair:week`, `chair:capture` (open/closed, rect, zoom, order) with every other window family (§5b).
- **C2 (12):** the behaviour behind the drawn gadgets: depth, zoom's two rects, the right button anywhere (a long-press at 393), the Amiga-key column with ⌃M and ⌃B proposed here.
- **C3 / C3-W (13):** the AppIcon states of §6 exactly: the notch; the tags READY, SENT, SEND FAILED, UNKNOWN, REC, 1:1; OFFLINE · AS OF with no fresh claim; one AppIcon per active project, a count only when not zero.
- **C4 (14):** the palette is a menu panel of §3/§4: paper, ink, the blue bar, the key column, the readable ghost stipple.
- **C5 (15):** `Send to ▸` joins the window menu of §3 between `Close window` and `Desk ▸`.
- **C6 (16):** capture from anywhere opens the Capture window (1440) or Speak (393); the pop-key.
- **C7 (17):** §5b's phone as drawn: one window fills the work area (≥ 700 px of content), 44 px screen bar, 44 px head row, 56 px shelf with the daily seats and More, every target 44 × 44, `Go ▸ Chair`; the strip menu form (§3a); the swipe between windows.
- **C8 (18):** the 12 px floor on the classes listed in the canvas README (R5); `--accent-text` for ember text; the raw buttons assigned to C8 there.
- **A1-F (02):** §7, all outcomes; the `Remove`/`Dismiss` raw chips on the item card.
- **A2-W (03):** §5a.
- **Seeds and rigs:** a destination path on a face reads `~/…`; no scratch path is ever drawn.
- **B1, B3:** their canvases draw on this material.

## 10. Limits and unknowns

- Stand-ins in the harness: depth; the AppIcon tags and counts; Park, Restore, the refused Restore and the claimed refusal; the needs-you number published from the Chair; the Chair windows are canvas windows (canvas README, "The stand-ins").
- The shelf scrolls at 1440 with several windows open (their window chips). Nothing leaves the screen. Folding window chips into their AppIcons is a C3 question; not drawn.
- ⌘ stands for the Amiga key; no Amiga-key glyph is drawn.
- Not verified: the owner's browser and screen; a real touch device (393 boards use a touch-enabled 393 viewport; the menu at 393 opens by the right button); all 19 hosts one by one; the Floor (out of scope).
