# Evidence — AIPI-2-04 — Configuration Migration: bridge.env Schema

- **Shipped:** 2026-05-07
- **Commit:** `67bc2f3` (`feat(bridge): AIPI-2-04 config migration — Settings(BaseSettings) + dep prune`)
- **Owner:** karol

## Files touched

- `bridge.py` (later `bridge/settings.py`): `Settings` became a `pydantic-settings.BaseSettings` subclass reading env + optional `bridge.env` file. `HOLDSPEAK_PSK` is `SecretStr` (auto-redacts to `**********` in `repr()`).
- `bridge.env.example` — new. Documents every field with a comment per section + `holdspeak device-psk show` cue for populating `HOLDSPEAK_PSK`. Defaults: `ESPHOME_HOST=aipi.local`, `ESPHOME_PORT=6053`, `HOLDSPEAK_HOST=127.0.0.1`, `DEVICE_ID=aipi-1`, `LOG_LEVEL=INFO`. Required: `HOLDSPEAK_PORT`, `HOLDSPEAK_PSK`.
- `.gitignore` — added `bridge.env`, `.pytest_cache/`.
- `requirements.txt` — removed `faster-whisper`, `gtts`, `pydub`, `requests`, `webrtcvad-wheels`. Added `pydantic-settings>=2`. Final list: `aioesphomeapi`, `pydantic`, `pydantic-settings`, `structlog`, `websockets`, `pytest`, `pytest-asyncio`. (Re-pinned to `==` in AIPI-2-08; dev deps split out to `requirements-dev.txt`.)
- Legacy STT/LLM/TTS imports + helpers + HTTP server + `<think>`-tag stripping deleted from the bridge entirely.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q tests/test_settings.py
…  passed

$ .venv/bin/python -m pytest -q
98 passed in 2.80s

$ grep -RnE "faster_whisper|gtts|pydub|requests|webrtcvad|LLAMA|WHISPER" bridge/ 2>&1 | head
(no output — all legacy refs removed)
```

`tests/test_settings.py` (added in AIPI-2-08) covers empty-PSK rejection, log-level normalisation, label fallback (defaults to `DEVICE_ID` when blank).

## Acceptance criteria — re-checked

- [x] `bridge.env.example` exists with per-field comments and required-vs-optional flags — file present at repo root.
- [x] `bridge.env` in `.gitignore` — verified by inspection.
- [x] Bridge with no config exits 1 with field-list errors — verified 2026-05-07 (`holdspeak_port: Field required` / `holdspeak_psk: Field required`).
- [x] Startup banner logs `psk_set=true/false` (never plaintext) — `bridge/cli.py:_run` builds the banner manually with `psk_set=True` boolean.
- [x] PSK redacted in logs — `pydantic.SecretStr` makes `repr(SecretStr('abc'))` → `SecretStr('**********')`. Plaintext requires explicit `.get_secret_value()`. Smoke-confirmed.
- [x] `requirements.txt` pruned — verified by inspection. Final list listed above.
- [x] No legacy imports/references in bridge — grep above returns empty.
- [x] `python -c "import bridge"` succeeds; full test suite (98 cases) passes.
- [x] `--check` continues working — verified 2026-05-07; deepened in AIPI-2-08.
- [x] **Empty PSK rejected at config load** (added in AIPI-2-08): `SecretStr("")` was truthy at the Pydantic-required level and silently passed config validation; now rejected upfront with a clear error. Unit-tested in `tests/test_settings.py`.

## Deviations from plan

- Story-04 originally targeted `bridge.py` ≤ 250 LOC after legacy deletion. Actual was ~430 at this story (still a major reduction from the ~415 LOC legacy + the new spine). The bridge subsequently grew to 1500 LOC before AIPI-2-08 split it into a package; the package's per-module sizes are 87–466 LOC.
- Empty-PSK rejection was added later (AIPI-2-08) rather than at this story. Captured because the inline acceptance bracket lists it as `[x]` per phase-close state.

## Follow-ups

- File-watch / HUP-based PSK reload-on-change is documented as deferred in `current-phase-status.md` "Decisions deferred" — not opened as a story unless rotation frequency demands it.
