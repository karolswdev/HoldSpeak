VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **r2 F1 is only partly paid. — Tenets 3/7; Article VI.** Prepare A → inline B accepted → close destination → send A failed → reopen destination: the header correctly says **LAST SEND FAILED**, but the expanded preview still shows B’s green **ACCEPTED BY SENDGRID** beside **Send again**, without identifying it as an earlier attempt. Reproduced at both widths; the rendered assertion fails. The receipt still uses the separately cached outcome at `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/SendWell.tsx:383`. Evidence: [1440 shot](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r3-p18y2js3/exact-order/old-success-after-new-failure-1440.png), [393 shot](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r3-p18y2js3/exact-order/old-success-after-new-failure-393.png).

2. **r2 F2 is paid.** At both widths, the held prepared send remains **SENDING** through Back → return, its destination’s Send stays disabled, and release produces **POSTED** without reloading. The destination header also correctly follows dispatch order. [Fresh observations](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r3-p18y2js3/review-summary.json).

3. **The clock correction and stated measurements reproduce with fresh data per width.** Clock changes alter raw screenshots but leave masked screenshots identical; B stays clean; no duplicate boards remain. Verified **120 renders, 238/238 named elements, 2,122 proposal controls × 9 points owned**, zero proposal text below 12 px, zero proposal raw buttons, and minimum contrast **4.504447711:1**. [Measurements and provenance](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r3-p18y2js3/review-summary.json).

4. **Nonblocking harness defect: the default combined-width run shares fixture history. — Tenet 3.** Desktop’s Priya row survives into the phone run; board 34b selects that earlier row, making 34/34b identical and correctly exiting **2**. The documented isolated phone invocation exits **0**. Evidence: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py:897`, [combined-run evidence](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r3-p18y2js3/combined-run-summary.json).

CONDITIONS:

Before owner ratification, prevent an earlier acceptance from appearing as the current expanded Send result. Fence the exact finding-1 sequence through reopening at both widths, with rendering and assertions changed together. Finding 4 is harness debt, not an additional canvas blocker.

MISSED:

1. Highest owner cost: the header and expanded receipt still derive their results separately.
2. Lower review cost: fresh browser contexts do not isolate the shared hub’s history.

TUESDAY: Running work is now readable; the older green receipt beside Send again can still mislead the owner about the latest failed attempt.

UNKNOWN: Reviewed `3ea08733..57150286` in a fresh worktree; no repository files changed. Evidence uses unchanged proposal modules and shim on an isolated real hub. Remote delivery, native key custody, actual atlas cases, and the full product suite were not verified.