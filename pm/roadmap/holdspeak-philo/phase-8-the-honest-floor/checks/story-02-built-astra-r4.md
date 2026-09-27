VERDICT: **BOUNCE on MERGE — PR #672 at `daedfc99`.**

FINDINGS:

1. **P2 — Workbench’s successful removal of B erases A’s unresolved failure and Retry. Tenet 3.** Reproduced at **1440 and 393**: refuse A’s Remove, remove B, then let B commit. The hub retains A, deletes B, and the failure disappears permanently. `useWriteReceipt.ts:172` still clears the local failure unconditionally; recording `subject` does not protect it. [1440 proof](/tmp/holdspeak-astra-672-r4.4i4p0vfz/probes/workbench-unrelated-commit-1440.json), [393 shot](/tmp/holdspeak-astra-672-r4.4i4p0vfz/probes/workbench-unrelated-commit-393.png).

   **Undo precedence itself is acceptable under Tenets 1 and 3.** A’s Retry returns when B is undone. The defect is its permanent loss when B succeeds.

2. **The r3 repairs are paid.** All **nine r3 probes pass**: renewed Workbench Undo preserves the item, phone failure/Retry are visible without scrolling, subject preservation works on the list, and repeated in-flight presses send one DELETE. [Results](/tmp/holdspeak-astra-672-r4.4i4p0vfz/r3-probes.log).

3. **The list-foot widening is lawful reuse of the existing seat.** At both widths, an initial rename refusal shows only the row chip while the field is open; after closing, one readable failure and Retry occupy the foot, with no top-bar duplicate. This preserves the ratified initial transition. [393 measurements](/tmp/holdspeak-astra-672-r4.4i4p0vfz/probes/rename-foot-only-393.json). The reopening exception below is inherited.

CONDITIONS:

Preserve A’s failure across B’s successful Workbench Remove. Fence **A refused → B removed → A’s Retry returns and works**, at both widths, alongside the cancellation path. Ship repair, fences and evidence together.

Classify the recurring resize console error below before claiming that fence green; record the inherited rename duplicate in the follow-up ledger.

MISSED:

1. The unrelated-failure fence exercises the **desk/list channel**, not Workbench’s local `useWriteReceipt`: `tests/e2e/test_philo8_one_delete_glass.py:790`. The two channels still clear failures differently.
2. **Inherited, Tenet 3:** close a failed rename, reopen that zone with F2, and submit the taken name again: the row chip and old receipt show together. This occurs on `daedfc99` and `a84d1a37`; round five moves the old copy into the foot. [Current shot](/tmp/holdspeak-astra-672-r4.4i4p0vfz/probes/rename-reopened-393.png), [baseline reproduction](/tmp/holdspeak-astra-672-r4.4i4p0vfz/baseline-rename.log).

TUESDAY: **Not yet—the owner can resolve B’s removal and lose the visible reminder and Retry for A’s failed removal.**

UNKNOWN:

Resize starts DELETE within **65–81 ms** and reaches GET 404, but **two of four runs** fail the console check with `Cannot read properties of null (reading 'x')`. Two baseline runs passed; the cause remains unclassified. [Failure](/tmp/holdspeak-astra-672-r4.4i4p0vfz/resize-rerun2.log).

**37 focused Vitest tests** and the **actual atlas delete case at both widths** pass. No full-suite or hardware verification. [Verification record](/tmp/holdspeak-astra-672-r4.4i4p0vfz/review-summary.json).

Initial load **4.56 / 13.09 / 14.56**; recorded probe one-minute loads **6.39–11.54**; final **4.04 / 5.89 / 8.77**. Archives were installed and built with Node 22; all **856 web source files** match the reviewed commit. Atlas Git metadata is blank, covered by [provenance](/tmp/holdspeak-astra-672-r4.4i4p0vfz/provenance.json). **The lane tree is unchanged.**