# HS-154-01 - The voice: browser default, kokoro-onnx extra, /api/tts

- **Project:** holdspeak
- **Phase:** 154
- **Status:** done
- **Depends on:** HS-153-06
- **Unblocks:** HS-154-03, HS-154-04, HS-154-05
- **Owner:** unassigned

## Problem

Every assistant turn needs a voice with zero egress and zero licence
surprise by default, and a better one the owner can opt into with the
trade-offs visible (settled design D1; the feasibility ruling in
HANDOVER supersedes RFC §6.8's server-side default).

## Scope

- **In:** `web/src/lib/tts.ts` — the ONE client seam: `speak(text)`,
  `enqueueSentence(text)`, `stop()`, `onStateChange`; browser
  `speechSynthesis` default with a sane voice pick; the server path
  used only when `GET /api/tts/status` says the extra is installed.
  Server: optional `holdspeak[tts]` extra (kokoro-onnx), `POST /api/tts`
  streaming WAV chunks, 404 without the extra; the weights download
  egress-badged + receipted via the Model Library pattern
  (`holdspeak/web/routes/model_library.py:83`); the GPL-3.0 note
  (phonemizer/espeak-ng) rendered where the extra is enabled in
  Settings — one line, no privacy novel. R4: first chunk > 2 s → fall
  back to the browser voice for that utterance (recorded, implemented).
- **Out:** auto-speak wiring (04), call mode (03), voice cloning.

## Acceptance criteria

- [ ] Without the extra: `speak()` uses speechSynthesis (vitest, mocked synth), `/api/tts` answers 404, Settings shows no dead TTS switch.
- [ ] With the extra (test-installable fake): `/api/tts` streams WAV chunks; the weights download writes a receipt and carries the egress badge; the GPL note renders.
- [ ] R4 fallback: a stubbed slow first chunk (>2 s) flips that utterance to the browser voice; a test proves it.
- [ ] Glass 1440 + 393: the Settings TTS block (extra off and on), zero overflow.

## Test plan

- **Unit:** `tests/unit/test_tts_route.py` (404 law, stream shape, receipt); vitest `tts.test.ts` (seam, fallback, sentence queue).
- **Integration:** glass leg `tts-settings` in `tests/e2e/test_hs154_call_glass.py`.
- **Manual / device:** story 05.

## Notes / open questions

- The extra's import must be lazy — the base install never pays for it.

## What shipped

### Files

- `holdspeak/web/routes/tts.py` — the TTS route module: `GET /api/tts/status`, `POST /api/tts` (streaming WAV), `POST /api/tts/download` (egress-badged, receipted). Lazy kokoro-onnx import; 404 with typed code when the extra is absent.
- `holdspeak/web/routes/__init__.py` — added `build_tts_router` to the route registry.
- `holdspeak/web_server.py` — mounted `build_tts_router(web_ctx)` in `_create_app`.
- `pyproject.toml` — added `tts` optional-dependency extra (`kokoro-onnx>=0.4.0`, `soundfile>=0.12.0`). The GPL-3.0 chain (phonemizer + espeak-ng) is documented in the comment.
- `web/src/lib/tts.ts` — the ONE client seam: `speak(text)`, `enqueueSentence(text)`, `stop()`, `onStateChange(cb)`. Browser `speechSynthesis` default with sane local voice pick (local English first); server path preferred when `GET /api/tts/status` says `{installed: true, model_ready: true}`; R4 law: 2 s `AbortController` timeout on the server fetch, falls back to browser voice on timeout/error. Sentence queue drains in order, `stop()` flushes.
- `web/src/pages/cores/settingsTts.tsx` — `TtsSettingsBlock` component: fetches `/api/tts/status`; extra-off shows BROWSER VOICE ACTIVE + one-line install instruction; extra-on shows BROWSER VOICE + SERVER VOICE status + download button with egress badge + GPL-3.0 note.
- `web/src/pages/cores/SettingsCore.tsx` — imported `TtsSettingsBlock`, rendered inside the "sounds" module case after Presence.
- `docs/api-surface.json`, `docs/API_SURFACE.md` — regenerated (564 routes, +3 for `/api/tts`, `/api/tts/status`, `/api/tts/download`).

### Tests

- `tests/unit/test_tts_route.py` — 10 tests: 404 law (status/post/download absent), status shape (without/with extra, with/without model), stream shape (WAV header, missing text 400, model not ready 503), download receipt + egress badge. All use a test-injectable fake `kokoro_onnx` module, not the real package.
- `web/src/lib/__tests__/tts.test.ts` — 9 tests: browser voice default (`speak()` calls `speechSynthesis.speak`), state transitions (idle/speaking/idle), `stop()` cancels + clears queue, sentence queue speaks in order, no-speechSynthesis silent no-op, server probe state, `_setPreferServer` override, R4 fallback (stubbed slow fetch > 2 s triggers browser voice), subscribe/unsubscribe.
- `tests/e2e/test_hs154_call_glass.py` — 2 tests: API 404 law on real hub (status/post/download), glass leg at 1440+393 (Settings loads, zero horizontal overflow, screenshots).
- `tests/unit/test_api_surface.py` — 5 tests pass (fence validates the regenerated manifest).
- Web baseline: zero BRANCH-NEW (1592 passed, 0 failed).

### Seams

- Client: `web/src/lib/tts.ts` is the ONE TTS seam. All callers import `speak`, `enqueueSentence`, `stop`, `onStateChange` from it.
- Server: `holdspeak/web/routes/tts.py` is the self-contained route module. The `_check_kokoro_available()` function caches the import probe. The `_get_kokoro()` singleton lazily initializes the engine.
- Settings: `TtsSettingsBlock` is a self-contained component that fetches its own status, isolated from the settings save flow (TTS has no persisted settings — the extra's presence is the entire config).

### Defects found

- None during implementation. The lazy-import + singleton pattern was clean from the start. The R4 fallback uses `AbortController` with a 2 s timeout, which cleanly cancels the fetch on slow server responses.

### Evidence

- `pm/roadmap/holdspeak/phase-154-the-call/evidence-story-01.md` — captured run: 15 passed (test_tts_route.py 10 + test_api_surface.py 5).
