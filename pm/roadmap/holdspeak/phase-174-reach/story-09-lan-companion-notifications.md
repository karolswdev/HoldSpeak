# HS-174-09 — LAN companion notifications

- **Project:** holdspeak
- **Phase:** 174
- **Status:** in-progress
- **Depends on:** HS-174-01
- **Unblocks:** HS-174-10
- **Owner:** unassigned

**CONDITIONAL: this story ships only if the companion track (the iPad
app, the Swift recreation from the finished web spec) wakes before or
during this phase. If the companion track remains dormant, this story
is deferred without blocking the phase's close.**

## Problem

The Bonjour mesh (mesh.py:1-45) advertises `_holdspeak._tcp` on
off-loopback binds for the iPad's NWBrowser. Today the mesh is
discovery only: the companion can FIND the desktop, but the desktop
cannot PUSH a notification to the companion. Phase 171's macOS
notifications reach the Mac; this story reaches the phone/iPad over the
LAN when the companion is listening.

## Scope

- In:
  - A notification push channel from the desktop to a discovered
    companion on the LAN (the reverse of the Bonjour discovery: the
    desktop discovers the companion's listener and pushes the needs-you
    count).
  - The payload is the aggregate needs-you count only (Article III:1;
    no Room content, no names, no details beyond the count unless the
    owner opts in at the settings level).
  - The companion's listener: a Bonjour service the companion
    advertises (`_holdspeak-notify._tcp`); the desktop discovers it
    and pushes over a simple HTTP POST.
  - Quiet hours and per-project mute from Phase 171 apply.
- Out:
  - Push notifications to iOS APNs (no hosted relay; Article III:1).
  - The companion app itself (that is the companion track).
  - Notification content beyond the count.
  - Cross-network push (LAN only; the tailnet is the desktop's reach,
    not the phone's).

## Acceptance criteria

- [ ] The desktop pushes the needs-you count to a discovered companion
      listener on the LAN.
- [ ] The payload is the count only (Article III:1); no Room content
      crosses the network.
- [ ] Quiet hours and per-project mute suppress the push.
- [ ] The companion's Bonjour service is discovered by the desktop.
- [ ] CONDITIONAL: if the companion track is dormant, this story is
      deferred and the phase closes without it.

## Test plan

- Unit: the push function sends the correct payload to a mock listener.
- Unit: quiet hours suppress the push.
- Integration: two machines on the same LAN; the desktop pushes to the
  companion's listener (or a test listener script).
- Manual: the companion receives the notification on the LAN.

## Notes / open questions

- The companion track is dormant (the standing rule: "web DeskOS is the
  spec; Swift recreates from the finished web spec"). This story is
  conditional; its deferral does not block Phase 174's close.
- The reverse Bonjour pattern (the companion advertises, the desktop
  discovers) is the opposite of the current flow (the desktop
  advertises, the companion discovers). Both can coexist: the desktop
  advertises `_holdspeak._tcp` and browses for
  `_holdspeak-notify._tcp`.
