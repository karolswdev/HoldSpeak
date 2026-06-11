# HS-56-05 — The native HUD frame

- **Project:** holdspeak
- **Phase:** 56
- **Status:** backlog
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
  - **Linux:** the freedesktop/GTK renderer updated to the same policy
    best-effort — code + tests only; the no-hardware posture stated plainly
    in evidence (the standing Phase-24/25 convention).
  - Mascot-off (ring-only) and presence-off behavior unchanged
    (regression-tested).
- **Out:** moving the native anchor corner unless evidence shows the card
  needs it (decide + document); any always-interactive panel (pointer events
  only when a card shows).

## Acceptance criteria
- [ ] On this Mac, live: a presented card renders in the native HUD at the
      larger frame, its buttons click, and keyboard focus verifiably stays
      in the foreground app (transcript + screen capture).
- [ ] Passive states keep the small frame; resolving/dismissing the card
      returns to it.
- [ ] Mascot-off keeps today's exact panel geometry + click-through (test on
      the policy/projection; live check).
- [ ] Linux renderer changes reviewed + unit-tested; posture documented.

## Test plan
- Unit on the window policy/projection extension; live macOS verification;
  full suite.

## Notes / open questions
- Pointer-events-only-when-carded is the focus-safety crux: get the
  ignoresMouseEvents toggling wrong and either buttons dead or clicks leak
  through to the app beneath.
