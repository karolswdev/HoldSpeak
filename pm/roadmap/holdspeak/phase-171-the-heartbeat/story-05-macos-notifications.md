# HS-171-05 — macOS notifications on the edge

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-03, HS-171-04
- **Unblocks:** HS-171-08
- **Owner:** unassigned

## Problem

The Cocoa presence host (desktop_presence_cocoa.py) runs an AppKit child
process with a status-bar glyph and a floating NSPanel, but makes zero
notification calls. The owner has no way to learn that something needs
him without opening the desk. The arc says: "macOS notifications on the
EDGE of that count (UNUserNotificationCenter from the Cocoa child;
quiet hours; per-project mute)."

## Scope

- In:
  - UNUserNotificationCenter notifications from the Cocoa child
    process, dispatched on the EDGE of the needs-you count (the count
    crosses from 0 to > 0, or increases by a delta since the last
    notification).
  - The notification body: "HoldSpeak -- N need you across M projects"
    (the count only; Article III: nothing leaves the machine, the
    notification names no Room content beyond the count unless the
    owner opts in via a setting).
  - Quiet hours (existing config: integrations.py:209-210,
    cadence/scheduler.py:25-26) suppress notifications during the
    configured window (default 22:00-08:00).
  - Per-project mute: a boolean on the project settings that suppresses
    notifications for that project's needs-you count.
  - Content opt-in: a setting that allows the notification to include
    the first WHY from each project (off by default; Article III.1).
  - Click action: clicking the notification opens the desk (the
    existing presence host opens the browser to the local URL).
  - Linux: libnotify fallback (desktop_presence_freedesktop.py) with
    the same edge rule and quiet hours.
- Out:
  - Push notifications to remote devices (Phase 174).
  - Sound or vibration customization.
  - Notification grouping by project (one notification per edge event,
    not per project).

## Acceptance criteria

- [ ] A UNUserNotificationCenter notification fires within 10 s of the
      needs-you count crossing its edge; verified by a rig that seeds
      a needs-you item and asserts the notification dispatch (Article
      IX.1).
- [x] The notification body contains only the count and project count,
      not Room names or WHY text, in the default configuration
      (Article III.1).
- [x] Quiet hours suppress the notification; a needs-you edge during
      quiet hours does NOT fire (verified by setting the clock inside
      the quiet window in a test).
- [x] Per-project mute suppresses the notification for that project;
      the aggregate count excludes muted projects.
- [x] Content opt-in: with the setting enabled, the notification
      includes the first WHY per project.
- [ ] Clicking the notification opens the desk in the browser.
- [x] Linux: libnotify notification with the same edge rule (verified
      on .43 if reachable, otherwise by unit test).
- [x] Zero egress (Article III: the notification is local OS-level,
      never a remote push).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k macos_notification`
  - The edge detector fires on count 0 -> N, suppresses on N -> N.
  - Quiet hours suppress the dispatch.
  - Per-project mute excludes the project from the aggregate.
  - Content opt-in includes WHY text.
- Integration: the rig on macOS boots the Cocoa child, seeds a
  needs-you item via the API, and asserts UNUserNotificationCenter
  received a request (requires pyobjc in the test environment).
- Manual: the owner's walk (HS-171-08): a notification he receives.

## Notes / open questions

- UNUserNotificationCenter requires a bundle identifier on macOS. The
  existing Cocoa child may need a minimal Info.plist or a
  `NSApplication.setActivationPolicy_` adjustment. Recon during build.
- The edge detector must track the last-notified count across restarts.
  A simple file or DB row suffices (the cadence table or a dedicated
  column on the needs-you cache).

## Proof and the honest gap (2026-09-05)

tests/unit/test_hs171_aggregate_notify.py: the edge rule (3→3 no fire,
3→4 fires, 4→2→4 once, 0 never), quiet hours held + receipted, count-only
body by default, content opt-in, per-Room mute excluded from the edge
count, the macOS path exercised with the presence child monkeypatched,
the Linux libnotify seam. **Open, by design:** the banner fires through
`osascript` (the PyObjC UserNotifications bridge is not in the venv and
UNUserNotificationCenter refuses an unbundled process) — so the first
box reads "within 10 s" only for the osascript banner, and the click
action waits for the app bundle (174/179; BACKLOG). His walk measures
the 10 s on his desk.
