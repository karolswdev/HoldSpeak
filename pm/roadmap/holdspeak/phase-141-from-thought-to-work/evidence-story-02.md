# Evidence — HS-141-02 The resumable thought

**Result:** done; final adversarial counsel **RATIFY**.

## Shipped contract

- Owner-only one-thought load and bounded unfinished pagination expose the four
  mandatory aggregate cursors and a compact continuity state. Raw text, source
  refs, prompts, hydrated context, native operation IDs, credentials, and result
  bodies stay out of list/load DTOs.
- Pagination uses an atomically allocated monotonic resume order and a signed
  keyset cursor. Same-second creates cannot leak into a fixed first-page
  snapshot.
- One logical refinement request owns immutable physical-attempt links. The
  base attempt and the runner's exact dialect follow-up must each bind their Ask
  and kernel identity durably before provider dispatch.
- The dialect child requires a durable retry plan naming the runner-derived
  child identity. A generic failed receipt or caller-forged child cannot
  authorize another attempt.
- Reconciliation is lookup-only: it may link one exact receipt-gated native Ask
  result, or terminalize stale, superseded, failed, refused, cancelled, missing
  child, or orphaned-before-binding states. It never dispatches, retries, edits
  a Note, or changes thought lifecycle.
- Winner proof checks the complete attempt/operation/receipt/projection-stage/
  Ask-result/result-ref/hash tuple and refuses multiple or mismatched winners.
- Continuity proof is hub-local because its native kernel/projection rows are
  hub-local. Paired sync carries no fake result links; NODE authority is not
  treated as owner read authority.

## Design and adversarial proof

The ratified design is
[`assets/hs-141-02-design.md`](./assets/hs-141-02-design.md). Design counsel
required immutable multi-attempt correlation, hub-local proof boundaries, and
named recovery for operations created before binding.

Implementation counsel reproduced and closed: same-second pagination leakage,
failed invocations holding the one-live slot, loose winner joins, NODE raw/list
access, forged dialect children, and the retry-planned/crash-before-child gap.
The final recovery rule looks up only the exact derived child: absence
terminalizes and releases the slot; an existing unbound child becomes named
orphaned state and is never rebound or retried. Final verdict: **RATIFY**.

## Local verification

Run by the orchestrator on the assembled tree:

```text
uv run pytest -q \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_inference_runner.py \
  tests/unit/test_ask_runner_migration.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot

86 passed in 25.52s
```

`uv run python -m compileall -q holdspeak` and `git diff --check` passed. GitHub
Actions was not watched or used as a gate.

## Honest boundary

This story exposes no user action that starts a model. Story 04 will invoke the
internal reservation/hook contract. Concrete attachment records remain Story
05, and the owner-facing Good-enough/reopen decision remains Story 06.
