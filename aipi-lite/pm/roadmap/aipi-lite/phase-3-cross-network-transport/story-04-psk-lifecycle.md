# AIPI-3-04 - PSK Lifecycle + Per-Device PSKs (paired with HS-15)

- **Project:** aipi-lite
- **Phase:** 3
- **Status:** backlog
- **Depends on:** AIPI-3-01
- **Unblocks:** AIPI-3-05
- **Owner:** unassigned

## Problem

Phase 2 ships a single shared PSK between bridge and HoldSpeak,
configured in `bridge.env` on the bridge host. Across networks +
multiple devices this gets uncomfortable:

- **Rotation** — when the user runs `holdspeak device-psk rotate`,
  every bridge needs the new value. If a bridge is on a different
  network, the user can't easily SSH home to update it.
- **Per-device secrets** — if the user has two AIPI-Lites + two
  bridges, they share the same PSK. A compromised bridge revokes
  all of them.
- **Multi-network labels** — see `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`
  §8: HoldSpeak's registry is in-memory + per-network labels can
  diverge across home/office/coffee-shop. Persistence is HS-15's
  job; the bridge needs to handle whatever HS-15 lands.

This story pairs with HoldSpeak HS-15's PSK lifecycle work. The
bridge side is small once HoldSpeak's schema settles.

## Scope

### In (when HoldSpeak HS-15 ships per-device PSKs)

- Update `bridge.env` schema to use the per-device secret the
  HoldSpeak side ships. Likely either:
  - A device-scoped PSK (`HOLDSPEAK_PSK_AIPI_1=...`,
    `HOLDSPEAK_PSK_AIPI_2=...`), with the bridge picking the right
    one based on `DEVICE_ID`.
  - Or a single PSK with a per-device-id derivation
    (less likely; HoldSpeak's HMAC primitive doesn't suggest this).
- Update the WS handshake to send the device-scoped PSK in the
  `DeviceHandshake.psk` field.

### In (regardless of HS-15 status)

- **Document the PSK rotation procedure for cross-network operation:**
  1. Run `holdspeak device-psk rotate` on the HoldSpeak host.
  2. Run `holdspeak device-psk show` to print the new value.
  3. Update `bridge.env` on every bridge host (SSH if needed; or
     a one-shot copy via `scp` / a sync tool).
  4. Restart each bridge process.
  5. Existing connections drop with code 4003 on next reconnect;
     bridges reconnect with the new PSK.
- **Optionally: bootstrap-token flow.** Bridge fetches PSK from
  HoldSpeak on startup using a one-time token (printed by
  `holdspeak device-psk bootstrap`). Reduces friction across
  networks. Out of phase 3 scope unless HoldSpeak HS-15 ships
  the server side; flagged as a phase-3-followup story.

### Out

- Implementing HoldSpeak's HS-15 schema. That's HoldSpeak's repo.
- mTLS / client cert auth. AIPI-3 stays at PSK-in-config.
- Browser/UI flows for PSK distribution.

## Acceptance Criteria

- [ ] Runbook section "PSK rotation across networks" exists in
  `docs/HOLDSPEAK_BRIDGE.md` covering the manual procedure
  (rotate, show, scp/edit, restart).
- [ ] If HoldSpeak HS-15 has shipped per-device PSKs by the time
  this story is implemented, the bridge handshake uses the
  device-scoped value + `bridge.env.example` reflects the new
  schema.
- [ ] If HS-15 has NOT shipped per-device PSKs, story status is
  `paused` with a note explaining the dependency, and the manual
  rotation procedure is the only deliverable.
- [ ] The bridge logs `disconnect.holdspeak code=4003` clearly
  enough that a user reading the log knows to update the PSK
  (existing AIPI-2-01 behaviour; this story confirms it's
  legible in the cross-network case).

## Test Plan

- **Manual:**
  1. Rotate the PSK via HoldSpeak's CLI.
  2. Without updating the bridge, observe its log fill with
     `reconnect target=holdspeak attempt=N` lines + the 4003 close
     code.
  3. Update `bridge.env`, restart the bridge, observe a clean
     handshake.
- **Unit:** none for the procedural deliverable. If the
  per-device-PSK flag lands, add a unit test that the right
  secret is selected by `DEVICE_ID`.

## Notes

- HoldSpeak HS-15 isn't scaffolded as a HoldSpeak phase folder yet
  (as of 2026-05-08; latest phase is 14). Story stays paused on
  the per-device PSK acceptance until that surfaces. The manual
  rotation runbook section can ship without HS-15.
- The bootstrap-token flow is genuinely useful for cross-network
  operation but adds protocol surface. Defer until users hit the
  pain in practice.
- The bridge's existing reconnect-with-backoff naturally handles
  the "PSK was rotated, bridge wasn't updated" case — it loops
  forever with structured logs. Verify the log volume is
  reasonable (don't flood) and that the close-code message
  surfaces the actionable next step.
