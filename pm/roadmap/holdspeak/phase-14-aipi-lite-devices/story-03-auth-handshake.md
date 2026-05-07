# HS-14-03 - PSK Auth + Handshake Protocol

- **Project:** holdspeak
- **Phase:** 14
- **Status:** backlog
- **Depends on:** HS-14-02
- **Unblocks:** HS-14-04
- **Owner:** unassigned

## Problem

The audio ingest endpoint accepts arbitrary connections. Even on a
LAN, that's untenable — anything that finds the port could push
audio that lands in the user's transcripts. We need a minimum-viable
auth model: a single shared pre-shared key (PSK) the device sends
during its first WebSocket frame; the server rejects connections
whose PSK doesn't match.

This story owns the **protocol contract** (the handshake schema +
error codes); HS-14-04 wires it into the actual route.

## Scope

- **In:**
  - PSK storage: extend the existing settings store
    (`holdspeak/config.py` / per-user settings JSON) with a
    `device_psk: str` field. Generated on first run if absent
    (cryptographically random; ≥ 24 chars; base64).
  - `holdspeak/device_audio.py:DeviceHandshake` Pydantic model:
    `{type: "hello", device_id: str, label: str, psk: str, version: int}`.
  - Constant-time PSK comparison (`hmac.compare_digest`) to avoid
    timing oracles.
  - Documented WebSocket close codes for auth failures: 4001
    (missing/invalid handshake), 4003 (PSK mismatch), 4009 (label
    conflict — surfaced from `DuplicateLabelError`).
  - `holdspeak/cli.py` (or equivalent) command:
    `holdspeak device-psk show` + `holdspeak device-psk rotate`.
    Rotating invalidates currently-connected devices on next
    auth check.
  - `tests/unit/test_device_handshake.py` covering: schema
    validation, PSK compare, close-code mapping.

- **Out:**
  - WebSocket route itself — HS-14-04.
  - Per-device PSKs / federation — phase 15+.
  - TLS / WSS termination — phase 15 (cross-network).
  - Audit logging of auth failures (lightweight log line is in
    scope; structured audit trail is out).

## Acceptance Criteria

- [ ] PSK is generated on first launch and stored in the existing
  settings store; `holdspeak device-psk show` prints it.
- [ ] `holdspeak device-psk rotate` regenerates and persists.
- [ ] `DeviceHandshake` model validates required fields and
  rejects extra fields strictly.
- [ ] PSK comparison uses `hmac.compare_digest`.
- [ ] Close codes 4001 / 4003 / 4009 are constants in
  `holdspeak/device_audio.py` and referenced (not duplicated)
  by HS-14-04.
- [ ] `tests/unit/test_device_handshake.py` ≥ 4 cases green.

## Test Plan

- Unit: `uv run pytest tests/unit/test_device_handshake.py`.
- Integration: covered in HS-14-04's end-to-end test.
- Manual: `holdspeak device-psk show` + `rotate` round-trip.

## Notes

- Why PSK and not OAuth / mTLS: this is a single-user product on
  a personal LAN. PSK is simple, auditable, and rotates with one
  command. mTLS comes when phase 15 ships cross-network.
- Why a separate story for the protocol vs the route: lets HS-14-04
  focus purely on the websocket lifecycle (connect / per-frame
  dispatch / clean close) without re-litigating auth shape.
- Cross-repo: the AIPI-Lite-side bridge needs a config knob for
  the PSK. Tracked in the AIPI-Lite roadmap (AIPI-2 — bridge
  protocol translator).
