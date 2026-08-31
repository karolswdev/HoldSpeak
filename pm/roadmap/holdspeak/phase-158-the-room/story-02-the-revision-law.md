# HS-158-02 - The revision law: one increment, one change, one event — atomically

- **Project:** holdspeak
- **Phase:** 158
- **Status:** done
- **Depends on:** HS-158-01
- **Unblocks:** HS-158-03, HS-158-04
- **Owner:** unassigned

## Problem

DOM-003/004 and API-001..004 are the aggregate's spine: every accepted
mutation increments `projects.revision` exactly once and appends its
`project_changes` row and `ServiceEventLedger` event in the same
transaction; writes take `expected_revision` + `command_id`; replays
return stored results; conflicts are typed. P0 froze the names
(`project_contracts`) — this story is their first consumer.

## Scope

- **In:** graduate `ProjectService` writes (create/update/archive +
  new `restore_project`, resource add/remove, meeting assoc/disassoc):
  one transaction per command; revision increment + `project_changes`
  append (`pchg_` deterministic ID) + `append_in_transaction` event
  (`project.created/updated/archived/restored/resource.linked/
  resource.unlinked`); optional `expected_revision`/`command_id`
  params (absent = legacy behavior, present = enforced — API-006
  compatibility); `project_commands` stores request hash + result for
  idempotent replay (API-002); results carry the envelope fields
  ADDITIVELY (existing keys unchanged; `result_kind`,
  `project_revision`, `changed_refs` added); typed errors from
  `ProjectErrorCode`. Routes pass the new params through. Every P0
  characterization update is deliberate, additive, named in this
  story's notes.
- **Out:** item commands (03), any read shape change beyond additive
  fields, MCP exposure (P6).

## Acceptance criteria

- [ ] TST-002-style: revision conflicts return typed `stale_revision` without partial mutation (forced mid-write failure leaves no orphan change/event row); same `command_id` + same hash replays the stored result; different hash returns `idempotency_conflict`.
- [ ] Every write's change row, ledger event, and revision commit atomically — proven by a fault-injection test.
- [ ] `restore_project` restores an archived Project (DOM-011) with event + revision; DELETE-is-archive behavior unchanged (the verb keeps its 157-pinned meaning; restore is a new POST route).
- [ ] Legacy calls without the new params behave exactly as the 157 pins say (additive keys only).
- [ ] `changed_refs` values parse through `holdspeak.refs` (the modules join the REF-001 fence list).

## Test plan

- **Unit:** `tests/unit/test_project_revision_law.py` (atomicity, conflicts, idempotent replay, restore); updated characterization files (additive deltas only).
- **Integration:** route-level pass-through tests.

## What shipped

- All eight ProjectService writes graduated to the revision law:
  one transaction = revision+1 exactly once + `project_changes` row
  (deterministic `pchg_`) + ledger event (`project.created/updated/
  archived/restored/resource.linked/resource.unlinked`; meeting
  association rides `project.updated` — §10 has no meeting event kind,
  no semantics invented) + additive envelope (`result_kind`,
  `project_revision`, `changed_refs` as canonical refs).
- `expected_revision` → typed `stale_revision` ConflictError (409),
  no partial mutation (fault-injection proven: a failure inside the
  transaction rolls back revision, change row, and event together).
  `command_id` → request-hash idempotent replay; different hash →
  `idempotency_conflict`. Absent params = exact legacy behavior.
- NEW `restore_project` + `POST /api/projects/{id}/restore`:
  archived → restored (lifecycle 'active', revision law); already
  active → honest `no_change` (no bump); unknown → 404. API surface
  regenerated.
- `project` joined `CITIZEN_TYPES` (deliberate, SRS §3.1-grounded:
  the aggregate is a citizen); changed_refs parse through
  `holdspeak.refs`.
- Eight characterization pins updated — every one a superset
  assertion (legacy keys still required; envelope keys now also
  asserted); zero status-code or message changes.
- `tests/unit/test_project_revision_law.py`: 40 tests (atomicity ×2
  fault injections, conflicts, replay, restore, exactly-one-increment,
  ref parsing). Orchestrator re-ran the full scoped set:
  334 passed, 1 skipped (the real-DB leg, correctly, under isolated
  HOME).

## Notes / open questions

- `is_archived` vs `lifecycle`: archive sets both; restore sets lifecycle='active' (no pre-archive lifecycle memory in P1 — posture history is P2 material).
- FOUND: `@observe_service` silently breaks `@staticmethod` descriptors (passes self positionally). Worked around with instance methods; worth a repo-wide audit note for counsel.
- project_service.py stays OUT of the ref fence list: it predates the central module (`qualified_ref` from db.relationships); its NEW emissions go through `holdspeak.refs`.
