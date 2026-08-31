# HS-158-03 - The items: typed workstreams, milestones, risks, dependencies, signals

- **Project:** holdspeak
- **Phase:** 158
- **Status:** backlog
- **Depends on:** HS-158-02
- **Unblocks:** HS-158-05
- **Owner:** unassigned

## Problem

SYS-030/031: the Project owns typed milestones, risks, dependencies,
workstreams, and signals with stable IDs, lifecycle, ordering,
revision, and provenance — created through the same application
service Web and MCP will use. `details_json` is closed per type
(AD-PRJ-008: no dumping ground).

## Scope

- **In:** `ProjectService` item commands under the 02 revision law:
  create/update/transition/list items (`pitem_` IDs); closed
  `details_json` schema per `item_type` validated before persistence
  (DB-004) — unknown fields refused; lifecycle per type (a date
  passing cannot complete a milestone — DOM-007 guarded at the
  service); `owner_ref`/`created_by_ref` as qualified refs through
  `holdspeak.refs`; `provenance_kind` = `owner` only in P1 (proposals
  are P2; the column exists, the enum is enforced). Routes:
  `GET/POST /api/projects/{id}/items`,
  `PATCH /api/projects/{id}/items/{item_id}`. Bounded,
  deterministically ordered lists (sort_key, then created_at, then
  id — NFR-002).
- **Out:** proposals/review flow (P2), item display polish beyond
  what 05's Room face needs, bulk operations.

## Acceptance criteria

- [ ] Each of the five item types round-trips with its closed details schema; an undeclared field or wrong type is a typed `validation` error.
- [ ] Item mutations obey the revision law (revision + change + event atomically; idempotent under command_id).
- [ ] Narrative prose cannot complete a milestone: transition requires an explicit lifecycle verb (DOM-007).
- [ ] List reads bounded + deterministically ordered; pagination stable.
- [ ] Route surface manifest updated; API-surface fence green.

## Test plan

- **Unit:** `tests/unit/test_project_items.py` (five types, closed schemas, lifecycle verbs, ordering, revision-law compliance).
- **Integration:** items routes through the real app.

## Notes / open questions

- Keep the per-type schemas minimal-but-real (the SRS table's common fields are first-class columns; details_json holds only type-specific extras).
