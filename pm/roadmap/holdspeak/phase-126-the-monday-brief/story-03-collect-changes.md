# HS-126-03 — Collect changes

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-02
- **Unblocks:** HS-126-07
- **Owner:** unassigned

## The thesis (the bar)

The Changed section reports material state transitions, not an observer log.
Reduce windowed `pipeline_events` by correlation so a person can see what
actually changed without being buried in retries and reads.

### What changes

1. Query pipeline events inside the brief period and group related attempts
   by correlation.
2. Reduce a failed operation followed by a successful retry to one cited,
   material change with its source reference.
3. Suppress successful repeated reads and other non-material observation
   noise.
4. Produce deterministic change candidates with concise text, detail, and
   priority suitable for brief persistence.

## Acceptance criteria

1. Each candidate cites the pipeline event or correlation chain that supports it.
2. A failed-then-retried operation creates one change, not multiple raw events.
3. Successful repeated reads do not appear in Changed.
4. Unrelated correlations remain distinct, and output ordering is deterministic.
5. Collection is limited to the requested brief window.

## Test plan

- Unit: reduce a correlation containing failure, retry, and success to one item.
- Unit: assert repeated successful reads yield no item.
- Unit: assert separate correlations and window boundaries are respected.
- Integration: seed `pipeline_events` and inspect collected candidates.
