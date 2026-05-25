# AIPI-2-07 - HoldSpeak → LCD Pushback (Status Frames + Link Indicator)

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01, AIPI-2-03 (control mapping baseline)
- **Unblocks:** —
- **Owner:** karol

## Problem

Phase 2's original scope explicitly carved LCD status pushback out
("LCD status pushback ... Lands as a dedicated AIPI-2-followup or as
the kickoff of AIPI-3"). HoldSpeak HS-14-07 had shipped, but the
bridge handler for inbound `status` frames was a no-op log stub — so
HoldSpeak was dutifully sending `Recording 12:34` / `Bookmark @ 47s`
/ `Saving meeting...` and the device's LCD silently ate them.

After the protocol-translator spine landed and the LCD UX surface
turned out to be smaller than feared, the followup promoted into a
real story rather than slipping to phase 3.

## Scope

### In

- **Three-zone LCD layout** in `aipi.yaml` with one owner per zone:
  - `mode_label` (top-left, firmware-owned) — physical mode:
    `HOLD` / `CONT` / `AP` / `RST`. Painted by `refresh_mode_label`
    on boot, mode toggle, Wi-Fi events. Bridge never touches.
  - `link_label` (top-right, bridge-owned, **NEW**) — WS state:
    `[--]` / `[..]` / `[OK]`. Painted via the `update_link` API
    service.
  - `ai_response_label` (bottom, bridge-owned) — HoldSpeak status
    text + an ASCII state symbol picked from the leading word.
- **New ESPHome API service `update_link`** in `aipi.yaml` mirroring
  `update_screen` for the new top-right label.
- **Activity state machine in `bridge.holdspeak`** with sticky vs.
  flash semantics: `ttl_ms == 0` replaces the persistent state;
  `ttl_ms > 0` paints, schedules a revert task, then repaints the
  sticky after the timeout. Newest paint cancels any pending revert.
- **Link transitions painted from `HoldSpeakLeg.session()`**:
  `[..]` before `websockets.connect`, `[OK]` after handshake,
  `[--]` in the outer `finally` (covers clean close, abrupt close,
  exception, cancellation). While `reconnect_with_backoff` sleeps
  between attempts the LCD shows `[--]`.
- **ASCII activity-symbol map** keyed on the leading word of
  HoldSpeak's status text, with `─` as the default for unknown
  words (so HoldSpeak can introduce new strings without a bridge
  release):

  | HoldSpeak text starts with | Symbol |
  |---|---|
  | `Listening` | `>>` |
  | `Recording` | ` *` |
  | `Transcribing` | `==` |
  | `Bookmark` | `\!//` |
  | `Saving` | `...` |
  | `Busy` | `[?]` |
  | `Ready` | `─` |
  | (anything else) | `─` |

- **Synthesised activity flashes** for events the server doesn't
  send a `status` frame for:
  - `error: session_busy` → `Busy  [?]` for 3 s.
  - Any other `error` frame → `Error: <reason>  /!\` for 5 s.
- **Generalised callback shape**: `HoldSpeakLeg.on_session_busy` is
  removed; `on_link_update(state)` and `on_activity_update(rendered)`
  replace it. The DeviceLeg method `update_link` mirrors
  `update_screen`; both service handles are cached on connect via
  `_cache_lcd_services`.
- **Documentation refresh** in `docs/HOLDSPEAK_BRIDGE.md` §5: drop
  the "no-op stub" caveat; add the symbol map + the link-state
  legend.

### Out

- LVGL builtin symbols (`LV_SYMBOL_AUDIO`, `LV_SYMBOL_MIC`,
  proper record dot, etc.). The Montserrat 10 font *probably*
  includes them, but unverified on this hardware build — ASCII
  ships first; LVGL symbols are an upgrade path.
- Real-time mic-level meter on the LCD. Constant LCD repaints
  during talk-time would burn ESPHome API roundtrips and might
  fight LVGL's redraw budget. Worth its own story.
- Bridge-driven mode-label override (top-left). Mode is
  firmware-owned by design; if HoldSpeak ever needs to drive the
  top label, that's a separate firmware change adding a third API
  service.
- `event` frames (device → server) for bookmark gestures. Phase 2
  scope still excludes this; HS-14-07's `MeetingSession.add_bookmark`
  hook stays dormant.

## Acceptance Criteria

- [x] `aipi.yaml` defines `link_label` (TOP_RIGHT) + `update_link`
  API service; `mode_label` repositioned to TOP_LEFT with short
  strings (`HOLD` / `CONT` / `AP` / `RST`).
- [x] `bridge.lcd` houses the `_pick_activity_symbol`,
  `_format_activity` helpers + the symbol map + the link-state
  constants.
- [x] `bridge.holdspeak.HoldSpeakLeg` paints the
  `[..]` → `[OK]` → `[--]` transitions across the WS lifecycle.
- [x] Sticky / flash / revert state machine implemented in
  `_paint_activity` + `_revert_activity_after`. New paint cancels
  in-flight revert; revert with no sticky falls back to "Ready".
- [x] `error: session_busy` paints `Busy  [?]` for 3 s; generic
  `error` frame paints `Error: <reason>  /!\` for 5 s.
- [x] `DeviceLeg.update_link` exists; `_cache_lcd_services` caches
  both `update_screen` and `update_link` handles on connect;
  `_on_disconnect` invalidates both.
- [x] Direct dispatch unit tests cover sticky, flash, revert,
  mid-flash cancellation, generic error, session_busy, unknown
  message types, malformed payloads. `tests/test_dispatch.py` (11
  cases) + `tests/test_lcd_helpers.py` (10 cases). Integration
  tests exercise link transitions across clean + invalid-ack
  closes (`tests/test_holdspeak_leg.py` — 4 added).
- [x] `docs/HOLDSPEAK_BRIDGE.md` §5 lists the link states + symbol
  map; the "no-op stub" caveat is removed.
- [ ] Live-hardware verification: status frames painted on the LCD
  during a real meeting, link indicator flips through
  `[..]` → `[OK]` → `[--]` on a HoldSpeak restart. **Pending
  hardware smoke alongside AIPI-2-01..05 verification.**

## Test Plan

- **Unit:** symbol picker (known + unknown words; trailing
  punctuation strip), activity sticky/flash/revert mechanics,
  link transitions on session lifecycle.
- **Integration (fake HoldSpeak):** `tests/test_holdspeak_leg.py`
  asserts `[..]` / `[OK]` / `[--]` paints across a clean + a
  handshake-failure session.
- **Hardware:** start HoldSpeak, run the bridge, watch the LCD;
  confirm status frames produce paints; pkill HoldSpeak, watch
  link drop to `[--]`; restart, watch link flip back. Captured in
  `evidence-story-07.md` at story close.

## Notes

- **Why not also drive the top label from the bridge?** The
  firmware paints `mode_label` based on local state (continuous
  mode + Wi-Fi). If the bridge starts pushing to it, every Wi-Fi
  event becomes a race. Three labels with one owner each
  eliminates the race entirely.
- **Revert default to "Ready" not the empty string.** When a
  flash arrives before any sticky has been seen (immediate
  post-connect), the revert needs a target. Empty would blank
  the line; "Ready" is a sensible default the user can read as
  "nothing to report".
- **ASCII over LVGL symbols** for v1 because Montserrat 10's
  symbol-glyph coverage isn't verified on this hardware build
  yet. A missing glyph renders as `?` or a square — better to
  ship something that always works.
- **Symbol map lives in the bridge, not in HoldSpeak.** HoldSpeak
  keeps its protocol unchanged; the bridge translates leading
  words. New status strings on the server side default to `─`
  until the bridge learns them.
- **Followup that fits naturally here:** mic-level meter. The
  bridge sees every UDP datagram; computing RMS and pushing a
  `=======` bar to the activity slot would make the device feel
  alive. Costs ESPHome API roundtrips per chunk — worth metrics
  before committing.
