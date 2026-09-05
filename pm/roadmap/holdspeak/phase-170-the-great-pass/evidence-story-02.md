# Evidence - HS-170-02

- **Story:** HS-170-02 - The species sweep (library-level fixes that lift every face at once; the canon guards made mechanical)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-05T05:29:01Z

- **Command:** `uv run pytest -q tests/unit/test_ux_canon_scan.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_design_system_guard.py tests/unit/test_frontend_density_guard.py tests/unit/test_interior_canon_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d0290c229376d72114c99af6f045fad2bee7f76

```text
..................................                                       [100%]
34 passed in 0.90s
```

### Captured run — 2026-09-05T05:29:14Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d0290c229376d72114c99af6f045fad2bee7f76

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2184 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```
