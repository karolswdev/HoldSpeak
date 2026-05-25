# HS-17-02 — `query` Frame + `last_segment` Case

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-14 (full phase — device WS substrate)
- **Unblocks:** AIPI-4-06 (device-side bridge story)
- **Owner:** karol

## Problem

AIPI-Lite roadmap story AIPI-4-06 wants the device to glance at the last transcript HoldSpeak produced — a quick LCD read-back after the user said something, without looking at the host screen. The device emits a `query` frame; HoldSpeak responds with the segment text as a regular `status` frame which the device's existing dispatch path paints to the LCD with a TTL.

This story owns the **server side**: the `query` frame schema, the `last_segment` lookup, the response. The bridge side (AIPI-4-06) is `blocked` until this lands.

## Scope

### In

- New inbound WS frame type in `holdspeak/device_audio_ws.py`:
  ```
  {"type": "query", "name": "last_segment", "at": int (unix_ms)}
  ```
  Pydantic model with `extra="forbid"` and `name: str`. Dispatch then checks the query name so unknown names can produce a visible status response instead of being rejected before the handler sees them.
- Handler: on receipt of a valid query, look up the "last segment" for this `device_id` and emit a `status` frame:
  ```
  {"type": "status", "text": "<segment text or fallback>", "ttl_ms": 5000}
  ```
- **`last_segment` lookup semantics** — decided in this story:
  - Prefer the most recent **finalized** segment (no in-progress / streaming previews).
  - Source: most-recent **active meeting segment** from this device; else fallback text `No transcript yet`.
  - "From this device" = `device_id` matches the WS-connection's device descriptor.
- Response size: HoldSpeak caps the response string at 500 chars to keep status frames bounded. Device-side LCD fit/scroll behavior remains bridge-owned.
- Unknown query names: HoldSpeak responds with `status` frame `{"text":"Unknown query: <name>","ttl_ms":3000}`. (No silent failure; the device's user gets visible feedback.)
- Concurrency: a `query` arriving while the previous query's response hasn't yet been emitted is fine (responses are independent status frames; no in-flight tracking needed in v1).
- Integration test `tests/integration/test_device_query_last_segment.py`: covers meeting-segment hit, no-recent-transcript fallback, unknown-query-name response.
- Unit tests for the model + the lookup helper.

### Out

- Other query names (`last_meeting`, `current_topic`, `next_action_item`, `current_speaker_label`, …). Each is its own story.
- Request/response correlation (`request_id` field). Not needed for v1 because the bridge gates queries on user input and waits for the next `status` frame; if multi-query patterns emerge, add the field.
- Streaming partial responses (e.g., the segment is still being transcribed; HoldSpeak streams the partial). Out — wait for finalized only.
- Query authorization (what if device A asks for device B's transcript?). Out — devices can only query their own transcripts via the `device_id` constraint above.
- Web UI changes — no web-side render of "device queried for last segment recently."
- Voice-typing transcript lookup. Current HoldSpeak has meeting transcript persistence by device, but phase 17 must not assume a durable per-device voice-typing transcript store exists. Add that store in a separate story before expanding `last_segment` beyond meetings.

## Acceptance Criteria

- [x] `DeviceQueryFrame` Pydantic model defined with `extra="forbid"` and `name: str`; handler dispatches `name=="last_segment"` and returns a visible status frame for unknown names.
- [x] WS handler dispatches `type=="query"` + `name=="last_segment"` to the lookup helper.
- [x] Lookup helper finds most-recent finalized active-meeting segment from `device_id`; returns fallback string when nothing found.
- [x] Response emitted as a `status` frame with `ttl_ms=5000`; text is the segment content (or fallback).
- [x] Unknown query name → `status` frame `{"text":"Unknown query: <name>","ttl_ms":3000}`.
- [x] Malformed `query` frame (missing field, wrong type) logged + dropped; WS stays open (same rule as HS-17-01).
- [x] `docs/DEVICE_PROTOCOL.md` gains a `query` frame section + the `last_segment` case.
- [x] Integration coverage in `tests/integration/test_device_audio_ingest.py` covers query response over a real WS handshake.
- [x] Unit tests cover the model; lookup is covered through the runtime callback path.

## Test Plan

- **Unit:** `tests/unit/test_query_frame_model.py` (Pydantic round-trip + validation); `tests/unit/test_last_segment_lookup.py` (meeting lookup + 60-min window + fallback).
- **Integration:** `tests/integration/test_device_query_last_segment.py` — query paths over a real WS handshake + frame exchange.
- **Manual (post-AIPI-4-06):** complete a meeting on a real AIPI-Lite; exit meeting; short-press left button; verify last segment text appears on LCD within ~1 s.

## Notes

- **Why active-meeting-only in v1:** the current database schema does not persist `TranscriptSegment.device_id`, so a correct historical lookup needs a persistence migration. This story unblocks the active-device bridge path without pretending historical per-device lookup exists.
- **Why `name: str` at the outer model:** unknown names must reach the handler so the device can get a visible "Unknown query" status. Per-query strict schemas can still be applied after dispatch once a query name is recognized.
- **Truncation lives on the device side** by design — the bridge knows the LCD width; HoldSpeak doesn't need to. Keeps HoldSpeak's response shape uniform across query types.
