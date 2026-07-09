# HS-90-03 — The factory on glass + the walk + the close

- **Project:** holdspeak
- **Phase:** 90
- **Status:** done
- **Shipped:** 2026-07-08 — the full lifecycle is on glass. The picker gained a `+ Spawn` row; the armed pull-out a SESSION row (Rename + a two-step-confirm ⌫ Kill). The walk passed 8/8 live through the desk's exact routes (spawn → picker → arm → C-c → steer → rename → kill → audit). Docs + final-summary shipped. **Phase 90 CLOSED 3/3.** Evidence: [evidence-story-03.md](./evidence-story-03.md), [screenshots](./screenshots/).
- **Depends on:** HS-90-01, HS-90-02
- **Unblocks:** —

## Problem

The factory (HS-90-01) and the manipulation UI (HS-90-02) meet here: the
desk can spawn a session, drive it, rename it, and end it — the full
lifecycle on glass — and the phase closes on a live walk.

## Scope

- In: spawn/kill/rename controls on the web desk (kill guarded by the
  arm + an explicit confirm); the closing walk (spawn → steer → rename →
  kill, live, from the desk); docs (USER_GUIDE factory + manipulation UI,
  SECURITY the lifecycle acts, ARCHITECTURE the factory paragraph);
  final-summary.
- Out: agent orchestration into spawned panes; cross-machine factory UI.

## Acceptance criteria

- [x] Spawn from the desk creates a session that appears in the pane
      picker; rename relabels it; kill (armed + a two-step confirm) ends
      it. Screenshot-verified (`screenshots/factory-*.png`).
- [x] The walk (`evidence-story-03.md`, 8/8 live through the desk's exact
      routes): spawn → in the picker → arm → `C-c` → steer
      (`WALKED_FROM_GLASS` landed) → rename → kill (session gone) → the
      audit read it all back.
- [x] Docs shipped in canon voice (no dashes / roadmap vocab, voice guard
      green): USER_GUIDE, SECURITY, ARCHITECTURE; final-summary written;
      suite + guards green.

## Implementation direction

- The factory controls live on the desk's session surface; kill wants a
  confirm (it is irreversible) on top of the arm.
- The walk is one captured run; the audit read-back is the proof the
  lifecycle went through the spine.
