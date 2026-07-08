# HS-89-04 — The robustness walk, the docs, the close

- **Project:** holdspeak
- **Phase:** 89
- **Status:** backlog
- **Depends on:** HS-89-01, HS-89-02, HS-89-03
- **Unblocks:** —

## Problem

First-class manipulation is proven by doing the things Phase 87 could
not, live, against the real machine: interrupt a runaway, drive a TUI,
attach a hand-started pane, steer a remote node — every one through the
one audited chokepoint. The walk is the acceptance.

## The walk (each beat a capture)

1. Interrupt: `C-c` a REAL runaway (`yes` / a hot loop) in an armed
   pane; it stops; the audit shows the `C-c`.
2. Drive: arrows + `Enter` navigate a REAL TUI (a `less`/menu) in the
   pane; the audit shows the sequence.
3. Attach: discover a pane started BY HAND (never registered), peek it
   free, arm it, steer it.
4. Remote: peek + steer a pane on a second (two-process) node; the
   node's worker log proves local execution; the audit names the node.
5. Crown cases: a recycled pane refuses+revokes for KEYS too; a quiet
   remote node refuses by name.
6. The audit: the trail for beats 1–5 read back — every key, who/when/
   what/where, the node named where remote.

## Acceptance criteria

- [ ] All beats captured against real tmux + a real runaway/TUI + a
      two-process remote; zero mocked frames; the audit rows match
      every claim.
- [ ] The chokepoint census covers `send_keys_to_pane`; the
      any-pane + remote paths still pass through `deliver`/`deliver_keys`
      only; the audit-completeness assertion holds for keys.
- [ ] Docs shipped in canon voice: USER_GUIDE "Take over a session"
      (watch free, manipulate armed, every key audited — say what
      refuses and when), SECURITY.md the manipulation-model update
      (any pane, any key, cross-machine — same consent), ARCHITECTURE.md
      the chokepoint paragraph updated; suite + guards green.
- [ ] final-summary.md — first-class agent manipulation, and what the
      factory (B3) inherits from this reach.

## Test plan

- Unit: the mechanical rules (census, audit-completeness for keys).
- Integration: the walk itself.
- Manual / device: the owner interrupts + drives a real session from
  the desk.

## Implementation direction

- **Walk rig:** extend `scripts/steer_walk_hs87.py` — one hub, real
  panes, a real runaway (`yes >/dev/null`) to `C-c`, a real TUI to
  drive, a hand-started pane to attach, a two-process node to steer.
- **The docs** lead with the consent sentence (watch free, manipulate
  armed, every key audited) and never say "safe" — they say what
  refuses and when (the no-reassurance canon).
- **final summary** records the B3 (the factory) handoff: spawn/kill
  ride this same spine next.
