# HS-17-07 — Meeting Intel Pushback to Device LCD

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-14-07 (device-status substrate); HS-17-05 (Recording-tick + status-emitter pattern)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

When a HoldSpeak meeting ends, the AIPI-Lite device's LCD shows `Saving meeting...` → reverts to `Ready` within a few seconds. **The intel pipeline (topic extraction, action items, summary) then runs invisibly to the device.** Even though the user is literally holding the artifact that captured the meeting, they get no feedback when intel completes or what it found.

User feedback 2026-05-10, post-AIPI-4-10 close: *"if meeting intel arrives - are we updating our screen? For some time? So we can actually verify that? And then go back to us with 'Ready' kind of thing? COME THE FRIG ON!"*

This story closes the gap: HoldSpeak's intel-completion code path pushes a sequence of status frames to attached devices, gives the user a beat to see the meeting's payload, then settles back to a quiescent sticky.

## Scope

### In

- **Intel-queued status** — fired when a meeting stops and the intel job lands on the queue (immediate; not gated on intel actually starting). Text: `Intel queued`, sticky (`ttl_ms: 0`).
- **Intel-processing status** — fired when the worker dequeues the job. Text: `Working on intel`, sticky.
- **Intel-ready status sequence** — fired when intel completes. A rotation of flashes (each `ttl_ms: 4000`):
  - `Topic: <T1>` (first topic, truncated to 30 chars).
  - For each top action item (limit 3): `Action: <truncated>`.
  - `Summary: <first 30 chars of summary>`.
  - End with a sticky `Ready  <LV_SYMBOL_OK>` to revert to neutral.
- **Intel-failed status** — if the intel pipeline fails or is unavailable (e.g., llama-cpp-python not installed, OpenAI key missing). Text: `Intel n/a · <reason>` truncated, flash `ttl_ms: 5000`.
- Emitter call sites in `holdspeak/intel.py` / `holdspeak/intel_queue.py` (or wherever the lifecycle hooks live).
- Integration test in `tests/integration/test_device_intel_pushback.py`: fake WS records the sequence over a simulated meeting with mocked intel completion; asserts the expected text/ttl_ms ordering.
- `docs/DEVICE_PROTOCOL.md` extended with the intel-status rows.

### Out

- Per-segment transcript snippets during the *active* meeting (separate story HS-17-08 candidate — much higher frame rate, different emitter).
- Bookmark-count tickers during recording (could fold into HS-17-05's Recording-tick payload — see HS-17-06's alternation pattern).
- Action-item detection *during* a meeting (MIR-01 realtime — HS-17-09 candidate).
- Multi-device coordination events (HS-17-10 candidate).
- Custom user-defined intel templates pushed to device (over-engineered for v1).

## Acceptance Criteria

- [ ] `holdspeak/device_status.py` (or a new sibling module) gains an `intel_queued` / `intel_started` / `intel_ready` / `intel_failed` emit set; `DeviceStatusEmitter.broadcast(...)` already does the cross-thread send.
- [ ] Intel queue hook fires `Intel queued` immediately on meeting stop.
- [ ] Intel worker hook fires `Working on intel` when dequeue starts.
- [ ] Intel completion hook fires the rotation sequence (`Topic` → 3× `Action` → `Summary` → sticky `Ready`).
- [ ] Truncation at 30 chars + `…` for any field exceeding that, verified per-field.
- [ ] Intel-failure path fires a single `Intel n/a · <reason>` flash + ends in `Ready` sticky.
- [ ] Integration test green; covers happy path + failure path + truncation + meeting-without-attached-device (no-op).
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification (with AIPI-Lite hardware + a non-trivial meeting): LCD shows the rotation in order, settles back to `Ready ✓`.

## Test Plan

- **Unit:** truncation helper; sequence builder (given intel result, emit ordered list of status frames).
- **Integration:** `tests/integration/test_device_intel_pushback.py` — fake WS records all status frames over a simulated meeting + intel completion.
- **Manual:** run a meeting on AIPI-Lite, end it, watch LCD as intel processes.

## Notes

- **Sequencing matters.** The rotation pacing is what makes this a feature vs. a wall of text. 4s per flash gives the user time to read; 5 flashes = 20s of "intel parade." Tunable; start at 4s.
- **Sticky-then-rotation pattern.** The sticky `Intel queued` / `Working on intel` are kept briefly so the device shows *something* while intel is running. Then the rotation is a sequence of flashes that revert to a new sticky `Ready` at the end.
- **Failure path is important.** When intel is "queued for later processing: llama-cpp-python is not available" (the literal text from `/api/meetings` for some setups), the device shouldn't be stuck showing `Intel queued` forever. A flash `Intel n/a` then revert is honest UX.
- **Truncation at 30 chars** is the same LCD width budget AIPI-4-06 (last-transcript gesture) uses. Centralize the truncation helper.
- **Per-segment transcript pushback** is the natural follow-up (HS-17-08 candidate). HoldSpeak's MeetingSession knows when each segment finalizes; pushing them as `ttl_ms: 3000` flashes would make the device show what's being typed in real time. Separate story because emitter cadence is much higher (per-segment vs. per-meeting) and needs its own throttling consideration.
