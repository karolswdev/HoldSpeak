# AIPI-4-03 — Multi-Device Meeting Verification

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** backlog
- **Depends on:** AIPI-2-05 (single-device meeting verification)
- **Unblocks:** —
- **Owner:** karol

## Problem

HoldSpeak's `MeetingSession.attach_device` accepts a list of devices. The bridge architecture is one-process-per-device (decided at AIPI-2-01). Phase 2 verified single-device meetings; phase 4 verifies that **two devices in one meeting actually work end-to-end**: per-segment label discipline, audio mixing without garbling, fairness during simultaneous talk, and recovery semantics when one bridge crashes mid-meeting.

This is largely a verification + ergonomics-doc story. Bridge code change is expected to be zero unless gaps surface during verification.

## Scope

### In

- Stand up two AIPI-Lite devices flashed with **distinct mDNS hostnames** (otherwise both advertise `aipi.local` and resolution becomes unpredictable — observed live 2026-05-10 with two devices on the LAN flapping between which `aipi.local` resolved to). Use the `device_name` substitution added 2026-05-10:
  - Primary: `esphome run aipi.yaml --device /dev/ttyACM0` (default `device_name=aipi`).
  - Secondary: `esphome -s device_name aipi-green run aipi.yaml --device /dev/ttyACM0` (or any unique name).
- And distinct `DEVICE_ID` (e.g., `aipi-1`, `aipi-2`) + distinct `DEVICE_LABEL` (e.g., `Karol-office`, `Karol-living-room`) in each device's `bridge.env`.
- Two `bridge.env` files (or two systemd unit instances using a templated unit pattern); two bridge processes.
- Start one HoldSpeak meeting with both attached: `POST /api/meeting/start {"devices":["aipi-1","aipi-2"]}`.
- Speak from each device individually; verify per-segment labels.
- Speak from both simultaneously; characterize HoldSpeak's mixing behavior; document.
- Crash one bridge mid-meeting (`pkill -f "bridge.*aipi-1"`); verify the other continues + the meeting persists; verify the crashed device rejoins on bridge restart.
- Update `docs/HOLDSPEAK_BRIDGE.md` with a "Multi-device meetings" section: how to set up the second device, the templated systemd unit pattern, expected behavior, troubleshooting.
- If gaps in label discipline surface (e.g., HoldSpeak collapses both devices into one speaker), open a follow-up story or fix in this one if scope-small.

### Out

- More than 2 devices (verification scope is 2; HoldSpeak supports more server-side).
- Multiplexing both devices through a single bridge process — one-per-device contract preserved (decided in phase 2; not revisited here).
- Audio mixing on the bridge side — HoldSpeak does its own (this story confirms the boundary).

## Acceptance criteria

- [ ] Two AIPI-Lite devices flashed with distinct `DEVICE_ID` + `DEVICE_LABEL`.
- [ ] Two `bridge.env` files (or `aipi-bridge@aipi-1.service` + `aipi-bridge@aipi-2.service` templated systemd units); both bridges running.
- [ ] HoldSpeak meeting started with both attached; both devices appear in `MeetingState.devices`.
- [ ] Single-device speech: speaking from device 1 → transcript segment tagged `Karol-office`; speaking from device 2 → transcript segment tagged `Karol-living-room`.
- [ ] Simultaneous-talk behavior documented: whether HoldSpeak interleaves, mixes, or prefers one. Whatever HoldSpeak does, it's not garbled — both speakers' content is recoverable from the transcript.
- [ ] Bridge-crash mid-meeting: kill one bridge process; the other continues streaming; meeting persists; HoldSpeak does not drop the other device. After restart, the crashed device's bridge re-attaches and resumes contributing.
- [ ] Runbook section "Multi-device meetings" shipped, including templated-systemd-unit example: `aipi-bridge@.service` with `EnvironmentFile=/etc/aipi-bridge/%i.env`.

## Test plan

- **Unit:** none — bridge code is unchanged unless gaps surface.
- **Manual (hardware):**
  1. Provision device 2 (re-use AIPI-1 phase or factory-flash).
  2. Configure `bridge.env` for each device with distinct identities.
  3. Start both bridges (background + log-tail via `journalctl -fu aipi-bridge@aipi-1.service` etc).
  4. Start meeting via `POST /api/meeting/start {"devices":["aipi-1","aipi-2"]}`.
  5. Speak alternately, then simultaneously.
  6. End meeting; review transcript for label correctness + segment ordering.
  7. Re-run with mid-meeting bridge kill; capture recovery log.

## Notes

- **DEVICE_ID must be unique per device** — bridge constraint, enforced by HoldSpeak's session arbiter.
- **DEVICE_LABEL CAN repeat** in principle (e.g., both labeled `Karol`) but is the wrong default — one of the goals is to know who said what.
- **Templated systemd unit pattern:** `scripts/aipi-bridge@.service` with `WorkingDirectory=/opt/aipi-bridge` and `EnvironmentFile=/etc/aipi-bridge/%i.env`. Document in runbook with one full example file.
- **HoldSpeak re-attach on bridge restart:** verify that `MeetingSession.attach_device` accepts a re-attach for the same `device_id`. If HoldSpeak rejects, that's an HS-side bug to file (story-blocker, not story-fix).
- **Per-host vs. per-network:** running two bridges on one host is the v1 expectation. If multi-device meeting reveals host-resource pressure (CPU dominated by RMS computation if AIPI-4-02 ships, or aioesphomeapi event-loop contention), document the multi-host pattern as a deferred decision.
