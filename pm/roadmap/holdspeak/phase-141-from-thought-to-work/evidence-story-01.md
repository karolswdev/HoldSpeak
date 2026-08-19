# Evidence — HS-141-01 Raw before AI

**Result:** done; final adversarial counsel **RATIFY**.

## Shipped contract

- One transaction creates the immutable raw UTF-8 snapshot/hash, ordinary
  working Note, revision history, aggregate command record, and qualified Inbox
  filing. A caller-stable request key makes lost-response retry return the same
  aggregate; a changed payload refuses.
- Content, lifecycle, attachment, and aggregate cursors are distinct. Every
  aggregate change has an immutable canonical command record, and every thought
  DTO/conflict returns the cursors required for the next safe command.
- Thought-owned Notes cannot be overwritten through generic Note routes,
  low-level public repository helpers, or paired-device last-write-wins merge.
  Completed thoughts refuse edits until an explicit Resume transition wins CAS.
- Filing remains independent organization: moving or unfiling a live thought
  does not destroy custody. Terminalization atomically closes the aggregate,
  Note, and qualified membership.
- Paired sync verifies canonical command continuity and hashes, replays exact
  suffixes, converges same-content lifecycle changes, and holds an absolute
  terminal fence keyed to the working Note. First tombstones, delayed filing,
  divergent live packets, and exact full-packet tombstone retries are covered.
- Raw original retrieval is owner/paired-device authorized and no raw mutation
  route exists. Existing ordinary Notes retain their prior CRUD behavior.

## Design and adversarial proof

The ruled implementation design is
[`assets/hs-141-01-design.md`](./assets/hs-141-01-design.md). Three implementation
rounds exposed one invariant class—lifecycle and sync ordering—so the
orchestration circuit breaker stopped patching. A fresh design beat introduced
the aggregate command ledger and independently versioned filing; design counsel
ratified it before implementation resumed.

Subsequent adversarial reproductions proved and fixed: caller-controlled Note
capture, forged command cursors, incomplete fresh-peer history, same-content
completion drift, tombstone-before-live resurrection, delayed membership,
missing-Note restart repair, raw-route authority, mandatory cursor responses,
same-payload terminal ordering, and exact tombstone replay. Final counsel verdict:
**RATIFY**.

## Local verification

Run by the orchestrator on the assembled tree:

```text
uv run pytest -q \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_web_routes_sync_primitives.py \
  tests/unit/test_primitive_contract.py \
  tests/integration/test_primitive_framework_sync.py \
  tests/unit/test_web_routes_primitives.py \
  tests/unit/test_web_routes_sync.py \
  tests/unit/test_db_primitives.py

109 passed in 25.33s
```

`uv run python -m compileall -q holdspeak` and `git diff --check` passed. GitHub
Actions was not watched or used as a gate, by owner ruling.

## Honest boundary

HS-141-01 ships no UI, model call, proposal, or external effect. Existing Notes
are not silently adopted into thoughts; the Phase-140 bridge requires its later
explicit adoption transaction. Older paired clients that lack the compound
thought bundle may read but receive a named conflict instead of overwriting a
thought-owned Note.
