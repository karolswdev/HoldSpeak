# HANDOVER — 2026-06-28 — Desk overlap + empty-zone coaching (owner device walk)

Two device-gap bugs the owner hit walking the merged build, both on `DeskDioramaStage`. Both fixed,
both verified on the real layout in the iOS Simulator (the actual app, full-desk seed), not seeded
mock views.

## 1. The Record / New orbs overlapped the list (lane / iPhone)

**Symptom (owner):** "when the primary desktop is full with different items, the new recording, and
the new button on the right, overlap them. Unacceptable."

**Cause:** on the phone (`.lane` camera) the desk is a scrolling card column. The Record orb
(bottom-left) and the New `+` FAB (bottom-right) float over it. The column reserved bottom padding
(`132 + botInset`), which only clears the orbs at the *end* of the scroll. Mid-scroll, rows passed
directly under the orbs and collided with the row text. (The iPad `.wide` diorama was fine: items sit
in the upper grid, the orb is in empty space.)

**Fix (v2, after the first pass was too weak on device):** a lane-only **solid control dock** behind
the orbs (`DeskDioramaStage.swift`, just before the Record orb block) — a short gradient lip (56pt)
over a **solid `DioPal.bgBot` base** (`150 + botInset`), seamless with the desk bg, `zIndex 71` (under
the orbs at 72/73, over the column). The solid base genuinely OCCLUDES rows scrolling past (a faint
fade left "Slack"/"Webhook" visible under the orbs), and the column's bottom inset was bumped to
`200 + botInset` so the last row rests above the dock. Gated by `camera.isLane`; the diorama is
untouched.

**Also (owner): the Record orb read optically smaller than New.** It was a 46pt disc vs the New FAB's
64pt. `DioRecordOrb` now uses a 64pt disc (icon 24, pulse rings + frame scaled to match) so the two
bottom controls read as a pair.

## 2. The empty-zone coaching fired on a zone that wasn't empty

**Symptom (owner):** created a zone, dived in, got the "this is empty, add this and that" coaching —
but "it wasn't empty, because every single zone inherits this tooling" (the global connectors / local
models / agents / chains show in every zone). The coaching contradicted what was on screen.

**Cause:** `DioZoneEmpty` headline read "`<name>` is empty" while `toolMembers()` (global connectors,
models, workflows) + `agentMembers()` + `chainMembers()` render in *every* zone (the owner's earlier
"tools are global at every level" decision — do NOT revert that). So the screen had the toolkit but
claimed to be empty.

**Fix (v2):** the copy reframe alone wasn't enough — on the lane the centred `DioZoneEmpty` card
rendered ON TOP of the inherited connector/agent rows (text-on-text: "Nothing filed in Lolll yet" over
"Webhook… your tailored agent"). So:
- The centred `DioZoneEmpty` overlay is now **diorama-only** (`!camera.isLane`), where the canvas is
  genuinely blank and a centred card fits.
- On the lane, a new compact **`DioLaneEmptyHint`** row is prepended to the top of the column (above
  the always-present toolkit rows) when a sub-zone has no filed content. No overlap; honest ("Nothing
  filed in `<name>` yet" + a Sub-zone button); the global toolkit lists cleanly below it.
- The headline reads "Nothing filed in `<name>` yet" (the zone's *content* is empty; the toolkit is
  global scaffolding, not zone content). `emptyZone` (no content + no child zones) was already right.

## Proof

`apple/scripts/desk-overlap-shot.sh` (new): builds the REAL app for the Simulator and screenshots a
full desk on iPhone + iPad. Before/after shots taken this session (full desk, and a dived empty zone
via a temporary `HS_DESK_DIVE=empty` seed, since removed). The fixed shots show the bottom rows fading
under the orbs, and "Nothing filed in Scratch yet" above the inherited connector rows. The device
build was reinstalled on the iPhone 17 Pro Max.

## 3. The whole recording UI overlapped the list (lane / iPhone)

**Symptom (owner, "here's how it looks when I'm recording"):** during a recording the live-capture UI
(the HEARING live transcript, the ASK LIVE lens chips, agent/crew markers, REC timer, STOP button) all
floated ON TOP of the scrolling list — text-on-text everywhere.

**Cause:** `DioAmbientRecorder` (zIndex 110) is a transparent bottom-anchored overlay, and `laneColumn`
kept rendering *underneath* it during `capturing` — the recorder is designed to float over the iPad
diorama (sparse canvas), but on the lane it floats over a dense list.

**Fix:** on the lane, don't render `laneColumn` while `capturing || weaving` — the ambient recorder
OWNS the surface (it floats over the desk gradient bg, no list behind). The iPad keeps the
ambient-over-canvas design (its canvas is sparse). Verified: the recording state now shows only the
live cards + transcript + ASK LIVE lenses/agents + STOP, cleanly, over a clean background.

## Still open (named, not fixed here)

- **Qlippy on the lane** floats at `y = h*0.66` and overlaps a mid-list row at the right edge — the
  same overlap class, smaller (a semi-transparent mascot). Not in the owner's named pair; a follow-up.
- The broader device-gap punch-list from [HANDOVER-2026-06-27-device-gap.md](./HANDOVER-2026-06-27-device-gap.md)
  (in-world editing for any remaining modals, mic on every input, etc.) continues.
