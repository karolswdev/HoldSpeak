# Material and PR results

Status: PRODUCT FROZEN — focused checks and final scoped UI observations pass;
HOLD for SHIP. Root accepted
the integrated-mic direction before the Pad/Capability amendment. No staging
or commit by this lane.

Library direction: [canvas-material-receipts/main.tsx](canvas-material-receipts/main.tsx).
Declared sample data; API routes intercepted; isolated HOME and machine lock.
Initial capture log: `.tmp/edges/material-canvas.log`. The root's canon
preflight then rejected the host-mic composition because `mic={false}` raised
the ceiling. Updated integrated-mic capture:
`.tmp/edges/material-integrated-canvas.log` (eight shots, no page errors).
Final populated-PR direction: `.tmp/edges/material-pr-populated-canvas.log`;
the canvas mounts the real PrReceiptsSection with declared result transport,
in a 640 px desktop frame and a 393 sheet. Resting/opened shots are
`pr-result-{1440,393}.png` and `pr-result-open-{1440,393}.png` in the same
scratch shot folder. All four were read; no page errors.

| Direction | 1440 | 393 |
| --- | --- | --- |
| Multiline material, one mic | `material-1440.png` | `material-393.png` |
| Plain draft outcome; technical receipt in output fold | `pr-result-1440.png` | `pr-result-393.png` |
| Inherited footer seam | `frame-before-1440.png` | `frame-before-393.png` |
| Reserved bottom band | `frame-after-1440.png` | `frame-after-393.png` |

These filenames identify local scratch captures under
`.tmp/edges/canvas-material-receipts/shots/`. The PNGs were excluded from
commits and are unavailable in a clean checkout. They are direction captures,
not retained application observations. The canvas expresses the approved
desktop-only frame scope.

Capability now uses PadGadget's default integrated mic with its original
label/scope. Root diagnosed the exact shared seam and extended ownership to
PadGadget's voice callback and `gadgets.test.tsx`: the callback consumes the
current value and onChange through a ref (`gadgets.tsx:411,457`). Held speech
therefore appends to newer edits and uses the current writer. No new public API,
StringGadget, scanner, ceiling or allowlist change. The host mic was removed;
the multiline editor owns exactly one mic.

PR results retain the performed action separately from the busy label. Only a
successful Draft review with nonempty output says `Review ready`. A generic
accepted request must not claim an agent is running. Operation/artifact IDs stay
inside the existing output disclosure, alongside the complete result text.

## Frame diagnosis and repair

The root's actual Calendar observation
`/Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/after-footer-completion-1440/observation.json`
records Retry at `(822, 658.5, 54, 28)` and three bottom-row points owned by
`desk-window-edge-b`. `window-chrome.css:96` sets that handle to `bottom: -3px`
and `height: 6px`; the frame mounts it after content (`DeskWindow.tsx:1342`).
`surface-footer.css:16` supplies horizontal padding and already reserves 24 px
for the corner grip, but reserves no bottom padding for this edge.

Implemented after GO: 6 px bottom padding on
`.desk-window-shell:not(.is-sheet) > .desk-surface-foot` in `window-chrome.css`.
Every edge/corner handler, the 6 px resize edge and the existing corner-grip
reserve remain. Root must verify Retry's nine points and actual edge/corner
drag; the direction and jsdom tests do not establish that proof.

## Focused validation

All collection/runs used `.tmp/edges/locked.py`, an isolated HOME and the
machine test lock. No provider, physical microphone, owner DB or owner state
was used. The PR tests mount controlled result state, not a real inference run.

Final collection: `.tmp/edges/material-integrated-collect.log`, **51 tests**
in these five approved files:

- `web/src/desk/__tests__/contextual.test.ts`
- `web/src/desk/components/__tests__/commonControls.test.tsx`
- `web/src/desk/components/PrReceiptsSection.test.tsx`
- `web/src/desk/surface/__tests__/surfaceFooter.test.tsx`
- `web/src/desk/surface/gadgets.test.tsx`

Final run: `.tmp/edges/material-integrated-run.log`:

```text
Test Files  5 passed (5)
     Tests  51 passed (51)
  Duration  2.22s
```

Canon collection: `.tmp/edges/material-canon-collect.log`, seven cases in
`tests/unit/test_ux_canon_ratchet.py`. Final run under the lock with eight
workers: `.tmp/edges/material-canon-run.log`:

```text
.......                                                                  [100%]
7 passed in 2.56s
```

The rejected host-mic composition is replaced, not waived. The initial PR
test's ambiguous fold/well text selector now presses the actual summary.
New exact cases:

- `keeps selected paragraphs and newer edits when a late voice result fills capability material`
- `shows Review ready for a completed draft and keeps identifiers inside the output fold`
- `retains the performed action so an accepted send is not reported as a ready review`
- `does not call an accepted draft ready without review output`
- `PadGadget keeps one mic and appends a late capture through the latest value and writer`

`git diff --check` passed on the eight owned product/test files and the newly
assigned PR-only scope in `delivery.css`. No broad suite
or quick check was run by this lane; root owns the build, actual browser
observations, review of frame behavior and release.

## Actual intermediate observations and PR repair

Bundle `11dccb95ec0cd276`, built by root, was checked against the real served
build marker in each isolated tour. Four screenshots per width were read in
`.tmp/edges/material-pr-after-{1440,393}/`; no page errors. Both widths retain
the edited paragraphs in local storage and after Close/reopen, with exactly
one material mic. The 393 PR resting headline and opened output were readable;
its scroll well had `scrollWidth = clientWidth = 363` and the headline was
inside the visible well. The exact replay request was
`POST /api/delivery/prs/declared-pr/393/draft-review` with `{}`.

**The desktop PR job did not pass visual review.** Its DOM visibility check
passed, but `pr-review-ready.png` shows the first column and Review ready
clipped left after More scrolls the table right. `pr-review-output.png` clips
left labels too. The inherited table minimum is 760 px (`delivery.css:229`),
while its stacked rules began only at a 520 px body. Companion's default
640 px window therefore falls between the two layouts.

Root confirmed the shots and settled the minimum repair: the existing PR-only
container query now extends through 760 px. Its row/result composition is
unchanged. No scroll reset, ledger rewrite or state change. The updated canvas
shows the actual populated component at both widths before this product change.
The PR file alone was rechecked afterward:
`.tmp/edges/material-pr-responsive-recheck.log` — **6 passed in 1.48s**.
The actual tour now fails on horizontal table overflow immediately after More,
or on a headline/output rectangle outside the visible work area. The final
bundle proof below verifies that repair; the intermediate desktop capture
remains the before evidence.

Two harness stops were preserved in scratch: the first used `recipe:` instead
of the canonical `persona:` object reference; the first phone reopen raced a
UI close with scratch cleanup. The private tour now waits for the exact UI
close reply and accepts cleanup 404 only after a fresh read proves the exact
row absent. No product exception was added.

## Final scoped UI proof

Both strengthened tours completed on root's frozen bundle
**`83e97b8c05b13ff5`**, built at **2026-10-16T13:52:28.717Z**. Each run
checked the served marker. Both observations and all eight PNGs were read:

- `.tmp/edges/material-pr-responsive-1440/observation.json`
- `.tmp/edges/material-pr-responsive-393/observation.json`

Each directory has `material-edited.png`, `material-recovered.png`,
`pr-review-ready.png` and `pr-review-output.png`. Edited paragraphs survive the
real Close/reopen path and match the stored durable draft exactly; the material
field has one integrated mic. PR titles, resting Review ready and opened output
are readable at both widths. IDs appear only in the output fold. There were no
page errors and no horizontal document overflow.

| Desk width | PR well scroll/client width after More | Resting headline inside visible well | Complete sample output inside visible work area |
| --- | --- | --- | --- |
| 1440 | 602 / 602; scrollLeft 0 | x 291–369, y 312.45–327.45 | x 303–865, y 398.45–550.45 |
| 393 | 363 / 363; scrollLeft 0 | x 23–101, y 382.45–397.45 | x 35–358, y 468.45–674.45 |

Each exact PR request remains
`POST /api/delivery/prs/declared-pr/393/draft-review` with `{}`. The real
isolated recipe writer, window lifecycle, local draft storage and browser UI
were exercised. Readiness/PR replies remain declared transport substitutions;
Run, inference, physical voice capture and GitHub were not exercised. Latest
voice completion is covered by the focused Pad/Capability regressions, not by
these browser captures. Root separately owns frame resize/target proof and the
whole release verdict.

Run tails: `.tmp/edges/material-pr-responsive-{1440,393}.log` both report
`verdict: captured` with the four named states and no error. The desktop run
waited on the machine lock and then ran unchanged; no bundle restart or build
mutation was made by this lane.

## Private tour command

`.tmp/edges/material_pr_tour.py` requires
`--width 1440|393 --out <new-directory> --build-id <root-built-id>`, creates its
own isolated HOME/Hub, and checks the served bundle ID before opening the app.
Four states per width: edited material, durable reopen, resting Review ready,
opened raw output/receipt. Recipe creation uses the real isolated writer;
readiness and PR responses are declared browser transport substitutions,
recorded in the observation. Run is never pressed; no inference/GitHub is
exercised. Root separately owns frame target and edge/corner resize proof.
