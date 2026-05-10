# HS-17-10 — Multi-Device Join/Drop Events to LCD

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-14-07 (device-status substrate); HS-14-06 (multi-device meeting attach); AIPI-Lite phase-4 multi-device verification (AIPI-4-03)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

When a meeting has multiple AIPI-Lite devices attached and a new device joins (or one drops mid-meeting), the *existing* attached devices get no LCD signal. The other person attaching their device to the same meeting is invisible to the user holding the first one.

User feedback 2026-05-10, after the two-device hostname rename landed (commit `7f34f71` adding `device_name` substitution): "When my daughter's device joins my meeting, I should know."

## Scope

### In

- New emitter in `MeetingSession.attach_device(...)`: after a successful attach, broadcast `<label> joined` (where `<label>` is the joining device's resolved label) as a status flash to all *other* currently-attached devices. `ttl_ms: 4000`.
- New emitter in `MeetingSession.detach_device(...)` / wherever device drops are handled: broadcast `<label> dropped` to all *remaining* attached devices. `ttl_ms: 4000`.
- Symbol: `LV_SYMBOL_PLUS` (U+F067) for join; `LV_SYMBOL_MINUS` (U+F068) for drop. Bridge-side, add `"<X> joined"` / `"<X> dropped"` to `_ACTIVITY_SYMBOLS` with the right glyphs (or pick from leading word).
- Joining device does NOT see its own join event (it's the one joining; the flash to it would be redundant).
- Integration test: simulate two devices, attach the second, verify the first sees the join flash; detach the second, verify the first sees the drop flash.
- `docs/DEVICE_PROTOCOL.md` extended.

### Out

- Pre-meeting "device available" / "device unavailable" notifications (those happen outside meetings; out of scope).
- Cross-meeting notifications ("Karol-living-room just started a meeting"). Way out of scope.
- Per-event audio cue (the LCD flash is enough; no audible chime needed; AIPI-Lite doesn't have a speaker stack anyway per `docs/DEVICE_AUDIO_OUTPUT.md`).
- Device label changes mid-meeting (rare edge case; out for v1).

## Acceptance Criteria

- [ ] `MeetingSession.attach_device` hook fires `device_status.broadcast(already_attached_ids, "<label> joined", ttl_ms=4000)` after a successful attach.
- [ ] `MeetingSession.detach_device` (or equivalent) hook fires `device_status.broadcast(remaining_attached_ids, "<label> dropped", ttl_ms=4000)` after a drop.
- [ ] Joining device does not receive its own join flash; departing device may have already disconnected (no-op if so).
- [ ] Bridge-side symbol map gains `"<X> joined"` / `"<X> dropped"` entries — but since the leading word isn't predictable, the picker would need a different match heuristic. Alternative: HoldSpeak emits status frames with explicit symbol hints (extend the protocol). For v1, just check for "joined" / "dropped" as **trailing** words and pick PLUS/MINUS in the bridge's picker.
- [ ] Integration test green: simulated 2-device meeting; attach + detach events produce the right device-side flashes.
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification: two AIPI-Lite devices on the LAN (e.g., `aipi.local` + `aipi-green.local` per the substitution pattern from commit `7f34f71`); attach second to a running meeting; LCD on the first shows the join flash.

## Test Plan

- **Unit:** symbol-picker extended for trailing-word matching ("joined" / "dropped"); event-payload formatting.
- **Integration:** simulated meeting with 2 attaching devices; record status frames per-device.
- **Manual:** two-device meeting on real hardware.

## Notes

- **Symbol picker change is the subtle bit.** The existing `_pick_activity_symbol` looks at the LEADING word. For "Karol-green joined", the leading word is the label (variable) — we can't map "Karol-green" to a symbol meaningfully. Two options:
  - Server-side: emit the symbol codepoint inline in the text (`Karol-green joined `) — protocol change, breaks the "bridge picks symbol from leading word" model.
  - Bridge-side: extend the picker to also check trailing words for `joined` / `dropped`.
  - Pragmatic: bridge-side trailing-word check, scoped to a small known list. Documented as such.
- **Truncation at 30 chars** applies to the combined `"<label> joined"` string.
- **Multi-attach race:** if two devices attach simultaneously, both should see each other's join (not just one). Per-device emission via `device_status.broadcast` handles this naturally.
- **Pairs with AIPI-4-03's verification.** Once both stories ship, the multi-device experience is real-world usable.
