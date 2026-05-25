# Phase 4 — Active Device

**Last updated:** 2026-05-10 23:10 (post AIPI-4-12/13/14/15 live tuning + commits 768c0b9 / 4b9f18e).

## Goal

Make the AIPI-Lite an *active* participant in HoldSpeak workflows. Today the device is mostly passive — it captures audio, paints whatever HoldSpeak tells it. This phase pushes the device toward initiative + responsiveness: emit meaning upstream (bookmarks, device-health), give the user real-time feedback (mic-level meter, polished symbols), and work in multi-device meetings.

This phase is **a sibling of phase 3, not a successor**. Active-device features are LAN-local and don't depend on cross-network transport. The two phases can ship in parallel; ordering is a scheduling choice, not a dependency.

## Scope

### In

- Bookmark gesture: left-button quick-tap during a meeting → outbound `event.long_press` frame → HS-14-07's dormant `MeetingSession.add_bookmark` server hook lights up.
- Mic-level meter: bridge computes RMS over UDP datagrams (~8 Hz) and pushes a bar to the LCD activity slot during sessions, **gated on a measurement spike** (API roundtrip cost is the open question).
- Multi-device meeting verification: two AIPI-Lites in one meeting; per-device-label discipline; recovery semantics.
- LVGL builtin symbols: replace ASCII activity glyphs with `LV_SYMBOL_*` constants where Montserrat 10 covers them on this hardware build.
- Battery + WiFi-RSSI pushback: device → server `device_health` frame on threshold-cross + 60s heartbeat. **Unblocked by HoldSpeak HS-17; bridge work still pending.**
- "Last transcript" gesture: left-button quick-tap *outside* a meeting → outbound query → HoldSpeak responds with last segment text → bridge paints to LCD. **Bridge-side implementation in progress; live verification pending.**

### Out

- Wake-word / VAD — phase 5.
- Cross-network transport — phase 3.
- Continuous-mode redesign — still deferred from phase 2.
- Mic-meter during meetings — only during voice-typing sessions (cost concern).
- More than 2 devices in multi-device verification.
- Custom HoldSpeak status-frame schemas (e.g., word-by-word streaming) — deferred pending field experience.

## Exit criteria (evidence required)

- [ ] AIPI-4-01: hardware short-press left-button during a real meeting → bookmark visible in HoldSpeak transcript at correct timestamp.
- [ ] AIPI-4-02: spike measures API roundtrip; if p95 < 50 ms ship meter at 8 Hz; 50–100 ms drop to 4 Hz; > 100 ms close as `infeasible at scale` with notes.
- [ ] AIPI-4-03: 2 AIPI-Lites in one meeting; transcripts correctly labeled per-device; one-bridge-crash-mid-meeting recovery.
- [ ] AIPI-4-04: verified-rendered symbol set documented + applied in `bridge/lcd.py`; ASCII fallback retained for symbols that don't render.
- [ ] AIPI-4-05: bridge-side ready (Pydantic model + emission cadence + tests) when HoldSpeak's reciprocal handler ships; live verification post-paired.
- [ ] AIPI-4-06: bridge-side ready (query frame + truncation + dispatch) when HoldSpeak's reciprocal handler ships; live verification post-paired.
- [ ] Runbook updated: multi-device section, bookmark-gesture section, mic-meter-mode section.
- [ ] All non-blocked stories ship with paired `evidence-story-{n}.md` files.
- [ ] `final-summary.md` records the blocked items as handoff to a future paired-HoldSpeak phase.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AIPI-4-01 | Bookmark gesture (left-button quick-tap during meeting) | done | [story-01-bookmark-gesture.md](./story-01-bookmark-gesture.md) | [evidence-story-01](./evidence-story-01.md) |
| AIPI-4-02 | Mic-level meter on LCD activity slot | backlog | [story-02-mic-level-meter.md](./story-02-mic-level-meter.md) | — |
| AIPI-4-03 | Multi-device meeting verification | backlog | [story-03-multi-device-meetings.md](./story-03-multi-device-meetings.md) | — |
| AIPI-4-04 | LVGL builtin symbols for activity slot | done | [story-04-lvgl-builtin-symbols.md](./story-04-lvgl-builtin-symbols.md) | [evidence-story-04](./evidence-story-04.md) |
| AIPI-4-05 | Battery + RSSI pushback (device → server) | backlog | [story-05-battery-rssi-pushback.md](./story-05-battery-rssi-pushback.md) | — |
| AIPI-4-06 | "Last transcript" gesture (left-button quick-tap outside meeting) | done | [story-06-last-transcript-gesture.md](./story-06-last-transcript-gesture.md) | [evidence-story-06](./evidence-story-06.md) |
| AIPI-4-07 | Remote gesture simulation services + bridge CLI (dev infra for hardware verification) | done | [story-07-remote-gesture-simulation.md](./story-07-remote-gesture-simulation.md) | [evidence-story-07](./evidence-story-07.md) |
| AIPI-4-08 | Link state re-trigger on device reconnect (bug from 2026-05-10 hardware smoke) | done | [story-08-link-state-retrigger.md](./story-08-link-state-retrigger.md) | [evidence-story-08](./evidence-story-08.md) |
| AIPI-4-09 | LCD-wide LVGL polish (link indicator + mode label) | in-progress | [story-09-lcd-wide-lvgl-polish.md](./story-09-lcd-wide-lvgl-polish.md) | — |
| AIPI-4-10 | Activity sticky re-publish on device reconnect (same race-class as AIPI-4-08, surfaced 2026-05-10) | done | [story-10-activity-republish.md](./story-10-activity-republish.md) | [evidence-story-10](./evidence-story-10.md) |
| AIPI-4-11 | Middle LCD zone for transient flashes (separate slot for flashes vs. Recording-tick; v2 persist-until-replaced) | done | [story-11-middle-lcd-zone.md](./story-11-middle-lcd-zone.md) | [evidence-story-11](./evidence-story-11.md) |
| AIPI-4-12 | Multi-line middle widget + montserrat_8 + scroll bottom (LCD density pass) | done | [story-12-lcd-density-pass.md](./story-12-lcd-density-pass.md) | [evidence-story-12](./evidence-story-12.md) |
| AIPI-4-13 | TX-arrow widget (top-right) for voice-typing state; stop clobbering bottom slot | done | [story-13-tx-arrow-widget.md](./story-13-tx-arrow-widget.md) | [evidence-story-13](./evidence-story-13.md) |
| AIPI-4-14 | Double-tap left-button cycles meeting-stat views (Numbers/Speakers/Intel) | done | [story-14-double-tap-cycle.md](./story-14-double-tap-cycle.md) | [evidence-story-14](./evidence-story-14.md) |
| AIPI-4-15 | Overlap windows on transcription passes — eliminate mid-sentence cuts at 10 s boundaries (HoldSpeak side) | done | [story-15-overlap-windows.md](./story-15-overlap-windows.md) | [evidence-story-15](./evidence-story-15.md) |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

Phase opened 2026-05-10 immediately after phase 2 closed.

**AIPI-4-07 + AIPI-4-01 shipped 2026-05-10 with full live-hardware verification.** The user plugged in the device + USB + ran HoldSpeak; the bridge + a remote-control CLI drove an end-to-end smoke. Bookmark gesture now demonstrably works: `--press left-short` during a meeting → bookmark visible in HoldSpeak transcript at the correct timestamp (`Bookmark @ 00:15`, `timestamp: 15.62406s`); LCD flashes `Bookmark  \!//` then HoldSpeak's server-pushed confirmation `Bookmark @ 16s  \!//`; sticky `Recording 00:00   *` reverts after TTL. Out-of-meeting: 5 `--press` invocations all logged `event.suppressed reason=not_in_meeting` with zero spurious bookmarks. Voice-typing trigger via `simulate_voice_typing` confirmed: `device.voice_assistant.start` / `stop` fire on the bridge with exact 3 s duration. Two bugs surfaced + fixed during the live pass: ESPHome `object_id` derivation (display name → API name strips non-alphanumeric chars; renamed `name: "left_button_sim"` to fix), and a disconnect-after-execute race (CLI was disconnecting before firmware finished publishing state edges; added `settle_s` wait). 131/131 tests passing; ruff clean. AIPI-4-01 + AIPI-4-07 both flipped `done` with paired evidence files. Bonus: the same hardware pass implicitly verified AIPI-2-07 (sticky/flash/revert state machine + bidirectional LCD pushback) and AIPI-2-08 (deepened `--check` against live firmware confirmed `prepare_speaker`/`restore_mic` removed, `update_link` exposed).

Pickup next: **finish AIPI-4-06 live verification** against HoldSpeak HS-17: complete a device-sourced meeting segment, leave meeting state, short-press left, and confirm the LCD shows the last segment via a server `status` response. AIPI-4-05 is also now unblocked by HS-17 but still needs bridge sensor/cadence work. AIPI-4-02 (mic meter) remains gated on a hardware spike; AIPI-4-03 (multi-device) needs a second AIPI-Lite to verify.

**Update 2026-05-10 23:10 — LCD UX pass shipped.** A long live-tuning
session against `aipi-green.local` produced four new stories worth of
LCD work, all `done` with paired evidence:

- **AIPI-4-11 v2** — middle slot persist-until-replaced (the original
  auto-clear-after-TTL behaviour was leaving the user staring at empty
  middle slots after short flashes). Story-11 updated.
- **AIPI-4-12** — multi-line wider middle widget + montserrat_8 (8 px)
  + SCROLL_CIRCULAR on bottom for forward-compat with long payloads.
  About 10 lines × ~28 chars of headroom in the middle now vs. the
  one-line teaser before.
- **AIPI-4-13** — TX state lives in a new top-right `tx_label` glyph
  (LV_SYMBOL_UP) painted firmware-side on right-button hold. HoldSpeak
  no longer pushes `Listening...` / `Thinking...` to the bottom slot,
  so meeting `Recording M:SS` survives every voice-typing press.
- **AIPI-4-14** — double-tap left button cycles through three
  meeting-stat views on the middle slot (Numbers → Speakers → Intel).
  Detection is firmware-side `on_multi_click` (bridge-side classifier
  missed fast taps because the 50 ms OFF debounce ate intermediate
  releases — fixed by lowering debounce to 20 ms + native pattern
  matching).
- **AIPI-4-15** — overlap windows on HoldSpeak's transcription passes
  (1.5 s of audio context prepended each pass) so sentences that span
  a 10 s `TRANSCRIBE_INTERVAL` boundary stop getting cut mid-thought.
  HoldSpeak-side change, tracked here because it's the user-visible
  fix to a UX problem surfaced by the AIPI-Lite hardware pass.

AIPI-4-06 also flipped `done` in this same session — single-tap
outside a meeting now emits a `query last_segment` frame and the
status reply paints to the LCD via the existing path. Commits
`4b9f18e` (firmware+bridge AIPI-4-14 / 4-06) and `0c0e7cf` on
HoldSpeak (HS-17-07 paged intel + AIPI-4-14 cycle handler + AIPI-4-15
overlap) carry the implementations.

What's still open in phase 4: **AIPI-4-02** (mic meter, gated on
hardware spike), **AIPI-4-03** (multi-device, needs second AIPI-Lite),
**AIPI-4-05** (battery + RSSI bridge half — HS unblocked, bridge
sensor/model/cadence still TBD per `/tmp/pi-handover.md`), and
**AIPI-4-09 firmware half** (HOLD/CONT/AP/RST text → LVGL glyphs on
the mode label).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| ESPHome `update_screen` API roundtrip too slow for mic-meter at 8 Hz | medium | Story-02 starts with a 30 s measurement spike; tier 8 Hz / 4 Hz / abort | If p95 > 100 ms, close story-02 as "infeasible" |
| Left-button short-press triggers AP-mode (false long-press) | low | Firmware debouncer with explicit short/long classification; AP-mode entry preserves long-press threshold | If false AP entries observed, raise long-press threshold or reroute gesture |
| Bookmark timestamp clock-skew (bridge clock vs. HoldSpeak clock) | low | Acceptable for v1; document in story-01 notes | If skew > 5 s in field reports, add offset-correction story |
| HoldSpeak rejects unknown frame types with `extra="forbid"` (story-05 / 06 if run against pre-HS-17 HoldSpeak) | medium during version skew | HS-17 accepts `device_health` and `query`; bridge tests cover the new query frame. Use current HoldSpeak for live verification | If field deploys mix old HoldSpeak + new bridge, suppress/rollback the new outbound frame |
| Multi-device per-bridge resource pressure (two bridge processes on one host) | low | Each bridge is bytes-only; stateless; CPU per-bridge is dominated by RMS computation if mic-meter ships | If `pgrep -c bridge` × footprint > host budget, document multi-host pattern |

## Decisions made

- 2026-05-10 — Phase 4 **parallels phase 3**, doesn't block on it. Active-device features are LAN-local; cross-network transport is orthogonal. Both phases can ship independently and stories may land in any order.
- 2026-05-10 — **AIPI-4-05 and AIPI-4-06 stay `blocked` until HoldSpeak ships paired handlers.** We do not merge half-protocols. `extra="forbid"` on the wire would silently reject our outbound frames; the right move is to coordinate the schema in HoldSpeak's protocol-doc story before any bridge code lands.
- 2026-05-10 — **AIPI-4-06 unblocked by HoldSpeak HS-17 and bridge-side implementation started.** `QueryFrame` now exists; left-button single-tap routes to bookmark in-meeting and `query:last_segment` out-of-meeting; status responses cancel the 2s timeout and are truncated to the LCD width budget.
- 2026-05-10 — **Mic-meter is gated on a measurement spike.** If API roundtrips don't permit 8 Hz updates, the story closes with documented "infeasible" — we don't trade visual polish for protocol noise or aioesphomeapi instability.
- 2026-05-10 — **Outbound `event.long_press` keeps the wire name `long_press`** even though our local gesture is "short-press." The wire vocabulary is HoldSpeak's choice (HS-14-07); renaming would require a paired protocol-doc story.

## Decisions deferred

- Mic-meter during meetings — gated on phase-4 spike findings.
- Custom HoldSpeak status-frame schema for word-by-word streaming preview — pending field experience.
- More-than-2-device meetings — phase-4 verification only goes to 2; HoldSpeak supports more server-side.
- Multi-host bridge pattern (one host per device) — only relevant if multi-device shows host-resource pressure.
