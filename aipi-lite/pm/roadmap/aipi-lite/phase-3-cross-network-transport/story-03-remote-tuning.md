# AIPI-3-03 - Remote-Friendly Tuning (Timeouts, Queues, Latency)

- **Project:** aipi-lite
- **Phase:** 3
- **Status:** backlog
- **Depends on:** AIPI-3-01
- **Unblocks:** AIPI-3-05
- **Owner:** unassigned

## Problem

The bridge's defaults (`ping_interval=15`, `ping_timeout=30`,
`AUDIO_QUEUE_MAXSIZE=500`, reconnect schedule
`[1, 2, 4, 8, 16, 30] s`) were chosen for sub-millisecond loopback
RTT. Across-the-internet paths add 20–100 ms steady-state RTT and
the occasional 500–1500 ms jitter spike (mobile networks especially).
Some defaults need to flex; others are fine. This story measures,
tunes, and exposes the right knobs.

## Scope

### In

- **Measure end-to-end latency** in story 02's cross-network rig:
  - Button release → text typed (voice typing).
  - Speech start → first transcript segment visible (meeting).
  - WS-level RTT via `websockets`' ping/pong telemetry (if
    accessible) or a manual roundtrip.
- **Identify which defaults need to grow.** Likely candidates:
  - `ping_timeout` (30 s today) — probably fine; we want to
    tolerate jitter spikes.
  - Reconnect floor (0.5 s today) — probably fine.
  - `AUDIO_QUEUE_MAXSIZE` (500 chunks today) — may need to grow if
    HoldSpeak's drain is briefly slower under WAN load.
- **Expose tunable knobs in `bridge.env`.** New env vars for
  whichever values warrant runtime tuning (likely
  `WS_PING_INTERVAL`, `WS_PING_TIMEOUT`, `AUDIO_QUEUE_MAX`). Mirror
  in `bridge.env.example` with comments explaining when to flex
  each one.
- **Document the latency budget** in the runbook — what to expect
  on LAN vs. Tailscale vs. Cloudflare Tunnel vs. cellular hotspot.

### Out

- Adaptive tuning (auto-grow queue under sustained backpressure).
  Static config is enough for v1.
- Bandwidth limiting / opus encoding to reduce wire bytes —
  AIPI-Lite's audio is already 256 kbps which is fine for any
  modern broadband or 4G+. Revisit only if cellular use surfaces
  problems.
- Deep WS-protocol-level changes (compression, multiplexing). Not
  needed at this scale.

## Acceptance Criteria

- [ ] Latency measurements captured in `evidence-story-03.md` for at
  least two scenarios (LAN baseline + one cross-network path).
  Data points: button release → text typed (voice typing); speech
  start → segment visible (meeting); steady-state ping RTT.
- [ ] At least one tunable env var added (likely
  `AUDIO_QUEUE_MAX`) with a sensible default + documented
  override. `bridge.env.example` updated.
- [ ] Reconnect resilience tested across a network drop on the
  bridge → HoldSpeak path: drop the network for 10 s, restore,
  verify voice typing works again without restarting the bridge.
- [ ] If any default *needed* to change for cross-network to work
  acceptably, document why in `evidence-story-03.md`. Defaults
  should not regress LAN behaviour.

## Test Plan

- **Manual** — measurement-heavy:
  1. With the cross-network rig from story 02 standing:
  2. Run a 10-utterance voice-typing session, log button-release
     timestamps and text-appears timestamps. Compute mean +
     p95 latency.
  3. Same rig, start a meeting; speak in 5-second bursts; log
     segment-visible timestamps. Compute speech-to-segment latency.
  4. Drop the bridge's network for 10 s with `iptables` or by
     toggling WiFi; restore; verify the bridge reconnects + voice
     typing works again.
- **Unit:** none. This story is pure measurement + config tuning.

## Notes

- The `websockets` library exposes ping/pong stats via the
  `ConnectionState` object on the connection — if we want
  fine-grained RTT logging it's available. v1 can rely on
  user-visible end-to-end latency instead.
- HoldSpeak's `RemoteAudioRecorder` enforces a 2 s queue cap on the
  *server* side; if the bridge's queue is much larger and the WAN
  drains slowly, frames get dropped server-side first. Make sure
  the bridge's `AUDIO_QUEUE_MAX` doesn't mask server-side
  backpressure — the existing `audio.queue.overflow` log on the
  bridge side is the right surface to watch.
- When latency is bad, the user-facing symptom is likely "I pressed
  the button, said something, released, and the text took 5 seconds
  to appear." Make sure the runbook expects this and doesn't claim
  LAN-tier latencies for WAN setups.
