# PHILO-6-03 · Toast that does not cover

Last updated: 2026-09-24 night — ratified placement built and verified; PR only, calling Muad’Dib counsel before merge.

The actual Muad'Dib counsel-on-built check is in the
phase roadmap [`checks/lane-b-built-muaddib.md`](../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/lane-b-built-muaddib.md);
the round-two canvas changes address those conditions.
The earlier canvas record was an Astra-invoked `claude -p` check at
`checks/story-03-canvas-zero-astra-invoked-claude.md`, not Muad'Dib's check of
record. The earlier parent reproduction is retained in `parent-shots/` and
`canvas-dw-final-validation.md`. Round two independently reproduces all 14
boards/probes in `../round-two/canvas/`; `../round-two/dw-validation.md` records
the successful capture.

**RATIFIED 2026-09-24 — BUILD EVIDENCE IN `placement-proof/`**

The owner accepted the Arrival slot, off-Arrival surface slots, and phone auto-scroll before build (`38cf713a`, merged as `d8f608c8`). The exact ChairHome patch is committed as `d1e355f2`; lane A reconciles it. The sections below retain the canvas-stage measurements and proposal history. They do not describe the current build status. The [placement lane report](placement-proof/lane-report.md) records six actual surface walks, Dismiss at both widths, raw red/green proof and the remaining limits.

This artifact records a placement proposal for the existing aftercare card.
At the canvas stage it did not apply product placement or edit `ChairHome.tsx`. The zero-token
render fix is a separate, focused implementation in
`web/src/components/AmbientLayer.tsx`.

The card keeps these exact strings and existing component species:

```text
Meeting ready
Architecture review
3 open
Open proposals
Dismiss
```

The fixture has honest nonzero data (`3 open`). The zero-token proof is under
[`zero/`](zero/); it omits the complete count paragraph when both counts are
zero, and omits each zero side independently. `intelligenceAttention.ts` is
untouched. The 0/0 card also withholds `Open proposals`; its real-producer
red/green and component shots are in `../round-two/README.md`. Dismiss stays.

## Current board and proposed board

The `today` board preserves the current production fixed position
(`bottom: 104px`) so the defect is visible. It is a comparison board, not a
ship recommendation. At 393 it intersects the readable summary and the
capture bar; at 1440 it intersects the capture bar. This is the retained
constant-offset failure.

The proposed, `summary-open`, and `capture` boards place the existing card in
normal document flow immediately before the existing CaptureBar. They use the
same real shell, the same Arrival species and the same card words and verbs.
At 393, the production CaptureBar is sticky at the chair bottom. A flow card
can pass under that bar at an intermediate scroll position; the phone
no-overlap figures below hold at the measured scroll or at the end-of-scroll
clearance. Auto-scroll to the measured slot is therefore the load-bearing
phone mechanism, accepted by the owner before build. The `capture` board is distinct:
it shows the existing pressed-mic visual as an explicit canvas fixture, with
no microphone or backend call. The product transition and its ChairHome seam were unimplemented at that canvas stage; the current build proof is in `placement-proof/lane-report.md`.

On a sparse 1440 desk with the summary closed, normal flow leaves space below
the card while the CaptureBar stays at the bottom. That is the actual canvas
geometry, not a crop or an extra layout proposal.

The `meetings` board adds the active production `DeskWindowFrame` for Meetings.
Its card is the first row inside `.desk-surface-body`, below the titlebar and
before the Meetings content rows. The content uses production `SurfaceSection`,
`SurfaceRows`, `SurfaceRow`, `Button` and `surface-token` species with fixture
meeting records. The `floor` board keeps the production DeskChrome, Dock and
`DeskListView` as the production Floor list mode; its card is a normal-flow row
above the visible Floor work area. The Floor has no existing normal-flow body
slot: the board makes that limit visible and places the proposal at the shell
boundary above the work area. It does not invent an overlay inside the world.
The list uses the same production Floor item species and the small local
fixture set is canvas-only. The spatial WorldStage renderer is not claimed by
this board: headless WebGL did not show furniture in the capture, so the board
uses the production Floor list mode to keep current-surface content visible.

The self-contained review page is
[`toast-placement.html`](toast-placement.html). It includes today, proposed,
summary-open, capture, Meetings and Floor at both 1440 × 900 and 393 × 852.
Individual shots
and machine-readable geometry are in [`shots/`](shots/):

| Board | 1440 × 900 | 393 × 852 |
| --- | --- | --- |
| today (current defect) | [today-1440.png](shots/today-1440.png) | [today-393.png](shots/today-393.png) |
| proposed | [proposed-1440.png](shots/proposed-1440.png) | [proposed-393.png](shots/proposed-393.png) |
| summary-open | [summary-open-1440.png](shots/summary-open-1440.png) | [summary-open-393.png](shots/summary-open-393.png) |
| capture | [capture-1440.png](shots/capture-1440.png) | [capture-393.png](shots/capture-393.png) |
| Meetings window open | [meetings-1440.png](shots/meetings-1440.png) | [meetings-393.png](shots/meetings-393.png) |
| Floor above work area | [floor-1440.png](shots/floor-1440.png) | [floor-393.png](shots/floor-393.png) |

The old fixed-offset candidate is parked under
[`rejected/`](rejected/). Its summary/capture fence was a false negative: it
did not inspect the BRIEF, calendar and meeting row, and the card covered
those readable regions. It remains as rejected evidence and is not the
proposal.

Earlier canvas captures and duplicate rejected files are parked outside the
commit under `.tmp/philo6-toast-pre-counsel/` and
`.tmp/philo6-toast-duplicate-evidence/`. One rejected candidate is retained in
this artifact. The authoritative proposed boards are under `shots/`.

## Measured geometry

The numbers below come from [`shots/facts.json`](shots/facts.json). The canvas
fence checks the NO CALENDAR, BRIEF and MEETINGS sections, complete summary
well, readable summary text, capture bar, current-surface content, fixed desk
chrome, horizontal overflow and the card's exactly two Button verbs. `today`
is reported as the current defect and is intentionally exempt from the proposed
no-overlap assertions. Every flow board passed those assertions at its recorded
scroll position, kept the card in the viewport and had no browser errors
(`shots/browser-errors.json`).

| Board / viewport | Card | Summary well | Summary text | Capture bar | Card intersections |
| --- | --- | --- | --- | --- | --- |
| today / 1440 | `(440,644)–(1000,796)` | `y 359.6–451.6` | `y 391.6–445.6` | `y 758–832` | capture: yes |
| proposed / 1440 | `(440,391.6)–(1000,543.6)` | closed | closed | `y 758–832` | none |
| summary-open / 1440 | `(440,495.6)–(1000,647.6)` | `y 359.6–451.6` | `y 391.6–445.6` | `y 758–832` | none |
| capture / 1440 | `(440,495.6)–(1000,647.6)` | `y 359.6–451.6` | `y 391.6–445.6` | `y 758–832` | none; pressed mic fixture |
| today / 393 | `(16,568)–(377,748)` | `y 456.6–602.6` | `y 488.6–596.6` | `y 573–711` | summary + capture: yes |
| proposed / 393 | `(12,381.6)–(381,561.6)` | closed | closed | `y 573–711` | none; scrollTop 99 |
| summary-open / 393 | `(12,373.6)–(381,553.6)` | `y 191.6–337.6` | `y 223.6–331.6` | `y 573–711` | none; scrollTop 265 |
| capture / 393 | `(12,373.6)–(381,553.6)` | `y 191.6–337.6` | `y 223.6–331.6` | `y 573–711` | none; scrollTop 265; pressed mic fixture |
| meetings / 1440 | `(39,133)–(649,285)` | titlebar `y 73–113`; content `y 312–498.9` | n/a | dock and menubar | none |
| meetings / 393 | `(15,289.1)–(378,469.1)` | titlebar `y 229.1–269.1`; content `y 496.1–712` | n/a | dock and menubar | none |
| floor / 1440 | `(440,66)–(1000,218)` | work area `y 230–828`; list content `y 323.4–589.4` | n/a | dock and menubar | none |
| floor / 393 | `(12,62)–(381,242)` | work area `y 250–727`; list content `y 343.4–681.4` | n/a | dock and menubar | none |

The harness also changes the summary length and scroll target. With the longer
summary probe, the 1440 card is `(440,513.6)–(1000,665.6)` beside summary text
`y 391.6–463.6`; the 393 card is `(12,362.6)–(381,542.6)` beside summary text
`y 158.6–320.6`, with `scrollTop 330` and the same CaptureBar `y 573–711`.
Both long-summary probes pass the same no-intersection fence.

At the phone width, `chair.css` makes the CaptureBar sticky. A normal-flow
card can pass under it during an intermediate scroll; the no-overlap values in
this table are measured at the stated scroll or at end-of-scroll clearance.
The auto-scroll in owner ask 2 is the mechanism that places the card above the
sticky bar when the aftercare signal arrives.

## Provenance and method

The canvas source is in
[`canvas/harness/`](canvas/harness/): `main.tsx`, `main.css`,
`vite.config.mjs` and `shoot.py`. It uses the Phase 4 canvas methods in
`pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-canvas/` and
`story-04-canvas/`. The harness imports the production `DeskChrome`, `Dock`,
`RuntimeBusProvider`, `Chair`, `DeskWindowFrame`,
`SurfaceSection`, `SurfaceRows`, `SurfaceRow`, `SurfaceLedger`,
`SurfaceLedgerRow`, `MeetingSummarySlab`, `Button`, `MicButton` and
`BriefEgress`, `DeskListView`, plus the production CSS from `web/src`. The
Floor board seeds three local fixture primitives for the production Floor list
species; it makes no hub request or write. The capture board's pressed-mic
state uses the production listening sprite and Button styling as a canvas
fixture only; it does not invoke microphone capture or a backend.

The retained phase-5 defect was inspected at
`pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`.
The canvas run used Node 22, the repository `.venv`, the cached Playwright
browser and an isolated HOME. No graph walk or product backend was started.

The original ChairHome seam proposal is preserved in
[`chairhome.patch`](chairhome.patch), with rationale in
[`chairhome-rationale.md`](chairhome-rationale.md). It is an actual unified
diff against the current ChairHome source; `git apply --check` passed. It adds
an empty `data-aftercare-slot` at `ChairHome.tsx:1442`, immediately before the
existing CaptureBar. It does not change the capture-clearance measurement at
`:685`. The patch alone places nothing: the future build needs the slot, an
AmbientLayer portal, auto-scroll, and the off-Arrival current-surface slot and
focus routing after ratification. The exact patch is now applied in the separate gated commit `d1e355f2`; no other ChairHome change is made by this lane.

Owner asks (both ratified before build):

1. Ratify the Arrival slot before the existing CaptureBar, plus top-of-current-
   surface flow slots off Arrival: inside an active Meetings window body below
   its titlebar and before content; in Floor above the work area.
2. Ratify auto-scroll to the measured Arrival phone slot. This MOVES the
   owner's reading position and scrolls the Arrival head off the phone. At
   another scroll position the sticky CaptureBar can cover the flow card.

## Reproduction

Start the harness Vite server, then capture the boards with an isolated HOME:

```sh
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright
HOME=$(mktemp -d) /Users/karol/dev/tools/wt-philo-6-b/web/node_modules/.bin/vite \
  --config docs/internal/philo/phase-6/toast/canvas/harness/vite.config.mjs
HOME=$(mktemp -d) /Users/karol/dev/tools/wt-philo-6-b/.venv/bin/python \
  docs/internal/philo/phase-6/toast/canvas/harness/shoot.py \
  docs/internal/philo/phase-6/toast/shots
```

The Vite process must be running for `shoot.py`. The zero proof commands and
raw output are in `zero/collect.txt`, `zero/red-origin-behavior.txt` and
`zero/green-focused.txt`.


The Floor canvas reserves the measured card and dock heights for these two
viewports. It is a shell-layout proposal with fixture content, not proof of
an implemented dynamic slot. Production build must measure the current shell
and fence the rendered transition after ratification. Spatial WebGL geometry
is not proved by the Floor list-view board.
