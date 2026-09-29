VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The destination can show an earlier success after the latest send failed. — Tenets 3/7; Article VI.** At both widths: prepare A → send inline B successfully → send A, which fails. A’s failure remains visible, but the destination still shows **ACCEPTED BY SENDGRID** from B. `lastFor` reverses preparation order, not dispatch order. Evidence: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/SendWell.tsx:297`, [fresh contradictory result](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/final-probes/last-send-wrong-393.png).

2. **A running prepared send disappears after Back → return. — Tenets 3/7; scar 3.** At both widths, holding the dispatch answer and reopening the update produces **zero prepared rows**, while the stored canvas row remains `dispatching`. The destination shows the previous failure and offers an enabled **Send again**. The filter explicitly excludes `dispatching`. Evidence: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/SendWell.tsx:294`, [four failing probes—two per width](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/final-probes/red-fences.json).

3. **The duplicate-board claim needs qualification. — Tenet 3; Article IX; nonblocking presentation issue.** Committed A3/A22 at 393 differ only in the menu clock. My isolated phone rerun captured identical bytes and correctly exited **2** on that pair. Record “B stays clean” as a fact, like the return to A, and exclude changing chrome from comparisons. Evidence: [pixel comparison and rerun measurements](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/review-summary.json).

4. **The original r1 probes have substantial, verified repairs.**

   | r1 | Recheck |
   |---|---|
   | F1 | Terminal failure remains visible without repositioning the view and survives Back → return; discard leaves DISCARDED. The broader last-result claim still fails finding 1. |
   | F2 | At 393, setup lands on the open form; Save → close shows the new destination without reload. |
   | F3 | All **232 named elements** passed visibility checks across 116 renders. The previously hidden outcomes are visible; finding 3 qualifies deduplication. |
   | F4 | Real SENT, UNKNOWN and manual records render as three rows, with **DELIVERY 2** and UNKNOWN kept separate. |
   | F5 | COMMENTED, BLOG POSTED, Confluence setup, named read failures, NO PREVIEW and KEY NOT SAVED are present. |
   | F6 | Check stays SENDER NOT VERIFIED after failure; prepared preview/receipt filenames match at both widths; tested literals preserve case. |

   Evidence: [independent transition probes](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/final-probes/probes.json), [Send board facts](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/phone/send/shots/facts.json), [Destinations board facts](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-693-r2-ljvsv8qh/phone/dest/shots/facts.json). Contrast remains **4.504447711:1**; no color repair is warranted.

CONDITIONS:

Before owner ratification:

- Keep a running prepared send visible through navigation and settlement.
- Derive the destination’s latest result from send order. Fence an older preparation dispatched after a newer inline send; use story 01’s real `dispatch_started_at` field.
- Capture both corrections at 1440 and 393, with words and fences together. Resolve or explicitly classify the redundant A3/A22 pair.

These are bounded canvas corrections; they require no remote transport build.

MISSED:

1. Highest cost: an earlier green result can misrepresent the owner’s latest failed attempt.
2. Next: running work disappears while another send remains available.
3. Review cost: clock changes can disguise identical boards.

TUESDAY: Setup and terminal receipts now work; the owner still cannot reliably see running prepared work or trust the destination’s latest-result summary.

UNKNOWN: Reviewed `d494845e..3ea08733` in a fresh worktree; repository files remain unchanged. Fresh browser probes used an isolated real hub and unchanged proposal modules/shim. Remote delivery, native key custody, actual atlas cases and the full suite were not verified. I reconciled the committed 1,936-control totals; the corrected-font rerun omitted the full pointer sweep.