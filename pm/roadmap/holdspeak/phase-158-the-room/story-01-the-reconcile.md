# HS-158-01 - The reconcile: the aggregate's bones, proven on a real-DB copy

- **Project:** holdspeak
- **Phase:** 158
- **Status:** done
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

## What shipped

- `holdspeak/db/schema.py` — SCHEMA_VERSION 66→67: `projects` +15
  columns (§5.1; lifecycle NOT NULL DEFAULT 'active', revision
  DEFAULT 0, rest nullable), `project_resources` +3 (§5.2), new
  `project_items` (17 cols, idx project_id+item_type),
  `project_changes` (11 cols, idx project_id+project_revision),
  `project_commands` (9 cols, idx project_id+status) — FKs ON DELETE
  CASCADE, named columns throughout.
- `holdspeak/db/projects.py` +408 lines: 13 named-column repo helpers
  (room fields get/update, item/change/command CRUD, resource room
  fields) — primitives for 02/03; nothing calls them yet.
- Canonical snapshot regenerated per the recorded `r'\s+'` gotcha —
  diff confined to the new lines.
- `tests/unit/test_project_room_schema.py` — 14 tests: fresh shape,
  legacy reconcile (adds columns, idempotent, archived survives),
  REAL-DB proof (owner's 38 MB DB at
  `~/.local/share/holdspeak/holdspeak.db` COPIED to tmp; reconcile
  changed=True then changed=False; IDs stable; 0 projects exist so
  the proof is structural).
- Orchestrator verification: the worker's note "lifecycle gets ''"
  was disproven empirically — a seeded legacy row reconciles to
  `lifecycle='active'`, `revision=0` (`_constant_default_for` only
  substitutes for function defaults). Scoped gates: 14+5+3+62+46
  green under isolated HOME (captured).

## Notes / open questions

- Lifecycle default for legacy rows is `active` (verified empirically post-reconcile); `is_archived=1` rows read archived regardless — 02 reconciles the two signals in the service, not the schema.
- The owner's real DB holds zero projects today — the real-DB proof is structural; the first real Project arrives via this phase's own work.
