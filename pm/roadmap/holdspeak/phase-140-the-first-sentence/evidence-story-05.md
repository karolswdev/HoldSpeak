# HS-140-05 evidence — The quiet return

**Date:** 2026-08-18
**Result:** done; Terra final verdicts RATIFY

## Shipped behavior

- Every onboarding disposition is guarded by the existing ordinary furnished
  seed on the server. Invalid dispositions are rejected before any seed side
  effect, and a seed failure cannot persist an exit.
- Copy, Keep as Note, Continue later, and help share one client handoff:
  ordinary seed, pre-reveal Desk refresh, best-effort content-free first-value
  receipt, disposition, then the final server-authorized refresh. Transcript
  arrival alone never leaves the editable first-value composition.
- The handoff is visibly single-flight. Competing mic, Copy, Keep, Setup, and
  exit actions are unavailable while it runs; a failure keeps the draft and
  stable note claim in place behind one Retry.
- Nonempty unkept text changes the exits to **Save draft & continue** or
  **Save draft & get help**. That explicit choice writes one stable
  `First dictation` Note, stages its post-reveal open, and never silently loses
  or secretly saves the sentence. The local duplicate clears only after the
  final refresh succeeds.
- A lost disposition response retries the idempotent seed and disposition but
  does not repost the Note. A kept or deferred Note opens once after the
  server reveals the normal Desk. Existing deep links survive the transition;
  one Chair and one chrome mount return.
- Record start and stop failures publish through the existing Desk receipt
  channel with an exact Retry. Stop remains in its stoppable state until the
  retry lands; non-Hero callers do not receive unhandled rejections.
- The genuine phone walk found and fixed a 464px returned Chair in a 393px
  viewport by making lane tracks shrinkable and constraining narrow chrome.
  No global overflow masking was added.

## Local verification

```text
npx vitest run src/desk/components/FirstWords.test.tsx src/desk/DeskApp.test.tsx src/desk/chair/Chair.test.tsx src/desk/chair/ChairHome.test.tsx src/desk/chair/hero/CaptureHero.test.tsx src/desk/store/__tests__/recordingSlice.test.ts --maxWorkers=2
Test Files  6 passed (6)
Tests       87 passed (87)

uv run pytest -q tests/integration/test_setup_first_value_journey.py tests/unit/test_desk_seed.py tests/unit/test_product_copy.py
32 passed in 6.11s

npm run build
1479 modules transformed; built successfully
```

`git diff --check` passed. The repository-wide TypeScript check retains the
same seven unrelated Agents, Meetings, DeliveryBoard, Models, and
meeting-configuration errors recorded in Story 03; it reports no Story 05
file errors.

## Bare-HOME browser acceptance

The authoritative walk used a bare `MeetingWebServer`, empty database, and
isolated temporary HOME. It did not call the old working-desk walker or inject
its Phase-132 fixtures. Continue was the first ordinary seed.

- [Fresh Chair, 1440×900](./assets/story-05/ordinary-continue-chair-1440x900.png)
- [Fresh Chair after reload, 393×900](./assets/story-05/ordinary-continue-reload-chair-393x900.png)
- [Six default drawers and Everyday context, 1440×900](./assets/story-05/ordinary-default-drawers-floor-1440x900.png)
- [Six default drawers and Everyday context, 393×900](./assets/story-05/ordinary-default-drawers-floor-393x900.png)
- [Controlled Keep opens one Note, 1440×900](./assets/story-05/ordinary-keep-controlled-transcript-1440x900.png)
- [Controlled Keep opens one Note, 393×900](./assets/story-05/ordinary-keep-controlled-transcript-393x900.png)
- [Walk method and simulation boundary](./assets/story-05/README.md)

At both widths the document and body equal the viewport width, Continue
survives reload, all six drawers exist, and there are no console/page errors.
The Keep pair controls only the browser transcription seam; it does not claim
a physical microphone or local-model pass.

## Counsel trail and remaining cold-walk issue

Three amendment rounds closed the running-lock race, invalid-disposition seed
side effect, hidden deferred-text write, lost-response Note replay, silent
Record failures, false fixture-backed browser evidence, and mobile overflow.
Independent cold-owner and Tuesday reviews return **RATIFY**.

Both reviewers separately assign one glass issue to HS-140-06: at 393px the
Floor crowds Everyday context against Reference and truncates nearby labels;
the default Floor also exposes three internal HoldSpeak roadmap/runtime
objects. Story 05 proves the lawful furnished return. The final cold walk must
remove that clutter before the phase can close.
