# PHILO-9-04 canvas: the desk debts (the selection and the list face)

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2). Nothing is built in product code. The story is `../../story-04-the-desk-debts.md`; the debts are measured in `docs/internal/philo/phase-9/grounding/README.md` "The D2 debts".

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<n>-<board>-<width>.png`; rendered facts: `shots/facts.json`.

## What the boards are, exactly

- **Everything is live.** `harness/shoot.py` starts a REAL hub (`scripts/graph_walk.py serve`, an isolated HOME from `tempfile.mkdtemp`, its own database) and serves the PRODUCT app (`web/index.html`, `web/src/main.tsx`) with vite.
- **Board 0 (today)** is vite with `PROPOSAL=0`: nothing is swapped. It is the product at this branch.
- **Boards 1-6 (the proposal)** are vite with `PROPOSAL=1`. `harness/vite.config.mjs` swaps three species for copies with marked `PROPOSAL` blocks:
  - `DeskListView` → `harness/ProposedDeskListView.tsx` (the SHOWN word; the fold line under the name);
  - `DeskSortableTable` → `harness/ProposedDeskSortableTable.tsx` (the sort headers as the library `Button`; `foldColumns`);
  - `WorkMenu` (`DeskMenu.tsx`) → `harness/ProposedDeskMenu.tsx` (keep the measured panel inside the viewport). Every WorkMenu consumer gets it, not the list only.
- **The proposed library CSS** is `harness/canvas.css`: the selection token and the 12 px floor. In the build these are edits of the named product rules (`web/src/styles/tokens.css`, `global.css:68-71`, `web/src/desk/components/list-view.css`), not overrides. The `:root body` prefix exists only to win in the dev server's style order.
- **Seed:** the grounding probe's objects (`docs/internal/philo/phase-9/grounding/probes/d2_probe.py.txt`): zones Payments, Hiring, Architecture reviews; seven notes; "Ledger cutover plan" filed in Payments. The fresh hub adds its own objects. This run has **24** objects (the grounding run had 27), so the counts below are for 24.

## Boards

| # | Board | What it shows |
|---|---|---|
| 0 | `0-today-list` | Today. "24 SHOWNS OF 24". At 393 only NAME is on screen: the KIND, ZONE and ATTENTION headers end at 764, 842 and 922 px on a 393 px viewport. |
| 0 | `0-today-row-menu` | Today. The row menu on a note row near the bottom edge. At 393 Delete is cut: top 839, bottom 867, viewport 852 (**15 px**, as the grounding measured). At 1440 it is in view (bottom 875 of 900). |
| 0 | `0-today-selection-zone`, `-field` | Today. New Zone opens the name field with "New zone" selected. The selection paints `rgb(39,33,34)` on the field `rgb(21,23,29)`: **1.14:1**. The selection is not visible. |
| 0 | `0-today-selection-palette` | Today. The palette field with "Ledger cutover" selected: the same 1.14:1. |
| 1 | `1-list` | The proposal. "24 SHOWN OF 24". All text 12 px. At 1440 the four columns stay. At 393 KIND, ZONE and ATTENTION fold into a second line in the name Button (`ZONE · EMPTY`, `NOTE · PAYMENTS`), and their sort Buttons join the NAME header (`NAME ↑ KIND ZONE ATTENTION`, right edge 374 of 393). |
| 2 | `2-sorted-by-zone` | The Zone sort Button pressed: `ZONE ↑`, `aria-pressed="true"`, the rows in zone order. At 393 the same Button sits in the NAME header. |
| 3 | `3-row-menu-bottom` | The same row menu near the bottom edge. At 393 the panel measures itself and moves up: Delete top 813, bottom 841, viewport 852 (in view). At 1440 no change (bottom 875 of 900). |
| 4 | `4-one-shown` | Dive into Payments: "1 SHOWN OF 1" (singular), the census `ALL · 1 ITEM`. |
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

| Measure | Today 1440 | Today 393 | Proposal 1440 | Proposal 393 |
|---|---|---|---|---|
| Visible text nodes under 12 px in the list | 41 | 30 | **0** (every board) | **0** (every board) |
| Raw (non-library) buttons in the list | 4 | 4 | **0** | **0** |
| Body cells past the right edge | 0 | 82 | 0 | **0** |
| Row menu's Delete (bottom / viewport) | 875 / 900 | 867 / 852, **cut 15** | 875 / 900 | **841 / 852** |
| Lowest text contrast in the list | 6.42:1 | 6.42:1 | 5.74:1 | 6.42:1 |
| The census `ALL` verb (dived) | not measured | not measured | 4.99:1 (`--accent-hover`) | 4.99:1 |
| Horizontal page overflow | no | no | no | **yes on board 4 only** (see Limits) |
| Page errors | 0 | 0 | 0 | 0 |

The `ALL` verb in the census is `--accent` on `--surface-2`: **3.92:1** (measured in an earlier proposal run of this harness, before this change), under 4.5. The canvas moves it to `--accent-hover` (4.99:1). `ATTN <n>` uses the same `--accent`; no seeded object had attention, so it was not rendered or measured (computed: 3.96:1 on `--surface-2`). The build should give it `--accent-hover` too.

## Three questions for the owner

1. **The selection token: the accent ground with the page ink** (`--selection-bg: var(--accent)`, `--selection-ink: var(--bg)`), desk-wide? It is 4.26:1 against the field and 4.56:1 for the selected text. The alternative, `--accent-ink` with light text, is 2.86:1 on the lighter ground. Note: in the palette the selected text and the active option are the same colour (board 6). **Recommended: yes, the accent ground with the page ink.**
2. **At 393, fold Kind, Zone and Attention into a second line under the name**, with their sort Buttons in the Name header (boards 1, 2)? Other options: (b) keep the columns and scroll the table sideways with the name column held; (c) keep only Name and Kind at 393 and drop Zone and Attention. (a) keeps every value and every sort on screen without a sideways scroll; its cost is rows about twice as tall at 393. **Recommended: (a), the fold line.**
3. **The menu keeps itself in the viewport** (the WorkMenu species measures its panel after layout and moves up when it would pass the bottom edge), for every menu on the desk, not only the list's row menu? **Recommended: yes, in the species.**

## Limits (what the boards are not)

- The CSS in `harness/canvas.css` is a statement of the library edit. It is not built; the product files are unchanged.
- Board 4 at 393 shows a horizontal page overflow (`document.scrollWidth > 393`). The list's headers and cells are inside 374 px on that board; the overflowing element was not found. Unknown whether today's product overflows in the same dived state (not shot).
- `ATTN <n>` was not rendered (no seeded attention).
- The fold at 393 uses a viewport media query (`max-width: 720px`). The product's list rules use `@container surface`; the build picks one.
- The seed gave 24 objects, not the grounding's 27; the debts reproduce the same (SHOWNS, the three columns off screen, Delete cut 15 px, 1.14:1).
- Pointer ownership of each Button was not probed.

## Fence sketch for story 04 (not built)

Real hub, isolated HOME, rendered at 1440 and 393; each red on main first:

| After | Assert | Red today |
|---|---|---|
| New Zone on the list; the palette with text selected | `getComputedStyle(field, '::selection')` over the field: at least 3:1; the selected text at least 4.5:1 | 1.14:1 |
| The list loads | no visible text node under 12 px in `.desk-listmode` | 41 / 30 nodes |
| The list loads; dive into a one-item zone | the status reads `N SHOWN OF M` for N = 24 and N = 1 | `24 SHOWNS` |
| The list at 393 | every visible header and cell ends at or before 393 px; each row's Kind and Zone text is readable in the row | three columns off screen |
| Any render | every `thead button` has class `btn` (a mutation back to a raw `<button>` turns it red) | 4 raw buttons |
| The row menu on a row near the bottom at 393 | the last menu item's bottom is at or above the viewport's bottom | cut 15 px |

## Reproduce

```bash
# from the repo root; the script boots the hub (isolated HOME) and vite on 127.0.0.1:4443
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py
```

The script refuses to start if port 4443 is already served (a stale server would answer with the wrong face).
