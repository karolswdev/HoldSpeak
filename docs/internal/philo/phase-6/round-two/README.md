# Lane B round-two verification

This is a records/canvas correction and one named render-only fence, based on
Muad'Dib's counsel on PR #647 at `f443a3ff`. Story 03 stays in progress.
No placement code, story flip, full suite, new graph walk or merge is claimed.

## Provenance and records

- `checks/lane-b-built-muaddib.md` in the phase roadmap matches the supplied
  counsel's `VERDICT:` block byte for byte, apart from the removed Scratch
  archive line and the requested heading. This is the check of record.
- Earlier 03 canvas, 04 built, and 05 design/built Markdown checks are renamed
  `*-astra-invoked-claude.md` and start with the provenance notice. The three
  corresponding JSON responses are renamed `*-astra-invoked-claude.json`.
  Their first line has the same notice in a `provenance` field. Parsing and
  comparison with `git show HEAD:<original-path>` verified that all other
  response fields are unchanged. The prior Astra rollout
  `01a0d668-0158-7040-92ce-2aea508c63e2` also records Astra launching the 04
  `claude -p` command with `rows/check-brief.md`; its misleading Markdown
  label is corrected for the same reason.
- The negative control directory is now
  `../body/negative-control-first-frame-393/`. Its observation and three PNGs
  are byte-identical to the originals. Raw observation paths remain historical.
- `git apply --check ../toast/chairhome.patch` passed from the repo root with
  its full path. ChairHome has no diff. The patch adds the empty slot at
  `ChairHome.tsx:1442`; a portal, auto-scroll and current-surface routing are
  still future build work.

## 0/0 render fence

The real `publishAftercare` path feeds the rendered AmbientLayer. The new
test first fails with the old unconditional Button, then passes with the
render guard. It covers the 0/0 state, transition to decided-only 0/2,
opener dispatch/dismissal, and a later empty card's Dismiss. The opener is
mocked at its boundary; these tests do not claim a live Meetings navigation.

- Worker red: [zero-pre-fix-red.txt](zero-pre-fix-red.txt), 1 failed / 4 passed;
  expected no Open proposals Button, received the existing Button.
- Parent collection: [frontend-collection.log](frontend-collection.log).
- Parent run: [frontend-green.log](frontend-green.log), 14 passed in two files.
  `HOME=$(mktemp -d) ./node_modules/.bin/vitest run
  src/components/AmbientLayer.test.tsx src/components/AftercareNote.test.tsx
  --maxWorkers=2 --reporter=verbose`, from `web/`, Node 22.
- Parent glass: [zero 1440](zero-component/zero-1440.png),
  [zero 393](zero-component/zero-393.png), [facts](zero-component/facts.json).
  Actual AmbientLayer and producer, isolated component fixture with API
  responses stubbed and WebSocket disabled. No count paragraph or dead opener;
  Dismiss works at both widths. This is not a hub or placement walk.

The retained fixture and Playwright script reproduce the component proof:

```sh
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
HOME=$(mktemp -d) web/node_modules/.bin/vite \
  --config docs/internal/philo/phase-6/round-two/zero-component/fixture/vite.config.mjs
# With the server running, in a second shell:
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python docs/internal/philo/phase-6/round-two/zero-component/shoot.py \
  .tmp/philo6-round2-zero-recapture
```

## Canvas verification

Astra independently ran `toast/canvas/harness/shoot.py` through DW with fresh
HOME and the cached Playwright browser. All 14 board/probe captures passed;
`today` is the deliberately failing placement comparison and exempt from the
proposal fences. [Full facts](canvas/facts.json) exactly match the worker's
geometry (the final worker record uses null for the non-Floor visibility
field; the parent capture used true for that inapplicable field), and [browser errors](canvas/browser-errors.json) is empty. The
[DW captures](dw-validation.md) have exit 0; full JSON is retained because DW
truncated the long stdout. No paired done evidence was added to the roadmap.

Astra opened both widths of Meetings and Floor, plus the phone Arrival
proposal. The card lies below the Meetings titlebar and above its content.
On Floor it precedes the actual `DeskListView`, whose three fixture rows stay
visible. All proposed cards are inside the viewport, with no measured
intersection with content, menubar or dock, and no horizontal overflow.

| Off-Arrival board | 1440 | 393 |
| --- | --- | --- |
| Meetings | [shot](canvas/meetings-1440.png) | [shot](canvas/meetings-393.png) |
| Floor, list view | [shot](canvas/floor-1440.png) | [shot](canvas/floor-393.png) |

Recommendation: keep the proposed before-CaptureBar slot on Arrival; use a
**top-of-current-surface flow slot off Arrival**. The Floor board uses the
real list mode. Spatial WebGL Floor geometry is not proved. The first spatial
canvas attempt showed a blank, clipped work area and was rejected; it is not
promoted to a passing board. The final canvas changes no product placement.
Ask 2 explicitly says phone auto-scroll moves the owner's reading position
and scrolls the Arrival head off the screen.

## Retained real-atlas proof and generated checks

These commands were run again over the actual retained cases, not samples:

- `rows/verify_parity.py`: [parity.log](parity.log). The sidecar verdict is
  FAIL 2:1 → PASS 1:1 at both widths. Rig refusal verdicts are `pass` on both
  sides. Story 04 box 5 and its evidence now say this and name the added HTTP
  393 viewport at `atlas-phase3.json:6500`.
- `body/verify_transition.py`: [transition.log](transition.log). Continuous
  reds have blanks at +159.1 / +77.3 ms; green traces each have 129 readable
  frames. No product S4 code or observation was changed in round two.
- All five generated `--check`s passed: OpenAPI, graph, API reference,
  boundary census and capability docs. Their raw logs are in this directory.
  The boundary census was regenerated after the render guard moved one
  source reference by two lines; no candidate was added or removed.

`dw check holdspeak-philo` passes. Repository-wide `.githooks/dw check` exits 1 with six inherited errors:
Phase 101's evidence/story status mismatch and missing final summaries in
152, 153, 154, 156 and 200. The same command against the retained pre-phase
archive at `66205729` produces identical lines. See [current](dw-check.log)
and [baseline](dw-check-baseline.log). This lane changes only the three
requested BACKLOG rows in `pm/roadmap/holdspeak/`; it does not repair old phases.

A worker capture used the mistyped output directory `docs/internal/philo-6/`.
The rollout confirms its origin; that duplicate is parked intact at
`.tmp/philo6-round2-mispathed-canvas/`, excluded from this commit.

## Limits

Floor canvas height reservations are specific to these two measured
viewports and fixture content; production dynamic-slot behavior remains a
build obligation. No spatial WebGL placement proof is claimed.

The off-Arrival slot remains a proposal. Owner ratification, product placement,
active-surface routing, the rendered placement transition and the closing
rehearsal are still owed. The collection-read bug is ledgered from the
recorded counsel and inspected source, not newly reproduced here. No broad
test-suite result is claimed under the scoped round-two brief.
