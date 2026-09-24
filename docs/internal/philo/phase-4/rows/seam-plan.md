# PHILO-4-02 — observed seam, before correction

The required 393 as-written run `20260924T065829Z` FAILS. Its first
decision row is `(12, 470, 369, 114)` in a 393×852 viewport. The three
bottom hit points at y=582 belong to `footer.arrival-capture-bar`.
The complete observation and shot are under this story's assets; retain
this red. The 1440 as-written run `20260924T065401Z` passes.

Muad'Dib's check (`checks/rows-seam-muaddib.md` in the phase) narrows the
claim: the current title and both verbs are readable; about 12 px of
bottom padding is covered. The whole-row fence is deliberately stricter.
A further wrapped line would put useful content under the bar.

Proposed correction: after a successful Generate renders its rows, move
the Arrival's existing scroll container only enough to bring the first
row above the capture bar. Use native instant nearest scrolling with
scroll-padding-bottom set from the measured capture bar height. Bind the
end-of-scroll clearance to the same height. Measure the container and bar;
do not use a fixed phone height. No automatic move on initial load,
failure, or triage. Keep the three-row cap, row
components, section order and all canvas geometry. Fence the rendered
Generate transition with browser hit tests, including a case where the
row starts covered. Re-run the actual atlas at both widths.

Additional existing obligation: the phase's story-03 amendment assigns
a breakage-in-lookback run here. Preserve the original as-written case.
Add a separately named variant with one extra setup request before the
first Generate: GET a deliberately absent decision, expect 404. The real
DecisionLifecycleService observer writes the pipeline failure. Run in a
process-only timezone chosen from the UTC hour to make the local hour 20,
asserted at runtime; no machine clock changes. Both daily
briefs must retain the same source failure with different item ids and
the old brief's durable rows/shelf unchanged. No Ack or Defer. Use the
same real LAN engine and cumulative chain, at both widths, and report
the variant separately. This pays the existing obligation; it does not
relax the as-written acceptance criterion.

Closing check correction: Generate already loses focus to body when it is
disabled during the request (PHILO-4-01). The scroll seam adds no focus
change; preserving Generate focus was not proved and is not claimed.
