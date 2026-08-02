# Evidence - HS-111-10

- **Story:** HS-111-10 - The refinement walk
- **Status:** done
- **Date:** 2026-08-02

## The walk

Every program and system surface opened on the LIVE hub (:8765) via
headless Playwright/puppeteer at 1440x900 and 393x852 (DPR 2), 79+
shots in `.tmp/hs-111-10-walk/`, the ~18-shot exhibit set in
[assets/hs-111-10/](./assets/hs-111-10/). Read-only: nothing decided,
steered, or armed; the one allowed mutation was a floor `NEW > New
Note` create (photographed) binned seconds later via
`DELETE /api/notes/:id` (200).

Surfaces walked, both viewports: the desk floor (spatial icons + the
ledger list view + a zone dive), Speak (face, Journal, Blocks, gear
door), Meetings (ledger, detail, Artifacts, Record bay, door, Live
resting), Agents (crew board, persona record — no live coder sessions
existed at walk time, so the session pullout could not be walked
honestly; the xterm PaneWell interior is proven on the DELIVERY
terminal, the same seam by construction per HS-111-06/11), Settings
(drawer face + Appearance/Transcription/Models/Delivery modules),
Delivery (board via the ⌘K deck, a REAL tmux pane in the xterm
terminal, story dossier), the Process window (zeroed instrument),
Project Memory, Ask (composer + grounding rack + a real send), one
RAW well open, and the error legs (bogus project window; palette miss
band). System chrome: Desk/Object/Go dropdowns OVER a window, the
floor right-click with the NEW> submenu open, an object right-click,
the palette with query+selection and the miss leg, the shortcut
sheet, the trust window, the shade, and the Desk-memory drawer face.

## Violations found → fixed in this story

1. **The Speak footer receipt bar was translucent** — door/Blocks
   content bled THROUGH the sticky bar (`--desk-window-well` is
   rgba). Fixed: the well tint now rides an opaque surface layer
   (`desk.css` `.speak-status`). Re-proven live (desktop-06: the bar
   covers scrolled content, and honestly shows `1 WARNING | Review`).
2. **Meetings detail hard-clipped a fact mid-token** at 1440
   (`TRANSCRIPT RETAINED · LAST DU…`). Fixed: `.gadget-fact` wraps
   instead of nowrap-clipping at the pane edge (`gadgets.css`).
3. **`← ALL` stamped over the census header** in the list view's zone
   dive at 393 — `.desk-surface` kept its `position: fixed` chrome
   placement inside the ledger head. Fixed: static inside
   `.desk-list-face`. Re-proven (mobile-44).
4. **The chrome-input mic sweep (the HS-111-08 named debt (b))** —
   all five naked chrome text wells are now kit species with the
   speak-to-fill mic: AttentionDrawer search → StringGadget,
   AttentionDrawer kind select → CycleGadget, InfoWindow rename →
   StringGadget (commit on focus-leaving-the-well so the mic press
   never commits-and-unmounts), SystemShade deny reason →
   StringGadget, the ⌘K palette query → StringGadget (kit gained an
   `inputRef` passthrough). WorldStage zone rename already carried a
   mic; its commit-on-blur got the same relatedTarget guard (pressing
   the mic used to commit-and-unmount mid-utterance). Off-kit radii
   died with the swaps (`--radius-sm` on `.desk-gate-reason` /
   `.info-name-input` deleted). Proven live: desktop-38 (palette mic),
   desktop-43/mobile-43 (drawer face).

## Chartered (named, not built — the walk must not balloon)

- **DeliveryListSection** (`desk/components/DeliveryListSection.tsx`)
  — the HS-94-08 semantic delivery table rendered under the List view
  and in CompanionCore still speaks the old dialect (Inter table,
  prose details). Refit to SurfaceLedger. Found BY the walk
  (mobile-44).
- **Mobile spatial floor label collisions** — at 393 the forced
  `?view=spatial` floor overlaps icon labels (the default arrival at
  ≤720 is the list view, so no user lands there without asking).
  Needs label culling/scale, not a CSS nit.
- **SystemShade row grammar** — sentence-case event rows
  ("Meeting saved · this_machine"); dialect refinement, pre-phase.
- **TrustWindow lede prose** — two sentences ride above the boundary
  facts; a copy-token pass, held for the sitting alongside the
  no-privacy-novels rule.
- **PM timeline wire nit** — Project Memory shows the in-flow
  `Not Found · Try again` leg for a REAL project with zero meetings
  (desktop-26); the face is honest, the wire answer is questionable.
- Carried from 07/08 unchanged: palette deep-settings + meeting
  content search, InlineEditor's native cluster (header-documented),
  composer→PadGadget migrations (all composers DO carry mics), the
  config-hermeticity gap (see verify below), multi-select.

## Honest gaps (not faked)

- **No printed Ask turn**: .43 is still down; the walk shot the full
  refusal leg (desktop-31: `✕ HUB> No language model on this hub…` as
  an in-flow error turn with every control still operable). The
  phase still owes the owner the printed-turn-with-receipt shot when
  a model returns.
- **No live coder session** existed, so the SessionPullout +
  steering face ride on their HS-111-04/11 evidence; the xterm well
  itself is proven here on the delivery terminal (desktop-23, a real
  tmux pane, FIND + mic, KEYS TransportRow, read-only).
- The integration suite runs with the ONE documented deselect
  (`test_web_aftercare_file_issue::test_filed_proposal_never_executes_until_approved_and_enabled`)
  — re-checked first: it still fails under the live hub's YOLO
  posture (the chartered hermeticity gap). One live-hub SIGKILL test
  flaked once under load and passed in isolation and on the clean
  recapture below.

## Census (full grep output in the first capture)

- `backdrop-filter`: 26 textual hits, **0 live blurs** — 19 explicit
  `none`, 7 `var(--desk-window-blur|--desk-aerogel-blur)` which
  tokens.css pins to `none` (HS-110-01).
- `border-left` violations: **0**.
- Emoji-as-icons in shipped tsx: **0** rendered pictographs (the two
  🤖 hits are the legacy-avatar filter guard + comment; glyph tokens
  ✕/✓/⚠/⚙/✦/⊘ are the kit's own grammar).
- Retired species (`Switch/Tabs/StatusPill/InlineMessage/Dialog/
  ConfirmAction/Skeleton/EmptyState/ChoiceCard/Disclosure`): **0**
  JSX usages outside tests.
- `InlineMessage`: **0** usages; 4 comment mentions only
  (Signal.tsx header, Signal.test.tsx, ComponentsCore, pageSupport).
- Naked `input/select/textarea` outside kit internals: pages/cores
  **4** (HistoryCore file-drop well; LiveCore preview textarea inside
  the gadget-string well with mic; ProjectMemory ask/search — both
  mic'd, chartered composer→PadGadget), desk components: InlineEditor
  cluster (chartered), the mic'd composers (AskPanel, PersonaChat,
  Pullout, SessionPullout, PrReceipts action pads,
  DeliveryTerminalWindow steer pad), InfoWindow tooltype select,
  WorldStage zone rename (mic'd). Every remaining site is either
  chartered by name above or already carries the speak-to-fill mic.

## Proof

### Captured run — 2026-08-02T10:45:54Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/f3f00f5d-a581-4e3f-aea5-6454420ea181/scratchpad/census10.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 80d6808c66f343e6c1767bc8b56298682fb3f4e7

```text
== 1. backdrop-filter in css/tsx ==
./desk/desk.css:3883:  backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4043:  backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4116:  backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4541:  backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4542:  -webkit-backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4796:  backdrop-filter: var(--desk-window-blur);
./desk/desk.css:4797:  -webkit-backdrop-filter: var(--desk-window-blur);
./desk/surface/gadgets.css:5:   backdrop-filter. Stories 02-08 consume these. */
./desk/surface/surface.css:594:   backdrop-filter removed; the receipt is an opaque beveled inset. */
live-blur declarations (var refs): 7
258:  --desk-window-blur: none; /* HS-110-01: no backdrop-filter — opaque surfaces */
300:  --desk-aerogel-blur: none; /* HS-110-01: no backdrop-filter — opaque receipt */
TOTAL textual hits: 26 (every declaration is none or a var resolving to none)

== 2. border-left violations ==
NONE

== 3. emoji pictographs in shipped tsx/ts (U+1F300+) ==
NONE rendered

== 4. retired species JSX usage (Switch/Tabs/StatusPill/InlineMessage/Dialog/ConfirmAction/Skeleton/EmptyState/ChoiceCard/Disclosure) ==
ZERO

== 5. InlineMessage remaining ==
usages: 0
mentions (comments only):
./components/signal/Signal.test.tsx
./components/signal/Signal.tsx
./pages/cores/ComponentsCore.tsx
./pages/pageSupport.tsx

== 6. naked input/select/textarea outside kit species ==
-- pages/cores --
pages/cores/HistoryCore.tsx:253:        <input
pages/cores/LiveCore.tsx:279:              <textarea
pages/cores/ProjectMemoryCore.tsx:262:          <textarea
pages/cores/ProjectMemoryCore.tsx:648:          <input
-- desk/components + desk/gl --
desk/components/AskPanel.tsx:467:                <textarea
desk/components/DeliveryTerminalWindow.tsx:104:        <textarea
desk/components/InfoWindow.tsx:195:                  <select
desk/components/InlineEditor.tsx:151:            <input
desk/components/InlineEditor.tsx:156:            <textarea
desk/components/InlineEditor.tsx:162:            <input
desk/components/InlineEditor.tsx:170:          <input
desk/components/InlineEditor.tsx:178:            <input
desk/components/InlineEditor.tsx:203:                      <input
desk/components/InlineEditor.tsx:212:                      <input
desk/components/InlineEditor.tsx:221:                      <input
desk/components/InlineEditor.tsx:275:              <input
desk/components/InlineEditor.tsx:282:              <input
desk/components/InlineEditor.tsx:288:            <input
desk/components/InlineEditor.tsx:293:            <textarea
desk/components/InlineEditor.tsx:303:                <textarea
desk/components/InlineEditor.tsx:311:                <input
desk/components/InlineEditor.tsx:316:                <select
desk/components/InlineEditor.tsx:327:                <select
desk/components/PersonaChat.tsx:327:            <input
desk/components/PrReceiptsSection.tsx:119:                                <textarea id={`pr-action-${key}`} value={w.text} onChange={(event) => patch(key, { text: event.target.value })} rows={w.action === "comment" ? 7 : 3} />
desk/components/Pullout.tsx:489:                  <textarea
desk/components/Pullout.tsx:650:                      <textarea
desk/components/Pullout.tsx:740:                <input
desk/components/SessionPullout.tsx:454:        <textarea
desk/components/SessionPullout.tsx:607:            <input
desk/gl/WorldStage.tsx:362:      <input
-- kit internals (input inside gadgets/Signal, by construction) --
desk/surface/gadgets.tsx
desk/surface/Surface.tsx
components/signal/Signal.tsx
```

### Captured run — 2026-08-02T10:46:10Z

- **Command:** `bash -lc uv run pytest -q tests/unit 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 80d6808c66f343e6c1767bc8b56298682fb3f4e7

```text
........................................................................ [ 99%]
.........                                                                [100%]
3465 passed in 161.71s (0:02:41)
```

### Captured run — 2026-08-02T10:49:35Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak/web && npm run check 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 80d6808c66f343e6c1767bc8b56298682fb3f4e7

```text

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.77s
```

### Captured run — 2026-08-02T10:50:10Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak && uv run pytest -q tests/integration --deselect tests/integration/test_web_aftercare_file_issue.py::test_filed_proposal_never_executes_until_approved_and_enabled 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 80d6808c66f343e6c1767bc8b56298682fb3f4e7

```text
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
FAILED tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id
1 failed, 762 passed, 3 skipped, 1 deselected in 297.57s (0:04:57)
```

### Captured run — 2026-08-02T10:55:55Z

- **Command:** `bash -c uv run pytest -q tests/integration --deselect tests/integration/test_web_aftercare_file_issue.py::test_filed_proposal_never_executes_until_approved_and_enabled 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 80d6808c66f343e6c1767bc8b56298682fb3f4e7

```text
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
763 passed, 3 skipped, 1 deselected in 285.86s (0:04:45)
```
