# PHILO-6-03 · Toast that does not cover

Last updated: 2026-09-24 night.

Muad'Dib's recorded check and paid conditions are in the phase roadmap
`checks/story-03-canvas-zero-muaddib.md`. Parent final reproduction is retained
in `parent-shots/` and `canvas-dw-final-validation.md`.

**CANVAS ONLY · PROPOSED · OWNER RATIFICATION PENDING · HOLD FOR SHIP**

This artifact records a placement proposal for the existing aftercare card.
It does not apply product placement or edit `ChairHome.tsx`. The zero-token
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
untouched.

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
phone mechanism, pending owner ratification. The `capture` board is distinct:
it shows the existing pressed-mic visual as an explicit canvas fixture, with
no microphone or backend call. The product transition and its ChairHome seam
remain unimplemented pending owner ratification.

On a sparse 1440 desk with the summary closed, normal flow leaves space below
the card while the CaptureBar stays at the bottom. That is the actual canvas
geometry, not a crop or an extra layout proposal.

The self-contained review page is
[`toast-placement.html`](toast-placement.html). It includes today, proposed,
summary-open and capture at both 1440 × 900 and 393 × 852. Individual shots
and machine-readable geometry are in [`shots/`](shots/):

| Board | 1440 × 900 | 393 × 852 |
| --- | --- | --- |
| today (current defect) | [today-1440.png](shots/today-1440.png) | [today-393.png](shots/today-393.png) |
| proposed | [proposed-1440.png](shots/proposed-1440.png) | [proposed-393.png](shots/proposed-393.png) |
| summary-open | [summary-open-1440.png](shots/summary-open-1440.png) | [summary-open-393.png](shots/summary-open-393.png) |
| capture | [capture-1440.png](shots/capture-1440.png) | [capture-393.png](shots/capture-393.png) |

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
well, readable summary text, capture bar, horizontal overflow and the card's
exactly two Button verbs. `today` is reported as the current defect and is
intentionally exempt from the proposed no-overlap assertions. Every flow
board passed those assertions at its recorded scroll position and had no browser errors
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
`RuntimeBusProvider`, `Chair`, `SurfaceSection`, `SurfaceLedger`,
`SurfaceLedgerRow`, `MeetingSummarySlab`, `Button`, `MicButton` and
`BriefEgress`, plus the production CSS from `web/src`. The capture board's
pressed-mic state uses the production listening sprite and Button styling as a
canvas fixture only; it does not invoke microphone capture or a backend.

The retained phase-5 defect was inspected at
`pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`.
The canvas run used Node 22, the repository `.venv`, the cached Playwright
browser and an isolated HOME. No graph walk or product backend was started.

The ChairHome seam is a proposal only in
[`chairhome.patch`](chairhome.patch), with rationale in
[`chairhome-rationale.md`](chairhome-rationale.md). It is an actual unified
diff against the current ChairHome source; `git apply --check` passed. It asks
the owning lane to place a measured aftercare slot immediately before the
existing CaptureBar and to ratify whether the transition auto-scrolls to that
slot. No ChairHome change is applied here.

Owner asks:

1. Ratify the normal-flow slot immediately before the existing CaptureBar.
2. Ratify auto-scroll to the measured phone slot as the phone mechanism; at
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
