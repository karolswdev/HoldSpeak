# HS-139-07 — The walk

- **Project:** holdspeak
- **Phase:** 139
- **Status:** ready
- **Depends on:** 139-01, 139-02, 139-03, 139-04, 139-05, 139-06
- **Unblocks:** phase close
- **Owner:** orchestrator adjudicates

## Problem

The reckoning is not done until the reforged room is walked on the real
hub, task-first, and the after-pictures sit next to the census's
before-pictures.

## Scope

- **In:** a reusable walk harness (scripts/) that boots the real hub +
  production bundle, opens every settings room at 1440 and 393,
  zero-console-error asserted, AND completes three real tasks on glass:
  (a) change the push-to-talk hotkey; (b) add + test a destination at
  393 width; (c) change a folded RAW knob and prove the write
  round-trips. Before/after pairs against audit/ shots. Full suite +
  web suite at the orchestrator's gate. Fresh counsel before close.
- **Out:** unit-test-only proof; waived screenshots.

## Acceptance criteria

- [ ] Every room shot at both widths, zero console errors, no
  horizontal page scroll anywhere.
- [ ] All three tasks complete on glass with their writes verified via
  the API.
- [ ] Control counts measured by the harness match the 139-05 bar
  (face ≤8 tiles, on-glass ≤40 excluding RAW).
- [ ] Fresh counsel finds no P0/P1; lower findings fixed or ledgered.

## Test plan

- **E2E:** the walk harness against the real hub.
- **Full gate:** isolated-HOME parallel pytest (excluding metal) + web
  vitest; CI green on the PR.
