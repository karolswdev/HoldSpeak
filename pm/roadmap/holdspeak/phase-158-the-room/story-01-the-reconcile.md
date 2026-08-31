# HS-158-01 - The reconcile: the aggregate's bones, proven on a real-DB copy

- **Project:** holdspeak
- **Phase:** 158
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-158-02
- **Owner:** unassigned

## Problem

The `projects` table is a knowledge-base container (name, keywords,
context_json, threshold). The Room needs identity, lifecycle, posture,
cadence, revision — and homes for items, changes, and commands.
SRS §5.1-5.3, §5.10-5.11 define the shapes; NFR-007/DB-001 demand
additive reconciliation that preserves every existing Project.

## Scope

- **In:** additive schema declarations in `holdspeak/db/schema.py`
  (the One Schema; `reconcile_schema` auto-adds declared columns):
  (a) `projects` gains §5.1's nullable/defaulted columns: `purpose`,
  `outcome_text`, `owner_ref`, `lifecycle` (default `active` — legacy
  rows are live projects), `posture`, `posture_reason`, `start_at`,
  `target_at`, `review_cadence_json`, `next_review_at`,
  `template_key`, `modules_json`, `revision` (default 0),
  `last_review_id`, `last_review_at`. `context_json` stays but is NOT
  truth for these (AD-PRJ-008).
  (b) `project_resources` gains `semantic_role`, `metadata_json`,
  `revision` (§5.2).
  (c) New tables: `project_items` (§5.3), `project_changes` (§5.10),
  `project_commands` (§5.11 first block) — named columns, FKs to
  projects, uniqueness per the SRS. IDs use `project_contracts`
  prefixes.
  (d) Canonical snapshot regenerated per the recorded gotcha (the
  test's normalizer is a literal-`\s+` no-op — regenerate with the
  IDENTICAL raw string so only new lines diff; build via a Python
  file, `uv run python`).
  (e) Repository layer additions in `holdspeak/db/projects.py` (or a
  sibling) for the new tables — reads/writes used by 02/03.
- **Out:** sources/observations/evidence/proposals/reviews/updates
  (P2), steward tables (P4), watch/setup tables (P1a), any service
  behavior change (02).

## Acceptance criteria

- [ ] TST-001: a pre-Project-Room database reconciles with zero data loss; repeated reconcile is idempotent; archive state survives. Proven against a COPY of the owner's real DB (copy to tmp; NEVER the live file; isolated HOME).
- [ ] All INSERTs named-column (the fence test stays green); no positional INSERTs; no destructive ALTER.
- [ ] Canonical schema snapshot regenerated; `tests/unit/test_db.py -k "schema or shape"` green; diff confined to new lines.
- [ ] `project_items.details_json` closed per `item_type` is declared (validation enforced in 03); FKs + uniqueness match the SRS shapes.
- [ ] P0's characterization suites still green (schema additions must not change any pinned shape).

## Test plan

- **Unit:** `tests/unit/test_project_room_schema.py` (reconcile fresh + legacy fixture + real-DB copy, idempotency, column presence/defaults); `tests/unit/test_db.py` snapshot legs; the positional-INSERT fence.
- **Scoped rerun:** P0 characterization files.

## Notes / open questions

- Lifecycle default for legacy rows is `active` (they are live projects; `is_archived=1` rows read as archived regardless — 02 reconciles the two signals in the service, not the schema).
