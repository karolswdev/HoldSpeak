# HS-56-05 — The native HUD frame

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** HS-56-02
- **Unblocks:** HS-56-07
- **Owner:** unassigned

## Problem
The native desktop HUD (the place the mascot matters most — the user is
dictating into another app) is a 408×132 click-through NSPanel sized for the
ring. The Qlippy card cannot fit and cannot be clicked there.

## Scope
- **In:**
  - **macOS:** the NSPanel grows to host the card (an edge-anchored frame
    sized from the window policy), `ignoresMouseEvents` managed so the
    card's buttons are clickable **while the panel stays non-activating**
    (keyboard focus never leaves the user's app — `NSWindowStyleMaskNonactivatingPanel`
    retained; verified live on this machine). Passive/dock-only states keep
    a small frame; card-bearing states size up; the policy/projection
    (`desktop_window_policy` / `build_presence_window_view`) extended to
    carry the card-frame signal.
  - **Linux:** the freedesktop/GTK renderer updated to the same policy and
    **proven live on real X11 metal** (the `.43` box over SSH — a real Xorg
    session, real xdotool click, real screenshots; upgraded from the
    code-only posture on user direction).
  - Mascot-off (ring-only) and presence-off behavior unchanged
    (regression-tested).
- **Out:** moving the native anchor corner unless evidence shows the card
  needs it (decide + document); any always-interactive panel (pointer events
  only when a card shows).

## Acceptance criteria
- [x] ~~On this Mac, live~~ — **waived by the user** ("I actually can't right
      now. But we can call the phase good": the Mac's screen stayed locked, so
      a live click lands on loginwindow). What WAS verified on this Mac: the
      renderer child boots and orders the panel up at the passive frame while
      locked. The interactive-card seam itself (the identical shared
      `presence_panel_frame` policy + page-probe + pointer-event toggle) is
      proven live end-to-end on the Linux box instead; the macOS-specific
      glue is unit-tested (`tests/unit/test_presence_panel_frame.py`). The
      ready-to-run proof script ships (`dogfood_story05_macos.py`) for any
      unlocked session.
- [x] Passive states keep the small frame; resolving/dismissing the card
      returns to it (the X server's own geometry log: 408x132 → 408x460 →
      408x132 at the same origin; unit-tested sync + hide-defers-to-card on
      both renderers).
- [x] Mascot-off keeps today's exact panel geometry + click-through (the
      passive frame is locked by test to the exact Phase-41 geometry; the
      page probe can never fire with the mascot off — the `is-in` class
      never appears).
- [x] Linux: live on the `.43` box's real Xorg session — the overlay grows
      for the card, a real X11 click on Approve records the audited
      decision, the active window never changes, and the X server reports
      the frame returning to passive (transcript + screenshots — see
      `evidence-story-05.md`; **two real production bugs found and fixed**:
      the unpinned Gdk import and fork-from-threads).

## Test plan
- Unit on the window policy/projection extension; live macOS verification;
  full suite.

## Notes / open questions
- Pointer-events-only-when-carded is the focus-safety crux: get the
  ignoresMouseEvents toggling wrong and either buttons dead or clicks leak
  through to the app beneath.
