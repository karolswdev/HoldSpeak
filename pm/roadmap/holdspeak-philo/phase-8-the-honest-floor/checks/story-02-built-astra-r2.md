VERDICT: BOUNCE on merge — PR #672 at `d3eab7e8`.

FINDINGS:

1. **A successful delete hides an unrelated failed rename. Tenet 3.** At both widths, deleting a decision clears “RENAME ZONE FAILED · NAME TAKEN” and its Retry while the zone remains unchanged. The unconditional clear is at `web/src/desk/store/dataSlice.ts:581`. [393 reproduction](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/unrelated-rename-393.json).

2. **Workbench Remove becomes inert after refusal. Tenet 3.** After a DELETE 403, another Remove sends **zero requests** and keeps the item. Retry works. Reproduced at 1440 and 393. `web/src/desk/components/WorkbenchWindow.tsx:1204` discards the promise, so the hook never receives the failure and never frees its key. [Proof](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/workbench-refusal-1440.json).

3. **A recreated reference cannot be deleted again. Tenet 3.** Delete A, recreate it through `POST /api/decisions` with the same ID, refresh, then Delete: no receipt, no request, **GET 200**. Committed keys persist for the host’s lifetime; `web/src/desk/hooks/useUndoReceipt.ts:91` rejects the new object. [Proof](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/recreated-same-ref.json). Different-object Undo is correct: [A stays deleted; B survives](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/different-object-undo.json).

4. **“No ‘Removal committed’ on refusal” is still false. Tenet 3.** The hook announces success before awaiting the write at `web/src/desk/hooks/useUndoReceipt.ts:67`. With a delayed 403, list and Floor show “Removal committed,” briefly alongside the failure. Workbench also shows it before its failure receipt takes precedence. Reproduced on all three surfaces at both widths; Retry succeeds. [Rendered transition](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/refusal-list-1440.json).

CONDITIONS:

Preserve unrelated failures and their Retry; make Workbench return a failure result the hook understands; permit deletion of legitimately recreated references; announce commitment only after success. Fence these through real producers and rendered transitions, and update code, story and evidence together.

The earlier repeat/Undo, host-hoist and foot fixes are paid. At **1440**, setup recovery plus Undo succeeds **6.72 seconds** after the pending receipt appears, preserving the object with zero DELETE requests; the identical probe fails on `b65107f5`. [Green](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/auto-recovery-1440.json), [red](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/red-auto-recovery-1440.json). The [resize probe](/tmp/holdspeak-astra-672-r2.stx_kqvq/probes/timed-resize.json) commits before the timer expires.

All **30 story 01 browser cases**, **66 focused Vitest cases**, and the actual atlas delete case at both widths pass. [Browser results](/tmp/holdspeak-astra-672-r2.stx_kqvq/regression.log), [unit results](/tmp/holdspeak-astra-672-r2.stx_kqvq/vitest.log), [remaining unit results](/tmp/holdspeak-astra-672-r2.stx_kqvq/story01-vitest.log), [atlas observations](/tmp/holdspeak-astra-672-r2.stx_kqvq/atlas-summary.json).

MISSED:

1. The failure double returns `false`; Workbench supplies `void`. Merely returning its promise also needs result normalization: `write()` resolves `{ok:false}`, whereas the hook checks literal `false`. `web/src/desk/hooks/__tests__/useUndoReceipt.test.ts:197`.
2. The refusal fence reads the receipt **500 ms after failure**, missing the contradictory transition. `tests/e2e/test_philo8_one_delete_glass.py:618`.
3. The error names only **HTTP 403**; the returned refusal detail is discarded by `web/src/desk/hooks/useWriteReceipt.ts:50`.

TUESDAY: No—the owner can lose a failed rename’s Retry or press an enabled Delete that sends nothing.

UNKNOWN: No full-suite or hardware/audio verification. The 403s were injected against objects created through the real hub. Browser runs were serial: initial load **2.73**, recorded adversarial samples approximately **7.5–13.1**. Archive Git metadata is absent; [provenance](/tmp/holdspeak-astra-672-r2.stx_kqvq/provenance.json) verifies all 856 web source files against the reviewed commits. The lane tree is unchanged.