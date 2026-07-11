# HS-92-03 — The first words land

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress (pre-close implementation; physical microphone/device walk pending)
- **Depends on:** HS-92-01, HS-92-02
- **Unblocks:** HS-92-09, HS-92-10
- **Owner:** unassigned

## Problem

The Web arrival is six wizard screens and introduces model/runtime choices
before the basic local transcription value. Native first boot teaches spatial
gestures while its visible “Talk to the desktop” option does not call the real
desktop dictation path. Failure must not erase the phrase or strand a user in a
first-run redirect loop.

## Scope

- **In:** Desk-first basic transcription path; durable onboarding disposition
  (`completed`, `dismissed`, `needs_help`) separate from first-success; optional
  advanced model setup after basic value; canonical Swift production route to
  real desktop dictation or removal of the false choice; exactly-once delivery;
  retained text with Retry/Copy/Keep; first-value measurement and UAT.
- **Out:** Replacing the dictation pipeline, correction memory, or advanced
  runtime editor; requiring an LLM for transcription; background hands-free
  capture changes.
- **Paths:** `holdspeak/setup_status.py`, `holdspeak/setup_runtime.py`,
  `holdspeak/web/routes/setup.py`, `holdspeak/web/routes/dictation/pipeline.py`,
  `holdspeak/web/routes/system/voice.py`, `web/src/pages/WelcomePage.tsx`,
  `web/src/desk/components/EmptyDesk.tsx`, Desk voice inputs,
  `apple/App/MeetingCaptureApp.swift`,
  `apple/App/MeetingCapture/DeskDioramaStage.swift`, the production
  `DictateView`/`DictateModel` files, UAT arrival/dictation scenarios, and their
  Python/Web/Swift tests.

## Acceptance criteria

- [x] A fresh Web user reaches a successful basic local dictation from the Desk
      in no more than three product steps, makes zero LLM placement decisions,
      and sees no more than two technical nouns before success.
- [x] The first-value instrument records steps, decisions, start/success times,
      destination, and failure category without storing phrase content or
      creating remote telemetry.
- [x] Continue later/dismiss is durable and never loops back to `/welcome`;
      Setup remains reachable with the exact unresolved checks.
- [x] Optional intelligent rewrite/model setup appears only after basic value or
      when explicitly chosen, and uses the canonical Runs-on picker.
- [x] The canonical Swift root's desktop-dictation action invokes the real
      remote dictation contract exactly once, creates no local Meeting, and
      shows the named paired destination before delivery and on the Receipt.
- [x] An unreachable hub, missing permission, missing local Whisper model,
      rejected token, and delivery conflict each retain editable text and offer
      the applicable Retry, Copy, Keep as Note, or Setup action.
- [x] Voice-to-fill on Desk inputs remains preview-before-commit and does not
      auto-submit; hotkey dictation preserves its existing immediate/preview
      preference until ControlMode lands.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_setup_status_doctor_drift.py tests/unit/test_remote_dictation_delivery.py tests/unit/test_dictation_preview.py tests/unit/test_transcribe_route.py`; Web Welcome/Desk component tests; Swift dictate-model tests.
- **Integration:** `uv run pytest -q tests/integration/test_setup_first_dictation.py tests/integration/test_web_welcome_wizard.py tests/integration/test_web_setup_route.py tests/integration/test_wake_ux.py tests/integration/test_voice_typing_via_device.py`; UAT scenarios updated from `pack-desk/15`, `pack-desk/16`, and `pack-d-honest-failure/03`.
- **Manual / device:** Real microphone on Web, physical iPhone, and physical iPad;
  successful basic path plus permission denial/recovery and unreachable desktop
  with a canary phrase delivered exactly once.

## Notes / open questions

If real desktop delivery cannot fit safely, remove the native choice in this
story and keep the existing dedicated Dictate room as the only honest route.

Implementation began on 2026-07-10 by direct owner instruction while Phase 91
remains current. Fresh Web arrival now opens a one-step `FirstWords` atom on the
Desk instead of redirecting through the six-screen wizard; basic browser audio
uses the existing local transcription route with no model choice, leaves the
result editable, and exposes Retry, Copy, Keep as Note, and Setup recovery.
Onboarding disposition and content-free first-value attempts are durable in
schema v14, independent of the first-success milestone, and terminal receipts
are idempotent so a replay cannot turn a failure into success.

The native Desk's “Talk to the desktop” choice now presents the production
`DictateView` rather than the meeting recorder. Release clears the listening
guard before transcription suspends, then calls the focused remote-dictation
contract once; the named paired Mac appears before delivery and in the receipt,
and no local Meeting is created. Permission, model, token, conflict, and
unreachable failures retain an editable local draft with Retry, Copy, and Setup.
Automated proof is green: focused Python journey/route/contract tests, three
Vitest component tests, TypeScript typecheck, all 524 Swift package tests with
9 expected skips, and the generated universal iOS Simulator host build. The
story remains open for its real Web microphone plus physical iPhone/iPad canary
walks; simulator compilation is not physical-device evidence.
