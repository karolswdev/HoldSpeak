# Phase 17 — Final Summary

- **Phase opened:** 2026-05-10
- **Phase closed:** 2026-05-10
- **Chunks shipped:** 7

## Goal — was it met?

Original goal:

> Light up the device -> server half of the AIPI-Lite protocol. Phase 14 made the device a remote audio source + a remote LCD; this phase makes the device an active participant that can push state upstream (`device_health`) and request state on demand (`query`).

**Yes.** HoldSpeak now accepts validated `device_health` frames, exposes live battery/RSSI state, answers `query:last_segment` with status frames, renders attached-device health in the dashboard, and documents the wire contract for AIPI-Lite phase 4.

Evidence:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md) ·
[05](./evidence-story-05.md) ·
[08](./evidence-story-08.md) ·
[13](./evidence-story-13.md).

## Exit criteria — final state

- [x] `holdspeak/device_audio_ws.py` accepts `device_health` frames; updates registry and active meeting descriptors — [evidence-story-01](./evidence-story-01.md).
- [x] `holdspeak/device_audio_ws.py` accepts `query:last_segment`; replies with `status` frames — [evidence-story-02](./evidence-story-02.md).
- [x] `docs/DEVICE_PROTOCOL.md` lists `device_health` and `query` schemas, examples, semantics, and error handling — [evidence-story-04](./evidence-story-04.md).
- [x] Dashboard shows attached-device battery/RSSI when present and hides missing values — [evidence-story-03](./evidence-story-03.md).
- [x] HS-17-01..04 stories show `Status: done` with paired evidence files — [evidence-story-04](./evidence-story-04.md).
- [x] `final-summary.md` records the handoff to AIPI-Lite phase 4 — this file.
- [x] Parent roadmap marks HS-17 `done` — `pm/roadmap/holdspeak/README.md`.

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-17-01 | `device_health` frame: schema, handler, state extension, protocol doc | this working set | 2026-05-10 |
| HS-17-02 | `query` frame + `last_segment` case | this working set | 2026-05-10 |
| HS-17-03 | Web UI device-health rendering | this working set | 2026-05-10 |
| HS-17-04 | Protocol-doc consolidation + final summary + phase exit | this working set | 2026-05-10 |
| HS-17-05 | Periodic Recording-tick status emitter | `fe9eb31` | 2026-05-10 |
| HS-17-08 | Per-segment transcript pushback | `6eba45b` | 2026-05-10 |
| HS-17-13 | Transcript noise filter for device LCD pushback | `2a6a476` plus this working set | 2026-05-10 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| HS-17-06 | Meeting title in device status | Nice LCD enrichment, not required to unblock active-device bridge frames. | future device LCD enrichment |
| HS-17-07 | Meeting intel pushback to device LCD | Needs more product design around post-meeting rotation and payload priority. | future device LCD enrichment |
| HS-17-09 | Realtime action items -> LCD flash | Depends on MIR realtime signal quality; not needed for phase 17 protocol close. | future MIR/device bridge phase |
| HS-17-10 | Multi-device join/drop events -> LCD flash | Useful polish but not part of `device_health` / `query` unblock. | future multi-device polish |
| HS-17-11 | Handshake/version startup flash | Firmware UX polish; protocol substrate already works. | future device startup polish |
| HS-17-12 | Bookmark count in Recording-tick payload | Enrichment of an existing ticker; not required for active-device protocol. | future device LCD enrichment |

## Surprises and lessons

- The active-device protocol was small, but state projection mattered. Registry state is canonical; active `MeetingState.devices` is a projection for web/runtime consumers.
- Historical `last_segment` lookup should not be faked. The SQLite `segments` table does not currently persist `device_id`, so v1 correctly answers from the active meeting only.
- Display output needs its own quality rules. The durable transcript remains canonical, while LCD pushback can filter silence/hallucination artifacts and acknowledge word-level noise with `{speaker}: ...`.
- The dashboard can cover this scaffold without a dedicated `/devices` page. Inline attached-device health is enough for phase 17.

## Handoff to AIPI-Lite phase 4

- AIPI-4-05 may move from `blocked` to `backlog`: HoldSpeak now accepts `device_health` frames:
  `{"type":"device_health","battery_pct":84,"rssi_dbm":-57,"at":1234}`.
- AIPI-4-06 may move from `blocked` to `backlog`: HoldSpeak now accepts `query:last_segment` frames and replies with normal `status` frames.
- The wire contract is documented in `docs/DEVICE_PROTOCOL.md` sections `3.5 device_health` and `3.6 query`.
- The executable contract is covered by `tests/unit/test_device_active_frames.py`, `tests/integration/test_device_audio_ingest.py::TestDeviceActiveFrames`, and `tests/integration/test_web_server.py::TestDeviceHealthEndpoint`.
- Cross-repo status edits in the AIPI-Lite repo remain a separate PMO-compliant change.

## Final Asset / Test Posture

- Broad regression: `.venv/bin/pytest -q` — `1774 passed, 21 skipped in 124.09s`.
- Focused device/web regression: `196 passed in 3.53s`.
- HS-17-03 web checks: `7 passed in 0.88s`.
- Web build: `cd web && npm run build` — 7 static pages built into `holdspeak/static/_built/`.
- Diff hygiene: `git diff --check` — passed.
- PMO contract: `.tmp/CONTRACT.md` written with all required boxes checked.
