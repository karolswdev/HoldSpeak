# AIPI-2-04 - Configuration Migration: bridge.env Schema

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01
- **Unblocks:** AIPI-2-06
- **Owner:** karol

## Problem

Today's `bridge.py` is configured via env vars pointing at a local
LLM endpoint (`LLAMA_HOST`, `LLAMA_PORT`, `LLAMA_MODEL`, etc.) and
ESPHome credentials. AIPI-2 deletes the LLM/STT/TTS code paths, so
all the LLM-side env vars are orphaned. We need a clean replacement
schema, a documented `.env.example`, and a startup-time validator
that fails loudly if anything required is missing.

## Scope

### In

- Define the new env schema:
  - `ESPHOME_HOST` — device hostname (default `aipi.local`).
  - `ESPHOME_PORT` — device API port (default `6053`).
  - `ESPHOME_PASSWORD` — device API password (optional; default empty).
  - `HOLDSPEAK_HOST` — HoldSpeak host (default `127.0.0.1`).
  - `HOLDSPEAK_PORT` — HoldSpeak port (no default; required).
  - `HOLDSPEAK_PSK` — base64 PSK from `holdspeak device-psk show` (required).
  - `DEVICE_ID` — stable identifier sent in the handshake (default
    `aipi-1`).
  - `DEVICE_LABEL` — human label shown in HoldSpeak meeting
    transcripts (default `${DEVICE_ID}`).
  - `LOG_LEVEL` — `INFO` default; `DEBUG`/`WARNING`/`ERROR` accepted.
- A Pydantic settings model (`BridgeSettings(BaseSettings)`) that
  reads from env + `bridge.env` file, validates types, and fails
  with a clear error when required vars are missing or malformed.
- A `bridge.env.example` documenting every field with the same
  comment-per-field style as `secrets.yaml.example`.
- A startup banner: when the bridge starts, log a single line
  summarising loaded config (with PSK redacted to `<set>` /
  `<MISSING>`).
- Decision: **`bridge.env` lives next to `bridge.py` at the repo
  root.** Not `secrets.yaml` — that file is owned by ESPHome and
  conflating the two concerns is messy. Add `bridge.env` to
  `.gitignore`.
- Delete from `bridge.py`:
  - All `faster_whisper` imports + the `WhisperModel` setup.
  - All `gtts` imports + the TTS helper functions.
  - All `pydub` imports + the volume-adjust helpers.
  - All `requests` imports + the LLM HTTP calls.
  - The local HTTP server that hosts TTS WAVs.
  - The `<think>`-tag stripping regex logic.
  - Any LLM-related env vars (`LLAMA_*`, `WHISPER_*`, etc.) +
    matching code paths.
- Remove orphaned packages from `requirements.txt`:
  `faster-whisper`, `gtts`, `pydub`, `requests`. Keep
  `aioesphomeapi`. Add `websockets`, `pydantic`, `pydantic-settings`,
  `structlog` (or whatever logger story-01 picks).

### Out

- Migration tooling for users on old env files. Phase 2 is a hard
  cutover; the runbook (story-06) tells users to populate
  `bridge.env` from scratch.
- Remote PSK distribution / secret management. The PSK lives in a
  local file on the host running the bridge.
- A web UI for configuration. CLI + env file is enough for v1.

## Acceptance Criteria

- [x] `bridge.env.example` exists, documents every field with a
  comment block per section, and gives explicit defaults +
  required-vs-optional for each. Includes the
  `holdspeak device-psk show` cue for populating `HOLDSPEAK_PSK`.
- [x] `bridge.env` is in `.gitignore` (added alongside the
  existing `secrets.yaml` line; `.pytest_cache/` also added).
- [x] Starting `bridge.py` with no `bridge.env` and no required
  env vars exits 1 with a clear field-list error:
  `holdspeak_port: Field required` / `holdspeak_psk: Field required`.
  Verified 2026-05-07.
- [x] Starting with a complete config banner-logs once on startup
  with `psk_set=true`/`false` (never the plaintext PSK). The PSK
  is `pydantic.SecretStr`, which makes `repr()` redact to
  `**********` automatically — any log that captures the model
  is safe.
- [x] PSK redacted in logs: `repr(SecretStr('abc'))` →
  `SecretStr('**********')`. Plaintext access requires explicit
  `.get_secret_value()`. Smoke test confirmed.
- [x] `requirements.txt` no longer lists `faster-whisper`, `gtts`,
  `pydub`, `requests`, or `webrtcvad-wheels`. Adds
  `pydantic-settings>=2`. Final list: aioesphomeapi, pydantic,
  pydantic-settings, structlog, websockets, pytest, pytest-asyncio.
- [x] `bridge.py` has no `import faster_whisper / gtts / pydub /
  requests / webrtcvad`, and no `LLAMA_*`/`WHISPER_*` references.
  The unused `os` and `dataclasses.dataclass` imports were also
  removed (Settings is now a `BaseSettings` subclass).
- [x] `python3 -c "import bridge"` succeeds. 35/35 unit tests pass.
- [x] `--check` continues to work end-to-end: against the live
  `aipi.local` device, `check.device.ok` is logged; against an
  absent HoldSpeak, the structured `ConnectionRefusedError`
  message + exit 1 are unchanged.

## Test Plan

- **Unit:** `BridgeSettings` validation — fixtures for missing
  required field, bad port type, valid full config.
- **Manual:**
  1. With no `bridge.env`: `python3 bridge.py` exits 1 with the
     missing-fields error.
  2. With a complete `bridge.env`: `python3 bridge.py --check`
     succeeds.
  3. `grep -rE "faster_whisper|gtts|pydub|requests|LLAMA" bridge.py`
     returns empty.

## Notes

- **`pydantic-settings`** is the right tool here — it reads env +
  `.env` files and produces a strict typed model in one move. Tiny
  dep; widely used.
- **PSK redaction in logs:** use a custom Pydantic `SecretStr` field
  for `HOLDSPEAK_PSK`, then never `repr()` the model directly in
  logs. Build the banner manually with `psk="<set>" if cfg.psk else "<MISSING>"`.
- The legacy bridge has roughly 415 lines; after deletion of the
  STT/LLM/TTS paths, target ≤ 250 lines. If we're materially over,
  the rewrite is doing too much.
- The README at the repo root currently describes the legacy
  architecture. Story-06 rewrites it — but during this story, add a
  one-line marker at the top of `README.md`:
  `> NOTE: AIPI-2 in progress; this README still describes the
  legacy STT/LLM/TTS bridge. New architecture lands in AIPI-2-06.`
- **Don't reuse `secrets.yaml` for bridge config.** ESPHome owns
  that file; the bridge uses `bridge.env`. Two files, two concerns,
  no surprises.
