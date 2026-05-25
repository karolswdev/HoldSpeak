# Phase 17 — Device Initiative

**Phase closed:** 2026-05-10. See [final-summary.md](./final-summary.md). This file is now frozen per PMO contract §6.

## Goal

Light up the **device → server** half of the AIPI-Lite protocol. Phase 14 made the device a remote audio source + a remote LCD; this phase makes the device an **active participant** that can push state upstream (`device_health`) and request state on demand (`query`). The two new frame types unlock AIPI-Lite phase 4 — the device-side roadmap's "Active Device" phase — which has bridge-side stories sitting `blocked` until HoldSpeak ships the paired schemas + handlers.

This phase is the **sibling of HS-14** (audio + status substrate) rather than a successor to it. It does not depend on HS-15 (cross-network); it can ship on the same LAN-local substrate phase 14 already provides.

## Scope

### In

- New device → server frame: `{"type":"device_health","battery_pct":int,"rssi_dbm":int,"at":int}`. Server handler updates the live device registry descriptor; active meeting state snapshots expose the same fields when a device is attached. State exposed via existing runtime/meeting APIs plus a new `GET /api/devices/health` (or equivalent) read endpoint.
- New device → server frame: `{"type":"query","name":"last_segment","at":int}`. Server handler looks up the most recent finalized meeting segment from this `device_id` and replies with a regular `status` frame carrying the segment text + `ttl_ms=5000`.
- Protocol documentation: `docs/DEVICE_PROTOCOL.md` (owned by HS-14-08) extended with both new frame schemas; backwards-compatible additions (no breaking changes to existing frames).
- Web UI affordance: current dashboard/meeting device surfaces render `battery_pct` and `rssi_dbm` when available; hidden when `None`. Minimum-viable styling, not a polish pass.
- Integration tests against a fake WS client covering both new frame paths + the lookup logic for `last_segment` resolution.
- Final-summary documenting handoff back to AIPI-Lite phase 4 (the unblock action for AIPI-4-05 / AIPI-4-06).

### Out

- Additional query names (`last_meeting`, `current_topic`, `next_action_item`, etc.) — each is its own story when AIPI-Lite needs it. Phase 17 ships `last_segment` only.
- Battery/RSSI alerting (HoldSpeak warning the user when a device is below 10 %) — UI consideration for a follow-up; out of scope here.
- Cross-network transport — HS-15 owns that.
- Request/response correlation (`request_id` field on `query` frames). Bridge-side AIPI-4-06 doesn't need it; revisit if multi-query patterns emerge.
- Persistent device-health history. Phase 17 stores last-known values in memory; a time-series for charging-curve analytics is future work.

## Exit criteria (evidence required)

- [x] `holdspeak/device_audio_ws.py` accepts `device_health` frames; updates the device registry / attached meeting descriptors; integration coverage is in `tests/integration/test_device_audio_ingest.py`.
- [x] `holdspeak/device_audio_ws.py` accepts `query` frames with `name="last_segment"`; replies with a `status` frame; integration coverage is in `tests/integration/test_device_audio_ingest.py`.
- [x] `docs/DEVICE_PROTOCOL.md` lists both new frame schemas; section "Frame types" updated with examples + field semantics.
- [x] Web UI: dashboard / meeting device surfaces show battery + RSSI when present, hide when None — verified by current web test stack and build.
- [x] All HS-17-01..04 stories show `Status: done` with paired `evidence-story-{n}.md` files.
- [x] `final-summary.md` records what shipped + the handoff to AIPI-Lite phase 4 (unblocking AIPI-4-05 / AIPI-4-06).
- [x] HoldSpeak `README.md` phase index flips HS-17 → `done`.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-17-01 | `device_health` frame: schema, handler, state extension, protocol doc | done | [story-01-device-health-frame.md](./story-01-device-health-frame.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-17-02 | `query` frame + `last_segment` case: schema, handler, lookup logic | done | [story-02-query-last-segment.md](./story-02-query-last-segment.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-17-03 | Web UI: device-health rendering in meeting view + device list | done | [story-03-device-health-ui.md](./story-03-device-health-ui.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-17-04 | DoD: protocol-doc consolidation + final-summary + phase exit | done | [story-04-dod.md](./story-04-dod.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-17-05 | Periodic Recording-tick status emitter (HS-14-07 spec drift, surfaced live 2026-05-10) | done | [story-05-recording-tick-emitter.md](./story-05-recording-tick-emitter.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-17-06 | Meeting title in device status (alternates with Recording-tick payload) | backlog | [story-06-meeting-title-in-status.md](./story-06-meeting-title-in-status.md) | — |
| HS-17-07 | Meeting intel pushback to device LCD (topic/actions/summary rotation post-meeting) | done | [story-07-intel-pushback.md](./story-07-intel-pushback.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-17-08 | Per-segment transcript pushback (live confirmation channel during meetings) | done | [story-08-per-segment-transcript-pushback.md](./story-08-per-segment-transcript-pushback.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-17-09 | MIR-01 realtime action items → LCD flash | backlog | [story-09-realtime-action-items.md](./story-09-realtime-action-items.md) | — |
| HS-17-10 | Multi-device join/drop events → LCD flash | backlog | [story-10-multi-device-join-drop-events.md](./story-10-multi-device-join-drop-events.md) | — |
| HS-17-11 | Handshake / version startup flash | backlog | [story-11-handshake-version-flash.md](./story-11-handshake-version-flash.md) | — |
| HS-17-12 | Bookmark count in Recording-tick payload | backlog | [story-12-bookmark-count-in-tick.md](./story-12-bookmark-count-in-tick.md) | — |
| HS-17-13 | Transcript noise filter for device LCD pushback | done | [story-13-transcript-noise-filter.md](./story-13-transcript-noise-filter.md) | [evidence-story-13](./evidence-story-13.md) |
| HS-17-14 | "Heard but filtered" ack marker for word-level Whisper hallucinations | done | [story-14-filter-ack-marker.md](./story-14-filter-ack-marker.md) | [evidence-story-14](./evidence-story-14.md) |
| HS-17-15 | LCD char limit bump (30 → 150) for the wider AIPI-4-12 middle widget | done | [story-15-lcd-char-limit-bump.md](./story-15-lcd-char-limit-bump.md) | [evidence-story-15](./evidence-story-15.md) |
| HS-17-16 | Overlap windows on `MeetingSession` transcription passes (sister of AIPI-4-15) | done | [story-16-overlap-windows.md](./story-16-overlap-windows.md) | [evidence-story-16](./evidence-story-16.md) |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

Phase 17 is closed for the substrate stories (HS-17-01..04). HoldSpeak accepts `device_health` frames, exposes live battery/RSSI state, answers `query:last_segment` over the existing status-frame path, renders attached-device health in the dashboard, and documents the AIPI-Lite phase 4 unblock contract.

**LCD enrichment 2026-05-10 update.** A live AIPI-Lite hardware tuning session (paired with AIPI-Lite phase 4) closed five more stories beyond the substrate:

- **HS-17-07** — Meeting intel pushback. Paged-rotation design (Topics → Actions → Summary, 4 s dwell per page on a daemon thread). Lives in `device_status.build_intel_pages` + `push_intel_to_devices`; wired to `_on_meeting_intel` in `web_runtime`. Demoed live via probe push; pending live verification with a real intel-completion event once a non-llama-cpp provider is available.
- **HS-17-13** — Whisper hallucination filter (already shipped earlier in session).
- **HS-17-14** — "Heard but filtered" ack: word-level hallucinations (real audio, garbage transcription) now push `{speaker}: …` to the LCD so the user gets feedback that they were heard. Pure silence still skips.
- **HS-17-15** — `LCD_TEXT_MAX_CHARS` bumped 30 → 150 to match AIPI-4-12's wider middle widget.
- **HS-17-16** — Overlap windows on `MeetingSession._transcribe_chunks`: each pass prepends the last 1.5 s of the previous pass's audio so sentences spanning a 10 s `TRANSCRIBE_INTERVAL` boundary don't get cut mid-thought. Sister story to AIPI-4-15 (filed on the AIPI-Lite side too because the user-visible UX problem surfaced via the device LCD).

Backlog remaining: **HS-17-06** (meeting title in status), **HS-17-09** (realtime action items → LCD), **HS-17-10** (multi-device join/drop events → LCD), **HS-17-11** (handshake/version startup flash), **HS-17-12** (bookmark count in Recording-tick).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `last_segment` semantics ambiguous (active meeting vs. saved meeting; recency window; per-session vs. global) | medium | Story HS-17-02 is meeting-segment-only for v1. Voice-typing history is excluded unless a durable per-device dictation transcript store exists by implementation time. | If field-use surfaces wrong-segment fetches, raise a follow-up to add explicit source filtering or a separate voice-typing transcript store |
| `device_health` frame frequency causes server-state churn (many small writes to MeetingState) | low | Bridge-side cadence is ≤ 1 frame/min/device by AIPI-4-05's contract; HoldSpeak just stores last value, no time-series | If churn becomes meaningful, add a debounce on the server side |
| Backwards-incompatible protocol additions break older AIPI-Lite bridges that don't know `device_health` | low | New frames are additive; older bridges never emit them; older HoldSpeak versions with `extra="forbid"` would reject — but AIPI-2's bridge gracefully handles rejection per AIPI-4-05's design | If field deploys mix old + new versions, document the version-skew matrix |
| Web UI device-health rendering relies on a sensible "None" rendering that doesn't suggest "broken" | low | Story HS-17-03 specifies "hide when None" rather than "show `--`"; pattern matches existing meeting-data nullability handling | If users misread the hidden state, swap to `--` placeholder |

## Decisions made

- 2026-05-10 — **HS-17 is the sibling of HS-14, not a successor to HS-15.** Active-device upstream frames are LAN-local and don't depend on cross-network transport. Pairs with AIPI-Lite phase 4 (parallel to AIPI-3 cross-network in the device-side roadmap).
- 2026-05-10 — **Ship `last_segment` only in this phase**; other query names get their own stories when AIPI-Lite needs them. Avoids speculative protocol surface.
- 2026-05-10 — **Reuse the existing `status` frame for `query` responses** rather than introducing a `query_response` frame type. The bridge's existing dispatcher handles `status` cleanly with TTL semantics; the cost (bridge can't disambiguate query response from spontaneous status) is acceptable for v1.
- 2026-05-10 — **Keep HS-17 scaffolded, not current.** PMO evaluation found it directionally useful but lower priority than project-aware intelligent typing. Phase 18 owns the current product push.

## Decisions deferred

- Persistent device-health history (charging-curve analytics; battery-life trend per device) — gated on whether users ask for it.
- Battery/RSSI alerting in the HoldSpeak web UI — UX consideration for a follow-up; phase 17 stops at "render the values when available."
- Additional query types (`last_meeting`, `current_topic`, `next_action_item`) — gated on AIPI-Lite phase-4 follow-ups; each is small but each is its own story.
- Request/response correlation on `query` frames — revisit if multi-query patterns emerge.
