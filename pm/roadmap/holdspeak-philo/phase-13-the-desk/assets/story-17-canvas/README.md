# PHILO-13-17 (C7) canvas: the phone desk

**Status: DRAFT, for Astra's check and then the owner's ruling. NOT RATIFIED** (UX-CANON A.2). Nothing here is built in product code. Every change lives under `harness/`.

Sources: the story (`../../story-17-c7-the-phone-desk.md`), the ratified C1 look (`../../design/workbench-look.md` §5b, the phone), B1's measured phone cost (`../../story-06-b1-one-open-grammar.md:74`: at 393 J1 takes 12 gestures and J3 prep 4. Every extra tap moves between Chair windows, `Go > Chair > <window>`), the aftercare red (`../../lane-rig-clearof-astra.md:17`: at 393 with Capture closed, the card has no host and floats as `ambient-aftercare-fixed` over work), and the owner's ruling that an arriving aftercare card opens the Capture window at 393.

## What main already gives (measured, not proposed)

C1's build already pays three of C7's lines on main `76c361537`, and these boards measure them:

- **The frame** is the 44 px screen bar plus the 56 px shelf: **100 px** (cap 142). Capture is a window on demand, never a bar. **Window content: 704 px** (floor 700) on all 14 boards at 393.
- **G5** (the Meetings footer chip ran under `MD` / `SRT`) is green on main. The egress chip has its own row (C1 round 3c). Board C7-7 measures 0 rendered overlaps.
- **The capture bar never sits over content.** It is inside the Capture window. The one case still red on main is the aftercare card (Q4 below).

## The proposal (`harness/c7.tsx`, Q1–Q6 in its header), 393 only

- **Q1 the swipe:** a horizontal touch swipe on the front window moves to the next open window (finger to the left) or back (to the right). The ring is the open Chair windows (Needs you, Brief, The week, Capture when open), then the open desk windows in the order they opened, and it wraps. A Chair window takes the work area the way `Go ▸ Chair` does: the desk window in front iconifies and is never closed.
- **Q2 the switcher:** the screen title is a library menu Button, `<front window> ▾`. It lists the same ring, with a check on the front window. **Any open window in 2 taps** (today: `Go > Chair > The week` = 3 taps, the row last in a 48-row menu).
- **Q3 Go, grouped:** Go leads with `Chair ▸ Desk ▸ Object ▸ Window ▸`, then its own rows (18 rows visible on the first panel). Today Desk, Object and Window ride flat inside Go. This makes the Desk, Object and Window menus reachable as menus.
- **Q4 aftercare:** an arriving aftercare card opens the Capture window at 393 (the owner's ruling). The card lands in Capture's slot and never floats over work.
- **Q5 44 px in every window:** at 393 every control in a window's body and footer owns 44 × 44. This is C1 R2's rule, not yet applied to every host. On main the meeting window's `Dictate about this` and `Record follow-up` are 27 px tall, and the Room's `Assign to …` and `Inspect …` are 27 px (recorded as `inherited_under_44` on main by the C5 run, `../story-15-canvas/shots/facts.json`).
- **Q6:** the aftercare card's eyebrow `Meeting ready` uses `--accent-text` (it reads 4.26:1 on main).

## What the boards are

The same method and harness as C5 (`../story-15-canvas/README.md`, "What the boards are"). The rig, the seed, the vite config and `board.py` (C1's ratified fence code, imported unchanged) live in `../story-15-canvas/harness/`. This folder holds `harness/seats-c7.mjs`, `harness/c7.tsx` and `harness/shoot.py`. Every press at 393 is a CDP touch tap, and every swipe is a CDP touch drag (start, six moves, end). At 393 **no target exception applies**: every target on every board owns its 44 × 44 box (C1's TARGETS44, unscoped).

## The boards (`shots/<board>-393.png`; 1440 controls `-1440.png`)

| Board | Shows | Acceptance line it answers |
|---|---|---|
| C7-1 the-frame (393 + 1440 control) | the Chair's Needs you: the frame 100 px, the content 704 px | 2 (content ≥ 700); Scope (frame ≤ 142) |
| C7-2a swipe-to-brief | one swipe: Needs you → Brief | 3 (a touch swipe moves to the next window) |
| C7-2b swipe-to-the-week | a second swipe: Brief → The week (a swipe back returns to Brief: fenced, no shot) | 3 (… and back) |
| C7-3a meeting-window | a desk window (the meeting) fills the work area | 3 (one window at a time) |
| C7-3b swipe-to-meetings | a swipe back: the meeting window → Meetings | 3 |
| C7-3c swipe-to-the-chair | past the first desk window, the Chair's window returns (The week) | 3 |
| C7-4a switcher-open | the screen title's switcher: Needs you, Brief, The week ✓, Meetings, Ledger cutover sync | the nav-cost fix (3 taps → 2) |
| C7-4b switcher-picked | the second tap: Needs you in front | the nav-cost fix |
| C7-5a go-grouped | Go: `Chair ▸ Desk ▸ Object ▸ Window ▸`, then its own rows | 5 (Desk, Object and Window menus reachable) |
| C7-5b go-object | `Go ▸ Object ▸` (the panel replaced, a back row first) | 5 |
| C7-5c go-window | `Go ▸ Window ▸` | 5 |
| C7-6 aftercare-opens-capture (393 + 1440 control) | an arriving card opens Capture at 393, the card in its slot, no fixed card. At 1440 Capture already holds it | 4 (no chrome over a content verb); the owner's aftercare ruling |
| C7-7 g5-meetings-footer | the Meetings record at 393: the egress chip on its own row; `MD`, `SRT`, `Park` clear and 44 px | 4 (G5) |
| C7-8 footer-verbs-44 | the meeting window: `Dictate about this`, `Record follow-up` own 44 px | 4 (hit ownership, the 44 px band) |
| C7-9 control-two-windows (1440) | two windows at 1440, unchanged | Out: the 1440 frame (the control) |

## Measurements

Read from `shots/facts.json` (run of 2026-10-02 on main `76c361537`; `ALL FENCES HELD`, exit 0):

| Measure | Value |
|---|---|
| Boards | 17 (14 at 393, 3 controls at 1440), each width on its own hub and HOME |
| Seat guard | `PHILO-13-15/17 SEAT GUARD (c7): 5 files, 5 seats, every anchor met` (3 C7 seats + 2 shared `~`-path seats) |
| Fence failures / browser errors | 0 / 0 |
| 393: the frame / the front window's content | 100 px on 14 of 14 / 704 px on 14 of 14 |
| 393: targets under 44 × 44 (every target, owned at 9 points) | 0 on 14 boards |
| Swipes landing where the ring says | 5 of 5 (→ Brief, → The week, ← Brief, ← Meetings, ← The week) |
| Taps to any open window | 2 (switcher), 1 swipe to a neighbour; today 3 to a Chair window |
| Texts under 4.5:1 in place / under 12 px / clipped / sideways strips / rendered overlaps | 0 / 0 / 0 / 0 / 0 |
| Exactly one blue title bar; the intended window in front, on the glass | 17 of 17 |

## Decisions for the owner (each with the recommended default)

1. **The swipe ring order.** (a) The Chair's windows first, then the desk windows in the order they opened; (b) the most recent first, like ⌃\`. **Recommended: (a)**, because it is a fixed order his thumb learns.
2. **A visible cue for the ring.** (a) None: the switcher is the cue (no counter, no dots); (b) a position token in the head (`2 OF 5`). **Recommended: (a)** (no prose, A.3; Tenet 1).
3. **The switcher in the screen title.** (a) The title becomes `<window> ▾`; (b) keep the title as a label and put the window list only in `Go ▸ Window`. **Recommended: (a)**: two taps from anywhere, on the bar he already reads.
4. **Go at 393.** (a) Group it: `Chair ▸ Desk ▸ Object ▸ Window ▸` first; (b) keep today's flat list. **Recommended: (a)**.
5. **Aftercare at 393 (his ruling, drawn).** When the card arrives while a desk window is in front, that window iconifies to its Dock chip and is not closed (the same rule as `Go ▸ Chair`, `chairWindows.ts` `openChairWindow`; C7-6 is shot from The week, so this case has no shot). **Recommended: as drawn.** Q4 opens Capture only on the Chair screen, not on the Floor.
6. **Q5's scope.** (a) Every control in a window body and footer at 393 owns 44 px; (b) only the footer verbs. **Recommended: (a)**, C1's ratified R2 rule applied to every host.

## Limits

- Not verified: a real phone (393 is a touch-enabled headless viewport) and real finger timing. A swipe that starts on a text field, a select, a menu or the Dock is ignored by design (the caret and the shelf keep their own drag).
- The swipe is drawn on the Chair screen. On the Floor at 393 the ring holds the desk windows only (not shot).
- The aftercare card is published through the product's own `publishAftercare` with a seeded meeting (the frame a finished meeting sends), not by a real meeting ending.
- Red before for Q1–Q3: not measured as a run, because the switcher, the swipe and the grouped Go do not exist on main. Q4's red is Astra's recorded observation (`../../lane-rig-clearof-astra.md:17`). Q5's red is the C5 run's `inherited_under_44` on main's product.

## Reproduce

```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-canvas/harness/shoot.py
```
