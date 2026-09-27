VERDICT: **BOUNCE on MERGE — PR #674 at `edd90f0e`.** The product checks pass; the new timing proof can falsely pass the pre-fix product.

FINDINGS:

1. **Blocking: `then` does not enforce “inside the undo window.”** On unchanged `267f692a`, `delete_then_leave.gone` fails normally. Injecting an 8.5-second scheduling pause after its pending check makes the same case **PASS**: before the face click, the receipt already says “Removal committed.” The timer supplied the DELETE/404 that the predicate attributes to leaving the face. [Reproduction and trace](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo803-check-fy7os9n1/timing-probe/probe.json:9). The gap lies between `docs/internal/philo/graph/atlas-phase8.json:2221`; `scripts/graph_walk.py:5013` supplies no deadline. This fails **Tenet 3 and Article IX**: the fence can certify a different job.

2. **The normal product runs pass.** I ran five actual atlas cases at **1440 and 393**: Undo, two deletes, Floor name refusal, Chair Delete withheld, and delete-then-leave. **10/10 passed**, with zero page errors. Both archives passed real `npm ci --ignore-scripts && npm run build`. All 207 scoped tests were verified: 206 passed in the archive; the Git-dependent test passed separately with repository history available. [Verification record](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo803-check-fy7os9n1/review-summary.json).

3. **The historical BLOCKED result is labelled honestly.** It proves no failed outcome at 1440. The stored 393 run fails because B remains **200**, and the merged runs reach **404/404**. That supports the repair, with the stated qualification; BLOCKED must remain distinct from red. `pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/main-267f692a/20260926T220819Z-case.p8.delete_twice.both_gone-muaddib-393/observation.json`.

4. **The rehearsal read-backs are real.** I also read its retained isolated database: both Undo rows have `deleted=0`; both widths’ A, B and leave rows have `deleted=1`. [DB read-back](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo803-check-fy7os9n1/rehearsal-db-readback.json:100). The summary correctly distinguishes the Opus stand-ins from Codex’s seven story-02 rounds, preserves the debts, and leaves owner review pending.

5. **Selection belongs in the ledger, not as a Phase 8 blocker.** The approximately **1.13:1** highlight/background contrast is credible; it is not the text contrast. Selection and replacement work. The shared `web/src/styles/global.css:68` explains the defect, and its `pm/roadmap/holdspeak/BACKLOG.md:1318` is an appropriate home under Tenets 1–3.

CONDITIONS:

- Enforce or observe the pending window **when the follow-up action is delivered**. An expired gesture must block. Fence the demonstrated delayed real-atlas case, then rerun the three affected gestures serially at both widths.
- Record this check and retain the exit-5 qualification. The existing `pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/story-03-the-atlas-cases-and-the-closing-proof.md:26` remains open.

MISSED:

1. The optional-step fence does not inspect `then`: `tests/unit/test_philo8_atlas.py:304` uses `tests/unit/test_philo_graph_atlas.py:85`, which visits only setup and the top-level trigger.
2. Rehearsal metadata falsely says HOME was removed. `scripts/philo8_rehearsal.py:228` only stops the hub; the directory remains. Correct the claim. This is a minor evidence defect.

TUESDAY: **Yes for the repaired jobs, with the recorded selection and menu defects; this is still rehearsal evidence, not the owner’s sitting.**

UNKNOWN: I did not rerun the full atlas or full suite. CI unit tests remain running; macOS integration/E2E remain queued. Live-case load averaged **2.92–11.80**, final **4.54 / 5.63 / 6.02**. **The lane tree is unchanged.**