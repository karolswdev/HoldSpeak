# Phase 17 — Device Initiative

**Last updated:** 2026-05-10 (scaffold tightened after PMO evaluation — not the current HoldSpeak product priority).

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

- [ ] `holdspeak/device_audio_ws.py` accepts `device_health` frames; updates the device registry / attached meeting descriptors; integration test `tests/integration/test_device_health_pushback.py` green.
- [ ] `holdspeak/device_audio_ws.py` accepts `query` frames with `name="last_segment"`; replies with a `status` frame; integration test `tests/integration/test_device_query_last_segment.py` green.
- [ ] `docs/DEVICE_PROTOCOL.md` lists both new frame schemas; section "Frame types" updated with examples + field semantics.
- [ ] Web UI: dashboard / meeting device surfaces show battery + RSSI when present, hide when None — verified in the current web test stack or by manual runtime evidence.
- [ ] All HS-17-01..04 stories show `Status: done` with paired `evidence-story-{n}.md` files.
- [ ] `final-summary.md` records what shipped + the handoff to AIPI-Lite phase 4 (unblocking AIPI-4-05 / AIPI-4-06).
- [ ] HoldSpeak `README.md` phase index flips HS-17 → `done`.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-17-01 | `device_health` frame: schema, handler, state extension, protocol doc | backlog | [story-01-device-health-frame.md](./story-01-device-health-frame.md) | — |
| HS-17-02 | `query` frame + `last_segment` case: schema, handler, lookup logic | backlog | [story-02-query-last-segment.md](./story-02-query-last-segment.md) | — |
| HS-17-03 | Web UI: device-health rendering in meeting view + device list | backlog | [story-03-device-health-ui.md](./story-03-device-health-ui.md) | — |
| HS-17-04 | DoD: protocol-doc consolidation + final-summary + phase exit | backlog | [story-04-dod.md](./story-04-dod.md) | — |
| HS-17-05 | Periodic Recording-tick status emitter (HS-14-07 spec drift, surfaced live 2026-05-10) | done | [story-05-recording-tick-emitter.md](./story-05-recording-tick-emitter.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-17-06 | Meeting title in device status (alternates with Recording-tick payload) | backlog | [story-06-meeting-title-in-status.md](./story-06-meeting-title-in-status.md) | — |
| HS-17-07 | Meeting intel pushback to device LCD (topic/actions/summary rotation post-meeting) | backlog | [story-07-intel-pushback.md](./story-07-intel-pushback.md) | — |
| HS-17-08 | Per-segment transcript pushback (live confirmation channel during meetings) | done | [story-08-per-segment-transcript-pushback.md](./story-08-per-segment-transcript-pushback.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-17-09 | MIR-01 realtime action items → LCD flash | backlog | [story-09-realtime-action-items.md](./story-09-realtime-action-items.md) | — |
| HS-17-10 | Multi-device join/drop events → LCD flash | backlog | [story-10-multi-device-join-drop-events.md](./story-10-multi-device-join-drop-events.md) | — |
| HS-17-11 | Handshake / version startup flash | backlog | [story-11-handshake-version-flash.md](./story-11-handshake-version-flash.md) | — |
| HS-17-12 | Bookmark count in Recording-tick payload | backlog | [story-12-bookmark-count-in-tick.md](./story-12-bookmark-count-in-tick.md) | — |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

Phase opened 2026-05-10 to scaffold the HoldSpeak-side half of AIPI-Lite phase 4. Pickup order: **HS-17-01** (device_health) first because it has the simpler state model + no transcript-lookup design surface; **HS-17-02** (query) second because the "what's the last segment" question opens decisions; **HS-17-03** (UI) third (visible payoff once both substrates are in place); **HS-17-04** (DoD) closes.

This phase is **scaffolded ahead of demand** — AIPI-Lite phase 4's bridge-side stories (AIPI-4-05 / AIPI-4-06) are themselves backlog. Pickup priority for this phase tracks the AIPI-Lite roadmap; no urgency until the device-side stories start moving.

This is **not the current HoldSpeak product phase**. The active product push is project-aware local intelligent typing, captured in [phase 18](../phase-18-intelligent-typing-copilot/). Do not pull HS-17 unless the user explicitly prioritizes AIPI-Lite hardware / active-device work.

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
