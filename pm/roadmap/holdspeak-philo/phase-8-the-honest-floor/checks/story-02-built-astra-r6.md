VERDICT: **BOUNCE on MERGE — PR #672 at `f95e03ab`.**

FINDINGS:

1. **P2 — An unrelated delete erases a transferred rename refusal. Tenet 3.** In WebKit, at **1440 and 393**: submit “Inbox,” wait for NAME TAKEN, visit Chair, return, then delete another decision. The decision reaches **404**, the zone remains “New zone,” but its failure and Retry disappear. `web/src/desk/DeskApp.tsx:161` transfers the chip’s refusal without its subject; the new delete clear therefore removes it. No refusal was injected. [1440 proof](/tmp/holdspeak-astra-672-r6.3g4z8xyl/webkit-probes/zone-unrelated_delete-after-1440.json), [393 shot](/tmp/holdspeak-astra-672-r6.3g4z8xyl/webkit-probes/zone-unrelated_delete-after-393.png). **The identical probe passes at both widths on freshly rebuilt `ba55892e`.** [Baseline](/tmp/holdspeak-astra-672-r6.3g4z8xyl/baseline-webkit.log).

2. **The requested repairs hold.** At both widths, New Zone and note edits preserve A’s Delete failure and reachable Retry; Retry deletes A. A refused note update clears when that note is deleted. A failure retained across New Zone remains dismissible through OK. Successful zone rename clears its earlier refusal. **14 Chromium cases and 42 focused Vitest tests pass.** [Verification record](/tmp/holdspeak-astra-672-r6.3g4z8xyl/review-summary.json).

3. **No mismatched recovery clear found among the 13 subject-less callers.** Their operations and refusal counterparts were inspected; none completes the primitive edit/delete whose subject-bearing failure would remain. [Call-site audit](/tmp/holdspeak-astra-672-r6.3g4z8xyl/subjectless-audit.json).

CONDITIONS:

Preserve `directory:id` when transferring the rename chip into the desk receipt. Fence **seated refusal chip → face change → unrelated delete succeeds → failure and reachable Retry remain**, at both widths. Ship the repair, fence, and corrected claims together.

MISSED:

The producer census omitted `DeskApp`’s receipt transfer. The existing `tests/e2e/test_philo8_one_delete_glass.py:921` leaves the field before waiting for a refusal chip; it misses this transition.

TUESDAY: **No—the owner can delete another object and lose an unresolved rename’s reminder and Retry.**

UNKNOWN:

No full-suite or hardware/audio verification. The **actual atlas delete case passes at both widths**. Both archives passed `npm ci --ignore-scripts && npm run build`; their 857 web source files match their reviewed commits. Blank archive revision metadata is covered by [provenance](/tmp/holdspeak-astra-672-r6.3g4z8xyl/provenance.json).

Initial load **11.53 / 14.38 / 15.29**; final **6.39 / 7.61 / 10.44**. **The lane tree is unchanged.**