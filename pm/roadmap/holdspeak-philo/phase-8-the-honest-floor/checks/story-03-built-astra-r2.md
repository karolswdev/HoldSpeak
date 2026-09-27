VERDICT: **BOUNCE on MERGE — PR #674 at `4905986f`.** The timing proof can still certify the pre-fix product.

FINDINGS:

1. **Blocking: the guard precedes Playwright’s wait, not actual delivery.** `scripts/graph_walk.py:3918` checks the guard; `scripts/graph_walk.py:3944` then permits a 10-second click wait. On unchanged `267f692a` at 393, I temporarily disabled only the click target for 8.5 seconds. The real guard read **Undo · 08s**; the actual click arrived with **pending=false, “Removal committed”**; the case **PASSED**. The timer again supplied the result attributed to leaving. [Event trace and verdict](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo803-r2-y8ncmrpa/runs/before/delete_then_leave.gone-393-click_wait/probe.json:17). This fails **Tenet 3 and Article IX**.

2. **The original reproduction is fixed.** Pausing before `_ui_step` now produces BLOCKED at both widths. All **219 scoped unit tests passed**; `dw check` is clean. I also confirmed that the revised fences reject an invalid `then` action, malformed guard minimum, and an optional-only-`then` case without the required predicate. [Verification record](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo803-r2-y8ncmrpa/review-summary.json:1).

3. **The baseline qualification is honest.** My normal pre-fix face-change runs returned **FAIL at both widths**. The list Undo returned BLOCKED at 393 because no receipt appeared; its product failure remains covered by `docs/internal/philo/phase-8/one-delete/README.md:14`. Stored observations match **26 FAIL + 2 BLOCKED**, **28 face + 5 operation passes**, and **36 Phase 7 runs**. These totals were audited, not rerun wholesale.

4. **The HOME correction is honest; the close remains premature.** Cleanup now measures removal, and retained rehearsal metadata admits the earlier retention. `scripts/philo8_rehearsal.py:232`. However, `pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/final-summary.md:3` cannot stand unqualified while finding 1 remains.

CONDITIONS:

- Enforce the guard at actual event delivery, including Playwright’s waiting period. Fence this real-atlas reproduction: expired actions must block; normal pre-fix failures must remain failures. Rerun the three affected gestures serially at both widths.
- Record this check and make the close conditional until the remaining blocker is paid.

MISSED:

1. The new regression test injects its pause **before** the guard, leaving waiting **inside** the click untested. `tests/e2e/test_philo8_03_then_guard.py:51`.
2. Minor documentation drift: the `docs/internal/philo/phase-8/atlas/README.md:43`, contradicting guarded Undo.

TUESDAY: Yes for the rehearsed product jobs, with the recorded selection/menu debts; this remains rehearsal evidence, not the owner’s sitting.

UNKNOWN: No full-suite, full-atlas, or full-rehearsal rerun. Reused r1 frontend builds after verifying product sources against Git. Sampled load: **2.04–7.02**; final **2.69 / 3.84 / 4.68**. **The lane tree is unchanged.**