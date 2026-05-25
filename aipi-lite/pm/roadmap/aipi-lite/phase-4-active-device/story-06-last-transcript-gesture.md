# AIPI-4-06 — "Last Transcript" Gesture (Left-Button Quick-Tap Outside Meeting)

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** in-progress
- **Depends on:** AIPI-4-01 (left-button short-press classification); HoldSpeak `query.last_segment` handler (shipped in HS-17)
- **Unblocks:** —
- **Owner:** karol

## Problem

Mid-conversation, you sometimes want to glance at what HoldSpeak just transcribed without looking at the host screen — to confirm a name was caught, to re-read a phrase, to verify a number. A short-press on the left button **outside** a meeting should query HoldSpeak for the last segment and paint it on the device's LCD.

This makes the device a passive read-only window into HoldSpeak's recent state. Bridge side is straightforward — emit a query, paint the response. HoldSpeak HS-17 shipped the paired `query:last_segment` handler on 2026-05-10, so this story is unblocked and now owns the bridge-side gesture, timeout, and LCD-width behavior.

## Scope

### In

- `QueryFrame` Pydantic model: `type="query"`, `name: Literal["last_segment"]`, `at: int`. (Future query names get added to the literal as new stories ship.)
- Bridge gates emission: short-press only emits a query when sticky activity does **NOT** match `Recording*` (in-meeting → AIPI-4-01 bookmark gesture wins).
- HoldSpeak responds with a regular `status` frame: `{"type":"status","text":"<last_segment_text>","ttl_ms":5000}`. Bridge's existing dispatcher paints it as a flash on the activity slot.
- Bridge truncates inbound text > 30 chars with `…` (LCD width budget).
- Timeout: if HoldSpeak doesn't respond within 2 s, paint `Query timeout` with the error symbol for 3 s.
- Tests: `QueryFrame` round-trip, gating logic, truncation, timeout.

### Out

- More query names (`last_meeting`, `next_action_item`, `current_topic`, etc.) — start with one. Each new query is its own story (small, but its own scope).
- Multi-segment scrollback — single segment only.
- Request/response correlation (e.g., `request_id` field). For v1 the bridge can't tell a "response" from a "spontaneous" status frame, but that's fine — paint either way.
- Server-pushed updates to last segment as it gets refined by HoldSpeak's transcription pipeline. One-shot fetch only.

## Acceptance criteria

- [x] **Blocked-on:** HoldSpeak ships `query` frame schema in `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` AND server-side handler with `case "last_segment":` returning a `status` frame. HS-17 shipped this on 2026-05-10.
- [x] `QueryFrame` Pydantic model added to `holdspeak_proto.py` with `extra="forbid"` and `name: Literal["last_segment"]`.
- [x] Bridge emits the query on left-button short-press when sticky activity does NOT match `Recording*`.
- [x] In-meeting short-press routes to AIPI-4-01 (bookmark gesture); not a query. Decision precedence is encoded in one place (the gesture dispatcher), not duplicated.
- [x] LCD paints the response as a 5 s flash via the existing dispatch path (HoldSpeak sets `ttl_ms`).
- [x] Truncation: text > 30 chars → first 29 chars + `…`. Tested.
- [x] Timeout: no `status` frame received within 2 s after the query → paint `Query timeout` with the error symbol for 3 s.
- [ ] Live verification post-paired: complete a meeting, exit meeting, short-press left button, verify last segment text appears on LCD within ~1 s.

## Test plan

- **Unit:** `QueryFrame` round-trip; gating dispatcher (in/out of meeting); truncation logic; timeout state machine.
- **Integration:** fake server replies with status frame after 100 ms; verify LCD paint. Fake server doesn't reply; verify timeout paint.
- **Manual (post-paired):** complete meeting → exit → short-press → observe LCD.

## Notes

- **Dependency on a paired HoldSpeak phase.** Resolved by HoldSpeak HS-17 on 2026-05-10. The bridge now sends the query and relies on the existing status-frame dispatcher for the response.
- **Why use the existing `status` frame for the response, not a new `query_response` frame:** the LCD dispatcher already handles `status` cleanly with TTL semantics; reusing it means zero new dispatch code. The cost is that the bridge can't disambiguate spontaneous status frames from query responses — for v1, both should paint the same way, so the cost is zero.
- **Why no request/response correlation:** the bridge sends one query at a time (gated on user input); HoldSpeak's response is the next status frame within 2 s. Correlation IDs would be over-engineering for the gesture's frequency. Revisit if multi-query patterns emerge.
- **30-char truncation:** the activity slot's width on this LCD with Montserrat 10 fits ~30 chars before wraparound. Empirical from AIPI-2-07 layout work; revisit if hardware changes.
- **Gating dispatcher precedence (in-meeting → bookmark; out-of-meeting → query) lives in one place** — `DeviceLeg._fire_single_tap_attempt`. AIPI-4-14's double-tap classifier remains layered above this and does not change single-tap semantics.
