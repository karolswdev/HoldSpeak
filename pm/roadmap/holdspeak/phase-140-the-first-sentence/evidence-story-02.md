# HS-140-02 evidence — The sentence becomes useful

**Date:** 2026-08-18
**Result:** done; Terra final verdicts RATIFY

## Shipped behavior

- A non-empty captured sentence stays in the existing editable field. Capture
  start, release, an empty result, and manual typing do not complete onboarding.
- Copy writes the current edited value and reports either `Copied to your
  clipboard.` or an inline manual-copy recovery. Its content-free selection
  event is recorded even when the browser refuses clipboard access.
- Keep mints one opaque local note id and reuses it across response loss,
  refresh failure, and page relaunch. The note route's existing upsert makes a
  retry one note, not two. The durable draft and id remain until refresh and
  handoff succeed.
- A confirmed Keep refreshes the Desk and stages a qualified `note:<id>` open.
  Arrival keeps the card hidden; the server-authorized normal Chair consumes
  the stage and mounts the existing Note pullout. Floor/List retain their own
  existing pullout ownership.
- Transcript receipt is a content-free event, not onboarding completion.
  Story 05 owns seed-before-reveal completion. A backend success receipt now
  requires a prior `transcript_received` event.
- First-value event payloads accept exactly `event_id` and `kind` at both the
  HTTP route and service boundary. Phrase, transcript, audio, clipboard, and
  note-body values never enter first-value records.

## Local verification

```text
npx vitest run src/desk/components/FirstWords.test.tsx src/desk/firstValue.test.ts src/desk/DeskApp.test.tsx --maxWorkers=2
Test Files  3 passed (3)
Tests       20 passed (20)

.venv/bin/pytest -q tests/integration/test_setup_first_value_journey.py tests/integration/test_setup_first_dictation.py tests/integration/test_web_setup_status_api.py tests/unit/test_setup_status.py
27 passed in 6.31s
```

`npm run build` passed after 1,479 modules transformed with only the existing
dynamic/static-import and large-chunk warnings. `git diff --check` passed.

## Isolated-HOME browser acceptance

The walk used the real loopback runtime against a temporary HOME and seeded
database. At both widths it edited a sentence in the first-value field, copied
the exact edited value through the browser clipboard, kept it once, and then
used the existing Continue later server exit. The normal Chair opened the
created **First dictation** Note with the exact edited body. There were zero
console/page errors and no horizontal document overflow.

- Useful editable result: [1440×900](./assets/story-02/useful-result-1440x900.png), [393×900](./assets/story-02/useful-result-393x900.png)
- Created note open on the Chair: [1440×900](./assets/story-02/kept-note-open-1440x900.png), [393×900](./assets/story-02/kept-note-open-393x900.png)

The headless browser could not supply a physical microphone, so real capture
remains in the final cold-device Story 06 walk. The focused stream-session test
proves that a real non-empty capture populates this same editable field and
that its telemetry contains no phrase.

## Counsel trail

Two independent reviews amended the first pass until transcript arrival no
longer completed onboarding, Copy refusals counted truthfully, relaunch and
confirmed-write refresh failure reused one id, and the normal Chair rendered
the staged Note without an arrival leak. Seed-before-reveal remains the named
HS-140-05 composer. Final verdicts: **RATIFY**.
