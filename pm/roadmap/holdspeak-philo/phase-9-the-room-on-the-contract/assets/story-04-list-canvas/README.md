# PHILO-9-04 canvas: the desk debts (the selection and the list face)

**Status: RATIFIED 2026-09-27 by the owner ("Ratify as drawn"), after Codex Astra r1 DNR → r2 DNR → r3 RATIFY** (`../../checks/canvases-astra-r1.md`, `../../checks/canvases-astra-r2.md`, `../../checks/canvases-astra-r3.md`; AskUserQuestion; review page https://claude.ai/artifact/ADQeZoxRYmWfYKEfL8wePT). His pick, verbatim: "Ratify as drawn (Recommended)", all seven recommendations. This canvas: Q6 the accent selection colours (`--selection-bg: var(--accent)`, `--selection-ink: var(--bg)`); Q7 at 393 the fold line (Kind, Zone and Attention on a second line under the name). Build exactly this. The seven answers across the four canvases: Q1 items after NEEDS YOU, omitted when empty; Q2 DELIVERED ×N; Q3 To + Mark delivered above the body; Q4 grant words set A; Q5 per-project list behind a visible ▸ Projects; Q6 the accent selection colours; Q7 at 393 the fold line.

Earlier status: (UX-CANON §A.2). Round two pays Codex Astra r1 finding 6 (`../../checks/canvases-astra-r1.md`); the ledger is at the end. Nothing is built in product code. The story is `../../story-04-the-desk-debts.md`; the debts are measured in `docs/internal/philo/phase-9/grounding/README.md` "The D2 debts".

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<n>-<board>-<width>.png`; rendered facts: `shots/facts.json`.

## What the boards are, exactly

- **Everything is live.** `harness/shoot.py` starts a REAL hub (`scripts/graph_walk.py serve`, an isolated HOME from `tempfile.mkdtemp`, its own database) and serves the PRODUCT app (`web/index.html`, `web/src/main.tsx`) with vite.
- **Board 0 (today)** is vite with `PROPOSAL=0`: nothing is swapped. It is the product at this branch.
- **Boards 1-7 (the proposal)** are vite with `PROPOSAL=1`. `harness/vite.config.mjs` swaps three species for copies with marked `PROPOSAL` blocks:
  - `DeskListView` → `harness/ProposedDeskListView.tsx` (the SHOWN word; the fold line under the name);
  - `DeskSortableTable` → `harness/ProposedDeskSortableTable.tsx` (the sort headers as the library `Button`; `foldColumns`);
  - `WorkMenu` (`DeskMenu.tsx`) → `harness/ProposedDeskMenu.tsx` (keep the measured panel inside the viewport). Every WorkMenu consumer gets it, not the list only.
- **The proposed library CSS** is `harness/canvas.css`: the selection token, the 12 px floor (list and menu), the list face as a `surface` container, the ember's lighter step for ATTN and ALL, the menu rows at 44 px at the narrow desk, and the ALL verb's position. In the build these are edits of the named product rules (`web/src/styles/tokens.css`, `global.css:68-71`, `web/src/desk/components/list-view.css`), not overrides. The `:root body` prefix exists only to win in the dev server's style order.
- **Seed:** the grounding probe's objects (`docs/internal/philo/phase-9/grounding/probes/d2_probe.py.txt`): zones Payments, Hiring, Architecture reviews; seven notes; "Ledger cutover plan" filed in Payments. The fresh hub adds its own objects. This run has **24** objects (the grounding run had 27), so the counts below are for 24.
- **A real Attention** (round two): `PUT /api/authority/control-mode {"control_mode": "neutral"}`, then `POST /api/desk/actuators/github/propose` with `source_ref: note:<Ledger cutover plan>` and the repo `example/payments`. Under the neutral mode the proposal asks for a per-action decision (`holdspeak/operation_policy.py`, `external_write`), so it waits `proposed` and never executes; the Desk projection counts it as `needs_attention` on that note (`holdspeak/db/projections.py` `_actuators`). Read back before the shots: `subject_counts` = `{needs_attention: 1}` (`facts.json` `_seed`). Nothing leaves the machine. (Under YOLO the same unregistered repo is refused and is a receipt, not attention.)

## Boards

| # | Board | What it shows |
|---|---|---|
| 0 | `0-today-list` | Today. "24 SHOWNS OF 24". At 393 only NAME is on screen: the KIND, ZONE and ATTENTION headers end at 764, 842 and 922 px on a 393 px viewport. |
| 0 | `0-today-row-menu` | Today. The row menu on a note row near the bottom edge. At 393 Delete is cut: top 839, bottom 867, viewport 852 (**15 px**, as the grounding measured). At 1440 it is in view (bottom 875 of 900). |
| 0 | `0-today-selection-zone`, `-field` | Today. New Zone opens the name field with "New zone" selected. The selection paints `rgb(39,33,34)` on the field `rgb(21,23,29)`: **1.14:1**. The selection is not visible. |
| 0 | `0-today-selection-palette` | Today. The palette field with "Ledger cutover" selected: the same 1.14:1. |
| 1 | `1-list` | The proposal. "24 SHOWN OF 24". All text 12 px. At 1440 the four columns stay. At 393 KIND, ZONE and ATTENTION fold into a second line in the name Button (`ZONE · EMPTY`, `NOTE · PAYMENTS`), and their sort Buttons join the NAME header (`NAME ↑ KIND ZONE ATTENTION`, right edge 374 of 393). |
| 2 | `2-sorted-by-zone` | The Zone sort Button pressed: `ZONE ↑`, `aria-pressed="true"`, the rows in zone order. At 393 the same Button sits in the NAME header. |
| 3 | `3-row-menu-bottom` | The same row menu near the bottom edge. At 393 every row is 44 px (10 rows), and the panel measures itself after layout and moves up: Delete top 797, bottom 841, viewport 852 (in view). At 1440 the rows stay 28 px and nothing moves (Delete bottom 875 of 900). |
| 4 | `4-one-shown` | Dive into Payments: "1 SHOWN OF 1" (singular), the census `ALL · 1 ITEM · 1 ATTN`, the row `NOTE · PAYMENTS · ATTN 1` at 393. No horizontal overflow (page width 393). |
| 7 | `7-attention` | The row with Attention in view: `ATTN 1` in the ATTENTION column at 1440, on the fold line at 393; 12 px, `--accent-hover`, 4.99:1. |
| 5 | `5-selection-zone`, `-field` | The proposed selection on the zone name field: the accent ground, the page ink. |
| 6 | `6-selection-palette` | The proposed selection on the palette field. |

## The strings (exact)

| Slot | Today | Proposed |
|---|---|---|
| Status, many | `24 SHOWNS OF 24` | `24 SHOWN OF 24` |
| Status, one | `1 SHOWN OF 1` | `1 SHOWN OF 1` (unchanged) |
| Sort verbs | `Name`, `Kind`, `Zone`, `Attention` (raw `<button>`) | the same words on the library `Button`; the sorted one adds `↑` / `↓` |
| Fold line at 393 | none (columns off screen) | `<KIND> · <ZONE>` and `ATTN <n>` when there is attention; a zone row reads `ZONE · <n> ITEM(S)` or `ZONE · EMPTY`. An empty token is not printed (no counter of zero) |

No prose, no modal, no new verb.

## The selection token (numbers)

WCAG ratios, measured in the browser (`facts.json` `selection`), at 1440 and 393 (the same at both widths):

| | Today (`--accent-soft`, `rgba(168,110,74,.12)`) | Proposed (`--selection-bg: var(--accent)`, `--selection-ink: var(--bg)`) |
|---|---|---|
| Selection against the field (`rgb(21,23,29)`) | **1.14:1** | **4.26:1** |
| Selected text against the selection | 14.21:1 | **4.56:1** |
| Unselected text against the field | 16.14:1 | 16.14:1 |

Both proposed ratios pass: the story needs 3:1 for the selection against the field; the text needs 4.5:1. The alternative from the same tokens, `--accent-ink` (`#8a5a3d`) with light text (`--text-on-accent`), computes to 3.09:1 on `--surface-1` and **2.86:1** on `--surface-2` (computed, not rendered), so it fails on the lighter ground.

## Measurements (`facts.json`)

The text scan and the contrast scan cover the list AND every open menu (the WorkMenu portals to `#desk-next`, outside the list).

| Measure | Today 1440 | Today 393 | Proposal 1440 | Proposal 393 |
|---|---|---|---|---|
| Visible text nodes under 12 px (list + open menu) | 41-46 | 28-31 | **0** (every board) | **0** (every board) |
| Raw (non-library) buttons in the list | 4 | 4 | **0** | **0** |
| Body cells past the right edge | 0 | 83-86 | 0 | **0** |
| Page width (`scrollWidth`) | 1440 | 393 | 1440 | **393** on every board (board 4 was 394 in round one) |
| Menu rows (height) | 28 | 28 | 28 | **44** |
| Row menu's Delete (top-bottom / viewport) | 847-875 / 900 | 839-867 / 852, **cut 15** | 847-875 / 900 | **797-841 / 852** |
| `ATTN 1` (12 px on `--surface-2`) | **3.92:1** (`--accent`, 10 px) | **3.92:1** | **4.99:1** (`--accent-hover`) | **4.99:1** |
| The census `ALL` verb (dived) | not measured | not measured | 4.99:1 | 4.99:1 |
| Lowest text contrast (list + menu) | **3.92:1** (ATTN) | 5.74:1 | 4.99:1 | 4.99:1 |
| Pointer ownership (real pointer + `elementFromPoint`) | not probed | not probed | **23 controls, 207 points, all owned** | **23 controls, 207 points, all owned** |
| Page errors | 0 | 0 | 0 | 0 |

**Pointer ownership** (`facts.json` `pointer`): the sort Buttons (boards 1, 2, 4), the census ALL verb (board 4) and the ten menu rows (board 3). Each control is probed at nine points: the centre, the four edge midpoints and the four corners, inset 1 px. At each point `elementFromPoint` must land inside the control, AND a real pointer move (`page.mouse.move`) must dispatch a `pointermove` whose target is inside the control (the grant canvas's method). At 1440 the points are on the painted face; at 393 on the 44 × 44 target (the face's width, 44 px tall on its centre; the sort Buttons are 44-71 px wide by the library's `min-inline-size`; the menu rows are 44 px tall). Per width: 23 controls (4 sort Buttons on boards 1 and 2; 4 sort Buttons and ALL on board 4; all 10 menu rows on board 3), 207 points, every point owned by both checks, at both widths (round three, Codex Astra r2 finding 3).

## Two questions for the owner

1. **The selection token: the accent ground with the page ink** (`--selection-bg: var(--accent)`, `--selection-ink: var(--bg)`), desk-wide? It is 4.26:1 against the field and 4.56:1 for the selected text. The alternative, `--accent-ink` with light text, is 2.86:1 on the lighter ground. Note: in the palette the selected text and the active option are the same colour (board 6). **Recommended: yes, the accent ground with the page ink.**
2. **At 393, fold Kind, Zone and Attention into a second line under the name**, with their sort Buttons in the Name header (boards 1, 2, 7)? Other options: (b) keep the columns and scroll the table sideways with the name column held; (c) keep only Name and Kind at 393 and drop Zone and Attention. (a) keeps every value and every sort on screen without a sideways scroll; its cost is rows about twice as tall at 393. **Recommended: (a), the fold line.**

**Settled, not asked:** every desk menu keeps its whole panel inside the viewport. It is the WorkMenu species' rule (`harness/ProposedDeskMenu.tsx`, the `useLayoutEffect` at :486: after layout the panel measures itself and moves up or left), mandatory for every menu, not only the list's row menu; at the narrow desk each row is 44 px.

## Limits (what the boards are not)

- The CSS in `harness/canvas.css` is a statement of the library edit. It is not built; the product files are unchanged.
- The seed gave 24 objects, not the grounding's 27; the debts reproduce the same (SHOWNS, the three columns off screen, Delete cut 15 px, 1.14:1).
- Today's product was not shot in the dived state, so whether today's board 4 overflows is unknown; the cause found (below) is in today's CSS as well.
- The menu at 393 covers the dock while it is open (board 3); the keep-in-view rule keeps it inside the viewport, not above the dock.
- Pointer ownership was probed on the controls this canvas changes, not on every control on the desk.

## Fence sketch for story 04 (not built)

Real hub, isolated HOME, rendered at 1440 and 393; each red on main first:

| After | Assert | Red today |
|---|---|---|
| New Zone on the list; the palette with text selected | `getComputedStyle(field, '::selection')` over the field: at least 3:1; the selected text at least 4.5:1 | 1.14:1 |
| The list loads | no visible text node under 12 px in `.desk-listmode` | 41 / 30 nodes |
| The list loads; dive into a one-item zone | the status reads `N SHOWN OF M` for N = 24 and N = 1 | `24 SHOWNS` |
| The list at 393 | every visible header and cell ends at or before 393 px; each row's Kind and Zone text is readable in the row | three columns off screen |
| Any render | every `thead button` has class `btn` (a mutation back to a raw `<button>` turns it red) | 4 raw buttons |
| The row menu on a row near the bottom at 393 | every menu row is at least 44 px; the last menu item's bottom is at or above the viewport's bottom | 28 px rows; cut 15 px |
| The list and an open menu | no visible text under 12 px; every text at least 4.5:1 on its composited ground | ATTN 3.92:1 |
| Dive into a zone at 393 | `document.documentElement.scrollWidth` equals 393 | (unknown on main; 394 in round one) |
| Any board at 393 | at the centre, edge midpoints and corners of each sort Button, the ALL verb and each menu row, both `elementFromPoint` and a real pointer move land in that control | not probed |

## Reproduce

```bash
# from the repo root; the script boots the hub (isolated HOME) and vite on 127.0.0.1:4443
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py
```

The script refuses to start if port 4443 is already served (a stale server would answer with the wrong face).

## Round two: Codex Astra r1 finding 6 → where paid

| Part | Change (file:line) | Proof |
|---|---|---|
| Menu rows at least 44 px at 393 (UX-CANON C, `docs/internal/UX-CANON.md:100`) | `harness/canvas.css:100-104` (`.desk-work-menu [role=menuitem]` `min-height: var(--desk-button-hit-size)` at the narrow desk, in the menu species' own file `chrome-menus.css`, which keeps its viewport block: the menu is portalled outside every `surface` container) | board 3 at 393: 10 rows × 44 px; the keep-in-view rule re-measured with those rows: Delete 797-841 of 852 |
| The portalled menu in the text and contrast scans | `harness/shoot.py` FACTS: the scan roots are the list and every `[role=menu]`; the menu's 10 px `.quiet` reason and `.desk-menu-well` keycaps go to 12 px (`harness/canvas.css:105-111`; product `chrome-menus.css:141`) | 0 text nodes under 12 px on every proposal board with the menu open; lowest ratio 5.74:1 there |
| Board 4's horizontal overflow at 393 | **The element: the census ALL verb's 44 px halo (`.btn::after`, `web/src/styles/global.css:185-198`).** `list-view.css:68` sets that Button `position: static`, so the halo resolves against `.desk-listmode` and spans the whole list plus 1 px each side (right edge 394). Fix: `harness/canvas.css:41-55` (`position: relative; inset: auto` — the insets reset because `pullout.css:268-273` gives `.desk-surface` `top: 60px; left: 18px`, which a bare `relative` shifted 60 px down onto the Name header, where its halo met the sort Buttons') | page width 393 on board 4 (was 394); ALL owned at all five points |
| A real nonzero Attention | `harness/shoot.py:247-262` (neutral mode + a GitHub proposal bound to the note, through the real routes; never executed) | `_seed.attention_subject_counts` = `{needs_attention: 1}`; ATTN 1 rendered on boards 4 and 7 |
| ATTN contrast | today 3.92:1 (`--accent`, 10 px); `harness/canvas.css:89-93` gives `.desk-list-attention` `--accent-hover`, as the ALL verb | 4.99:1 at 12 px, both widths |
| Container queries per canon | `harness/canvas.css:79-87` makes `.desk-list-face` the `surface` container (not `.desk-listmode`: layout containment would capture its fixed foot); the fold is `@container surface (max-width: 720px)` (`:119`), as `list-view.css` does. "The build picks one" is removed | the fold renders at 393 on every board; 1440 keeps the four columns |
| Pointer ownership | `harness/shoot.py:178-218` (`POINTS`, `HIT`, `PM_ARM`, `PM_READ`) and `:326` (`pointer()`): nine points (centre, edge midpoints, corners), `elementFromPoint` and a real pointer move each; 44 × 44 at 393 (round three) | 23 controls, 207 points per width, all owned |
| Questions | two kept (selection, fold); the menu rule stated as settled | this README |

Found on the way: the Floor's list is in no window body, so no ancestor is a `surface` container and the two `@container surface (max-width: 720px)` blocks in `list-view.css` never apply to it today. That is why its columns run off the right edge at 393. The container above repairs it.
