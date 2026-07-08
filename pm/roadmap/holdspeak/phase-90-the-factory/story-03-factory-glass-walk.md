# HS-90-03 — The factory on glass + the walk + the close

- **Project:** holdspeak
- **Phase:** 90
- **Status:** backlog
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

- [ ] Spawn from the desk creates a session that appears in the pane
      picker; rename relabels it; kill (armed + confirm) ends it.
- [ ] The walk: spawn → arm → steer (a key + text) → rename → kill, live,
      captured (screens + the audit trail).
- [ ] Docs shipped in canon voice (no dashes / roadmap vocab in
      user-facing docs); final-summary written; suite + guards green.

## Implementation direction

- The factory controls live on the desk's session surface; kill wants a
  confirm (it is irreversible) on top of the arm.
- The walk is one captured run; the audit read-back is the proof the
  lifecycle went through the spine.
