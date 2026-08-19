# HS-141-07 — Typed outcomes, not magic

- **Status:** backlog
- **Depends on:** 141-04, 141-05, 141-06
- **Unblocks:** 141-08, 141-09

## Problem

AI prose is not a domain write. HoldSpeak needs useful suggested shapes without
a universal JSON mutation or a parallel proposal lifecycle.

## Scope

Add a narrow availability/schema adapter for a real additional local outcome.
Phase 141 supports Desk Decision. The completed working Note is already the
local Note result and must not be suggested again as a duplicate. Present an
editable Decision preview frozen to raw/working/context revisions. Acceptance
calls the canonical typed service with a stable request ID and returns its write
receipt. The refinement record may link preview/result; it owns no external
approval lifecycle.

## Acceptance

- [ ] Model can suggest the registered Desk Decision shape; redundant Note is
  suppressed unless a future adapter defines a distinct named purpose.
- [ ] Preview names source and context revisions and is not product state.
- [ ] Accept performs one owner-authorized typed service write; retry is stable.
- [ ] The caller-stable request ID maps to exactly one Desk Decision creation
  result; an ambiguous response is recovered by that mapping, never by a broad
  content search or arbitrary upsert.
- [ ] Source/context drift shows **Update proposal**, never a generic disabled
  action or stale write.
- [ ] Generic Note/Artifact/follow-through/Jira/calendar are not offered.

## Tests

Focused adapter/schema/service/idempotency/staleness/UI tests; forbidden-kind
and model-fabricated-field assertions.
