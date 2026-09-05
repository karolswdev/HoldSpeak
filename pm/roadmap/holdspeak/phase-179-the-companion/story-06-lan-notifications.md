# HS-179-06 — LAN notifications

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-02
- **Unblocks:** HS-179-07
- **Owner:** unassigned

## Problem

Phase 174 story-09 (LAN companion notifications) was CONDITIONAL on
the companion track waking. This phase wakes the track. The companion
must advertise `_holdspeak-notify._tcp` on the LAN, the desktop must
discover it and push the needs-you count when the edge crosses, and
the companion must fire an iOS local notification.

## Scope

- In:
  - The companion advertises `_holdspeak-notify._tcp` via Bonjour
    (the reverse of the desktop's `_holdspeak._tcp`).
  - The desktop discovers the companion's listener via NWBrowser
    (174's LAN notification push channel).
  - On needs-you count edge crossing (171's edge rule), the desktop
    pushes the count to the companion via HTTP POST.
  - The companion receives the push and fires an iOS local
    notification (UNUserNotificationCenter).
  - Quiet hours and per-project mute from 171 apply (the desktop
    suppresses the push, not the companion).
  - The payload is the count only (Article III.1).
- Out:
  - APNs or any hosted relay (LAN only; Article III).
  - Notification content beyond the count.
  - Background app refresh (the companion must be running or
    backgrounded with a Bonjour service to receive the push).

## Acceptance criteria

- [ ] The companion advertises `_holdspeak-notify._tcp` on the LAN.
- [ ] The desktop discovers the companion's listener and pushes the
      needs-you count on edge crossing.
- [ ] The companion fires an iOS local notification with the count
      (Article III.1 -- count only, no Room content).
- [ ] Quiet hours and per-project mute suppress the push.
- [ ] Verified on two devices on the same LAN.

## Test plan

- Unit: the companion's Bonjour service registration; the notification
  trigger logic; the desktop's push function with a mock listener.
- Integration: two devices on the LAN; the desktop pushes to the
  companion.
- Manual: the owner's phone receives a notification from his desktop
  on his LAN.

## Notes / open questions

- iOS backgrounding limits may prevent the Bonjour service from
  running when the app is fully suspended. The companion may need a
  background mode (Bonjour or network extension) to keep the listener
  alive. This is a design-time decision with iOS API constraints.
