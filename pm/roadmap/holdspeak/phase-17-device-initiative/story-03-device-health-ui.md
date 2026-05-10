# HS-17-03 — Web UI: Device-Health Rendering

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-17-01 (device_health frame + state extension must exist)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

HS-17-01 lights up `battery_pct` + `rssi_dbm` on the server side; HoldSpeak now *knows* device health but doesn't *show* it. The web flagship UI's current dashboard / meeting device surfaces should render these values so the user can see, at a glance, that a remote device is healthy / about to die / on a weak WiFi signal.

This is a minimum-viable affordance — read-only rendering, no thresholds, no alerts, no styling pass. Polish is a follow-up if the affordance proves useful in field use.

## Scope

### In

- **Current dashboard / active meeting surface:** each attached device descriptor renders alongside its label:
  - Battery: `▮▮▮▮▯ 78%` (or numeric-only `78%` if a battery-glyph stack is too much) — when present.
  - RSSI: `-67 dBm` plain numeric — when present.
  - Hidden entirely when `battery_pct` / `rssi_dbm` is `None` (rather than `--` placeholder; rationale in HS-17 status doc's "Active risks").
- **Device list:** only extend it if such a surface already exists by implementation time. Do not create a dedicated `/devices` page in this story.
- "Stale" indicator: if `last_health_at` is older than 5 minutes, render the values with a `(stale)` suffix or grey-out treatment.
- Current web test stack coverage for: device-with-health renders fields; device-without-health hides fields; stale device shows stale indicator. If the repo has no browser E2E harness, use the existing Astro/static route tests plus a manual runtime screenshot.
- No new design tokens; reuse existing typography + spacing from the web design system (phase 10 / 12 lineage).

### Out

- Alerting / warning UI when battery is low. Follow-up if the affordance proves useful.
- Battery-level icons / SVG glyph set — text-based glyphs (▮▯ or just numeric) for v1.
- Historical battery curve graph. Out (no persistence in HS-17-01).
- Per-device health page (`/devices/{id}/health`). Out — just inline in existing views.
- Mobile-specific layout adjustments beyond preserving the current responsive layout.

## Acceptance Criteria

- [ ] Current dashboard / active meeting surface renders battery + RSSI inline with the attached-device descriptor when values are present.
- [ ] Existing device list, if present, shows the same fields. If no such list exists, do not create one solely for this story.
- [ ] Absent values: no placeholder text; the entire field block is hidden.
- [ ] Stale values (`last_health_at` > 5 min ago): rendered with a `(stale)` suffix or visual-grey treatment.
- [ ] Current web test stack covers present / absent / stale paths, or evidence explains why manual runtime verification is the right coverage for this scaffold.
- [ ] No regressions in existing dashboard / meeting tests.
- [ ] Manual: live AIPI-Lite device (or simulated frame in dev) shows battery + RSSI on the meeting page; values update on subsequent frames.

## Test Plan

- **Unit / static route:** component or route rendering with present / absent / stale fixtures in the existing web stack.
- **Browser E2E, only if already present:** fake WS pushes a `device_health` frame; active meeting surface reflects the values; staleness behavior after time advancement.
- **Manual:** real AIPI-Lite device + a meeting; observe values updating as the device drains battery / walks toward WiFi-edge.

## Notes

- **"Hidden when absent" rationale:** showing `--` for an absent value invites the reading "device is broken / I should fix something." For AIPI-Lite devices that pre-date AIPI-4-05's bridge support, the value is *legitimately unknown*; rendering it as missing rather than missing-value is the truthful affordance.
- **Stale threshold of 5 minutes** is empirical: AIPI-4-05's bridge sends every 60 s on heartbeat (plus threshold-cross emissions). Anything older than 5× the heartbeat probably means the device is offline or the WS dropped without us noticing. Tunable.
- **No new design tokens.** This story should land in the existing web design system without expanding it; if the affordance turns out to need polish, that's HS-17-followup or a phase-12-style design pass.
- **Localization:** match existing meeting-view i18n conventions (probably none in v1; mirror whatever the surrounding labels do).
