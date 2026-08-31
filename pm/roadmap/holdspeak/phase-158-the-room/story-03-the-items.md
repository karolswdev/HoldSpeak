# HS-158-03 - The items: typed workstreams, milestones, risks, dependencies, signals

- **Project:** holdspeak
- **Phase:** 158
- **Status:** done
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

## What shipped

- Four ProjectService item commands under the revision law:
  `create_item` / `update_item` / `transition_item` / `list_items` —
  each mutation one transaction (revision+1, change row,
  `project.updated` event — §10 has no item event kind, none
  invented), envelope additive, `expected_revision`/`command_id`
  honored. Items are project-OWNED records, not citizens:
  `changed_refs` carries `project:<id>`, `item_id` rides the payload
  (no `pitem` ref type — §3.2 respected).
- Closed vocabularies: severity `critical|high|medium|low` (nullable,
  validated; SEVERITY_RANK 0-3); per-type lifecycles (milestone
  planned|reached|missed|dropped; risk open|mitigated|accepted|closed;
  dependency healthy|at_risk|broken|resolved; signal active|retired;
  workstream active|paused|done — grounded in #514's vocabulary, no
  SRS doc prescribed exact names; choice documented).
- Closed `details_json` per type (DB-004): unknown fields/wrong types
  → typed `validation`. DOM-007 guard: transition requires an
  explicit verb (People-service convention:
  `POST /items/{id}/transition` with `{"verb": ...}`).
- INHERITED 04 DUTY PAID: `_read_room_items` severity ordering is now
  an explicit CASE rank (critical first; alphabetical-DESC bug dead);
  04's ordering tests extended to prove all four levels + null.
- Routes: GET/POST items, PATCH item, POST transition; API surface
  regenerated (574 routes). 57 new tests; orchestrator re-ran the
  scoped set: 249 passed under isolated HOME (captured).

## Notes / open questions

- Per-type schemas stayed minimal-but-real: common fields are columns; details_json holds only type-specific extras.
- The api-surface manifest had pre-existing consumer drift on /room (the live extraction sees the 05-adoption WIP web consumer); regenerated — the branch head stays fence-green even though this commit's manifest references web work landing in 05's commit.
