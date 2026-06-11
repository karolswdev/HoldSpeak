# Phase 56 — Qlippy, the Presence Enhancer: final summary

**Status:** CLOSED (7/7) — 2026-06-11 (opened and closed the same day)
**Branch → PR:** `phase-56-qlippy` → PR to `main`, merged on green CI
**Backlog:** candidate **J** shipped; candidate **G** absorbed-shipped
(privacy visible at decision points — the three answers live on every
actionable card, verbatim, doc-locked).

## What the phase shipped

The presence layer got a face. **Qlippy** — the PixelLab paperclip homage —
lives on the presence surface behind a double opt-in (`presence.enabled` AND
`presence.mascot`, both off by default) as two layers:

- **The dock**: an ambient 9-frame sprite mirroring the runtime state map
  (listening / thinking / the complete flourish / error / sleeping after
  five quiet minutes). No buttons, no sound.
- **The card**: a sliding, focus-safe, one-at-a-time card (FIFO + "+N"
  hint, pause-on-hover, aria-live announce, reduced-motion fades) for
  exactly four moments: **a decision needs you** (the marquee — sticky,
  never auto-deciding), **the result of an approved action**, **learned
  from you** (only when a correction was actually taught AND has real
  reach), and **a finished meeting left open items**.

The invariants held end to end: **Qlippy never acts on his own** — the
card's Approve sends the byte-identical decision request the dashboard
sends (audit parity proven live, side by side); the machine payload never
rides a broadcast; flag-unset is byte-identical (the served page compared
equal); every card dismissible, ignoring always safe.

## Story by story

1. **HS-56-01 — assets + the gate**: the sprite pack vendored with
   provenance; `presence.mascot` round-tripping `/api/settings`; the
   settings sub-toggle (inert when presence is off).
2. **HS-56-02 — the dock + the card shell**: `qlippy.js` (framework-free,
   gated twice, no POST in the shell — locked), the full Signal motion
   spec, `presence-app.js` re-dispatching the socket as DOM events.
3. **HS-56-03 — the actuator card (G absorbed)**: `actuator_proposed` from
   the aftercare route + `actuator_result` broadcasts (wire-safe), the
   executor's observational `on_result` hook, Approve/Decline ≡ the
   dashboard (byte-asserted), the three privacy answers verbatim-locked.
4. **HS-56-04 — learning + aftercare cards**: `learning_event` under the
   honest-reach rule (the wire's count IS the route's count),
   `aftercare_ready` from the wrap flow (only finished + non-empty), the
   intel queue's `on_meeting_ready` observer.
5. **HS-56-05 — the native HUD frame**: one pure `presence_panel_frame`
   policy for both renderers (passive = the exact pre-phase click-through
   geometry, locked); card presence read from the page itself. **Proven
   live on real Linux metal** (the `.43` Xorg box): a real xdotool click on
   the real overlay's Approve recorded the audited decision; xwininfo
   logged 408x132 → 408x460 → 408x132 at one origin; the active window
   never changed. The macOS live click was waived by the user (locked
   screen); the macOS glue is unit-tested and its proof script ships.
6. **HS-56-06 — docs**: the typing guide's presence section gained the
   Qlippy story; the never-acts guarantee + privacy answers are pinned by a
   doc-drift test against both the guide AND `qlippy-events.js`.
7. **HS-56-07 — closeout**: the all-in-one live dogfood (below), this
   summary, BACKLOG flips, PR.

## The closeout dogfood (one live runtime, zero mocks, zero page errors)

```
PASS  the dock followed real socket broadcasts [('listening', 'listening'),
      ('processing', 'thinking'), ('complete', 'approve')] and settled idle
PASS  the queue held a race: the sticky decision card stayed, '+1' queued
PASS  audit parity: card approval (approved, 'web-user') == dashboard
      approval (approved, 'web-user'); no side effect on either
PASS  the queued learned card presented (matches 2)
PASS  the aftercare card presented from a real wrap ('Your meeting left 1 open item')
PASS  the served /presence page is byte-identical with the mascot on vs. off
PASS  mascot off: Qlippy stayed hidden through a proposal AND activity
PASS  presence off entirely: Qlippy never appears (the double gate)
PASS  zero page errors across the whole run
RESULT: PASS
```

Five screenshots (`story07-*.png`), all reviewed.

## Real finds along the way (the phase's bonus value)

- **The unpinned `Gdk` import** (Phase 41, latent on GTK3-only boxes):
  on a GTK4-shipping machine the overlay exploded at import. Pinned.
- **fork-from-threads deadlocked the GTK overlay child** under a running
  server — the exact production configuration. Switched to `forkserver`.
  Both found because the user insisted the Linux proof run on a real
  machine (`.43`) instead of staying code-only. Real metal keeps winning.
- The non-loopback bind refusal (Phase 50's guard) held during dogfooding —
  a pleasant honest-by-default sighting.

## Numbers

- Suite: 2568 (phase open) → **2602 passed, 17 skipped** (phase close).
- 7 commits, one per story, each with evidence in the same commit.
- New tests: mascot gate (5), shell locks (5), actuator broadcasts (4),
  learning/aftercare broadcasts (8), panel frame (11), doc lock (1) = +34.

## What did NOT ship (deliberately)

The Wisp sidekick, wave-hello onboarding, milestone cards, sound, the
`questioning` state, per-surface mascot toggles — all out-of-scope by the
phase doc; candidates for a future delight pass.

## Follow-ups

- The macOS live HUD click proof: `dogfood_story05_macos.py` is ready to
  run in any unlocked session (geometry oracle → real Quartz click →
  frontmost-app assertion).
- Next per the agreed sequence: **K — languages + spoken-symbol
  dictionary**.
