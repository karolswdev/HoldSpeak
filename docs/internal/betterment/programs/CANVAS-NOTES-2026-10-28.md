# Programs canvas notes (2026-10-28)

Canvas: `canvases/programs-2026-10-28.html` (one self-contained page; the
sprites are inlined from the generator's own `render()`). Shots:
`canvases/shots/` (`canvas-1440.png` is the whole page at a 1440 viewport;
`1440-<section>.png` per section; `393-programs.png`,
`393-program-running.png`, `393-program-done.png` are the phones at their
real 393 × 852). Design: `PROGRAMS-DESIGN-2026-10-28.md` §9, §9b and "Runs on".
The owner's "go with suggestions" (2026-10-27) pre-approves the recommended
direction; he judges it live on his desk.

## The recommendation: C, the ledger

The board's open question was how one step's row reads. Three directions were
drawn with the same Running data (The hub stops stalling, six steps, two wait
on him).

- **C, the ledger (recommended).** One 32 px ListView row per step: number,
  title (with "after 4, 5" in muted words), the six station dots and one state
  word, the agent's sprite and name (with the engine for pi), the time in this
  state, the last checkpoint, Open. The words form of the track is drawn once,
  in the Gate fold of the selected step.
- **A, the track is the row.** The six stations as words on every row. 58 px a
  step.
- **B, the card.** A card per step, three a line, the track as the footer.
  93 px a card. It is a card inside a window, and the order zig-zags.

The reason, in his terms: a Senior Architect, tired on a Tuesday, twenty
steps, wants the whole program on one screen, the red and the ember found in
one look, and words only where he looks. The canvas proves it: twenty C rows,
a two-item well and the status bar fit a full-height window (1000 × 864 under
the menu bar) with no scroll (scroll overflow measured 0 px). A would need
1 160 px for the rows alone.

## Measurements (read from the page with Playwright, 1440 viewport)

| Part | Value |
|---|---|
| Toolbar | 36 px (`--wb-toolbar-h`) |
| Status bar | 24 px (the place-line bar of §9b: 26 px, its ghost Buttons are 20 px) |
| Programs ListView row | 32 px; column head 26 px; band caption 26 px |
| Board row, C | 32 px |
| Board row, A | 58 px |
| Step card, B | 93 px |
| Your turn well | caption 26 px; one item 32 px (verbs `sm` 24 px) |
| Station track, dots form | 98 px (six 8 px dots, the lit one 10 px, five 10 px links); its column with the word: 262 px at 1440 |
| Station track, words form | 736 px at 1440 (Gate fold and the three moments) |
| At 393 | the track is a StateChip; a step row is 60 px (two lines); every plated verb 44 px high (measured: Merge 77 × 44, Not yet 82 × 44, Fix now 86 × 44, Later 68 × 44, Skip 63 × 44); toolbar verbs 44 px |
| Breath | the lit station's ring 2 → 5 px and back, 2.4 s ease-in-out (the kit's `kit-lamp-live`); a box-shadow; none under reduced motion; nothing moves on hover |

Type steps (UX-CANON §C, as the window grammar of 2026-10-24 amends them):
title bar 13.5/600; primary (a row's name) 13/600, 14/600 at 393; body 13;
metadata 12 sans muted in sentence case (not mono: mono only for code, ids and
the check command); the 12 px floor holds everywhere. No display step inside
the Program window (it is a list window); the empty state's line is 15/600.

## The kit pieces each part is made of

PG-FACES builds only from these. A piece marked NEW is added to the kit
(`web/src/desk/surface/`, documented in `contract.md`) before use.

| Part | Kit pieces |
|---|---|
| Both windows | the window frame and title chip (20 px sprite), `Toolbar`, `ToolbarFold`, `StatusBar` (items with `lamp`, `live`), library `Button` (primary, ghost, dense) |
| Programs list | `ListView` (column head, 32 px rows), band captions as ListView groups, `StateChip` (active = Your turn, working = Running, idle = Drafting / Parked, success = Done), `countWords` for "2 of 6 steps", the "Done in 1 h 12" word as ok ink |
| Templates fold | `ToolbarFold` with a menu (`DeskMenuList` species, `--depth-menu`), one row per template with its 20 px sprite and one line |
| Empty state | `SurfaceState` empty with the 64 px program sprite, one line, one primary `Button` |
| Your turn well | `SurfaceWell` with the ember rule (the AskWell family), `DotWord` tone ask, `Button` per verb; Answer opens the lane's `AskWell` |
| Board (C) | `ListView` rows; **NEW `StationTrack`** (`form="dots"` for the row, `form="words"` for the Gate fold; stations BRIEF · WORK · CHECK · REVIEW · PR · MERGE; states passed / current / ahead / skip; a person station draws an `Avatar`); `DotWord` for the state word (through `stateWords`); the agent's 20 px sprite (`spriteUrl("coder", …, 20)`) |
| Race | the same rows, indented contender rows (a ListView child row with the elbow rule) |
| Gate fold | `FoldGadget`, `StationTrack form="words"`, `SurfaceCode` for the command, six `DotWord`s, `Button` Open log (a Note pullout) |
| Checkpoints fold | `FoldGadget`, `SurfaceLedger` rows: by (agent sprite, the program sprite as the engine's mark, `Avatar` for him), the line, the time |
| Drafting | `StringGadget` (with its mic) for a step's title, `PadGadget` (with its mic) for the goal and the brief, `Token`s for the files it owns, `CycleGadget` for Runs on, effort and after, `CheckGadget` for When idle, `EditInPlace` for the title in the title bar |
| Runs on picker | a menu in the `DeskMenuList` species (or `Popover`): Claude Code, Codex, then "pi on an engine" with the Engines window's own rows (cartridge sprite, the five words of `features/runson/stateWord.ts`: Ready, Limited, Broken, Waiting, Off), a `CheckGadget` When idle at its foot, Engines… opens the Engines window |
| When idle | `CheckGadget` (`variant="token"` in the toolbar; the box form on a step row and in the picker). The sliding toggle is dead (HS-111-01) |
| Held step | `DotWord` idle with the hollow dot: "Ready · waiting for qwen" (a new word through `stateWords`) |
| 393 | the same `ListView` rows in two lines with `StateChip`; `ToolbarFold` folds to More ▾; plated Buttons own 44 × 44 |
| Seams | Needs you: `NeedsRow` (group = the Program's title, due word "Now"); Agents: the Conductor row with a step line (a ghost `Button` link to the Program); Today: one Since morning line; Dock: the Agents tile's `IconLamp` (ask = ember, breathing) |
| Ecosystem §9b | the Note's place line (`StatusBar` items as ghost dense `Button`s with a 14 px sprite: Project ▸ HoldSpeak · From the meeting of Tue 28 Oct · For Alice); a `Token` "No project" that files it (`zone_file`); the Room's Programs fold (`FoldGadget` + `ListView` rows: `StateChip`, "4 of 6", the your-turn `DotWord` only when not zero); the person's room line under Commitments; the 1:1 brief's "To show them" and "To ask"; the Needs you row "Ask Alice to review PR #1591" with Send… (the prepared send); the Note's `ToolbarFold` verb "Run as a program" |
| The program sprite | `WORLD["program"]` in `web/scripts/gen-icons-d.py` (the parts are printed on the canvas), exported at 64, 48, 32 and 20 by `gen-illustrated-icons.py` |

## Words used on the faces (for `stateWords` and the copy guard)

Step: Planned, Ready, Ready · waiting for qwen, Working, Asks you, Checking,
Check failed · log, In review, Findings, Waits for Alice, PR open, Merge?,
Merged #n, Parked, Failed, Race of 2. Program: Drafting, Running, Your turn,
Done, Done in 1 h 12, Parked. Gate: Checked · green, Check failed, the six
section names. Verbs: New program, Templates, Start, Park, Resume, Add step,
Race, Runs on: <x> ▾, When idle, Control: Owner ▾, Merge, Not yet, Fix now,
Later, Skip, Answer, Open, Open log, Open note, Send…, Run as a program.

## Small choices the canvas made (say if another is wanted)

- The Done window's toolbar shows **Open note** (the handover note) in place
  of Start / Park / Resume, which have nothing to do on a Done program.
- The empty state's words are the design's, cut to two plain sentences: "A
  program is a goal cut into steps. An agent does each step."
- A human reviewer's station draws her portrait in place of the dot, and the
  row's word is "Waits for Alice".
- Band captions in the Programs list are sentence case sans 12 (the window
  grammar), not mono caps.

## What the canvas could not establish

- Whether three breathing stations at once read as busy at the board's
  density; if they do, only the selected step breathes.
- Tokens and minutes from the harness: only minutes are drawn.
- The desk floor is CSS, not a recorded hub shot; the windows, menu bar and
  dock use the kit's values. No product guard reads `docs/` canvases
  (`scripts/ux_canon_scan.py` scans `web/src` only), so the copy here is
  proven by reading, not by a guard.
