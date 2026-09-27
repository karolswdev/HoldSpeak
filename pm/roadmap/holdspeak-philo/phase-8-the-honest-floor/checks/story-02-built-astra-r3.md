VERDICT: **BOUNCE on merge — PR #672 at `a84d1a37`.**

FINDINGS:

1. **P1 — Workbench’s renewed Remove hides Undo. Tenet 3.** After a refusal, press Remove again: the old failure remains, no Undo appears, and the item is deleted when the window expires. Reproduced at **1440 and 393**, with one new DELETE and an empty item list. `web/src/desk/components/WorkbenchWindow.tsx:1900` gives `writeReceipt` priority over the pending undo receipt. [1440 proof](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/workbench-new-window-1440.json), [393 shot](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/workbench-new-window-393.png).

2. **P2 — The phone list’s refusal is outside the viewport. Tenet 3.** Delete the visible decision at 393 and refuse its DELETE: GET remains **200**, but the failure occupies **y = −1196…−1138** and Retry is also offscreen. The pending receipt disappears without a visible failure. The fallback sits above the scrolling work at `web/src/desk/components/DeskReceiptRow.tsx:39`. [Measurements](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/phone-refusal-visibility.json), [shot](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/phone-refusal-visibility.png).

3. **The requested state repairs are paid.** All **13 selected r2 probes pass**. All three production commit callbacks return the boolean result; none discards a fallible write. At both widths, successful deletion of B preserves A’s failure, and successful Retry of A clears it. Repeated presses during a held commit send exactly **one DELETE** on list and Workbench, at both widths. Recreated references can be deleted again. [R2 results](/tmp/holdspeak-astra-672-r3.s1cybxvg/r2-probes.log), [six additional passing checks and three visibility failures](/tmp/holdspeak-astra-672-r3.s1cybxvg/r3-probes.log).

4. **Overlap ruling: acceptable by itself under Tenets 1 and 3.** The transient handoff never claims “Removal committed” on refusal and settles to the named failure. I would not require atomic clearing for this merge. However, “one render” is not evidence of one frame: the measured DOM overlap lasted **135–430 ms**. [Transition evidence](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/refusal-floor-1440.json). Finding 2 still requires the resulting failure to be visible.

CONDITIONS:

Fix findings 1–2. Fence **refusal → ordinary Remove → visible Undo → item retained** at both widths, and **phone refusal → readable failure and reachable Retry without scrolling**. Ship code, fences, and evidence together.

MISSED:

1. The Workbench fence waits through the renewed cancellation window without checking its receipt: `tests/e2e/test_philo8_one_delete_glass.py:694`.
2. DOM visibility and an automated Retry click do not prove viewport visibility; the click can scroll to the hidden control.
3. The changed resize assertion permits the correct in-flight wording, but still lacks an elapsed-time bound: `tests/e2e/test_philo8_one_delete_glass.py:781`. My [timed probe](/tmp/holdspeak-astra-672-r3.s1cybxvg/probes/timed-resize.json) confirms the actual fix: DELETE began **23 ms** after the press. Add that timing protection to the checked-in fence.

TUESDAY: **No—the owner can start a deletion whose Undo is hidden, or receive a refusal outside the visible list.**

UNKNOWN:

No full-suite, hardware/audio, or Clear done glass verification; its result contract was inspected. **37 focused Vitest tests** and the **actual atlas delete case at both widths** pass. [Vitest](/tmp/holdspeak-astra-672-r3.s1cybxvg/vitest.log), [atlas observations](/tmp/holdspeak-astra-672-r3.s1cybxvg/atlas-summary.json).

Initial load: **4.46 / 13.33 / 15.25**; recorded probe one-minute loads: **5.96–13.17**. The archive was installed and built with Node 22. Atlas Git metadata is blank; [provenance](/tmp/holdspeak-astra-672-r3.s1cybxvg/provenance.json) confirms all **856 web source files** match the reviewed commit. The lane tree remains unchanged.