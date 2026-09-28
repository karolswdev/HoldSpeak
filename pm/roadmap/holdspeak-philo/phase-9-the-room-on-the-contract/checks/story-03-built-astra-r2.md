VERDICT: **RATIFY-WITH-CONDITIONS**

Reviewed `e77a5416` in a fresh worktree. Both round-one blockers are paid. Receipt isolation remains incomplete. No tracked files changed.

FINDINGS:

1. **Refused delivery is fixed.** The real hub refuses the draft delivery, writes no delivery row, and preserves `update_not_published`. At 1440 and 393, RECEIPTS shows a failure chip and **MARK DELIVERED · REFUSED · NOT PUBLISHED**. [1440 shot](/tmp/astra-pr686-r2-CXsr2W/atlas-refusal-1440/20260928T170022Z-case.p9.receipt_refusal_truth-astra-1440/after.png), [393 observation](/tmp/astra-pr686-r2-CXsr2W/atlas-refusal-393/20260928T170100Z-case.p9.receipt_refusal_truth-astra-393/observation.json).

2. **Review identity is fixed.** At both widths, Review opens the run’s accepted review by ID, shows only Close, and creates no new open review. The rendered identity assertions also pass. [Review observation](/tmp/astra-pr686-r2-CXsr2W/atlas-review-393/20260928T170200Z-case.p9.steward_review_identity-astra-393/observation.json).

3. **“Names the project’s ID exactly” is not robust.** Create project B, then create a risk in B whose **title equals A’s ID**: B’s CREATE ITEM receipt appears in A. Reproduced through real producers at both widths. The `holdspeak/services/project_service.py:296` accepts any matching JSON value, including free text. [Current observation](/tmp/astra-pr686-r2-CXsr2W/atlas-free-text-scoped-393/20260928T170509Z-case.p9.receipts_free_text-astra-393/observation.json), [same failure on `62375d84`](/tmp/astra-pr686-r2-CXsr2W/atlas-free-text-base-1440/20260928T170537Z-case.p9.receipts_free_text-astra-1440/observation.json). **Inherited, not a new blocker; fails Tenets 3 and 7.** The original foreign-project-name case is fixed, but the class is not.

4. **Independent checks pass within scope.** Story glass plus atlas validation: [117 passed](/tmp/astra-pr686-r2-CXsr2W/glass-atlas.log). Receipt mapping: [3 passed](/tmp/astra-pr686-r2-CXsr2W/receipt-vitest.log). Original refusal/review walks and the actual atlas delivery case pass at both widths; [walk results](/tmp/astra-pr686-r2-CXsr2W/verification-summary.json). Generated API reference checks pass. No new false-success rendering was observed for current producer outcomes. The committed six regression reds fail on the claimed visible or durable outcomes.

CONDITIONS:

Before merge, correct the story/evidence claim that the inherited leak is fully paid and give the remaining case an explicit backlog home and lane-owner disposition. Alternatively, fix it by matching the producer’s project-identity field and fence this case through the real producer. **I do not promote this inherited defect into a new code blocker.**

MISSED:

The remaining owner cost is misattributed project history. The isolation fence tests a foreign project’s name; it does not test another write’s free-text fields.

TUESDAY:

Yes for delivery confirmation and reopening a completed review; the Room’s receipt history still needs the named isolation debt.

UNKNOWN:

No full-suite or complete 2,941-test rerun; not every terminal outcome was produced live. All new walks used isolated homes. Session: `01a0e8f0-fd01-7ed2-86fb-82e3ba7a6d63`.