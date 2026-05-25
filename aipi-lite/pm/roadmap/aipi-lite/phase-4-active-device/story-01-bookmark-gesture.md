# AIPI-4-01 — Bookmark Gesture (Left-Button Quick-Tap During Meeting)

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-2 (full phase — bridge spine + LCD pushback)
- **Unblocks:** —
- **Owner:** karol

## Problem

During meetings the user might want to mark an important moment (an action item, a key insight, a moment to revisit) without breaking flow. HoldSpeak's `MeetingSession.add_bookmark` server hook (HS-14-07) already accepts `{"type":"event","name":"long_press"}` from devices and persists a meeting-relative bookmark — but **no AIPI gesture currently emits the frame**. The hook is dormant and the device's most distinctive UX (it's in your hand, not your keyboard) goes unused.

## Scope

### In

- New firmware gesture: **left-button short-press** (press + release within 500 ms). Distinct from the existing left-button long-press (AP-mode entry, owned by AIPI-1-05).
- Bridge subscribes to the left-button binary_sensor state via aioesphomeapi; debounces; classifies short vs. long.
- Bridge gates emission on **in-meeting state**, derived from sticky activity matching `Recording*` (no new state needed; the LCD pushback substrate already tracks this).
- On qualifying short-press, emit `EventFrame(type="event", name="long_press", at=<unix_ms>)` to HoldSpeak. Wire name `long_press` matches HS-14-07's expected vocabulary regardless of our local gesture name; renaming the wire vocabulary is HoldSpeak protocol-doc territory and out of scope here.
- LCD flash: `Bookmark  \!//` for 1.5 s via the existing activity-flash mechanism (the symbol map already includes `Bookmark` from AIPI-2-07).
- `EventFrame` Pydantic model — verify it already exists in `holdspeak_proto.py` (story 01 stubbed it); add tests if absent.
- Unit tests: gating (in-meeting vs. not-in-meeting), debounce timing, frame round-trip.

### Out

- Other event names (`bookmark_long`, `pause`, etc.) — start with one.
- Server-side acknowledgement of the bookmark — bridge fire-and-forgets; if HS adds an ack frame later, that's a separate story.
- Renaming the wire event from `long_press` → `bookmark` — requires paired HoldSpeak protocol-doc work.
- Bookmark from outside a meeting — short-press outside a meeting routes to AIPI-4-06 (last-transcript gesture) per that story.

## Acceptance criteria

- [x] **Design decision (2026-05-10):** classifier lives bridge-side, not firmware-side. `aipi.yaml` already exposes `left_button` as a binary_sensor with a 50 ms debounce filter (AIPI-1-05) — the bridge subscribes to its raw state via `subscribe_states` and does its own short-vs-long classification against `BOOKMARK_PRESS_THRESHOLD_MS=500`. Long-press AP-mode-entry stays firmware-owned (uses ESPHome's native long-press detection on the same binary_sensor and runs locally; doesn't depend on the bridge). No `aipi.yaml` change required.
- [x] Bridge subscribes to left-button state via aioesphomeapi `subscribe_states`; entity key cached on connect via `_cache_button_entities` (sibling helper to `_cache_lcd_services`); classifier in `_handle_left_button_state` uses 500 ms threshold.
- [x] Short-press while in-meeting (HoldSpeakLeg's sticky text starts with `Recording`) emits `EventFrame(type="event", name="long_press", at=<unix_seconds_float>)` to HoldSpeak via the existing `control_queue`. Wire vocabulary `long_press` matches HS-14-07's expected name regardless of our local "bookmark" gesture name. Note: `at` is float seconds (`time.time()`), not unix-ms — matches the existing `holdspeak_proto.EventFrame.at: float | None` shape and HoldSpeak server-side conventions.
- [x] Short-press while not in-meeting: logged as `event.suppressed` with `reason="not_in_meeting"`; no frame emitted. Same suppression path triggers if `is_in_meeting` callback is unwired (conservative default).
- [x] LCD flash painted via `HoldSpeakLeg.paint_bookmark_flash()` — `Bookmark  \!//` for `BOOKMARK_FLASH_MS=1500`; reverts to sticky activity via the existing `_paint_activity` state machine. Sticky text is preserved across the flash (verified in `test_holdspeak_paint_bookmark_flash_does_not_overwrite_sticky`).
- [x] Tests: `tests/test_bookmark_gesture.py` — 23 cases covering `_cache_button_entities` (resolve / missing / lookup error), `_handle_state_change` dispatch (uncached / other-key / left-button-press), `_handle_left_button_state` classifier (press timestamp, short-press spawn, long-press no-spawn, release-without-press, press-press-release latest-wins, post-release timestamp clear), `_fire_bookmark_attempt` gating + emission (in-meeting emit + flash + timestamp; outside-meeting suppression; unwired-callback suppression; flash-error swallowing), `HoldSpeakLeg.is_in_meeting` (default / Recording / Listening / Ready), `HoldSpeakLeg.paint_bookmark_flash` (callback path + sticky preservation). One file rather than the originally-planned `test_event_frame.py` + `test_bookmark_gating.py` split — `EventFrame` model round-trip is already covered in `tests/test_models.py` from AIPI-2-01.
- [x] **Live-hardware verification (2026-05-10):**
  - `python -m bridge --press left-short` during an active HoldSpeak meeting → bookmark appeared in `/api/meetings/{id}` at `timestamp: 15.62406s` with auto-formatted label `Bookmark @ 00:15`. Bridge log: `event.bookmark.emitted` at 21:01:41.599; HoldSpeak server log: bookmark `created_at: 2026-05-10T15:01:41.606825` (~7 ms server-processing delta). See `evidence-story-01.md` for the full trace.
  - LCD flash painted: `update_screen.ok msg="Bookmark  \!//"` at 21:01:41.599 (local flash from `paint_bookmark_flash`); HoldSpeak then pushed back its own confirmation `status text="Bookmark @ 16s" ttl_ms=2500` which the bridge re-painted as `Bookmark @ 16s  \!//`; sticky `Recording 00:00   *` reverted at 21:01:44.108 (TTL expired). The bidirectional pushback validates AIPI-2-07's sticky/flash/revert state machine alongside the bookmark gesture.
  - Out-of-meeting suppression: 5 separate `--press left-short` invocations with no active meeting all logged `event.suppressed reason=not_in_meeting`; no transcript bookmark generated.

## Test plan

- **Unit:** `EventFrame` round-trip; gating logic (mock sticky-activity state); debounce thresholds.
- **Integration:** fake `websockets.serve` records emitted event frames; bridge driver simulates short-press while sticky activity is `Recording`.
- **Manual:**
  1. Start a meeting from HoldSpeak (`POST /api/meeting/start {"devices":["aipi-1"]}`).
  2. Wait for `Recording...` to appear on LCD activity slot.
  3. Quick-tap the left button.
  4. Verify LCD flashes `Bookmark  \!//`; verify HoldSpeak meeting view shows a bookmark at the corresponding meeting-relative timestamp.
  5. Outside a meeting: quick-tap the left button → expect no bookmark emission; expect `event.suppressed` log line.

## Notes

- **Wire-vs-local-name divergence is deliberate.** Our local gesture is "short-press"; HoldSpeak's wire vocabulary is `long_press` (a name baked in by HS-14-07 before we shipped a gesture). We honor HoldSpeak's vocabulary on the wire and document the gesture separately. If HoldSpeak ever ships a `bookmark` wire alias, switch then.
- **Clock skew tradeoff:** the `at` timestamp is the bridge's `time.time_ns() // 1_000_000`. If the bridge host's clock skews from HoldSpeak's host clock (typically same machine, but not always), bookmarks land at slightly wrong meeting-relative offsets. Acceptable for v1.
- **Long-press timing in firmware:** must start counting from press-edge; short-press fires on release-before-threshold; long-press (AP-mode) fires on threshold-elapsed-while-pressed. ESPHome's `binary_sensor.on_multi_click` filter primitives cover this cleanly.
- **Why left-button, not right:** right-button is voice typing (press-and-hold semantic); a quick-tap on right would conflict with the press-and-release for voice typing. Left button is currently single-purpose (AP-mode entry on long-press), so adding short-press is non-conflicting.
