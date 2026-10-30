# Engines canvas notes (2026-10-30)

Canvas: `canvases/engines-2026-10-30.html` (one self-contained page; the
sprites are the real 20 px and 64 px PNGs, inlined). Shots: `canvases/shots/`
(`canvas-1440.png` is the whole page; `1440-dirA.png`, `1440-dirB.png`,
`1440-dirC.png` are the three directions; `1440-m*.png` the moments;
`1440-mPhone.png` the 393 window). Owner, 2026-10-30: "why the 'engines' page
looks so fucking bad … we somehow regressed to an old version". His "go with
suggestions" (2026-10-27) pre-approves the recommended direction; he judges it
live on his desk.

## The cause

His hub has Builder tools on (`ui.builder_tools: true`). `RunsOnCore.tsx`
swapped the whole window to the parked drag switchboard when Builder tools was
on (Betterment E5 parked it "behind Builder tools"), so he never saw the
grammar face. The grammar face itself still had faults: an inspector that
repeats the selected engine, a column of grey "Not assigned" pickers, host
chips on the job rows and in the status bar (A.9).

## The recommendation: B, two lists

Three directions with his desk at full size (12 engines, 11 jobs, two found):

- **A, one list of engines with Used for.** The jobs are a column; the editor
  is a fold under the list. Three presses to move a job; the fold pushes the
  list off screen.
- **B, two lists (recommended).** "What HoldSpeak does" (one row per job: the
  job, its engine as a picker Button, the state) beside "Engines" (one row per
  engine: sprite, name, where it runs in words, the state). Selecting a job
  lights its engine's row (a blue edge): the wires' meaning without wires.
  Two presses to move a job. Both lists fit a 700 px window with no scroll
  (measured: rows 32 px, overflow 0 px in both panes).
- **C, a fold per engine.** The jobs hide inside the engines; a job with no
  engine has no place.

In his terms: tired on a Tuesday, he opens Engines to ask "is my stuff up and
what runs what?" or to say "put summaries on OpenRouter". B answers the first
with one look and the second in two presses on the job's own row.

## Rules the build keeps

- Builder tools no longer changes what Engines draws. The switchboard species
  stays in the kit (parked here, not deleted).
- No host, address or scope chip on a row or the status bar. The address is a
  fact row in the engine's own fold (A.9: Engines is where the choice is made).
  The Add flow keeps its chip at the act.
- Rows 32 px at the desktop, 44 px and two lines at 520 px or less; jobs first
  when stacked. Every verb a library Button; states through `stateWords`.
- The split is a container query (two panes from 880 px of window width).
- Delight: the agent and cartridge sprites on every engine row; the breathing
  lamp while checking; the status bar's Find on LAN fact breathes while it
  looks.

## Deviation from the brief

The brief asked each job for a "Change in Settings ▸ Runs on" verb. Settings
has no assignment editor: Betterment ST1 and ST7 made Engines the one home of
the assignments (Settings ▸ Meetings shows "Summaries run on …" with
**Engines ›**), and "Runs on" may not be visible text
(`tests/unit/test_engines_name_guard.py`). The change stays in the job's row.
