# Evidence - HS-150-04

- **Story:** HS-150-04 - The web-inherited baseline (the debt rider)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T21:20:52Z

- **Command:** `bash -c uv run --python 3.13.11 python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 236dae0bc29ed6b1d6679af59fb1db6ca730d6d0

```text
Running vitest...

=== Web baseline report ===

BASELINE-MATCHED (6):
  src/desk/__tests__/chat.test.ts > the turn wire > posts question + the 12-turn tail + grounding refs; returns the honest egress
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

BRANCH-NEW (1):
  BRANCH-NEW: src/pages/cores/__tests__/ModelLibraryCore.test.tsx > ModelLibraryCore > keeps radio selection inert, restores Add focus, and maps Mod+Enter to the sole action

Suite totals: 1402 passed, 7 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

## Orchestrator triage note (2026-08-29)

Verified with my own run: the checker against the FULL web suite
(1409 tests) reports exactly the six chartered names
baseline-matched, zero branch-new, exit 0 — and the builder's
break-one proof showed BRANCH-NEW detection with exit 1, reverted
clean. All six re-verified byte-identical to main before listing
(no healing, no drift — the charter's names held). The checker is
stdlib-only, consumes --run or a prior JSON (the sweep hook the
close story needs), and counts only status==failed (skipped/todo
excluded honestly). Two arcs of carried debt end here: web
failures now speak the house vocabulary.

### Captured run — 2026-08-29T21:21:43Z

- **Command:** `bash -c uv run --python 3.13.11 python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0468f84a5701cd5cc605c538a0b2c5437f838e3e

```text
Running vitest...

=== Web baseline report ===

BASELINE-MATCHED (6):
  src/desk/__tests__/chat.test.ts > the turn wire > posts question + the 12-turn tail + grounding refs; returns the honest egress
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 1403 passed, 6 failed, 0 skipped

VERDICT: baseline-subset/exact, zero branch-new
```

## Orchestrator triage note (2026-08-29, after the gate refused once)

The FIRST capture attempt recorded exit 1 — and that refusal was
the story proving itself: the checker's second-ever real run caught
ModelLibraryCore ("…restores Add focus…") FLAPPING (green in the
orchestrator's run minutes earlier, red under capture — a
focus-timing shape). Serial ×2: 7/7 green twice. Ruling: a flake is
NOT inherited debt and never enters the baseline (baselining a
flake hides a reliability defect) — the protocol now says so in
tests/WEB_BASELINE.md, with this test as the flake families' first
web member (recurrence = DIAGNOSE). The re-capture above is green:
exactly the six chartered names baseline-matched, zero branch-new,
exit 0. Both-direction proof verified (the builder's break-one +
revert-clean); all six re-verified byte-identical to main at build
time. Two arcs of carried debt end with the vocabulary unified.
