# The Workbench look (PHILO-13-11, C1) — the settled design for build

**Status: DRAFT, round two (Muad'Dib's read paid: the fixed Desk's one needs-you number, no scratch paths, the 393 shelf, the menu place), for Astra's check and the owner's ratification.** The canvas is `../assets/story-11-canvas/` (README, `index.html`, `shots/`). Nothing is built in product code. When the owner ratifies, his word goes here verbatim, and the build matches the boards, board beside shot (UX-CANON §A.2).

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

The alternative on board C1-7, **Honest 2.0**, puts the four pens on every body too. The contrast scan on the Chair at 1440 finds 8 texts under 4.5:1 (lowest 1.56:1) against 2 for Steel, both inherited body tokens (`shots/facts.json`, `_cmp_*`). Recommended: Steel.

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
| `--wb-screen-h` | `28px` | screen title bar |
| `--wb-gadget-w` | `26px` (393: `44px`) | one gadget |
| `--wb-raised` | `inset 1px 1px 0 --wb-hi, inset -1px -1px 0 --wb-lo` | a raised plate |
| `--wb-sunken` | the same, reversed | a pressed plate, an open wing, a running icon |
| `--wb-drop` | `4px 4px 0 rgba(0,0,0,.32)` | window and menu drop, no blur |
| `--wb-stipple` | 1 px lines every 4 px, 16 % ink | the drag bar |

Re-pointed existing tokens: `--desk-window-head-fill` → steel, `--desk-window-head-front` → blue, `--desk-window-keyline` → ink, `--gadget-fill` → steel, `--gadget-fill-hover` → steel-2; the work band: `--desk-work-top` = the screen bar, `--desk-work-bottom` = the shelf (84 px; 393: 72 px).

Contrast: ink on steel 7.81:1, ink on blue 5.40:1, ink on paper 17.12:1, REC on paper 5.73:1, text on the ember ink 5.24:1. Every word on the frame is 12 px or more.

The full rule set, each section naming its product file, is `../assets/story-11-canvas/harness/canvas.css` §1–§8.

## 3. The gadget set (→ `DeskWindow.tsx`, `pullout.css`, `window-chrome.css`)

One composition for every `DeskWindowFrame` host and every Chair window (board C1-2a):

- **Left, flush to the corner:** close. Glyph: a small white square in the middle (2.0).
- **Right, flush to the corner, in this order:** iconify (the window falls to its Dock chip; 3.9's gadget for today's minimize), zoom (a small black rect in a big rect), depth (two overlapping rects, the front one white).
- **Bottom right, on the frame:** the sizing gadget (two nested corners). It replaces the grip.
- Each gadget is a library `Button variant="chrome"`, an SVG glyph, 1 px ink divider, raised bevel on the bar's own fill; pressed = sunken. Accessible names: `Close <window>`, `Iconify <window>`, `Zoom <window>`, `To back <window>`.
- **393:** a window is a sheet. Close at the left, depth at the right, 44 × 44 px each; the title on the same line; the wings on a second line inside the bar; the sheet's top radius goes (0).
- The traffic lights (`.desk-traffic`, red/amber/green) are removed.
- **The title bar is the drag bar:** steel (front: blue), stipple, the title on a solid plate in 12 px bold mono ink, never shrinking (max 45 % of the bar). Wing tabs are raised steel; the open one is sunken paper (a cycle gadget). Whatever a host puts in its actions slot wears the steel plate and the 12 px floor.
- **One front window.** Today two windows can wear `is-front` at once (grounding `faces-surfaces.md:219`). The build derives `is-front` from the one `panelOrder` for every window family, Chair windows included. Only that window is blue.
- **The right button** on the title bar opens the window's menu at the pointer, beside the title so the name stays readable (board C1-2b): Iconify ⌘M, Zoom ⌃M, To back ⌃B, Close window ⌘W, then `Desk ▸` and `Go ▸` from the verb registry, every row with its Amiga-key column (⌘ is the Amiga key). The key wells are raised steel caps. ⌃M and ⌃B are proposals for C2's fence (no verb shows a key that does not run).

What C2 builds behind these gadgets: depth (send to back; the canvas stands in by reordering `panelOrder`), zoom between two remembered rects, the right button anywhere in a window, the shortcuts.

## 4. The screen title bar (→ `DeskChrome.tsx`, `chrome-menus.css`, `attention.css`)

Board C1-1. One line, 28 px, paper with an ink rule:

`[mark] HoldSpeak · Desk Object Go Window │ <front window name> ······ [hub lamp] [egress chip] [bell n] [Search ⌘K] [day · time]`

- The front window's name is the screen's title, in 13 px bold display ink, ellipsized. With no desk window open, it names the front Chair window (`Needs you`). It reads the same mark as the blue frame, so the bar never disagrees with the glass.
- Menu titles hover inverted (ink plate, paper text), as Workbench did.
- The status controls (egress, bell, search) are raised steel plates; the clock sits in a steel plate at the right edge.
- The bell's count is THE needs-you number (§5a) on the ember ink plate (5.24:1; today `--accent` at 3.79:1).
- **393:** one line: the mark (picture only), `Go`, the front window's name, the egress chip at its lamp, search at its glyph, the time. 28 px.

## 5. The Chair composed of windows (→ `web/src/desk/chair/**`, `chair.css`)

Boards C1-1, C1-4a, C1-4b. The Chair is a Workbench screen. The Arrival's existing sections move, unchanged, into four windows:

| Window | Sections (by their test ids) | 1440 place |
|---|---|---|
| Needs you | headline, SETUP blocker, coverage, needs-you, muted | left, top → above Capture |
| Capture | the capture bar (Talk, Write a thought, Record meeting, Schedule), the aftercare slot | left, bottom, 100 px |
| Brief | the brief section, its date, its receipt, its SEND well | right, top half |
| The week | week strip, calendar events, armed recordings, meetings, thoughts, agents | right, bottom half |

- Each is a `DeskWindowFrame` host (ids `chair:needs`, `chair:capture`, `chair:brief`, `chair:week`) with the full gadget set; its body scrolls by itself; the Chair as a whole never scrolls at 1440.
- Zoom fills the screen (C1-4b); depth sends it back; close sends it to the back of the Chair (a Chair window is never lost; B2 remembers each rect).
- The capture bar is no longer a bar over content: it lives in its window.
- **393:** the windows stack as title bars; ONE is open (default Needs you) and fills the rest of the screen; its zoom gadget opens another (C1-4b-393, C1-6a). C7 owns the phone gesture (swipe).

## 5a. One meaning of "needs you" on every face (story 03, A2; drawn fixed)

The canvas draws the Desk after A2, not today's contradictions:

- **One number:** `needsYou = R1 ranked rows + R2 meeting-path blockers + R3 failed summaries` (story 03). On the seeded week it is 8 (7 actions + 1 blocker). The Chair head (`8 need you`), the bell, the Dock's Intelligence icon and the Desk memory icon carry the same 8 on every board. The build reads H-A2's `needsYou.ts`; the canvas publishes the Chair's count.
- **A narrower count says what it counts:** the Chair's capped list is `ACTIONS 5 OF 7` (its `2 MORE · Show all` stays); Meetings' head says `All summaries done` or `N meetings need summaries`; the Room says `N open here` / `Clear here`, its section `OPEN HERE`, its empty line `Nothing open`. Only the one number is ever called "needs you". The Chair window's name, `Needs you`, is the window's title.
- No counter of zero: an empty narrower count says the true thing in words.

## 6. The AppIcon shelf and live state (→ `window/Dock.tsx` logic by H-C3; `dock.css` by C3-W)

Boards C1-1, C1-3 (the states).

- The Dock is a steel shelf across the full width, 76 px (393: 68 px). It never leaves the viewport: the shelf scrolls inside itself when it is full; an icon never shrinks (1440: 66 px at least; the Chair's shelf fits with no scroll).
- **393:** the shelf shows the daily seats first (Intelligence, Meetings, People, the first project), each 85 px, and ends on a whole icon; a 48 px `More AppIcons` gadget (▸, library Button) stays at the right edge and moves one page; the shelf snaps to whole icons.
- An AppIcon is the 32 px sprite over its name (12 px bold mono ink). At 393 the name goes to the accessible name; the picture and the state stay.
- **States drawn ON the icon:**
  - rest: no plate;
  - running: a sunken steel plate, the name inverted (ink plate, paper text);
  - front: the name on the blue plate;
  - a count: an ember-ink notch at the top right (`7`, `3`), never a zero (A.8);
  - a state tag: a paper tag at the top, ink text: `● REC 12:04` in REC red on Meetings (393: `REC 12:04` at the foot; only when the hub confirms, A3), `1:1 14:30` on People;
  - one AppIcon per active project: the drawer sprite, the project's name, its needs-you count.
- No status window.
- Open windows that are not applications keep their chips: raised steel tabs (front: blue), 200 px at most, ellipsized.

## 7. Parked and Restore (A1-F → `HistoryCore.tsx`, `WorkbenchWindow.tsx`)

Boards C1-5a–f.

- **Meetings:** the selected record's footer verb is `Park` (library Button, ghost, dense). No confirm: Restore undoes it (Tenet 1). Park removes the row from the list and writes the receipt `PARKED <hh:mm>` + `Restore` in the footer's receipt slot.
- **The Parked filter:** a `CheckGadget variant="token"` reading `PARKED <n>` under the facets. It is absent while nothing is parked (A.8). On: the list gives way to the parked rows: `SurfaceLedgerRow` with the park time, the primary title, a `PARKED` chip and `Restore`.
- **Restore:** the row returns to the list; the token and the receipt go when nothing is parked.
- **The Workbench window:** `Remove` on an item parks it (drawn: single; bulk `Clear done` parks the same way, not drawn); the same receipt, the same token above the items, the same parked rows with Restore.
- The words: `Park`, `PARKED`, `Restore`. Never `Delete` or `DELETED` on these two faces.
- H-A1 supplies the routes and the client functions; the canvas keeps the parked set in the harness.

## 8. The seven criteria: where to check each

| # | Criterion | Board | What to check |
|---|---|---|---|
| 1 | Every window carries one gadget set — close, depth, zoom — in one place | C1-2a, C1-2c, C1-2d, C1-4b, C1-6b | close at the left; iconify, zoom, depth at the right of every title bar; the sizing gadget bottom right. Fence: 147 window observations, each one close + one depth (+ one zoom at 1440); no traffic light visible |
| 2 | A screen title bar names the front window and the time | C1-1, C1-2a, C1-2c | the name after the menus equals the one blue window (Needs you → Payments ledger cutover → Meetings after depth); the time at the right. Fenced on every board |
| 3 | One material as tokens, worn by every DeskWindowFrame host | C1-3, C1-2a, C1-5e | the token sheet; Meetings, the Room, People, the Workbench window and the Chair windows wear the same frame, bar and gadgets |
| 4 | The Chair is composed of windows (brief, needs you, the week), not one scrolling page | C1-1, C1-4a, C1-4b | four windows, each with its own gadgets and scroll; the Chair does not scroll at 1440 |
| 5 | The 12 px floor and library Buttons throughout | C1-2b, C1-3, all | fence: 0 texts under 12 px and 0 raw buttons in the proposal; inherited ones listed in the canvas README |
| 6 | Both widths | every board at 1440 and 393; C1-6a, C1-6b | the 393 frame is 96 px; gadgets 44 × 44 px |
| 7 | Live state on the AppIcons, not in a status window | C1-1, C1-3, C1-6a | REC on Meetings, 1:1 on People, counts on projects, the one needs-you number on Intelligence and Desk memory; no status window |
| A2 | One meaning of needs you (drawn fixed) | every board | Chair head = bell = Dock = 8; narrower counts named (`ACTIONS`, `All summaries done`, `Clear here`); fenced on all 29 |

## 9. What each later story inherits

- **C1 build (11):** the tokens (§2), the frame, title bar and gadget set (§3) in `DeskWindow.tsx`, `pullout.css`, `window-chrome.css`; the single `is-front`; the screen title (§4); the Chair as windows (§5). Fences that assert the traffic lights or the Chair's one-page structure change in the same commit.
- **C2 (12):** the behaviour behind the drawn gadgets: depth, zoom's two rects, the right button anywhere, the Amiga-key column with the keys ⌃M and ⌃B proposed here.
- **C3-W (13):** the AppIcon states of §6 in `dock.css`, exactly: the notch, the tag, running, front.
- **C4 (14):** the palette is a menu panel of §3/§4: paper, ink, the blue bar, the key column.
- **C5 (15):** `Send to ▸` joins the window menu of §3 between `Close window` and `Desk ▸`; its canvas draws on this material.
- **C6 (16):** capture from anywhere opens the Capture window of §5.
- **C7 (17):** the 393 frame of §3–§6 (28 px bar, 68 px shelf) as the start; the swipe between open windows; one window open.
- **C8 (18):** the inherited texts under 12 px listed in the canvas README (the Chair's ranking tokens, row details).
- **A1-F (02):** §7.
- **A2-W (03):** §5a: the Chair, the bell, the Dock and the narrower relabels as drawn.
- **Seeds and rigs:** a destination path on a face reads `~/…`; no scratch path is ever drawn.
- **B1, B3:** their canvases draw on this material.

## 10. Limits and unknowns

- The depth gadget, the AppIcon values and Park/Restore are stand-ins in the harness (canvas README, "The stand-ins").
- The shelf scrolls at 1440 with several windows open (C1-2a–d, C1-5a–f: their window chips). Nothing leaves the screen. Whether to fold open-window chips into their AppIcons instead is a C3 question; not drawn.
- ⌘ stands for the Amiga key; no Amiga-key glyph is drawn.
- Not verified: the owner's own browser and screen; a real touch device (393 boards use a 393 viewport with touch enabled, and the menu at 393 is opened by the right button, not a long-press); the Floor (out of scope).
- The Honest 2.0 contrast counts are from the Chair at 1440 and two windows; the other faces were not scanned.
