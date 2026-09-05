# HS-169-07 - The close (gates, the sweep, counsel, the debt ledger, final summary; 168 folded)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** in-progress
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

## Delivered

_(pending)_
