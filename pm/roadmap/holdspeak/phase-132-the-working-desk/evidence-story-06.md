# Evidence - HS-132-06

- **Story:** HS-132-06 - Desk writes report their failures
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:26:49Z

- **Command:** `bash -c cd web && npx vitest run src/desk/hooks/__tests__/useWriteReceipt.test.tsx src/desk/components/__tests__/writeReceipts.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts --reporter=dot`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0f2b94a8d90b991f46f8319179e1ce70987af49f

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

··························

 Test Files  3 passed (3)
      Tests  26 passed (26)
   Start at  16:26:49
   Duration  3.43s (transform 3.06s, setup 285ms, import 4.12s, tests 1.28s, environment 1.31s)
```

## Orchestrator notes

- Also verified: forbidden WorkbenchWindow regions untouched (diff grep for
  PadGadget/dropHover/RUN chip = empty); desk.test.ts + 92 neighbor tests
  green in the worker's round; npx tsc --noEmit clean under my own run.
- Round 2 added the populated-floor mount: DeskChrome system bar carries
  the backstop receipt; near-mount claims silence it so one failure prints
  once. Guard proved end-to-end by injecting a swallowed write (2/7 guard
  assertions failed, then reverted).
- Recorded ledger (accepted, unfixed): 12 pre-existing swallowed writes
  outside scope (deliveryFactory, gate, prReceipts, steering x3, dataSlice
  update/delete/file verbs, recordingSlice); the catch-and-return-null
  genus at the api layer degrades reasons to WRITE REFUSED; createPrimitive
  200-without-id still quiet (pre-existing).
