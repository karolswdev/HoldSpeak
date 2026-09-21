# HS-202-01 - The first-use fence

- **Project:** holdspeak
- **Phase:** 202
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** Astra (lane A; Muad'Dib checks the built fence)

## Problem

From the surface inventory of 2026-09-20 (`docs/internal/SURFACE-INVENTORY-2026-09-20.md`, §6 story 01; appendices 01–04; Astra's check `docs/internal/checks/surface-inventory-astra.md`). The Seven Tenets govern: first-use first (2), one obvious move (3), the component framework (5), Workbench 2.0+ (6); Articles III and VI; UX-CANON A.

## Scope

- **In:** One deterministic, isolated smoke at 1440 and 393: the doors to the five jobs, visible completion of each, the truthful host before and after a run, save and refind, restart; it requires the expected content to load (no green on a loading ellipsis). Reuses the existing source-button ratchet; adds no census gates
- **Out:** the owner's real recording and real dictation (the sitting's exits, story 06); everything the inventory's §6 ledger records; faces the five owner jobs do not touch; the broad census numbers as gates (they are diagnostics re-run at phase close).

## Acceptance criteria

- [x] The normal smoke reports the observed inventory defects on this branch, with the failed step in plain words, at 1440×900 and 393×852.
- [x] An explicit expected-failure verification runs the same assertions, requires the exact named failures, and proves the working Phase 201 pieces. Setup, loading, import, save, or backend errors cannot count as an expected final-state failure.
- [x] Fixture audio, a stub engine, visible completion, planned and actual hosts, note save confirmation, and note/meeting recovery after a hub restart are checked. Surfaces must load their own content markers. Shots from both widths ship with the evidence.
- [x] The existing source-button ratchet is unchanged. No product controls or census gates are added; the owner's real voice remains the sitting's exit.

## Test plan

- **Focused:** collect and run `tests/e2e/test_hs202_first_use_smoke.py` normally and with `HS202_EXPECTED_FAILURES=1`; run the unchanged `tests/unit/test_ux_canon_ratchet.py`.
- **Full:** the isolated-HOME suite in `CLAUDE.md`, excluding `tests/e2e/test_metal.py`; name the expected failure mode when used. Read the output and restore unrelated generated evidence before staging.
- **Glass:** inspect the fence's screenshots at both widths. The owner's real recording and dictation remain story 06 / Phase 201 story 07.

## Notes / open questions

Lanes are assigned at build time under TWO-BRAINS §4 (default: Astra takes the backend and verification-harness work, Muad'Dib the faces; either brain checks the other's built lane before merge).

## Delivery boundary — owner's lane brief, 2026-09-20

This story ships the fence before repairs. The owner explicitly requires a
RED run on `50ca0dd6` plus a GREEN verification run with named expected
failures, proving that the assertions fire and that the working Phase 201
pieces pass. The unmarked smoke remains red until the repair stories land;
the phase's green-on-main exit remains open. This is fixture coverage,
never evidence of the owner's real voice or his sitting.

The acceptance list above makes the owner's explicit lane delivery order
concrete. It replaces the scaffold's generic repair-story requirement for a
green product smoke and its face-control checklist. Those remain obligations
of the repair stories and phase exit; no product repair is claimed here.

The built walk also found stale state after import: the transcript loads,
but the selected row withholds Run summary until reopened. The fence names
this `import-refresh` separately from the post-run `record-refresh` check.
It belongs to HS-202-02. Generic Notes search is also classified precisely:
Enter commits the highlighted row, but the typed query highlights an
unrelated program. Exact-title note search works. The owner may overrule
these amendments at the sitting.

## Delivery record

Astra verified the fixture fence; Muad'Dib checked it in two rounds.
Normal RED and strict GREEN are captured in [the evidence](evidence-story-01.md).
The full suite is not green: all eight failures have a classification and
follow-up in [the verification ledger](verification-ledger-story-01.md).
This done call covers the owner's RED-fence delivery boundary only.

## Follow-up — match the ruled story 02 design

The phone menus fold into Go: New Note and the Object and Window entries
must be reachable there, with no unusable separate title announced. Desktop
still checks all four menus. The note editor autosaves, so the fence checks
its own fresh Kept receipt for the edit before Save closes it, then checks
closure and exact persistence. This does not claim that Save emits a second
receipt. The literal after-click wording and source counsel are recorded in
[the follow-up check](checks/story-01-followup-muaddib.md); the owner may
overrule the interpretation. Story 01 stays done; no product code changes.


Verification is partial against the requested story 02 GREEN: the receipt,
New Note and both restart legs pass, but import-refresh remains red at both
widths and folded Object/Window entries are off-screen at 393. Inventory
still reports the exact original failures; strict mode plus the unchanged
ratchet passes 6 tests. See the final follow-up table in the evidence and the
remaining findings in the ledger. No source changes hide those failures.
