# HS-56-02 — The dock + the card shell

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** HS-56-01
- **Unblocks:** HS-56-03, HS-56-04, HS-56-05
- **Owner:** unassigned

## Problem
The presence page is a ring + label. Qlippy needs (a) an ambient dock that
mirrors `runtime_activity` with character, and (b) the sliding card component
every later story presents into — with the motion spec, the queue discipline,
and the accessibility story right from the start.

## Scope
- **In:**
  - **The dock** on `/presence`, behind the mascot flag: sprite-strip
    animation (`steps(9)`, `image-rendering: pixelated`), the RFC dock map
    (listening/recording/meeting_live → listening; transcribing/processing/
    saving/typing → thinking; error → error; complete → one `approve`
    flourish then idle; idle → `sleeping` after 5 min), driven by the same
    `runtime_activity` stream `presence-app.js` consumes.
  - **The card shell**: the RFC anatomy (Qlippy bay with state sprite +
    composited glyph slot, headline (display face) + detail (muted), optional
    mono preview block, 0–3 action buttons + dismiss ✕) and motion
    ("Signal settle": ~360–460 ms slide-in on `--ease-standard` + fade, a
    one-time settle bob + accent glow on `alert`, ~260–320 ms slide-out;
    pause-on-hover cancels auto-dismiss; FIFO queue with a "+N" hint; cards
    present one at a time). Reduced-motion: crossfade, sprite loops paused.
    ARIA live-region announce on present.
  - A small internal API (`present(card)`, `resolve()`, `dismiss()`) the
    event stories hook into, plus a dev/mock trigger usable from tests and
    screenshot scripts.
  - Flag off → none of this renders (byte-identical page output).
- **Out:** real event wiring (03/04); the native frame (05).

## Acceptance criteria
- [x] Dock states animate per the map (incl. sleeping after the idle
      threshold and the complete flourish); reduced-motion respected.
      (Live dogfood: listening → thinking → approve flourish → idle; the
      5-min sleep is a locked constant; reduced-motion pauses loops.)
- [x] The card shell implements the anatomy + motion spec; two queued mock
      cards present FIFO with the "+N" hint; pause-on-hover holds; dismiss
      slides out. (All proven live; 6/6 dogfood, zero page errors.)
- [x] Behind the flag: flag-off behavior identical (proven live: nothing
      renders, nothing listens; the served HTML carries the inert hidden
      skeleton — the honest deviation recorded in evidence §4, the price of
      keeping scoped CSS on static markup).
- [x] Page-content/behavior tests green; `npm run build` clean; screenshots
      committed (dock states + the alert + learned cards) and reviewed.
      (5 locks; full suite 2578 passed, 17 skipped.)

## Test plan
- Page locks + a Playwright behavior pass using the mock trigger (present →
  queue → hover-hold → dismiss; reduced-motion variant). Full suite.

## Notes / open questions
- Keep the card's interactivity assumptions soft: in the native HUD the panel
  is click-through until HS-56-05 — the card must inform even when it cannot
  be clicked there.
