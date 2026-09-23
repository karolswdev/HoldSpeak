# PHILO-3-01 canvas: the receipt strip at 393

`receipt-strip-393.html` (+ `.png`) shows the BUILT phone placement of the desk's
backstop write receipt in its three states: create failed, read failed, clean.
Each frame is the top 200 px of a real 393 px rig run on the final bundle
(`story-01-shots/20260923T065532Z-...failure_named-muaddib-393/before.png`,
`20260923T065539Z-...decisions_read.failure_named-muaddib-393/before.png` and `after.png`).
The strip stays as built until the owner rules.

**The one question:** ratify this strip under the bar at 393 (the create
label cuts the cause at the 12 px floor), or give the receipt its own
full-width row that moves the work down while a failure stands?

## Ruling (the owner, 2026-09-23): "Full-width row, work moves down"

While a failure stands, the write receipt takes its own full-width row above
the work at 393, so the whole cause reads with nothing cut; the desk shifts
down by one row until Retry or OK; the strip under the bar is withdrawn.

Built: `web/src/desk/components/DeskReceiptRow.tsx` (the row, in the desk
flow between the bar and the work, seated by the shell's one phone fact
`useCompactViewport`), `web/src/desk/hooks/write-receipt.css` (the row rules;
the label wraps, never cut; no viewport query). `receipt-row-393.html` / `.png`
shows the three states from real rig frames (create failed
`20260923T153941Z`, read failed `20260923T154013Z` before Retry, clean
`20260923T154013Z` after Retry). The strip board above
(`receipt-strip-393.*`, `state-*.png`) is the withdrawn design, kept as the
record of what was ruled on.
