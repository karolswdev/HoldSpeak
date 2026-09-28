# Evidence - PHILO-9-04

- **Story:** PHILO-9-04 - The desk debts: the selection and the list face (canvas first)
- **Status:** done
- **Date:** 2026-09-27

## Summary

- **The ratified design:** the owner ratified the list canvas "as drawn" on 2026-09-27 (`assets/story-04-list-canvas/` on PR #681, `design/philo-9-canvases`): Q6 the selection token `--selection-bg: var(--accent)` / `--selection-ink: var(--bg)` desk-wide; Q7 at 393 Kind, Zone and Attention fold into a second line in the name Button, their sort Buttons in the NAME header, by `@container surface`. Settled: every desk menu keeps itself in view, 44 px rows at 393; "SHOWN" for any count; all list text 12 px or more; the sort verbs the library Button; ATTN 4.99:1.
- **The port (the harness is not shipped):** the three PROPOSAL species copies and `canvas.css` are now edits of the named product rules. `web/design-tokens.json` (+ generated `web/src/styles/tokens.css`, `web/src/lib/tokens.gen.ts`): `--selection-bg`, `--selection-ink`. `web/src/styles/global.css` `::selection` reads them. `web/src/desk/components/list-view.css`: the 12 px floor (`--desk-surface-label-size`) on the band, mark, ledger cell, status, census, sortable head and group head and the Kind/Zone/Attention cells; the census ALL verb `position: relative; inset: auto` and `--accent-hover`; `.desk-list-attention` `--accent-hover`; the sort-Button rules; `.desk-list-face` is the `surface` container; the fold block `@container surface (max-width: 720px)`. `web/src/desk/components/chrome-menus.css`: the work menu's quiet reason and keycap wells at 12 px; its rows `min-height: var(--desk-button-hit-size)` at `max-width: 420px`. `DeskSortableTable.tsx`: `SortButton` (the library `Button`, ghost, dense, `aria-pressed`) and `foldColumns`. `DeskListView.tsx`: `FoldLine`, "SHOWN" for any count, `foldColumns={["kind", "zone", "attention"]}`. `DeskMenu.tsx`: the `useLayoutEffect` keep-in-view rule in the `WorkMenu` species (every consumer). Two vitest expectations that asserted the defect move with it (`DeskListView.test.tsx` "SHOWNS of" → "SHOWN OF"; `containerQueryLaw.test.ts` 2 → 3 `@container surface (max-width: 720px)` blocks, and the list face's container).
- **The fences (ship with the story):** `tests/e2e/test_philo9_04_desk_debts_glass.py` (7 tests × 1440 and 393, the real hub on an isolated HOME, the canvas harness's probes: composited contrast, text-size scan of the list AND the portalled menu, header and cell geometry, the nine-point pointer pass by `elementFromPoint` and a real `pointermove`); `tests/unit/test_philo9_04_sort_button_fence.py` (the structural fence and its mutation); `docs/internal/philo/graph/atlas-phase9.json` with four face cases at both widths (`case.p9.list_status.shown`, `case.p9.list_columns.in_view`, `case.p9.list_sort.zone_pressed`, `case.p9.list_row_menu.delete_in_view`), fenced by `tests/unit/test_philo9_04_atlas.py` (the general atlas fences applied to the file); `atlas.schema.json` admits job `p9`. The selection contrast and the 12 px floor have no atlas predicate (the rig reads no computed style); `excluded.p9.selection_and_text_floor` says so and names the glass. Story 05 assembles.
- **Proof scripts:** `assets/story-04-proof/` (`red_main.sh` puts main's seven product web files in place from `origin/main` by `git show`, builds, runs the fences and the rig, then puts the branch back; `green.sh`; `docs_nav.sh` = the CI Documentation Navigation job; `web_unit.sh`; `make_atlas.py` writes the atlas file; `rig_all.sh`; `swap.sh`).

### The red-first matrix (the charter's D2 rows) — first capture (red on main `1afcc576`), second capture (green)

| D2 row | 1440 on main | 393 on main | 1440 branch | 393 branch |
|---|---|---|---|---|
| Selection ≥ 3:1 (zone field, palette field) | **red** 1.14:1 | **red** 1.14:1 | 4.26:1 (text 4.56:1) | 4.26:1 (text 4.56:1) |
| List text ≥ 12 px (list + open menu) | **red** | **red** (the four text runs on main counted 24, 28, 34 and 46 nodes under 12 px, 10 px `ZONE`, `1 ITEM`, `NOTE`, the status, the sort verbs; the capture's grep does not pair each count with its width) | 0 | 0 |
| "SHOWN" (glass: many; atlas: 2 of 2) | **red** `24 SHOWNS OF 24`; `2 SHOWN OF 2` not found | **red** | `24 SHOWN OF 24`, `1 SHOWN OF 1`, `2 SHOWN OF 2` | the same |
| Every kept column in view | preservation green (glass and `case.p9.list_columns.in_view`) | **red** heads end 685/764/842/922; the row outside the viewport | four heads in view | `NAME ↑ KIND ZONE ATTENTION` ends 374; 0 cells past the edge; page width 393 (dived too) |
| Row menu's last entry in view | preservation green (glass; atlas Delete 847-875 of 900) | **red** Delete 839-867 of 852, rows 28 px | 847-875 of 900 | 797-841 of 852, ten rows × 44 px |
| Sort verbs are the library Button | **red** 4 raw; `aria-pressed=None` | **red** | `.btn`, `aria-pressed="true"` | the same |
| Structural fence + mutation | **red** raw `<button>` at `DeskSortableTable.tsx:96` | — | green; the mutation turns it red | — |

### The face matches the ratified canvas (built vs the canvas's `shots/facts.json`)

| Measure | Canvas (proposal) | Built |
|---|---|---|
| Selection vs field / selected text | 4.26:1 / 4.56:1 | 4.26:1 / 4.56:1 |
| 393 header row | `NAME ↑ KIND ZONE ATTENTION`, 67-374 | the same, right edge 374 |
| 1440 heads (right edges) | 227, 952, 1058, 1163, 1261 | 227, 952, 1058, 1163, 1261 |
| Sort Button faces 1440 / 393 | KIND 31.7×24 / 44×24; ATTENTION 71.3×24 | the same |
| Row menu Delete 1440 / 393 | 847-875 / 797-841, rows 28 / 44 | the same |
| ATTN 1 | 12 px, 4.99:1 | 12 px, 4.99:1 |
| Lowest text contrast (list + menu) | 4.99:1 | 4.99:1 |
| Page width dived at 393 | 393 | 393 |
| Pointer ownership (nine points each, both checks) | 23 controls, 207 points per width | 1440: 21 controls, 189 points; 393: 19 controls, 171 points; 0 not owned (4 sort Buttons, 3-6 name Buttons, ALL, 10 menu rows) |

- **Shots (1440 and 393, from the green capture):** `assets/story-04-shots/` — `list-*` (Attention in view), `columns-*`, `sorted-by-zone-*`, `one-shown-*`, `row-menu-bottom-*`, `selection-zone-*`, `selection-zone-field-*`, `selection-palette-*`, with the measurements beside them (`*.json`). Walked by eye at both widths: the fold line under each name at 393 (`NOTE · PAYMENTS · ATTN 1`), the four columns at 1440, the menu inside the viewport at 393, the selected name visible.
- **Web unit:** baseline-subset, zero branch-new (2927 passed); vitest `Test Files 323 passed`, `Tests 2927 passed`, no `Errors` line; `npm run check` (tokens, token gate, architecture guard, typecheck, tests, build, bundle gate) green.
- **Generated docs:** `docs/generated/api-reference.json` regenerated (the new glass names four routes as test candidates); every Documentation Navigation check exit 0.
- **Not paid here (BACKLOG "PHILO-9-04 follow-ups"):** the Workbench terminal's own xterm selection (computed 1.12:1, the same on main); the editor's AI bar over a selection (covers the body at 393); at 393 the open menu covers the dock (a stated canvas limit).
- **Unknown:** the atlas file is new here; story 01 was to fix the phase atlas file's name first and has not; if story 01 or 03 adds `atlas-phase9.json` too, the merge takes both case lists (story 05 assembles).

## Round two — Codex Astra counsel on built @f58cb5b0, DO-NOT-RATIFY (`checks/story-04-built-astra-r1.md`)

- **Finding 1 (merge blocker) PAID.** The desk-wide `::selection` ink (`--bg`) met the CodeMirror theme's own tint ground (`deskEditorTheme.ts:33`): selected note text 1.33:1 at both widths (main 12.99:1 text, but its selection ground 1.14:1). The editor now takes the same pair: `.cm-selectionBackground, ::selection` ground `var(--selection-bg)`, `::selection` ink `var(--selection-ink)` (`web/src/desk/components/deskEditorTheme.ts`). Fence: `test_the_editor_selection_is_readable[1440, 393]` (real selection in the CodeMirror body; every host in the edit window measured). Red at `f58cb5b0` (1.33:1) and on main (the title field and body selection 1.14:1 against the ground); green after: body 4.56:1 text / 3.92:1 against the editor ground, title and tags fields 4.56 / 4.26 (capture 06:13:09Z red; the green capture below).
- **The selection census (every host in the web source):** CSS `::selection` hosts — every `input` and `textarea` (the library field, the palette, the zone name field, the thread composer, the Ask panel, the session and coder pullouts: `grep '<textarea'`, 8 files) take the global pair; measured rendered: the list zone field, the palette field, the edit window's title and tags fields, the thread composer's textarea (`test_the_thread_composer_selection_is_readable`, red on main 1.14:1, green 4.26 / 4.56). CodeMirror: one theme (`deskEditorTheme.ts`) for every `DeskEditor` (notes, knowledge bases, the Thought document pane) — fixed and measured on the note editor. `contenteditable`: no editing host in the source (only the keymap and focus guards name it). xterm.js: its own canvas selection (`XtermPane.tsx:53`), computed 1.12:1, unchanged from main — ledgered (BACKLOG "PHILO-9-04 follow-ups").
- **Finding 2 PAID (inherited on main):** the Launch submenu of the Floor menu opened at the bottom-right at 1440 ended at 1474 × 1034 (main and `f58cb5b0`); main's Desk menu itself ended at 1454 × 906. The same measurement in the `WorkMenu` species now covers its desktop submenu (`DeskMenu.tsx`, the round-two `useLayoutEffect`): past the right edge the submenu opens on the parent panel's left side; past the bottom it moves up. Fence: `test_the_launch_submenu_keeps_itself_in_view` (1440 only; at the narrow desk the submenu replaces its panel). Red on main and at `f58cb5b0`; green after: Desk menu 1166–1432 × 566–892, Launch submenu 899–1165 × 438–892.
- **The claim narrowed:** "every desk menu keeps itself in view" is proved for what was exercised: the list's row menu (1440, 393), the Floor's Desk menu and its Launch submenu (1440). The rule is the `WorkMenu` species' (every consumer gets it), but other menus and submenus were not each measured; Astra sampled the menu bar menus (fit).
- **Finding 3:** the list repairs match the canvas (Astra's own reading); nothing to pay.
- **CI on `f58cb5b0` (run 36381571475):** Documentation Navigation, DeskOS Web Quality, Critical Journeys (G0), Linux Smoke, Route screenshots pass; the macOS jobs were cancelled by the round-two push.
- **CI on `0d7e987b` (run 36387708744), classified:**
  - Documentation Navigation, Critical Journeys (G0), Linux Smoke, Route screenshots, **Integration Tests (macOS)**: pass.
  - **Unit Tests: fail, inherited.** 24 failed + 31 errors; every one of the 55 is in main's own red on `1afcc576` (run 36369788814, job 108763477466: 27 failed, 31 errors; 58 ids, a superset: the Playwright-browser-missing unit rigs, the Phase 143 censuses, `test_product_copy`, `test_thread_modes`, the git-show-of-history tests). Branch-new: none.
  - **DeskOS Web Quality: fail, one vitest case, not this diff:** `RecallFace.test.tsx` "Carry into brief … keeps focus" (a focus assertion). `RecallFace` imports neither file round two changed; the same job passed on `f58cb5b0`; the file passes 5/5 locally at `0d7e987b`. Flaky; re-run on the next head.
  - **E2E Tests (macOS): fail.** (1) **Mine:** `test_the_launch_submenu_keeps_itself_in_view` hit the suite's 300 s per-test bound on the runner (the spatial Floor plus the nine-point pointer pass over every submenu row; the other fences took up to 200 s each there), which ends the pytest process; every other PHILO-9-04 fence passed in that job (18 of 18). Paid: `@pytest.mark.timeout(900)` on it, `600` on the two other pointer-pass fences. (2) **Inherited:** the `test_philo8_one_delete_glass.py` 1440 reds (main's run lists 16 E2E reds, this family among them); of the two not in main's list, `test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]` fails locally on main's product (`swap.sh main`) as on the branch (the palette option "detached from the DOM"), and `test_the_list_palette_delete_removes_the_selected_object[1440]` passes locally on both (flaky). PR #682 (`fix/main-e2e-inherited-reds`) is the home of that family.
- **The raw-`<button>` ratchet (Muad'Dib's word, 2026-09-28):** A1 106 → 105 in `tests/ux_canon_ceiling.json` (per-rule and the `DeskSortableTable` face, now `{A8: 1}`) and `A1_RATCHET` in `tests/unit/test_ux_canon_ratchet.py`, dated with the reason. Capture 09:37:16Z: the four canon fences 59 passed; the healing notice no longer lists A1 (A3-prose 48 → 43 and B 32 → 30 still heal, not lowered here: not this story's).
- **Green after round two:** capture 06:27:52Z (the glass, 19 cases incl. the five round-two runs, the unit and atlas fences, 237 passed; the rig's eight atlas runs pass); web unit 06:37:07Z (zero branch-new, 2927 passed, no Errors line, `npm run check` green); Documentation Navigation 06:40:25Z (every step exit 0). A capture at 06:18:29Z failed on a stale atlas source anchor (`DeskMenu.tsx`'s line moved); the atlas was regenerated and the next capture is green.

## Proof

### Captured run — 2026-09-28T04:58:37Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/red_main.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f3b2c1a2190dc69fb0f7b635f18ea147cc53d3

```text
origin/main = 1afcc57692325328964b0d63721d74d4af3c80ba
✓ built in 4.58s
(an empty diffstat above = main's product files are in place)
E               AssertionError: 24 SHOWNS OF 24
E               assert ('24 SHOWNS OF 24' == '24 SHOWN OF 24'
E                 
E                 - 24 SHOWN OF 24
E                 + 24 SHOWNS OF 24
E                 ?         +)
E                   AssertionError: [{'cls': '', 'px': 10, 'text': 'ZONE'}, {'cls': '', 'px': 10, 'text': '1 ITEM'}, {'cls': '', 'px': 10, 'text': 'ZONE'}...': '', 'px': 10, 'text': '1 ITEM'}, {'cls': '', 'px': 10, 'text': 'NOTES'}, {'cls': '', 'px': 10, 'text': 'NOTE'}, ...]
E                   assert 34 == 0
E               AssertionError: 24 SHOWNS OF 24
E               assert ('24 SHOWNS OF 24' == '24 SHOWN OF 24'
E                 
E                 - 24 SHOWN OF 24
E                 + 24 SHOWNS OF 24
E                 ?         +)
E               AssertionError: [{'in_view': True, 'right': 67, 'text': ''}, {'in_view': False, 'right': 685, 'text': 'NAME ↑'}, {'in_view': False, 'r...ext': 'KIND'}, {'in_view': False, 'right': 842, 'text': 'ZONE'}, {'in_view': False, 'right': 922, 'text': 'ATTENTION'}]
E               assert False
E                +  where False = all(<generator object TestDeskDebtsGlass.test_every_kept_column_is_in_view.<locals>.<genexpr> at 0x115b4c860>)
E                   AssertionError: ('zone field', {'end': 8, 'field_bg': 'rgb(21,23,29)', 'length': 8, 'selected_text_vs_selection': 14.21, ...})
E                   assert 1.14 >= 3.0
E                   AssertionError: [{'cls': '', 'px': 10, 'text': 'NOTE'}, {'cls': '', 'px': 10, 'text': 'NOTE'}, {'cls': '', 'px': 10, 'text': 'PERSONAL...cls': '', 'px': 10, 'text': 'NOTE'}, {'cls': '', 'px': 10, 'text': 'WORK'}, {'cls': '', 'px': 10, 'text': 'NOTE'}, ...]
E                   assert 24 == 0
E               AssertionError: [{'library': False, 'pressed': None, 'text': 'NAME ↑', 'visible': True}, {'library': False, 'pressed': None, 'text': '...ed': None, 'text': 'ZONE', 'visible': True}, {'library': False, 'pressed': None, 'text': 'ATTENTION', 'visible': True}]
E               assert ([{'library': False, 'pressed': None, 'text': 'NAME ↑', 'visible': True}, {'library': False, 'pressed': None, 'text': '...ed': None, 'text': 'ZONE', 'visible': True}, {'library': False, 'pressed': None, 'text': 'ATTENTION', 'visible': True}] and False)
E                +  where False = all(<generator object TestDeskDebtsGlass.test_the_sort_headers_are_the_library_button.<locals>.<genexpr> at 0x112f43ac0>)
E               AssertionError: [{'library': False, 'pressed': None, 'text': 'NAME ↑', 'visible': True}, {'library': False, 'pressed': None, 'text': '...ed': None, 'text': 'ZONE', 'visible': True}, {'library': False, 'pressed': None, 'text': 'ATTENTION', 'visible': True}]
E               assert ([{'library': False, 'pressed': None, 'text': 'NAME ↑', 'visible': True}, {'library': False, 'pressed': None, 'text': '...ed': None, 'text': 'ZONE', 'visible': True}, {'library': False, 'pressed': None, 'text': 'ATTENTION', 'visible': True}] and False)
E                +  where False = all(<generator object TestDeskDebtsGlass.test_the_sort_headers_are_the_library_button.<locals>.<genexpr> at 0x116f3c2b0>)
E                   AssertionError: ('zone field', {'end': 8, 'field_bg': 'rgb(21,23,29)', 'length': 8, 'selected_text_vs_selection': 14.21, ...})
E                   assert 1.14 >= 3.0
E               AssertionError: [{'cls': '', 'px': 10, 'text': '24 ITEMS · 9 ZONES · 1 ATTN'}, {'cls': 'desk-list-status', 'px': 10, 'text': '24 SHOWN...-table-sort is-current', 'px': 10, 'text': 'Name'}, {'cls': 'desk-sortable-table-sort', 'px': 10, 'text': 'Kind'}, ...]
E               assert 46 == 0
E               AssertionError: [{'cls': '', 'px': 10, 'text': 'ZONE'}, {'cls': '', 'px': 10, 'text': 'EMPTY'}, {'cls': '', 'px': 10, 'text': 'ZONE'},...: '', 'px': 10, 'text': '1 ITEM'}, {'cls': '', 'px': 10, 'text': 'ZONE'}, {'cls': '', 'px': 10, 'text': '1 ITEM'}, ...]
E               assert 28 == 0
E               AssertionError: [{'bottom': 603, 'h': 28, 'text': 'Open', 'top': 575}, {'bottom': 631, 'h': 28, 'text': 'Get Info', 'top': 603}, {'bot...m': 715, 'h': 28, 'text': 'Continue in thread', 'top': 687}, {'bottom': 743, 'h': 28, 'text': 'Edit', 'top': 715}, ...]
E               assert (867 <= 852)
E       assert 'import "./list-view.css";\nimport { useRef, type KeyboardEvent, type ReactNode } from "react";\nimport { useRovingRow...le-actions">{rowActions(item)}</td>\n            ) : null}\n          </tr>\n        );\n      })}\n    </>\n  );\n}\n' != 'import "./list-view.css";\nimport { useRef, type KeyboardEvent, type ReactNode } from "react";\nimport { useRovingRow...le-actions">{rowActions(item)}</td>\n   
E       AssertionError: raw <button> in DeskSortableTable.tsx: lines [96]
E       assert [96] == []
E         
E         Left contains one more item: 96
E         Use -v to get more diff
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[393]
FAILED tests/unit/test_philo9_04_sort_button_fence.py::test_a_raw_button_mutation_turns_the_fence_red
FAILED tests/unit/test_philo9_04_sort_button_fence.py::test_the_sortable_table_has_no_raw_button
14 failed, 2 passed in 132.69s (0:02:12)
case.p9.list_status.shown 1440 exit=1  
case.p9.list_status.shown 393 exit=1  
case.p9.list_columns.in_view 1440 exit=0  
case.p9.list_columns.in_view 393 exit=1  
case.p9.list_sort.zone_pressed 1440 exit=1  
case.p9.list_sort.zone_pressed 393 exit=1  
case.p9.list_row_menu.delete_in_view 1440 exit=0  
case.p9.list_row_menu.delete_in_view 393 exit=1  
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050219Z-case.p9.list_columns.in_view-muaddib-1440/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050219Z-case.p9.list_columns.in_view-muaddib-1440/after.png']
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 160, 'w': 1082, 'h': 41}
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050239Z-case.p9.list_columns.in_view-muaddib-393/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050239Z-case.p9.list_columns.in_view-muaddib-393/after.png']
NOTE: predicate: the text scope is outside the viewport: {'width': 393, 'height': 852}
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050441Z-case.p9.list_row_menu.delete_in_view-muaddib-1440/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050441Z-case.p9.list_row_menu.delete_in_view-muaddib-1440/after.png']
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 252, 'h': 28}
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050500Z-case.p9.list_row_menu.delete_in_view-muaddib-393/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050500Z-case.p9.list_row_menu.delete_in_view-muaddib-393/after.png']
NOTE: predicate: the control is outside the viewport: {'width': 393, 'height': 852}
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050318Z-case.p9.list_sort.zone_pressed-muaddib-1440/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050318Z-case.p9.list_sort.zone_pressed-muaddib-1440/after.png']
NOTE: predicate: aria-pressed=None, wanted 'true'
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050403Z-case.p9.list_sort.zone_pressed-muaddib-393/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050403Z-case.p9.list_sort.zone_pressed-muaddib-393/after.png']
NOTE: predicate: aria-pressed=None, wanted 'true'
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050056Z-case.p9.list_status.shown-muaddib-1440/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050056Z-case.p9.list_status.shown-muaddib-1440/after.png']
NOTE: predicate: '2 SHOWN OF 2' NOT in observe_at text
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo9-04-main/20260928T050139Z-case.p9.list_status.shown-muaddib-393/before.png', '.tmp/graph-walk/philo9-04-main/20260928T050139Z-case.p9.list_status.shown-muaddib-393/after.png']
NOTE: predicate: '2 SHOWN OF 2' NOT in observe_at text
✓ built in 4.62s
 9 files changed, 237 insertions(+), 36 deletions(-)
```

### Captured run — 2026-09-28T05:05:52Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f3b2c1a2190dc69fb0f7b635f18ea147cc53d3

```text
HEAD = 1afcc57692325328964b0d63721d74d4af3c80ba; product diff vs origin/main:
 9 files changed, 237 insertions(+), 36 deletions(-)
✓ built in 4.59s
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_the_sortable_table_has_no_raw_button
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_a_raw_button_mutation_turns_the_fence_red
PASSED tests/unit/test_philo9_04_atlas.py::test_every_named_case_is_in_the_atlas
PASSED tests/unit/test_philo9_04_atlas.py::test_every_case_runs_at_both_widths
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_keeps_its_human_sentence]
PASSED tests/unit/test_philo9_04_atlas.py::test_face_checks_read_what_is_readable
PASSED tests/unit/test_philo9_04_atlas.py::test_the_menu_case_asks_44px_at_393_only
PASSED tests/unit/test_philo9_04_atlas.py::test_every_face_case_without_an_op_is_excluded_with_a_reason
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_ui_action_is_one_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_state_id_resolves]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_precondition_check_compares_two_snapshots]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_reference_inside_the_atlas_resolves]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_clock_a_case_uses_is_declared]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_precondition_check_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_case_carries_one_trigger]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_check_asserts_the_result_the_trigger_must_produce]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_face_cases_carry_both_ruled_viewports]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_step_acts_on_a_root_placeholder]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_navigation_steps_carry_no_selector]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_desk_face_case_crosses_the_gate_first]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_captured_id_names_the_field_it_reads]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_predicate_is_a_kind_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_predicate_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[393]
232 passed in 367.91s (0:06:07)
case.p9.list_status.shown 1440 exit=0  
case.p9.list_status.shown 393 exit=0  
case.p9.list_columns.in_view 1440 exit=0  
case.p9.list_columns.in_view 393 exit=0  
case.p9.list_sort.zone_pressed 1440 exit=0  
case.p9.list_sort.zone_pressed 393 exit=0  
case.p9.list_row_menu.delete_in_view 1440 exit=0  
case.p9.list_row_menu.delete_in_view 393 exit=0  
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
rig cases not passing:        0
```

### Captured run — 2026-09-28T05:15:03Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f3b2c1a2190dc69fb0f7b635f18ea147cc53d3

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:5> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:5> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:6> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:7> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:8> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:9> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:10> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:11> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:12> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:13> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:14> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:15> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:16> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
```

### Captured run — 2026-09-28T05:15:33Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f3b2c1a2190dc69fb0f7b635f18ea147cc53d3

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2927 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
 Test Files  323 passed (323)
      Tests  2927 passed (2927)
   Duration  34.35s (transform 15.34s, setup 32.35s, import 93.21s, tests 92.31s, environment 116.35s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  323 passed (323)
      Tests  2927 passed (2927)
✓ built in 4.59s
bundle gate passed (Desk JS 1334505 B; Desk CSS 323393 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T06:13:09Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/red_r2.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02d56179ea59ea3b7ff648065199d5232dd531fe

```text
=== product at f58cb5b0 (f58cb5b06)
✓ built in 4.62s
E                   AssertionError: {'cls': 'cm-line', 'ground': 'rgb(28,31,39)', 'host': 'codemirror', 'selected_text_vs_selection': 1.33, ...}
E                   assert 1.33 >= 4.5
E                   AssertionError: {'cls': 'cm-line', 'ground': 'rgb(28,31,39)', 'host': 'codemirror', 'selected_text_vs_selection': 1.33, ...}
E                   assert 1.33 >= 4.5
E               AssertionError: [{'bottom': 892, 'in_view': True, 'label': 'Desk menu', 'left': 1166, ...}, {'bottom': 1034, 'in_view': False, 'label': 'Launch submenu', 'left': 1208, ...}]
E               assert False
E                +  where False = all(<generator object TestDeskDebtsGlass.test_the_launch_submenu_keeps_itself_in_view.<locals>.<genexpr> at 0x110e3b6b0>)
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_launch_submenu_keeps_itself_in_view
3 failed, 2 passed in 53.18s
✓ built in 4.63s
=== product at origin/main (1afcc5769)
✓ built in 4.64s
E                   AssertionError: {'cls': '', 'ground': 'rgb(21,23,29)', 'host': 'input', 'selected_text_vs_selection': 14.21, ...}
E                   assert 1.14 >= 3.0
E                   AssertionError: {'cls': 'thread-composer-input', 'ground': 'rgb(21,23,29)', 'host': 'textarea', 'selected_text_vs_selection': 14.21, ...}
E                   assert 1.14 >= 3.0
E                   AssertionError: {'cls': '', 'ground': 'rgb(21,23,29)', 'host': 'input', 'selected_text_vs_selection': 14.21, ...}
E                   assert 1.14 >= 3.0
E               AssertionError: [{'bottom': 906, 'in_view': False, 'label': 'Desk menu', 'left': 1208, ...}, {'bottom': 1034, 'in_view': False, 'label': 'Launch submenu', 'left': 1208, ...}]
E               assert False
E                +  where False = all(<generator object TestDeskDebtsGlass.test_the_launch_submenu_keeps_itself_in_view.<locals>.<genexpr> at 0x112d132a0>)
E                   AssertionError: {'cls': 'thread-composer-input', 'ground': 'rgb(21,23,29)', 'host': 'textarea', 'selected_text_vs_selection': 14.21, ...}
E                   assert 1.14 >= 3.0
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_launch_submenu_keeps_itself_in_view
FAILED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]
5 failed in 55.48s
✓ built in 4.55s
 10 files changed, 252 insertions(+), 37 deletions(-)
```

### Captured run — 2026-09-28T06:18:29Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/green.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 02d56179ea59ea3b7ff648065199d5232dd531fe

```text
HEAD = f58cb5b06d743e4078b3a62fcd34a56c0820ef22; product diff vs origin/main:
 10 files changed, 252 insertions(+), 37 deletions(-)
✓ built in 4.62s
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_clock_a_case_uses_is_declared]
PASSED tests/unit/test_philo9_04_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_case_carries_one_trigger]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_face_cases_carry_both_ruled_viewports]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_predicate_is_a_kind_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_predicate_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_keeps_its_human_sentence]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_ui_action_is_one_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_precondition_check_compares_two_snapshots]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_precondition_check_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_check_asserts_the_result_the_trigger_must_produce]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_step_acts_on_a_root_placeholder]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_navigation_steps_carry_no_selector]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_desk_face_case_crosses_the_gate_first]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_captured_id_names_the_field_it_reads]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_launch_submenu_keeps_itself_in_view
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_the_sortable_table_has_no_raw_button
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_a_raw_button_mutation_turns_the_fence_red
PASSED tests/unit/test_philo9_04_atlas.py::test_every_named_case_is_in_the_atlas
PASSED tests/unit/test_philo9_04_atlas.py::test_every_case_runs_at_both_widths
PASSED tests/unit/test_philo9_04_atlas.py::test_face_checks_read_what_is_readable
PASSED tests/unit/test_philo9_04_atlas.py::test_the_menu_case_asks_44px_at_393_only
PASSED tests/unit/test_philo9_04_atlas.py::test_every_face_case_without_an_op_is_excluded_with_a_reason
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_state_id_resolves]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_reference_inside_the_atlas_resolves]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[393]
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
1 failed, 236 passed in 413.74s (0:06:53)
case.p9.list_status.shown 1440 exit=0  
case.p9.list_status.shown 393 exit=0  
case.p9.list_columns.in_view 1440 exit=0  
case.p9.list_columns.in_view 393 exit=0  
case.p9.list_sort.zone_pressed 1440 exit=0  
case.p9.list_sort.zone_pressed 393 exit=0  
case.p9.list_row_menu.delete_in_view 1440 exit=0  
case.p9.list_row_menu.delete_in_view 393 exit=0  
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
rig cases not passing:        0
```

### Captured run — 2026-09-28T06:27:52Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02d56179ea59ea3b7ff648065199d5232dd531fe

```text
HEAD = f58cb5b06d743e4078b3a62fcd34a56c0820ef22; product diff vs origin/main:
 10 files changed, 252 insertions(+), 37 deletions(-)
✓ built in 4.57s
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_clock_a_case_uses_is_declared]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_case_carries_one_trigger]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_face_cases_carry_both_ruled_viewports]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_predicate_is_a_kind_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_predicate_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_keeps_its_human_sentence]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_ui_action_is_one_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_precondition_check_compares_two_snapshots]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_precondition_check_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_check_asserts_the_result_the_trigger_must_produce]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_step_acts_on_a_root_placeholder]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_navigation_steps_carry_no_selector]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_desk_face_case_crosses_the_gate_first]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_captured_id_names_the_field_it_reads]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_launch_submenu_keeps_itself_in_view
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_the_sortable_table_has_no_raw_button
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_a_raw_button_mutation_turns_the_fence_red
PASSED tests/unit/test_philo9_04_atlas.py::test_every_named_case_is_in_the_atlas
PASSED tests/unit/test_philo9_04_atlas.py::test_every_case_runs_at_both_widths
PASSED tests/unit/test_philo9_04_atlas.py::test_face_checks_read_what_is_readable
PASSED tests/unit/test_philo9_04_atlas.py::test_the_menu_case_asks_44px_at_393_only
PASSED tests/unit/test_philo9_04_atlas.py::test_every_face_case_without_an_op_is_excluded_with_a_reason
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_state_id_resolves]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_reference_inside_the_atlas_resolves]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[393]
237 passed in 413.41s (0:06:53)
case.p9.list_status.shown 1440 exit=0  
case.p9.list_status.shown 393 exit=0  
case.p9.list_columns.in_view 1440 exit=0  
case.p9.list_columns.in_view 393 exit=0  
case.p9.list_sort.zone_pressed 1440 exit=0  
case.p9.list_sort.zone_pressed 393 exit=0  
case.p9.list_row_menu.delete_in_view 1440 exit=0  
case.p9.list_row_menu.delete_in_view 393 exit=0  
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
rig cases not passing:        0
```

### Captured run — 2026-09-28T06:37:07Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02d56179ea59ea3b7ff648065199d5232dd531fe

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2927 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
 Test Files  323 passed (323)
      Tests  2927 passed (2927)
   Duration  35.18s (transform 16.35s, setup 33.83s, import 97.11s, tests 95.46s, environment 117.39s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  323 passed (323)
      Tests  2927 passed (2927)
✓ built in 4.59s
bundle gate passed (Desk JS 1334646 B; Desk CSS 323393 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T06:40:25Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0af176f2640ed7af2861adf4005713110f353bc

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:5> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:5> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:6> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:7> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:8> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:9> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:10> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:11> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:12> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:13> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:14> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:15> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:16> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
```

### Captured run — 2026-09-28T09:24:35Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d70e976979b3af3ed6c87590a98de9d7f462ca5

```text
HEAD = 0d7e987baf9a0f47f1232e7d833963436cd9bbb6; product diff vs origin/main:
 10 files changed, 252 insertions(+), 37 deletions(-)
✓ built in 4.53s
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_clock_a_case_uses_is_declared]
PASSED tests/unit/test_philo9_04_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_case_carries_one_trigger]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_face_cases_carry_both_ruled_viewports]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_applicable_predicate_is_a_kind_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_predicate_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_keeps_its_human_sentence]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_ui_action_is_one_the_rig_implements]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_precondition_check_compares_two_snapshots]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_precondition_check_observes_a_selector_or_a_route]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_check_asserts_the_result_the_trigger_must_produce]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_no_step_acts_on_a_root_placeholder]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_navigation_steps_carry_no_selector]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_desk_face_case_crosses_the_gate_first]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_captured_id_names_the_field_it_reads]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_selection_is_visible[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_list_text_is_12px_and_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_status_says_shown[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_every_kept_column_is_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_launch_submenu_keeps_itself_in_view
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_the_sortable_table_has_no_raw_button
PASSED tests/unit/test_philo9_04_sort_button_fence.py::test_a_raw_button_mutation_turns_the_fence_red
PASSED tests/unit/test_philo9_04_atlas.py::test_every_named_case_is_in_the_atlas
PASSED tests/unit/test_philo9_04_atlas.py::test_every_case_runs_at_both_widths
PASSED tests/unit/test_philo9_04_atlas.py::test_face_checks_read_what_is_readable
PASSED tests/unit/test_philo9_04_atlas.py::test_the_menu_case_asks_44px_at_393_only
PASSED tests/unit/test_philo9_04_atlas.py::test_every_face_case_without_an_op_is_excluded_with_a_reason
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_state_id_resolves]
PASSED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_case_reference_inside_the_atlas_resolves]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_sort_headers_are_the_library_button[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_row_menu_keeps_itself_in_view[393]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[1440]
PASSED tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_open_row_menu_text_is_12px[393]
237 passed in 487.49s (0:08:07)
case.p9.list_status.shown 1440 exit=0  
case.p9.list_status.shown 393 exit=0  
case.p9.list_columns.in_view 1440 exit=0  
case.p9.list_columns.in_view 393 exit=0  
case.p9.list_sort.zone_pressed 1440 exit=0  
case.p9.list_sort.zone_pressed 393 exit=0  
case.p9.list_row_menu.delete_in_view 1440 exit=0  
case.p9.list_row_menu.delete_in_view 393 exit=0  
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
VERDICT: pass terminal=settled
NOTE: predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
VERDICT: pass terminal=settled
NOTE: predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: aria-pressed='true', wanted 'true'
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
VERDICT: pass terminal=settled
NOTE: predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
rig cases not passing:        0
```

### Captured run — 2026-09-28T09:37:16Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/ratchet.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b69f77b9a8414dde26d161519602d144a65d6de8

```text
...ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
59 passed in 3.07s
```
