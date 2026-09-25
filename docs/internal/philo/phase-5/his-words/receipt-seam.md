# PHILO-5-04 — Fresh-read receipt seam

RATIFIED WITH CONDITIONS — [Muad'Dib's check](checks/receipt-seam-muaddib.md).
No product edit before the actual missing-receipt red.

The owner's lane brief requires a fresh/reopened Desk read with the next-day
decision in visible brief rows and `Brief ready …`. The existing brief loads
on that read, but its receipt does not: `ChairHome.tsx:523-532` sets `brief`
from GET `/api/brief/latest`; `briefKept` starts null at line 679 and is set
only by that browser's Generate handler at line 709. Codex's MCP generation
cannot set local React state. A browser Generate would create another brief
and would invalidate the requested proof that Codex did the job.

Tuesday: the owner should see the existing receipt for the saved brief that
Codex made. He should not have to generate it a second time.

Settled design:

- Reuse `briefReceipt` and the existing receipt slots in all rendered brief
  branches. When the latest-brief GET succeeds, set `briefKept` from that
  same returned brief, or clear it on a null response. Move the state
  declaration next to `brief`. Leave the receipt untouched on a failed read;
  a failure is not an absent brief.
- No new label, layout, verb, transport, operation, summary subscription or
  already-open brief refresh behavior. This uses the already-ratified receipt
  face; the narrow scope amendment is receipt hydration on a fresh read.
- Keep the real Codex run's strict receipt fence and retain its missing-
  receipt shots/readback before any fix. After the fix, run the same ordinary-
  language job from a fresh Codex session and isolate every hub HOME.
- Add a focused rendered fence using the real producer's retained brief
  response, including its generated timestamp, items and sections. Fence
  populated and empty/handled branches, and null/read failure. Run the
  existing brief receipt and load/date suites. No broad suite.

The Article III receipt now also identifies the latest durable brief on
arrival. This broadens the meaning of the existing face; it is not a claim
that product behavior remains unchanged. The subsequent Generate test must
replace the first receipt with a different real producer's count or time.
The timestamp comes from the producer's period end, not the wall clock at
which Codex called Generate.

This is a diagnosed surgical seam within Astra's lane role. It changes
product behavior and therefore visibly amends the phase's no-face-change
scope for this one existing receipt. The owner directly requires the result;
this is not an assertion that the present tree already satisfies it. The
four inherited product defects remain ledgered. Owner review stays pending,
and the PR stays unmerged.

Closing disposition: [Muad'Dib's check](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/checks/story-04-closing-muaddib.md)
adds two presentation-debt rows; the current lane ledger has six repairs
owed. No additional product change was requested.
