# AIPI-4-11 — Middle LCD Zone for Transient Flashes

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-2-07 (three-zone LCD substrate); AIPI-4-08 + AIPI-4-10 (republish patterns)
- **Unblocks:** —
- **Owner:** karol

## Problem

The LCD currently has three zones:

- **Top-left:** mode label (`HOLD` / `CONT` / `AP` / `RST`), firmware-owned.
- **Top-right:** link indicator (LV_SYMBOL_WIFI / LV_SYMBOL_REFRESH / LV_SYMBOL_CLOSE post-AIPI-4-09), bridge-owned.
- **Bottom:** activity slot (`Recording 04:25  ` / per-segment flashes / bookmark flashes / etc.), bridge-owned via `update_screen`.

User-observed 2026-05-10, just after HS-17-08 (per-segment transcript pushback) landed: *"our 5 second updates always win and overwrite what the screen was showing. Don't we have a 'center' text area? Or just the top and bottom?"*

The activity slot is the catch-all for both **persistent state** (Recording-tick every 5s, HS-17-05) and **transient flashes** (per-segment text, bookmark confirmations, session_busy, error). When a flash lands and a 5s tick fires within its TTL, the tick wins and the user never finishes reading the flash. The `_paint_activity` state machine respects TTL but only against `_paint_activity` itself — a new sticky from HoldSpeak overrides.

The LCD is 128×128. Between the top row (mode + link, ~12 px) and the bottom row (activity, ~12 px), there's ~100 px of unused vertical space. Adding a dedicated middle zone separates the two content lifetimes cleanly: **persistent → bottom, transient → middle.**

## Scope

### In

**Firmware (`aipi.yaml`):**
- New LVGL label `ai_segment_label` (or `lcd_middle_label`) widget positioned at center of the display, aligned MIDDLE (or MID_LEFT for left-aligned long text).
- Default text empty (no glyph at boot).
- Font: same Montserrat 10 as the rest, possibly slightly larger or different style if it doesn't conflict (single-line constraint).
- New ESPHome API service `update_middle` (mirror of `update_screen` / `update_link`).
- Reflash required.

**Bridge (`bridge/`):**
- `bridge/device.py`: new method `update_middle(text)` mirroring `update_screen` / `update_link`. Service handle cached on connect via the existing `_cache_lcd_services` (extended).
- `bridge/holdspeak.py`: dispatch policy for inbound `status` frames:
  - `ttl_ms == 0` (sticky) → bottom (`update_screen`, current behavior).
  - `ttl_ms > 0` (flash) → middle (`update_middle`). Flash + revert state machine stays in HoldSpeakLeg but paints to the middle, not the bottom.
  - Existing `paint_bookmark_flash` (AIPI-4-01) also paints to middle.
  - `error: session_busy` / generic `error` flashes go middle.
- New optional callback `on_middle_update` on HoldSpeakLeg.
- `cli.py`: wires `device.update_middle` to `holdspeak.on_middle_update`.

**Tests:**
- `tests/test_lcd_zones.py` — new file. Cover the dispatch policy (sticky → bottom; flash → middle; error → middle).
- Extend existing tests to assert the right zone gets each paint.

**Documentation:**
- `docs/HOLDSPEAK_BRIDGE.md` / `docs/LCD_SYMBOLS.md` updated with the three-zone layout description.

### Out

- Multi-line text in the middle zone. Single line, truncated to LCD width (same 30 chars as the bottom).
- Color-coded zones (LCD is monochrome).
- Animated transitions between zones (LVGL supports them; over-engineered for v1).
- A FOURTH zone. Three is plenty.
- Re-positioning existing widgets. Mode + link stay top, activity stays bottom.

## Acceptance Criteria

- [x] `aipi.yaml` defines `lcd_middle_label` widget (CENTER aligned, 120 px wide, single line) + `update_middle` ESPHome API service. Compiled + OTA-flashed to `aipi-green.local` 2026-05-10.
- [x] `bridge/device.py`: `update_middle(text)` method; `_update_middle_service` cache populated by `_cache_lcd_services`; invalidated on disconnect; `update_middle.service.missing` warning when firmware predates AIPI-4-11.
- [x] `bridge/holdspeak.py`: `_paint_activity` refactored to route by ttl_ms — sticky (ttl=0) → `_call_activity` (bottom); flash (ttl>0) → `_call_middle` (middle). Bookmark flash + error flash + session_busy flash all land in middle. `_revert_activity_after` renamed `_clear_middle_after` (empties middle slot after TTL); the sticky on the bottom is independent and never gets clobbered by a flash.
- [x] `cli.py:_run` adds `_on_middle` async wrapper wired to `device.update_middle`; passes it as `on_middle_update` to `HoldSpeakLeg`.
- [x] Unit tests: `tests/test_dispatch.py` + `tests/test_holdspeak_leg.py` + `tests/test_bookmark_gesture.py` all updated to assert flash → middle, sticky → activity. 145/145 passing; ruff clean.
- [x] Live verification (2026-05-10): meeting on AIPI-Lite hardware, user spoke. Bottom row ticked `Recording 00:00 → 00:01 → 00:02 → ...` once per second (238 ticks over the test meeting); middle row flashed `Karol: stupidly enough that` and `Karol: Okay, it's just a dumb…` then cleared. Zero collision between zones.
- [ ] `docs/HOLDSPEAK_BRIDGE.md` updated with the three-zone layout — **deferred follow-up** (runbook update; not blocking).

## Test Plan

- **Unit:** mock `on_activity_update` + `on_middle_update`; `_paint_activity` with ttl_ms=0 → activity called, middle not. ttl_ms=3000 → middle called, activity not. Revert task after flash → middle painted with empty / previous-middle-sticky.
- **Integration:** existing `test_holdspeak_leg.py` fake-WS tests extended to assert middle paints alongside the activity paints they already check.
- **Live:** meeting with attached device → segments appear in middle, Recording-tick in bottom, both visible simultaneously.

## Notes

- **Why split sticky vs. flash by zone, not by content type?** TTL is the cleanest signal: HoldSpeak's frame schema already carries it, no new protocol surface. Content-type-based routing (e.g., "Bookmark" → bookmark zone) would require a richer protocol or content-introspection in the bridge.
- **The middle zone's "sticky" semantic.** Within the middle zone, a flash paints then reverts to *empty* (not to a previous flash) because there's no persistent state for transient content. So the natural revert is to clear. Alternative: keep the last flash visible for N more seconds before clearing — feels like "the last thing said is still there for a moment." Pick during implementation.
- **OTA-friendly for the user.** After AIPI-4-07 added the `ota: - platform: esphome` block, subsequent firmware updates can be OTA from the bridge host. No need to plug USB again for this story.
- **Pairs beautifully with the entire HS-17 LCD-enrichment backlog.** Once the middle zone exists, HS-17-07 (intel pushback rotation), HS-17-09 (action item flashes), HS-17-10 (multi-device join/drop), HS-17-11 (handshake version flash) all naturally use the middle zone. The bottom zone stays the persistent meeting state.
- **User's instinct was right** — when a UX surface has two distinct content lifetimes (persistent vs. transient), they want two zones. Don't bury this insight in a workaround.

## v2 — persist-until-replaced (2026-05-10)

The original v1 design cleared the middle slot to empty after each flash's TTL. Live use surfaced the problem: short flashes vanished before the user finished reading them. v2 reverses the policy — flashes paint to middle and **stay** until another flash replaces them. The `_middle_clear_task` + `_clear_middle_after` machinery was removed from `bridge/holdspeak.py`. Trade-off: stale content can sit on screen indefinitely after a meeting ends; partially mitigated by HS-17-14 word-hallucination ack (so quiet meetings still produce flash events) and AIPI-4-14 cycle (so the user can manually advance views). Tests in `tests/test_dispatch.py` and `tests/test_holdspeak_leg.py` updated to assert the new semantic.
