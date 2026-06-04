# HS-37-02 — Proposal persistence + lifecycle

- **Project:** holdspeak
- **Phase:** 37
- **Status:** not-started
- **Depends on:** HS-37-01
- **Unblocks:** HS-37-03, HS-37-04
- **Owner:** unassigned

## Problem

A proposal that lives only in memory can't be approved later, audited, or shown in the UI.
The proposal needs a durable home with an explicit status lifecycle and the audit fields
that make "no silent egress" provable after the fact.

## Scope

- **In:**
  - A repository in `holdspeak/db/` (default: a dedicated `ActuatorRepository`, mirroring
    the `IntelRepository` queue + `PluginArtifactRepository` precedents) storing proposals
    with:
    - the status ladder **`proposed → approved → executed | rejected | failed`**,
    - an **idempotency key** (a re-proposal of the same action for the same meeting/window
      doesn't duplicate),
    - `created_at` / `decided_at` / `decided_by` / `executed_at`,
    - the `target` / `action` / `preview` / `payload` / `reversible` from the
      `ActuatorProposal`,
    - an **audit trail** (per-transition: actor, from→to, timestamp, result/error).
  - Wire the host's `proposed` result (HS-37-01) to **persist** a proposal row when an
    actuator runs (still no execution).
  - Regenerate the canonical fresh-build schema snapshot
    (`tests/fixtures/db_schema_canonical.txt`) in the **same commit** as the schema change.
- **Out:**
  - The approval UI/API (HS-37-03) and execution (HS-37-04) — this story persists + reads,
    and exposes the repo methods those stories call.

## Acceptance criteria

- [ ] Proposals persist + reload with all fields; the status ladder is enforced (illegal
      transitions rejected, e.g. `executed` → `proposed`).
- [ ] Idempotency: proposing the same action twice for the same meeting/window yields one
      row.
- [ ] Each status transition writes an **audit entry** (actor / from→to / timestamp /
      result).
- [ ] `TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` passes with the
      snapshot regenerated in this commit.
- [ ] Suite green; the db package stays ruff-clean.

## Test plan

- Unit: round-trip a proposal; assert all fields + the audit trail.
- Unit: legal vs illegal transitions; idempotent re-proposal.
- Unit/regression: fresh-build schema snapshot matches (regenerated here).
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green;
  `uv run ruff check holdspeak/db/` clean.

## Notes / open questions

- Call domain methods as `db.<repo>.<method>(...)` (the Phase-31 container pattern); add
  the repo to the `Database` container + re-export in `holdspeak/db/__init__.py`.
- If a fake db double is used in tests, it needs the new repo property
  (`actuators = property(lambda self: self)` pattern from the Phase-31 lessons).
- Decision (deferred): audit log as a dedicated table vs the existing activity ledger —
  default a dedicated table tied to the proposal row.
