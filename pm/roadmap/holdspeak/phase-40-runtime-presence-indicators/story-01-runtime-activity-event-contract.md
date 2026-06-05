# HS-40-01 — Runtime Activity Event Contract

- **Project:** holdspeak
- **Phase:** 40
- **Status:** implemented in `/tmp`
- **Depends on:** none
- **Unblocks:** HS-40-02, HS-40-03, HS-40-04
- **Owner:** unassigned

## Problem

The runtime has useful status fragments (`voice_state`, transcription loading,
meeting active, intel state, last error), but the UI has to infer what
HoldSpeak is doing from multiple fields and websocket message types. A visible
presence indicator needs one small contract that says: "what is happening
right now, why, and when did it change?"

## Scope

- **In:**
  - Add a normalized runtime activity payload, likely under
    `/api/runtime/status["activity"]` and `state["runtime"]["activity"]`.
  - Payload fields: `state`, `source`, `label`, `detail`, `started_at`,
    `updated_at`, `last_event`, `last_error`.
  - States: `idle`, `listening`, `recording`, `transcribing`, `processing`,
    `typing`, `complete`, `meeting_live`, `saving`, `error`.
  - Update `WebRuntime` status transitions around hotkey/device dictation,
    transcription, injection, meeting start/stop/save, and runtime errors.
  - Broadcast `runtime_activity` over the existing websocket whenever the
    state changes.
- **Out:**
  - UI layout work beyond minimal fixtures needed for tests.
  - Persisting activity history to the database.
  - Reworking `VoiceTypingSession` arbitration.

## Acceptance Criteria

- [ ] `/api/runtime/status` includes an `activity` object with stable keys.
- [ ] Existing `/api/runtime/status` callers still receive the current top-level
      fields (`voice_state`, `transcription`, `meeting_active`, `state`, etc.).
- [ ] Websocket clients receive `runtime_activity` messages on state changes.
- [ ] Hotkey/device dictation paths set activity through recording,
      transcribing/processing, typing/idle, and error.
- [ ] Meeting paths set activity through meeting live, saving, idle/error.
- [ ] Unit tests cover payload derivation and transition helpers without real
      audio, Whisper, keyboard injection, LLM, or network calls.

## Test Plan

- Unit: focused tests for any new runtime activity helper/model.
- Unit/integration: fake `WebRuntime` callback tests for status changes and
  broadcast payload shape.
- Regression: existing runtime/system route tests continue to pass.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / Open Questions

- 2026-06-05 — Implemented in `/tmp`: `holdspeak/runtime_activity.py` defines
  the JSON-safe activity contract, state normalization, desktop window policy,
  and tracker snapshot/update behavior. `WebRuntime` exposes the snapshot on
  `/api/runtime/status` and broadcasts `runtime_activity` websocket messages.
  Focused tests cover the activity model and runtime broadcast path.
- Keep the schema intentionally boring and JSON-safe. This is a UI contract,
  not a telemetry analytics schema.
- If hotkey press and recorder start are currently too tightly coupled, record
  the earliest reliable state as `recording`; a later story can split
  `listening` from `recording` if the callback seam is added.
