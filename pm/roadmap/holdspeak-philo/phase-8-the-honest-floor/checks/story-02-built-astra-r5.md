VERDICT: **BOUNCE on MERGE — PR #672 at `ba55892e`.**

FINDINGS:

1. **P2 — New Zone erases an unrelated Delete failure and Retry. Tenet 3.** Reproduced at **1440 and 393**: refuse A’s Delete, then create a zone. POST returns **201**, A remains **GET 200**, but its failure and Retry disappear. `web/src/desk/store/dataSlice.ts:382` calls the unconditional `web/src/desk/hooks/useWriteReceipt.ts:239`. [1440 proof](/tmp/holdspeak-astra-672-r5.3eyl9ues/probes/desk-create_zone-after-1440.json), [393 proof](/tmp/holdspeak-astra-672-r5.3eyl9ues/probes/desk-create_zone-after-393.json).

2. **The Workbench repair is paid.** The r4 probe passes at both widths: A’s failure returns after B’s Undo, survives B’s successful commit, and its reachable Retry deletes A. [1440](/tmp/holdspeak-astra-672-r5.3eyl9ues/probes/workbench-unrelated-commit-1440.json), [393](/tmp/holdspeak-astra-672-r5.3eyl9ues/probes/workbench-unrelated-commit-393.json). Successful zone rename also preserves the Delete failure at both widths; Retry works.

3. **The sprite guards are sound; the classified error did not recur.** The callbacks at `engine.ts:423`, `:571`, `:678` retain their URL check and additionally skip destroyed sprites only. At `-n 4`: **38 passes, two timeouts before resizing, zero page errors** across 40 runs. Two serial reruns pass, with DELETE starting **69–72 ms** after resize and reaching GET 404. [Verification record](/tmp/holdspeak-astra-672-r5.3eyl9ues/review-summary.json).

CONDITIONS:

Preserve unresolved Delete failures across unrelated successful desk writes. Fence **A refused → New Zone succeeds → A’s failure and reachable Retry remain → Retry deletes A**, at both widths. Ship the repair, fences, and corrected claims together.

MISSED:

“One rule in both channels” remains stronger than the implementation. The desk’s subject check sits inside `deletePrimitive`; other successful writes bypass it. The create path reproduces this; `updatePrimitive` also clears unconditionally at `web/src/desk/store/dataSlice.ts:547`, inspected but not exercised.

TUESDAY: **No—the owner can create a zone and silently lose the reminder and Retry for an unresolved deletion.**

UNKNOWN:

No full-suite or hardware/audio verification. **39 focused Vitest tests** and the **actual atlas delete case at both widths** pass. [Atlas observations](/tmp/holdspeak-astra-672-r5.3eyl9ues/atlas-summary.json). The two parallel receipt timeouts remain a limitation; I do not claim 40/40 green.

The archive passed `npm ci --ignore-scripts && npm run build`; all **857 web source files** match the reviewed commit. Atlas revision metadata is blank, covered by [provenance](/tmp/holdspeak-astra-672-r5.3eyl9ues/provenance.json). Initial load **26.89 / 23.73 / 21.66**; resize one-minute loads **13.05–26.59**; final **5.13 / 11.48 / 15.81**. **The lane tree is unchanged.**