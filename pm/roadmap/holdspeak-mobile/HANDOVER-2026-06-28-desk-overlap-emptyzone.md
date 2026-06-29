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

**Fix:** a lane-only bottom fade behind the orbs (`DeskDioramaStage.swift`, just before the Record orb
block) — a `LinearGradient(.clear → DioPal.bgBot)` `172 + botInset` tall, `zIndex 71` (under the orbs
at 72/73, over the column). The column now dissolves into the desk beneath the controls, so they read
as a floating toolbar instead of litter on the list. Gated by `camera.isLane` so the diorama is
untouched.

## 2. The empty-zone coaching fired on a zone that wasn't empty

**Symptom (owner):** created a zone, dived in, got the "this is empty, add this and that" coaching —
but "it wasn't empty, because every single zone inherits this tooling" (the global connectors / local
models / agents / chains show in every zone). The coaching contradicted what was on screen.

**Cause:** `DioZoneEmpty` headline read "`<name>` is empty" while `toolMembers()` (global connectors,
models, workflows) + `agentMembers()` + `chainMembers()` render in *every* zone (the owner's earlier
"tools are global at every level" decision — do NOT revert that). So the screen had the toolkit but
claimed to be empty.

**Fix:** reframe the headline to "Nothing filed in `<name>` yet" (`DeskDioramaStage.swift` ~L211). The
zone's *content* (what you file) is what's empty; the toolkit is global scaffolding, not zone content.
This is honest with the inherited tools present and keeps the no-prose rule (states the fact in the
fewest words). The predicate (`emptyZone` = no content + no child zones) was already right; only the
claim was wrong.

## Proof

`apple/scripts/desk-overlap-shot.sh` (new): builds the REAL app for the Simulator and screenshots a
full desk on iPhone + iPad. Before/after shots taken this session (full desk, and a dived empty zone
via a temporary `HS_DESK_DIVE=empty` seed, since removed). The fixed shots show the bottom rows fading
under the orbs, and "Nothing filed in Scratch yet" above the inherited connector rows. The device
build was reinstalled on the iPhone 17 Pro Max.

## Still open (named, not fixed here)

- **Qlippy on the lane** floats at `y = h*0.66` and overlaps a mid-list row at the right edge — the
  same overlap class, smaller (a semi-transparent mascot). Not in the owner's named pair; a follow-up.
- The broader device-gap punch-list from [HANDOVER-2026-06-27-device-gap.md](./HANDOVER-2026-06-27-device-gap.md)
  (in-world editing for any remaining modals, mic on every input, etc.) continues.
