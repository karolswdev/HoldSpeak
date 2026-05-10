# HS-17-11 — Handshake / Version Startup Flash

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-14-07 (device-status substrate); HS-14-08 (DEVICE_PROTOCOL.md — protocol versioning)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

When the AIPI-Lite bridge handshakes with HoldSpeak, the bridge logs are full of useful info (HoldSpeak version, protocol version, registered device count, etc.) but the device's LCD shows nothing distinguishing — just goes from `[--]` to `[OK]` (or now the LVGL wifi glyph) and `Ready ✓`. Hard to know at a glance which HoldSpeak you're connected to, especially when debugging multi-device or multi-machine setups.

User feedback 2026-05-10 during the two-device mDNS-conflict debugging: "I wish the device LCD told me which HoldSpeak this is."

## Scope

### In

- After `hello-ack` is sent server-side (in `holdspeak/device_audio_ws.py`'s handshake handler), the server emits a single startup flash to the just-connected device:
  - `HS v<version>` (e.g., `HS v0.2.0`) — 3-second flash.
  - Or richer: `HS v0.2.0 · <hostname>` if HoldSpeak knows its public host name.
- The flash uses `ttl_ms: 3000` and reverts to whatever sticky was there (which the bridge sets to `Ready` on connect via `_paint_activity("Ready")`).
- The version string is read from `holdspeak/__init__.py:__version__` or `pyproject.toml` (whichever is the canonical source).
- Symbol: optional. Could include `LV_SYMBOL_OK` (already used for Ready) or `LV_SYMBOL_HOME` (U+F015 — "this is home base").
- Integration test: handshake → ack → expect a version status frame within 100ms.
- `docs/DEVICE_PROTOCOL.md` extended.

### Out

- Ongoing version polling (version doesn't change mid-session).
- Detailed build metadata (commit hash, build time) — too long for the LCD.
- Cross-device version mismatch warnings (each device has its own bridge; they don't compare). Could be a future story if mismatch becomes an issue.

## Acceptance Criteria

- [ ] `holdspeak/device_audio_ws.py` handshake handler emits a `Hello v<version>` status flash via `device_status.send(device_id, ..., ttl_ms=3000)` immediately after `hello-ack`.
- [ ] Version string is from a single canonical source (`__version__` or `pyproject.toml`).
- [ ] Truncation if the combined version+hostname string exceeds 30 chars.
- [ ] Integration test green.
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification on AIPI-Lite hardware: restart bridge, observe a brief `HS v0.2.0` flash on the LCD just after connect, then revert to `Ready ✓`.

## Test Plan

- **Unit:** version-string builder (mock the version source).
- **Integration:** `tests/integration/test_device_handshake_flash.py` — handshake completes, status frame with version text arrives within 100ms.
- **Manual:** bridge restart on real hardware.

## Notes

- **Pairs with `--check` deepened verification** (AIPI-2-08): `--check` already validates HoldSpeak's `hello-ack` echoes the configured `device_id`. The version flash gives the user the same info visually without running `--check`.
- **`hostname`-or-not** — if the HoldSpeak host is a known short name (e.g., `karol-laptop`), showing it is useful. If it's a generic `localhost`, less so. Probably skip hostname for v1; just the version.
- **One flash per session.** The flash fires once on connect; doesn't repeat on heartbeats. Idempotency is intrinsic — `device_status.send` is fire-and-forget; the second hello-ack of a reconnect cycle naturally fires another flash.
- **Could grow** — over time, this slot could rotate: version → meeting count → uptime → next intel batch ETA, etc. v1 stays single-line + version-only.
