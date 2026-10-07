# The Conductor canvas: the faces

**Status: RATIFIED by the owner 2026-10-06 ("Yes I approve"). Build what is drawn: default agent Claude Code; the launch sheet shows on every hand-off.** (UX-CANON A.2). Nothing in product code changes. Every change is in `harness/`.

Source: `docs/internal/CONDUCTOR.md` (the loop, "F faces", "The Control-mode mapping"). Method: the story-15 canvas (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/`). Its runner and C1's fences are imported unchanged (`harness/board.py`).

## What the boards are

- **The app:** the product on main `8f958800e`, served by vite with `harness/vite.config.mjs` against a real hub (`scripts/graph_walk.py serve`) on `HOME=/tmp/kcanvas-*`. Each width has its own hub and HOME. The run removes the HOME at the end. The owner's DB is never read.
- **The seed** (`harness/seed_db.py`): the story-15 seed (Project `Payments ledger cutover`, action item `Write the rollback runbook`, decision `Freeze the old ledger on Nov 5`, people), plus two agent sessions written by the product's own hook ingest: Claude Code waiting with a question, Codex working.
- **The seats** (`harness/seats.mjs`): 18 named anchors in 6 product files. A missing anchor stops the server (`CONDUCTOR CANVAS SEAT GUARD (k): 6 files, 6 seats, every anchor met`).
- **The proposal** (`harness/conductor.tsx`): library species only (Button, StateChip, EgressChip, SurfaceLedgerRow, SurfaceSection, SurfaceFooter, ChoiceCard, Disclosure, ProjectButton, Card, DeskWindowFrame). Stand-ins S1–S7 are named in its header. Nothing leaves the machine. No agent starts.

## The boards (`shots/<board>-1440.png`, `shots/<board>-393.png`)

| Board | Q | Proposes |
|---|---|---|
| K1a agents-found | Q1 | First run: an **Agents** card after Connections. Rows Claude Code, Codex: `INSTALLED`, `SIGNED IN`, `HOOKS` lamps; a tmux row; one verb **Install hooks** (`THIS DEVICE`) |
| K1b agents-done-receipt | Q1 | Done: the card folds to its receipt (`2 AGENTS READY`, `CLAUDE CODE · HOOKS IN`, `CODEX · HOOKS IN`, `TMUX 3.5A`) |
| K1c agents-not-installed | Q1 | Not installed: `CLAUDE NOT INSTALLED` + **Copy install** per agent; **Check again** |
| K2a object-menu | Q2 | **Hand to agent** in the Object menu (393: Go ▸ Object ▸) |
| K2b context-menu (1440) | Q2 | The same registry verb in the object context menu. 393: main has no row long press (a press opens the object), so the phone path is K2a |
| K2c command-deck | Q2 | The same verb in ⌘K |
| K2d door-row-verb | Q2 | **Hand to agent** on Door rows (action item, decision) |
| K2e room-row-verb | Q2 | **Hand to agent** on Room OPEN HERE rows (action item, issue) |
| K3a launch-sheet-claude | Q3 | The launch sheet: a docked desk window (the Ask AI posture). AGENT pick; BRIEF `6 SOURCES · 4.2 KB` with its source rows, `PEOPLE CUT · 3 NAMES`, `ACCEPTANCE · 3 CHECKS`, BRIEF TEXT; WHERE `~/dev/payments-ledger`, `NEW WORKTREE`, `hs/<item>`; `CONTROL · YOLO`; footer egress `API.ANTHROPIC.COM`; **Cancel** / **Launch** |
| K3b launch-sheet-codex | Q3 | Codex picked: the egress chip follows the pick (`API.OPENAI.COM`) |
| K3c control-mode-mapping | QC | `CONTROL · YOLO` unfolds the mapping well (the owner question, below) |
| K4a door-row-in-flight | Q4 | The Door row wears `CLAUDE CODE · WAITING` |
| K4b room-in-flight | Q4 | Room rows: `CLAUDE CODE · WAITING`, `CODEX · WORKING`, `PR #412 · OPEN` + `GITHUB.COM` **Open PR** |
| K4c agents-session-pin | Q4 | The AGENTS section lists every live session (K3's refetch) and names its item (`↳ Write the rollback runbook`, `↳ ISSUE #418`) |
| K5a needs-you-coder-row | Q5 | Needs you row R5: the question, `CLAUDE CODE · WAITING · 1 MIN`, the Project; **Speak answer** (the face's one primary), **Open**. The head counts it (`13 need you`) |
| K5b speak-answer-recording | Q5 | Speak answer opens the session window: the question, then an answer well in the body with the steer composer, its mic already recording |
| K5c enter-sends | Q5 | Enter sends; the composer empties; `sent` |
| K6 follow-through-receipt | Q6 | On merge the runbook leaves OPEN HERE (`2 open here`); the Room receipt line: `DONE · Write the rollback runbook · PR #413 MERGED · <time>`; its session leaves AGENTS |

## K7a: People MCP access (Conductor R7). **DRAFT, for the owner's ratification.** Not built in product code.

The owner, 2026-10-06: "the default should be on, for HOLDSPEAK_MCP_PEOPLE_ACCESS, and I guess there's an affordance to set it somewhere, right?"

| Board | Proposes |
|---|---|
| K7a people-access | Settings › **People** (a new module: main has no People module; stand-in S8). Group `MCP ACCESS`. Row **Access**: one `FilterTokens` strip `OFF` / `READ` / `WRITE`, with the current mode pressed (default `WRITE`). Row **Agents**: `AGENTS · READ` (`AGENTS · NONE` when off) and the source token: `DEFAULT`, `SETTING` or `ENV`. The Settings hub gets a **People** row with `MCP · WRITE` and `AGENTS · READ`. The strip reads and presses the REAL route `GET` and `PUT /api/settings/people-access` (an admitted owner-only kernel operation with a receipt). |

- **Shots:** `shots/K7a-people-access-1440.png` and `shots/K7a-people-access-393.png`.
- **Facts:** `shots/K7-facts.json`.
- **Fences:** `ALL FENCES HELD` at both widths.
  - The front window is `Settings · People`, with one blue title bar.
  - Contrast, clipping and text size: 0 findings.
  - This board's own controls: 0 targets under 44 px at 393.
  - At 393, main's Dock chip under `More` is recorded as main's, not as a failure.
- **Run:** `PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright .venv/bin/python docs/internal/conductor-canvas/harness/shoot_k7.py`. It seats only the Q7 anchors (`seats.mjs` `K7`, `CANVAS_SEATS=k7`). The K boards' seats were drawn on `8f958800e`, and their faces are built since then.
- **Owner questions:**
  1. Is a new **People** module in Settings correct, or should the control live in the People window?
  2. When the env var overrides the setting, should the strip be disabled under the `ENV` token? (This state is not drawn.)

## Fence results (`shots/facts.json`, run of 2026-10-06 on `8f958800e`: `ALL FENCES HELD`, exit 0)

| Measure | Value |
|---|---|
| Boards | 35 (18 at 1440, 17 at 393; K2b at 393 recorded as not drawn) |
| Fence failures / browser errors | 0 / 0 |
| This canvas's targets under 44 × 44 at 393 | 0 |
| Window content at 393 | 704 px on every windowed board |
| Windowless faces (first run, Floor list, ⌘K) | 0 blue title bars (law: none) |
| Recorded as main's, not failed | the Dock chip under `More` at 393 (every 393 board); ⌘K at 1440, the Floor list's selected row reads 3.5:1; ⌘K at 393, the Floor list strip under the deck; ChoiceCard's hidden radio (1 px, the card owns the tap); the session window at 393 (main's `minW 420` and its footer: `Keep as note` past the edge), the same on a control run with no answer well (`_main_session_window_393`) |

## Owner questions

1. **QC, the Control-mode mapping** (K3c). Proposed default, as drawn: `SECURE` LAUNCH · YOU PRESS LAUNCH, BASH · EVERY CALL WAITS, QUESTION · TO NEEDS YOU. `NORMAL` LAUNCH · ON THE VERB, BASH · READ · TEST · GIT READ PASS, QUESTION · DRAFT · YOU SEND. `YOLO` LAUNCH · ON THE VERB, BASH · PASS IN ITS WORKTREE, QUESTION · ROUTINE ANSWERED, REAL · TO NEEDS YOU. Rule it, or change a cell.
2. **The default agent.** The sheet opens on Claude Code (drawn). (a) Claude Code; (b) Codex; (c) the last one picked.
3. **Hand to agent in YOLO.** (a) the sheet every time (drawn); (b) YOLO launches straight with the default agent, and the sheet only in Secure and Normal. Recommended: (b), with the launch receipt on the row (Tenet 3).

## What main already gives (measured here)

- The hook ingest, `/api/coders/sessions` (both sessions, state, question), the session window and its steer composer, the Room OPEN HERE row, the Door row grammar, the verb registry (one verb reaches the Object menu, the context menu and ⌘K with no other edit), Go ▸ Object ▸ at 393.
- Dark on main: the Agents window says `No sessions` while `/api/coders/sessions` holds two; the arrival AGENTS section reads `/api/coders/status`, which lists none of them (count 0); the session window shows the question only when `awaiting_response` is set, and a `Notification` hook does not set it; the steer composer is in the footer, and only when the pane is armed or the posture authorizes it (`SessionPullout.tsx`). The cause of the Agents window's empty list is not verified.

## Reproduce

```bash
# from the worktree root; both widths, each on its own hub and HOME (removed at the end)
uv sync --python 3.13 --extra test; (cd web && npm ci)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python docs/internal/conductor-canvas/harness/shoot.py
```

`ONLY_WIDTH=393` limits the run. `harness/dev.py proposal k <statefile>` holds one stack up for iteration.
