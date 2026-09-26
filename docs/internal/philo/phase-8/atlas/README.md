# PHILO-8-03 — the atlas cases for the Floor repairs

Lane: Fedaykin (Opus 5.5) for Muad'Dib, 2026-09-26. Branch `feat/philo-8-03-atlas` from main `ce772ef9`.

## The file

`docs/internal/philo/graph/atlas-phase8.json` (new, `extends` `atlas.json`, the per-phase form of `atlas-phase3.json` and `atlas-phase7.json`): 19 cases (14 face at 1440 and 393, 5 `.op`), 3 states, 1 clock, 2 exclusions. Decided here (the charter's "Decisions deferred"): a new file, not `atlas-phase7.json`, so the Phase 7 file keeps its 27 cases unchanged.

| Case | Face | Trigger | Expected (every part on the same observation) |
|---|---|---|---|
| `case.p8.zone_create.second_unnamed` | the list | the second New Zone | `all_of`: the create answers 201 (`protocol_status`); the hub lists "New zone" and "New zone 2" (`protocol_reads`); the open field reads "New zone 2" (`input_value`) and is visible, in the viewport, unobscured (`hit_target`) |
| `case.p8.zone_create.second_unnamed_floor` | the spatial Floor | the same | the same |
| `case.p8.zone_rename.list` | the list | Enter in the row's field | `all_of`: "Platform" readable in the row; the hub lists "Platform" |
| `case.p8.zone_rename.name_taken_list` | the list | Enter on "Inbox" | `all_of`: "NAME TAKEN" readable in the row's chip; the hub keeps "New zone" |
| `case.p8.zone_rename.name_taken_floor` | the spatial Floor | the same | the same |
| `case.p8.zone_rename.f2_row` | the list | F2 on the focused Inbox row | `all_of`: the row's field reads "Inbox"; visible, unobscured |
| `case.p8.chair.no_new_zone` | the Chair | search "New Zone" | "No matching tools or Desk items." readable |
| `case.p8.list_delete.gone` | the list | the row menu's Delete (right-click) | `all_of`: "Removal committed" readable; the hub answers 404 |
| `case.p8.list_delete.undo` | the list | the row menu's Delete, then (`then`) Undo on the pending receipt | `all_of`: "Restored Atlas list delete" readable; the hub answers 200 |
| `case.p8.list_delete.long_list_393` | the list, 20 more decisions, scrolled to its end | the last decision row's Delete | `all_of`: "Removal committed" readable in the viewport; 404 |
| `case.p8.delete_twice.both_gone` | the spatial Floor | A's Delete, then (`then`) select B and Delete while A's receipt is pending | `all_of`: "Removal committed" readable; A 404 AND B 404 |
| `case.p8.delete_then_leave.gone` | the spatial Floor | Delete, then (`then`) go to the Chair while the receipt is pending | `all_of`: the DELETE is sent after the press (the face change commits it: `protocol_status` on the pinned `trigger_route`); the hub answers 404 |
| `case.p8.chair.delete_withheld` | the Chair, a decision still selected from the Floor, Delete pressed | search "Delete" | `all_of`: "Open the Floor or the list" readable; the row `aria-disabled="true"`; the hub answers 200 |
| `case.p8.decision_heads.hidden` | a decision with its context only | open it from Search | `all_of`: "DECISION CONTEXT" readable; no "CONSEQUENCES" (`text_absent`: an absence has no readable form) |

The `.op` siblings (headless, `/api/mcp` into the owning hub): `case.p8.zone_create.second_unnamed.op`, `case.p8.zone_rename.list.op`, `case.p8.zone_rename.name_taken_list.op` (MCP answers `code: conflict`, `error: zone_name_taken`, `existing_name: Inbox`), `case.p8.list_delete.gone.op` (the receipt read back by its own id), `case.p8.delete_twice.both_gone.op` (both receipts read back). Excluded with their reasons in the file: the face-only cases (no new durable outcome), and F2 on a zone on the Chair (no face path selects a zone and reaches the Chair; unit-fenced in `web/src/desk/__tests__/philo801ZoneVerbs.test.ts`).

## The story's proposed ids

- `case.p8.zone_rename.chair` is not a face case: the owner's Q2 (c) withholds New Zone on the Chair, and F2 on a zone there cannot be reached by a face path (`excluded.p8.chair_f2_face`). The Chair's half is `case.p8.chair.no_new_zone`.
- `case.p8.list_delete.long_list_393` runs at 393 (the ruled width) and at 1440 (the brief's law: every face case at both widths).
- Added beyond the story's list, from the lane's brief: `…second_unnamed_floor`, `…name_taken_list`, `…name_taken_floor`, `…f2_row`, `case.p8.chair.no_new_zone`, `case.p8.chair.delete_withheld`, `case.p8.decision_heads.hidden`.

## The rig: 1.4.0 → 1.5.0 (`scripts/graph_walk.py`)

The FINDING's two unchecked assumptions (`docs/internal/philo/phase-7/floor-diag/FINDING.md` "Could not verify") were both true: the rig had no right-click and no HTTP-status predicate. Added, additive, schema-declared (`atlas.schema.json`, `graph.schema.json`), fenced (`tests/unit/test_philo8_atlas.py`):

- `click` / `click_role` take `button: "right"` (any other value, or a button on another action, is blocked by name).
- `protocol_reads {expect: [{status, row?}]}`: the hub's status for each of the case's `expected.reads`, in order; `row {path, match}` asks for exactly one matching row. A read not sent FAILS. Decidable headless.
- `all_of {predicates: [...]}`: two or more parts on the same observation; no nesting, no `unchanged`, no placement fence. The snapshot reads an `input_value` part's selector.
- A trigger's `then: [ui steps]`: the rest of one owner gesture, fired right after the trigger and before any observation. Needed by the three cases that live inside the 8 s undo window: between setup and trigger the rig settles, checks preconditions, reads the hub and takes a 2x screenshot, and under load 20–35 that took longer than 8 s. Written first with the second act as the trigger, main PASSED `delete_twice` and `delete_then_leave` at 1440 (the timer had committed the first delete before the trigger), and the phase build FAILED `list_delete.undo` at 393 (the Undo came after the commit). Those runs are superseded, not retained as verdicts.

One more rule, recorded: a step that does not exist on main is `optional` (the list's name field; the list receipt's Undo), so main runs to a `fail` verdict (the outcome absent), never `blocked`; an optional step never carries the outcome (fenced: every case with one uses `all_of` on the outcome).

## Also changed

- `docs/internal/philo/graph/atlas-phase7.json`: three state source lines re-anchored (`web/src/desk/verbRegistry.ts` 204 → 220, 160 → 176, 547 → 568). Story 01 moved them; `tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase7.json]` was RED on main `ce772ef9` before this change. No case changed.
- `tests/unit/test_philo_graph_atlas.py`: the op-sibling count 39 → 44; `zone.update` joins the producer operations.
- `docs/generated/api-reference.json` regenerated (the new files name routes).
