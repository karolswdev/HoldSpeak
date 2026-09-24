# PHILO-4-04 canvas — The triaged headline

**PROPOSED — owner ratification pending. Canvas only; the product is unchanged.**

Muad'Dib's final check: **RATIFY for presentation**, all four conditions
paid. Astra agrees; no open dissent. The owner has not ratified either option.

The section must tell the owner that the six rows have been handled while
keeping the brief's original counts. After Muad'Dib's check, the recommended
option keeps the headline and date in their ratified positions and adds only
`ALL 6 HANDLED` below the date. The alternative adds `SNAPSHOT` to the date
line and moves it above the headline. Both use the existing 12 px
`surface-receipt-line` species and add no control.

Open [triaged-headline.html](triaged-headline.html). It contains every board
as an embedded image and requires no network. The source harness imports
the real `Chair`, `SurfaceSection`, library `Button`, `BriefEgress`, and
production styles from this worktree. The screenshots show the BRIEF
section in the Chair, as in story 01's canvas; they are not full Arrival
walks or evidence of implemented behavior.

## Owner asks

1. Choose the **recommended one-line option** (board 7c): keep the existing
   `SEP 21 – 23 · GENERATED SEP 23 17:40` below the headline and add only
   `ALL 6 HANDLED` below it. Or choose the alternative (board 7b): move the
   date above the headline and label it
   `SNAPSHOT · SEP 21 – 23 · GENERATED SEP 23 17:40`. That alternative moves
   the date when the last row is handled and adds the word `SNAPSHOT`.
   Both preserve the historical counts exactly.
2. Use `ALL 6 HANDLED` below it after all six Arrival items have an Ack or
   Defer state. Keep the same placement during Generate and after its
   success or failure. “Handled” means triaged; it does not mean the work
   or a deferred commitment is complete. **The count covers Arrival rows
   only; it excludes THIS WEEK. It can be smaller than the headline's
   total.** For example, five handled Arrival rows plus one commitment in
   THIS WEEK would show `ALL 5 HANDLED` under a headline that also counts
   the commitment. This is a scope example, not a newly observed producer run.
3. Keep `No changes` for a brief with no items. Show no handled count for
   that state. Use no triage time: the face does not receive one.

Tuesday question: after Ack or Defer on the last row, can you tell that
this brief has been handled and that the waiting counts describe its
saved snapshot?

Muad'Dib publishes this artifact for the owner. Build starts only after
the ratification word in a follow-up brief, as the lane brief and
UX-CANON A.2 require. This PR must remain open; story 04 stays backlog.

## Exact face strings

| String | Meaning |
| --- | --- |
| `BRIEF` | Existing section label, with no zero counter |
| `THIS DEVICE` | Existing egress chip for the local route |
| `Generate` | Existing library Button |
| `SNAPSHOT · SEP 21 – 23 · GENERATED SEP 23 17:40` | Alternative snapshot/date line, above the headline |
| `1 thing changed, 3 things waiting, 2 decisions waiting.` | Unchanged stored headline from the six-row acceptance fixture |
| `ALL 6 HANDLED` | Current Arrival triage state: below the existing date in the recommended option; below the headline in the alternative |
| `No changes` | Existing empty-brief result |
| `SEP 21 – 23 · GENERATED SEP 23 17:40` | Existing date line on the baseline, empty and recommended one-line boards |
| `GENERATING…` | Existing in-progress generation state; Generate disabled |
| `BRIEF DID NOT GENERATE · HTTP 500` | Existing failure fixture; Generate enabled |
| `Brief ready · 6 items · 5:40 PM` | Existing receipt species, same-day Generate success with the original generation time |

Only `ALL <n> HANDLED` is new in the recommended option; the alternative
also adds `SNAPSHOT`. Names,
counts and dates use the existing short-label grammar; no new sentence is
added. The preserved historical headline remains the producer's text.

## Boards

Each board is captured at 1440 × 900 and 393 × 852, device scale 2.
The PNG is cropped to the section; its filename names the viewport.

| Board | 1440 | 393 | Purpose |
| --- | --- | --- | --- |
| Empty, current | [shot](shots/7a-empty-original-1440.png) | [shot](shots/7a-empty-original-393.png) | Story 01 board 7a as built: `No changes` |
| All handled, current | [shot](shots/7b-fully-triaged-original-1440.png) | [shot](shots/7b-fully-triaged-original-393.png) | Story 01 board 7b as built: bare historical counts |
| All handled, alternative | [shot](shots/7b-fully-triaged-proposed-1440.png) | [shot](shots/7b-fully-triaged-proposed-393.png) | Snapshot/date, unchanged headline, current handled state |
| One line, recommended | [shot](shots/7c-one-line-proposed-1440.png) | [shot](shots/7c-one-line-proposed-393.png) | Original headline and date positions, with only the handled line added |
| Generating, proposed | [shot](shots/8a-quiet-generating-proposed-1440.png) | [shot](shots/8a-quiet-generating-proposed-393.png) | The same saved result and handled state remain visible |
| Failed, proposed | [shot](shots/8b-quiet-failed-proposed-1440.png) | [shot](shots/8b-quiet-failed-proposed-393.png) | The same saved result and handled state remain visible |
| Same-day success, proposed | [shot](shots/9-same-day-success-proposed-1440.png) | [shot](shots/9-same-day-success-proposed-393.png) | Handled state and generation receipt coexist |

## Data and source limits

Base: `280ee7ce` (main after PR #626, stories 01/02/03 merged).
Current quiet branch: `web/src/desk/chair/ChairHome.tsx:1368-1400`.
Current date line: `ChairHome.tsx:158-167`. Anchors name this base and
must be checked again before build.

The exact six-row fixture is the story 01 round-five `_compose` fixture
required by story 04: m1 changed; o1, u1, l1 waiting; d2, c1 decisions.
The real `MondayBriefService._compose` reproduces its stored headline.
This is **not** a full `generate` fixture: story 02 established that the
full producer places this c1 under THIS WEEK. The corrected provenance
is recorded in the story 01 canvas README, round-six item 7. Neither the
old ratified boards nor the stored counts are rewritten here.

The date values retain the story 01 example. The route's date helpers
derive these labels from `generated_at`; this canvas does not claim a
new live producer run. The 5:40 PM success receipt uses the saved
`generated_at`, as `briefReceipt` does; it is neither a click time nor a
handled timestamp.

The shelf API exposes item-id → state (`MondayBriefService._load_shelf`,
`holdspeak/services/monday_brief_service.py:1209-1214`). It does not expose
the DB's `updated_at`. No API/schema change is needed for this proposal.

## Build seams after ratification

- Derive the positive count from the actual Arrival brief items with
  stored `acknowledged` or `deferred` shelf states. Require every counted
  item to have one of those states. No `ALL 0 HANDLED`.
- A quiet branch is not sufficient proof: `ChairHome.tsx:883-885` also
  filters raw-id text. Hidden, unshelved items must not produce an
  `ALL … HANDLED` claim. THIS WEEK is outside this Arrival item's scope.
- Keep the snapshot label meaningful if the quiet branch is reached
  without complete triage. Do not infer handling from the absence of
  visible rows. Keep the empty-brief board unchanged.
- Retain the generation receipt/status wherever the click leaves the
  face. Canvas states show the intended placement; rendered transition
  fences must prove it in the build.
- Preserve `data-testid="arrival-brief-date"` on the date-bearing line.
  The alternative snapshot marker also carries this existing date anchor.
- The durable handled line uses the receipt CSS species without
  `role="status"`; generation status/receipts keep their existing live
  regions. Muad'Dib's inferred 401 role-count impact was not confirmed:
  those fences query testids, not the count of live regions. The build
  must verify actual transitions and announcements.
- Write the intended-state fence against the ratified strings, prove it
  red before the fix, and read the stored headline and six items back
  unchanged after real shelf writes. Change words and their fences in
  the same build commit. Run actual atlas cases through `graph_walk.py`
  at both widths in isolated HOMEs; no sample-atlas substitution.

## Evidence boundary

The command/output record is [validation.md](validation.md), copied
from `dw evidence capture` with its auto-created `Status: done` metadata
corrected visibly to canvas-only. Captured commands and output are unchanged.
The paired `evidence-story-04.md`
is reserved for the later done-flip: the gate rejects new paired evidence
without a story flip. No acceptance box is checked by this canvas commit.

Existing Generate/date tests check the unchanged baseline. The canvas
probe checks rendered labels and geometry, not product behavior,
durability, full-face clearance, real pointer transitions or owner use.
The product fence, real atlas walks and owner's sitting remain pending.

Observed by Astra on 2026-09-24: all 14 final section shots inspected. Both
baseline boards at both widths are byte-identical to the corresponding
story 01 shots. All 14 have a 12 px text floor, viewport-width document
scroll size, no raw buttons, no zero BRIEF count and no browser errors.
The snapshot precedes the unchanged headline in the alternative boards;
the recommended one-line board preserves headline → date → handled order.
The handled line coexists with each generation state. Generate is disabled
only on the generating board. Measurements: [shots/facts.json](shots/facts.json).
The existing Generate/date tests collected 16 tests and passed all 16.
The final capture adds the one-line pair; the other 12 PNGs are unchanged
from the first inspected capture. The date-anchor and static-state changes
affect DOM semantics, not pixels.

Muad'Dib's [canvas check](../../checks/story-04-canvas-muaddib.md) asks
for the one-line option, explicit count scope, honest evidence metadata,
and the date/live-region build seams. The one-line board and asks address
those conditions. Owner ratification is still pending.

One initial command used the broad `test:desk` npm wrapper. It was stopped
with exit 143 when its built-in directory filter was noticed; no full-suite
result is claimed. The next command named only the two focused files and
passed. Both command outputs are retained in validation.md.

## Reproduce the canvas

Use the repository's pinned dependencies in this worktree. This session
used an independent `web/node_modules` copy and
`uv sync --extra test --no-install-project`; no shared environment symlink.
The default Homebrew Node is broken on this machine, so the installed
Node 22.21.0 was placed first on PATH. `uv run --no-sync` avoids the
package build hook, which would run npm install/build unnecessarily.

From the worktree root, start the canvas server:

```sh
web/node_modules/.bin/vite --config pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-canvas/harness/vite.config.mjs
```

With an isolated HOME and the existing Playwright browser-cache path,
run `harness/shoot.py <output-directory>` and then `harness/page.py`.
The latter packages `shots/` into the self-contained HTML and its two
overview PNGs. The exact commands used here are in validation.md. These
scripts do not start a hub or write the owner's desk.
