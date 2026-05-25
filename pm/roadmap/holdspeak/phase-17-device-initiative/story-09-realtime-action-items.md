# HS-17-09 — MIR-01 Realtime Action Items to Device LCD

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-14-07 (device-status substrate); MIR-01 (HS-2-* meeting-side multi-intent routing — must be running during the meeting, not deferred)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

MIR-01 (HS-2's meeting-side multi-intent routing) classifies utterances mid-meeting against the user's block taxonomy. When a segment routes as an **action item**, MIR-01 records it server-side — but the device that captured the audio has zero feedback that an action was just spotted. The user has to wait for post-meeting intel (HS-17-07) to find out.

This story closes that loop: when MIR-01 spots an action, the device gets an immediate flash. Turns the device into a live "this just got captured as an action" indicator.

## Scope

### In

- New hook in MIR-01's action-detection code path (`holdspeak/intent_router.py` or the meeting-side equivalent): when a segment is routed as a `block_actions` (or whatever the action block ID is in the project's taxonomy), call `device_status.broadcast(attached_ids, "Action: <truncated>", ttl_ms=4000)`.
- 4s flash so the user has time to read it before it reverts to the Recording-tick sticky.
- Truncation at 30 chars + `…` (same width budget as HS-17-08).
- Symbol: `LV_SYMBOL_BELL` (already in the bridge's `_ACTIVITY_SYMBOLS["Bookmark"]` map) or a new `LV_SYMBOL_FLAG` (U+F024) entry. Bridge-side, add `"Action"` to the symbol map.
- Integration test: fake MIR pipeline → action detection → device sees `Action: <text>` flash.
- `docs/DEVICE_PROTOCOL.md` extended.

### Out

- Non-action MIR routings (decisions, ideas, blockers, etc.). Could be additive follow-ups; v1 ships actions only since they're the most user-relevant.
- Action-item editing / re-classification — the original flash has expired by the time any edit happens; no re-paint needed.
- Action-item count badge in the periodic tick — could combine with HS-17-12 (bookmark-count) into a generalized "annotations counter."
- Deferred (post-meeting) action items — HS-17-07 (intel pushback) covers that path.

## Acceptance Criteria

- [ ] MIR-01 action-routing hook fires `device_status.broadcast(attached_ids, "Action: <truncated>", ttl_ms=4000)` when a segment classifies as an action AND ≥ 1 device is attached.
- [ ] Truncation at 30 chars + `…` for the combined `"Action: <text>"` string.
- [ ] Bridge-side: `"Action"` added to `_ACTIVITY_SYMBOLS` with `LV_SYMBOL_BELL` (or `_FLAG` if a separate icon is desired).
- [ ] Integration test green: simulated meeting with MIR pipeline classifying 2 utterances as actions → device sees 2 `Action:` flashes.
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification: real meeting with action-y utterances ("we need to ship X by Friday", "Karol takes the runbook") → LCD flashes each action.

## Test Plan

- **Unit:** truncation + payload formatting.
- **Integration:** mock MIR with deterministic action routing on specific utterances; fake WS records flashes.
- **Manual:** real meeting on AIPI-Lite + verbalized action items.

## Notes

- **Project taxonomy dependency.** This needs the user to have configured at least one `block_actions`-style block in their MIR config. Without it, MIR routes nothing as actions and this story produces zero flashes. Document the prerequisite.
- **Visual distinguishability.** Action flashes should look different from segment flashes (HS-17-08) — different symbol (bell/flag vs. nothing or audio) gives the user a glance-able cue.
- **MIR-01's deferred path** routes actions post-meeting via the intel pipeline (which then goes through HS-17-07). The realtime path is a separate optional layer — only fires if the MIR config is set to live-route rather than deferred. Document both paths.
- **Combines with HS-17-08** — both are flashes during a meeting. Order matters: if a segment finalizes AND it classifies as an action, we want the action flash (more semantic value), not just the segment flash. Implementation should prefer action-flash and skip the segment-flash for that specific segment.
