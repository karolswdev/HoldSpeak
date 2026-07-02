# HS-77-02 — A real runtime_queue frame for the Queue HUD

- **Status:** done
- **Severity:** MED
- **Depends on:** —
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; the schema-sensitive guards
  (snapshot/matrix/serialization) updated per the documented recipes when
  they fire; full suite green at ship.

## Done

Shipped: the pure frame builder, three transition broadcast sites, and
the HUD's real feed (rows reconcile in; a departing row resolves through
the ledger's own linger — the proof run caught the first pass deleting
instantly). 3/3 unit + the Playwright reveal/linger/prune proof. See
[evidence-story-02.md](./evidence-story-02.md).
