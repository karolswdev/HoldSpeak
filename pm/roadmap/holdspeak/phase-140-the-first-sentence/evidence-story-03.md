# HS-140-03 evidence — Recovery stays here

**Date:** 2026-08-18
**Result:** done; Terra final verdicts RATIFY

## Shipped behavior

- Permission denial names browser or operating-system microphone access and
  leaves one Retry. No-speech, timeout, and transcription failure remain
  distinct, keep the textarea editable, and do not pretend one failure is
  another.
- Unavailable local transcription leaves one enabled Setup action. The mic bar
  is a neutral disabled status, not a duplicate call to Setup.
- Streaming capture uses `retainScope: "first-words"`. A named refusal is not
  overwritten by socket close, the live session is cleared and cancelled, and
  Retry stays disabled while the local retention write is unsettled.
- A proven retained capture survives reload and is retried before any new
  recording, including when the browser cannot start fresh microphone capture.
  A retention claim appears only after the write reports success.
- A late IndexedDB recovery read cannot replace a capture the owner already
  started.

## Local verification

```text
npx vitest run src/desk/components/FirstWords.test.tsx src/lib/dictationRecovery.test.ts src/lib/__tests__/micStreamSession.test.ts --maxWorkers=2
Test Files  3 passed (3)
Tests       37 passed (37)

npm run build
1479 modules transformed; built successfully
```

`git diff --check` passed. The repository-wide TypeScript check still reports
seven inherited errors in unrelated Agents, Meetings, DeliveryBoard, Models,
and meeting-configuration files; it reports no Story 03 file errors.

## Isolated-HOME browser acceptance

The real loopback hub, with a fresh temporary HOME, produced its genuine named
local-transcription-unavailable refusal. At 1440×900 and 393×900 the typed
fallback remained editable, exactly one enabled Setup action was present,
there were zero enabled Retry controls, and no page errors occurred.

- [Unavailable transcription, 1440×900](./assets/story-03/transcription-unavailable-real-1440x900.png)
- [Unavailable transcription, 393×900](./assets/story-03/transcription-unavailable-real-393x900.png)
- [Walk method and scope](./assets/story-03/README.md)

Headless Chromium could not honestly exercise physical microphone denial or a
real silent utterance on this host. Those physical-device legs remain named in
HS-140-06; their UI contracts are covered by the focused tests here.

## Counsel trail

The first audit found discarded named refusals, an unproven retention claim,
an overlapping live session, a Retry/write race, and duplicated Setup wording.
The implementation and browser walk closed each finding. Independent cold-owner
and Tuesday counsel re-audits returned no blockers or should-fixes: **RATIFY**.
