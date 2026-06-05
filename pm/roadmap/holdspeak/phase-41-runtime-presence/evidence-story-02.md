# Evidence — HS-41-02 — Web presence card

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The first **visible** win, with **zero new dependencies**: the runtime maps its
dictation + meeting lifecycle into the `runtime_activity` contract, broadcasts it
over the existing websocket, and the dashboard renders a live Signal presence
card. With the dashboard open you now see "what the copilot is doing."

- `web_runtime.py` — `RuntimeActivityTracker` wired in; `_set_runtime_activity`
  (updates the snapshot, stores it on `runtime_status["activity"]`, broadcasts);
  `_broadcast_runtime_activity` (**web-only** here — the desktop host fan-out is
  HS-41-03); `_set_voice_state` enhanced to map voice → activity; and lifecycle
  mappings across transcription warming/loading/error, the dictation transcribe
  loop (processing → typing → complete / no-speech / error), and the meeting
  path (start → meeting_live, segment, intel streaming/complete, saving →
  saved/failed, `actuator_proposed`). The snapshot rides on `/api/state`.
- `web/src/pages/index.astro` + `web/src/scripts/dashboard-app.js` — the Signal
  presence card (tokens-only: pulsing ring keyed to state tone, label + 2-line
  detail, source/desktop-policy meta), `role="status"` + `aria-live="polite"`,
  a `prefers-reduced-motion` guard, an Alpine `applyActivity()` driven by the
  `runtime_activity` WS message + seeded from `/api/state`.

### Salvage + corrections

Ported from codex PR #17 by 3-way-applying the `web_runtime` / `index.astro` /
`dashboard-app.js` additions onto post-Phase-40 `main`, then:

- **Stripped the desktop-presence host** (import, `self.desktop_presence`, the
  `handle_activity` fan-out, the `close()` call) — that's HS-41-03, behind the
  opt-in flag. `_broadcast_runtime_activity` is web-only here.
- **Fixed an off-token drift**: the card used `var(--line-height-snug)`, which is
  **not** a defined Signal token → corrected to `--line-height-normal` (the
  design canon rejects off-token values).
- Ported the two **web-only** mapping tests (dropping the desktop-host test +
  its now-absent `build_desktop_presence_host` monkeypatch) + the
  presence-indicator markup test.

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- Live capture: a real `MeetingWebServer` with a `recording` activity snapshot →
  the dashboard renders the card (`presence cards: 1 label: Recording`).
  Screenshot `evidence/web_presence_card.png` — orange pulsing ring, "Recording"
  + detail, `Hotkey · Desktop active` meta.
- Targeted: `.venv/bin/python -m pytest -q tests/unit/test_web_runtime.py tests/unit/test_web_presence_indicator.py`
  → `14 passed`.
- Ruff (touched py) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2228 passed, 16 skipped` (2224/16 at HS-41-01; +4).
- Bundle rebuilt; `git status` shows **no** `holdspeak/static/_built/`.

## Acceptance criteria — re-checked

- [x] Dictation/meeting lifecycle drives `runtime_activity` broadcasts; the
      dashboard card reflects state live —
      `test_runtime_activity_snapshot_and_broadcast`,
      `test_meeting_broadcasts_map_to_runtime_activity` + the live screenshot.
- [x] Rich Signal (not flat — pulsing ring, tone, aria-live, reduced-motion
      guard); behavior unchanged when idle (the mapping is additive; existing
      `web_runtime` tests pass).
- [x] Bundle rebuilt; no `_built/` staged; screenshot captured.

## Deviations from plan

- The desktop-host fan-out + its test are deferred to HS-41-03 (the renderer
  seam), keeping HS-41-02 dependency-free and web-only.
