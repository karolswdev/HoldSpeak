# Evidence — HS-72-04 — One actuator lifecycle

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **Schema v5** (`SCHEMA_VERSION 4 → 5`, `holdspeak/db/core.py`): a proposal
  is owner-typed. `actuator_proposals` gains
  `origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting','desk'))`
  and `meeting_id` drops NOT NULL (null exactly when `origin='desk'`).
  SQLite cannot drop NOT NULL in place, so the v≤4 upgrade runs the
  documented rebuild recipe inside the Phase-50 backup-then-apply path:
  FKs suspended, copy into the new shape (rows attached to the old
  `'companion'` sentinel become `origin='desk'` with NULL `meeting_id`,
  ids preserved verbatim so audit rows stay attached), swap, recreate
  indexes, **delete the sentinel meeting**. Fresh DBs get the new shape
  from `SCHEMA_SQL` directly.
- **The sentinel is dead everywhere**: `_COMPANION_MEETING_ID`, the
  on-demand fake-meeting creation, and the `AND m.id != 'companion'`
  exclusion in `db/meetings.py list_meetings` are all gone.
- **One decision lifecycle**: `actuator_shared.decide_proposal(ctx, db,
  proposal_id, *, decision, actor, belongs, executors)` — validate →
  scope-check (`belongs`) → audited transition → wire-safe terminal-
  rejection broadcast → execute-on-approve for targets in `executors`.
  All four decision routes are now thin callers: the meeting proposal
  route (`belongs`: origin=meeting + the meeting id; executors: slack —
  the HS-61-01 consent model preserved verbatim) and the three desk relay
  routes (`belongs`: origin=desk + target; executors: their target).
  Four copies of the skeleton became one.
- **Repository**: `record_proposal(..., origin="meeting")` validates the
  origin pairing (`meeting` requires a real meeting id; `desk` forces
  NULL); `ActuatorProposalRecord` carries `origin`;
  `proposal_to_dict` emits it (additive wire field).
- **Contract**: `actuator-proposal.schema.json` gains `origin` (enum) and
  nullable `meeting_id` with the pairing documented; the golden fixture
  updated (the schema's `additionalProperties: false` caught the new wire
  field exactly as designed — the HS-72-01 guard working in anger).
- **Snapshot**: `tests/fixtures/db_schema_canonical.txt` regenerated with
  the test's identical normalizer expression (the documented no-op regex,
  newlines preserved).

## Preserved by design (not "fixed")

- Slack's approve→execute-inline (Phase 61) — now expressed as the
  `executors` map entry rather than an inline branch.
- Voice macros stay immediate-dispatch (Phase 52) — untouched.
- Non-slack meeting targets keep Phase-37 behavior (approval flips state
  only) — the empty `executors` entries.

## Verification artifacts

- `tests/unit/test_db_actuator_origin.py` (new, 4 tests): the **real
  v4→v5 upgrade** proven against a v4-shaped database — desk rows
  re-typed with NULL meeting_id, meeting rows untouched, audit preserved
  verbatim, the sentinel meeting gone, and the pre-migration backup
  (`v4.db.<ts>.bak`) present (the Phase-50 contract). Plus the
  origin-pairing validations.
- The affected slice: **123 passed** (db + schema policy + origin + the
  three relay suites + api-surface + primitive-contract).
- Every actuator/proposal/qlippy test file: **99 passed** (executor,
  repository, contract, reference, github/webhook actuators, live
  proposals, presence broadcasts, meeting proposals API — the Phase-56
  audit-parity behavior intact through the shared service).
- `contracts/validate.py`: ALL CHECKS PASSED (the updated proposal schema
  + fixture).
- Full python suite at ship: **3062 passed, 37 skipped, 0 failures**.
- One test expectation updated honestly: the relay slack test asserted the
  sentinel (`meeting_id == "companion"`); it now asserts
  `origin == "desk"` + `meeting_id is None` — the new contract, not a
  weakening.

## Acceptance criteria — re-checked

- [x] One propose→approve→execute implementation (`decide_proposal` +
      the execute legs in `actuator_shared`; four routes are thin callers).
- [x] The sentinel meeting row is gone (code, data migration, and the
      list_meetings exclusion).
- [x] Proposals carry an owner-typed origin, schema-enforced
      (CHECK constraint + repo validation + wire schema).
- [x] Migration honors the Phase-50 matrix (backup-then-apply proven in
      the new test; refuse-newer untouched and still covered by
      `test_db_schema_policy`).

## Deviations from plan

- The scaffold suggested the shared service might live under
  `holdspeak/plugins/`; it lives in `web/routes/actuator_shared.py`
  because HS-72-03 had already established that module as the shared
  seam and both callers are routers. Same architecture, shorter path.

## Follow-ups

- The coders status payload still reports desk connector config
  (`connectors.*`) — placement decided in HS-72-10.
- `ActuatorProposal` Pydantic/plugins contract (`plugins/actuators.py`)
  untouched — proposals flow through the DB repo; if the plugin-side
  dataclass ever grows origin, the wire schema already covers it.
