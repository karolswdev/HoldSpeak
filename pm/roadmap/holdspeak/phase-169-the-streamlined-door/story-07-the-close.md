# HS-169-07 - The close (gates, the sweep, counsel, the debt ledger, final summary; 168 folded)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** done
- **Depends on:** HS-169-05, HS-169-06
- **Unblocks:** -
- **Owner:** unassigned

## Problem

Every phase closes on the full suite, the sweep against main's baseline, counsel's ratification, and an honest debt ledger.

## Scope

- **In:** full suite in an isolated HOME (`-n auto`; live walks NEVER beside it); the sweep on branch-new names only against main's baseline at the branch base; web full + baseline; counsel RATIFY on this phase's diff; final-summary.md with the debts (168's ledger folded: the name derivation at finalize; the Room stats row at 640; the emojiGuard blind spots; the fifth template per provider; the three composers of ConnectionsService; the acli per-process lock); PR to main on the local gates; merge on the owner's word.
- **Out:** new features.

## Acceptance criteria

- [ ] Suite totals read from the output; zero unexplained branch-new failures.
- [ ] Counsel RATIFY (or RATIFY-W-C with every M/S paid).
- [ ] final-summary.md written; PR opened; merge only on the owner's word.

## Test plan

The full-suite command from CLAUDE.md in an isolated HOME; `scripts/check_web_baseline.py --run`; `.githooks/dw verify --all`.

## Delivered (2026-09-05)

- Counsel on the build diff: RATIFY-W-C, every M/S paid (S-3 documented).
- Unit fast lane 8011 passed / 14 failed (8 inherited at ce629cc2; 6
  branch-new paid: the API-surface manifest regenerated, the branch_ci
  read classified in the effect fence, ProjectRoomCore's model-host
  lookup classified in the route census, the 166 baseline tests seeded
  with a GitHub proposal, one xdist flake 3× serial green).
- Non-unit half 1307 passed; the 49 branch-new failures were the
  retired faces' rigs and two integration tests: 26 re-pointed through
  the Room's entries (no capability lost), 21 retired with reasons
  naming their replacements, the blank + cancel legs ported to a new
  door-legs rig, the rest selector/fixture edits.
- Web baseline on the final tree: 2426 passed, zero branch-new.
- The phase's rigs alone (door, room, door legs, 168 connections, 168
  wings, the isolated walk) captured in evidence-story-07.md.
- final-summary.md: what shipped, what the desk found, the debt ledger
  (incl. the three legs whose live coverage is to be re-pointed), the
  Tuesday Arc pointer.
- Phase 168 closed as superseded inside this branch (05 and 07 flipped
  with their evidence).
- PR feat/the-streamlined-door → main on the local gates; merged on the
  owner's word ("LET'S MERGE").
