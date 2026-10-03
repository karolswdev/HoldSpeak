# PHILO-13-15 (C5) canvas: Send to ▸ from any document window

**Status: DRAFT, for Astra's check and then the owner's ruling. NOT RATIFIED** (UX-CANON A.2: the canvas comes before the build). Nothing here is built in product code. Every change lives under `harness/`.

Sources: the story (`../../story-15-c5-send-to-from-any-document-window.md`), Phase 12's design (`../../../phase-12-send-from-the-floor/design/floor-send.md` §2, §3, §6, §7) and its canvases F–J (`../../../phase-12-send-from-the-floor/assets/story-02-canvas/`), the ratified C1 look (`../../design/workbench-look.md`), fork 5 (the default stands: the title-bar menu and the Object menu, one composition).

## What the boards are

- **The app:** the PRODUCT app on main `76c361537`. The C1 frame and Chair and the C2 window menu are built there. Vite serves it with `harness/vite.config.mjs` against a REAL hub (`scripts/graph_walk.py serve`) on `HOME=tempfile.mkdtemp(prefix="p13c57-", dir="/tmp")`. The run removes the HOME when it ends. Each width runs on its own hub and HOME.
- **The seed:** C1's seed (`harness/seed_db.py`), plus `Vendor call` (a meeting with no summary) and `Cutover requirements` (an accepted artifact). The real FILE destination `Team updates` is made through the routes.
- **The seats** (`harness/seats-c5.mjs`, plus `harness/seats-common.mjs` for the `~` path): one named hook per anchor in each product file. If a file or an anchor is missing, the server stops (the seat guard; its line is in `shots/facts.json`, `_seat_guard_<width>`).
- **The proposal** (`harness/c5.tsx`, P1–P7 in its header) and **the stand-ins** (S1–S3 in the same header): `Slack #leads` and `PAY-118` are stand-in destinations. Their preview is the real hub's render. Their Send is answered in the shim with the outcome the board names. Nothing leaves the machine. The `Team updates` send is a REAL send into the scratch HOME.
- **The fences:** C1's ratified fence code, imported unchanged (`harness/board.py`): in-place contrast, clipped text, sideways strips, rendered overlap, 44 × 44 targets at 393. There are also new fences: one blue title bar, the 12 px floor, no modal, no scratch path, and for each arrival the window name, the picked row, the preview's first field and Send each WHOLE on screen. Every 393 press is a touch tap (CDP), and every window menu at 393 is a touch long press.
- **The 393 target fence is scoped to C5's own surfaces** (the menus and the SEND wells). Small targets elsewhere are recorded as `inherited_under_44` in `facts.json`. C7 (story 17) draws them fixed.

## The boards (`shots/<board>-1440.png`, `shots/<board>-393.png`)

| Board | Shows | Acceptance line it answers |
|---|---|---|
| C5-1 window-menu-send-to | the meeting window's right-button menu (393: long press) leads with `Send to ▸`; its rows are the saved destinations `<name> · <CHANNEL>` | 2 (gesture 1–2 of 3); 3 (one composition, the title-bar menu) |
| C5-2 object-menu-send-to | the menu bar's Object menu (393: the Object group inside Go) gives the same `Send to ▸` for the front window (the artifact) | 3 (one composition, the Object menu) |
| C5-3 picked-preview-in-view | after the pick, the window's SEND well shows the picked row, its preview and Send in view; the hub holds **0** send rows | 2 (gesture 3; the preview arrives in view); 4 (zero rows until Send) |
| C5-13 second-pick-in-place | a second pick changes the open well in place (no remount) | "Rendered transitions": a second pick |
| C5-14 digest-keeps-destination | Summary → Digest keeps the picked destination | "Rendered transitions": Summary → Digest |
| C5-4 sending | in flight: `SENDING` (stand-in) | the send states: in flight |
| C5-5 sent-file | settled: a REAL send to `Team updates`, `SAVED` + the file; the hub holds 1 row | the send states: settled; "real-send leg" (FILE) |
| C5-6 failed | `FAILED · CONNECTION FAILED · NOTHING SENT` (decision window, stand-in Jira) | the send states: failed; the decision kind |
| C5-7 unknown | `UNKNOWN · TIMED OUT` + Check (decision window, stand-in Slack) | the send states: unknown |
| C5-8 withheld-no-summary | a meeting with no summary: the window menu has no `Send to` | 3 (withheld); "Refusals" (known no summary) |
| C5-9 no-destination-add | no saved destination: `Send to ▸ Add destination` | 3 (`Add destination` with none) |
| C5-10a room-checking | the Room while the latest-update read is pending: `Send to · CHECKING` (not a refusal) | "Refusals": `pending` never refuses |
| C5-10b room-cant-check | the read failed: `Send to · CAN'T CHECK`; the rows stay | Scope "The reads": a failed read shows `CAN'T CHECK` |
| C5-11 room-update-picked | the Room's latest published update in the Update posture, its well picked, in view, clear of the sticky Back strip | the project kind; Scope "The arrival" |
| C5-12 artifact-window-well | the artifact window's own SEND well on `artifact:<id>`, picked and in view; its Copy, Dictate and lineage verbs are library Buttons (0 raw `<button>`) | "Artifact": picked; no raw `<button>` |
| C5-15 brief-window-picked | the Chair's Brief window: `Send to ▸` picks into its own well | the brief kind |
| C5-16a offline-menu | the hub does not answer: `Send to · OFFLINE`; the rows are the last read | the send states: offline |
| C5-16b offline-well | the pick still opens the well, which says what it cannot read (`CANNOT READ SENDS`, `NO PREVIEW · NO ANSWER` + Retry) | the send states: offline |

Not drawn, on purpose (Tenet 1): the Room open on another update switching to the linked one (Phase 12 G9), and Intelligence → BRIEF keeping the handed brief id (I2/I3). They look the same as C5-11 and C5-15. Only the mechanism differs, and it is fenced in the build (acceptance "Rendered transitions"). The same-second tie is a backend fence (handoff H-C5).

## Measurements

Read from `shots/facts.json` (run of 2026-10-02 on main `76c361537`; `ALL FENCES HELD`, exit 0):

| Measure | Value |
|---|---|
| Boards | 36 (18 at 1440, 18 at 393), each width on its own hub and HOME |
| Seat guard (both widths) | `PHILO-13-15/17 SEAT GUARD (c5): 7 files, 8 seats, every anchor met` |
| Fence failures / browser errors | 0 / 0 |
| Boards with exactly one blue title bar; the intended window in front, on the glass | 36 of 36 |
| Texts under 4.5:1 (3:1 large), in place / under 12 px / clipped / sideways strips / rendered overlaps | 0 / 0 / 0 / 0 / 0 |
| Arrival boards with the window name, the picked row, the preview's first field and Send each whole on screen, with no rig scroll | 6 of 6 per width (C5-3, C5-11 (the Room's name is in its wings row: the row, the field and Send), C5-12, C5-13, C5-14, C5-15); C5-4–7 check the name and the open row |
| Hub send rows before / after Send (C5-3 / C5-5) | 0 / 1, at both widths |
| Raw `<button>` in the artifact window | 0 (main: three raw `<button>` sites in `web/src/desk/pullouts/ArtifactPullout.tsx`) |
| 393: C5's own targets under 44 × 44 / the front window's content | 0 / 704 px |
| 393: inherited targets under 44 × 44 (recorded, not C5's; C7 Q5 draws them fixed) | the meeting window's `Dictate about this`, `Record follow-up` (27 px tall); the Room's `Assign to …` and `Inspect …` (27 px); `desk-chip quiet` Buttons (27 px) |
| Overlap waivers used | `sticky` only (Room content under its Back strip) |

## Decisions for the owner (each with the recommended default)

1. **Where `Send to ▸` sits in the window menu.** (a) first, its own group above Iconify; (b) after Close window. **Recommended: (a)**, because it is the 3-gesture path and the menu's only document verb.
2. **Offline.** (a) `Send to · OFFLINE` keeps the last-read rows, and a pick opens the well, which names what it cannot read; (b) withhold `Send to` while the hub does not answer. **Recommended: (a)**, the same rule as `CAN'T CHECK`: an unknown never withholds, and the well tells the truth.
3. **The 393 Object menu.** On main the Object verbs ride flat inside Go, and `Send to ▸` leads that group (C5-2-393). C7's canvas proposes `Go ▸ Object ▸` (story 17, board C7-5b). **Recommended: take C7's grouping**. C5 then needs no Go-specific placement.
4. **The SENDING chip colour.** On main its word reads 4.26:1 (`--accent`), and the canvas draws it on `--accent-text` (P7; this also changes the PREPARED chip, the same species). **Recommended: yes**. The build edits `surface/patterns/state-chip.css`.

## Limits (what the boards are not)

- The stand-in destinations' SEND answers come from the shim. Only `Team updates` is a real send. The real-send legs for Slack, Jira, GitHub, Confluence and email are the story's acceptance, not this canvas.
- The menu reads its destinations and facts in the shim. The rig starts the read before it opens the menu. An open menu that re-renders on a read transition is a build fence (Phase 12 story 03 notes).
- The meeting form picker is a native `<select>` (CycleGadget). C5-14 drives it with `select_option` at both widths. That proves the Digest state, not the gesture.
- The Meetings window's document is read from its open record's well (stand-in S3).
- Not verified: the owner's browser, a real touch device (393 is a touch-enabled headless viewport).

## Reproduce

```bash
# from the worktree root; both widths, each on its own hub and HOME (removed when it ends)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/harness/shoot.py
```

`harness/dev.py proposal c5 <statefile>` holds one stack up for iteration (`STACK_STATE=<statefile> NO_WARMUP=1`). It is not part of the proof.
