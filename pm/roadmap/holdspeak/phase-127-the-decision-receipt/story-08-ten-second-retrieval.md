# HS-127-08 — Ten-second retrieval

- **Project:** holdspeak
- **Phase:** 127
- **Status:** backlog
- **Depends on:** HS-127-07
- **Unblocks:** HS-127-09
- **Owner:** unassigned

## The thesis (the bar)

Decision memory earns its cost only when the answer arrives before archive
archeology begins. “Why Kafka?” must rank the governing receipt ahead of the
meeting, artifact, and other supporting material.

### What changes

1. Index decision text, rationale, alternatives, owner, and work-link labels.
2. Extend FTS query and ranking with receipt-first result semantics.
3. Return concise receipt facts, lifecycle, and evidence/work links.
4. Preserve existing `decisions_memory_fts` behavior for its current callers.

## Acceptance criteria

1. Queries match every indexed receipt field, including linked-work labels.
2. A relevant receipt ranks before its supporting artifact or meeting.
3. Results identify current versus superseded receipts and expose lineage.
4. Search remains local and gives an honest empty result when nothing matches.

## Test plan

- Search: verify field coverage and ranking for “Why Kafka?”-style queries.
- Search: assert a superseded predecessor carries its lifecycle signal.
- Regression: run existing decision-memory search cases unchanged.
