# Evidence - PHILO-9-05

- **Story:** PHILO-9-05 - The atlas: assembly, rerun and equivalence
- **Status:** done
- **Date:** 2026-09-28
- **Branch:** `feat/philo-9-05` from main `79fdee3c` (stories 01, 02, 03, 04, 07 merged). The product under test is main: this story changes no product file.

## Summary

- **The census** (each story's criteria against the atlas; below).
- **The five authored gaps** (`docs/internal/philo/graph/atlas-phase9.json`, written by `assets/story-05-proof/add_atlas.py`): `case.p9.update.delivered_row.op`, `case.p9.grant.project_allowed`, `case.p9.grant_route.project_allowed`, `case.p9.grant.desk_reads_desk`, `case.p9.connections.never_checked_face`; two new states (`p9_grant_face`, `p9_connections_face`), two exclusions with reasons (the agent side of the grant; the face cases with no twin). Muad'Dib's brief authorized authoring only the gaps the census proves. It overrides the story's Scope line "Out: authoring a new face case" for the three face cases, and the story's Notes say so.
- **No fold.** `atlas-phase9-steward.json` (story 02) stays its own file. Story 02's retained observations (`docs/internal/philo/graph/observations/muaddib/20260928T1449*-case.p9.*`) name that path and its sha256, and the owner rules "never delete, park instead". The phase atlas is the two files.
- **The phase fences** (`tests/unit/test_philo9_atlas.py`, 43 tests): the 16 general fences and the OpenAPI route check applied to BOTH Phase 9 files (the general fences read `atlas.json` only by default, the Phase 8 law), the counts over every atlas file, the story 05 ids, widths (face at 1440 and 393, the rest headless), the three equivalence pairs and their shared values, each admitted-write twin reading its receipt WITH its actor, every face case without a twin excluded by name, no optional trigger and no optional step but the gate's. `assets/story-05-proof/mutations.py`: 8 mutations, 8 red. `tests/unit/test_philo_graph_atlas.py`: the `.op` sibling count 44 → 45, and `project.mark_update_delivered` / `project.list_updates` added to its producer and read sets.
- **Generated:** `docs/generated/openapi.json` (it was stale on main: the grant route `PUT/DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}` and `POST /api/updates/{update_id}/delivered` were missing; the new route case's OpenAPI fence needs them), `api-reference.json`, `graph.json` (the OpenAPI hash), `repository-tree.json`.

## The census

| Story | Criterion (short) | Atlas cases | Covered / gap |
|---|---|---|---|
| 01 | tools, envelopes, residual set, palettes, discovery, `get_room`, needs-you parity, the delivery table | none in an atlas file. The rig's `op` step drives the job on a real hub in `tests/unit/test_philo9_rig_op.py`; the rest is backend fences | covered by the story's own fences (no face criterion; the story says so) |
| 01 / 03 | F2: a past-due milestone shown, health turned | `case.p9.room_items.late_row` | covered (face); the Room read is in `test_philo9_rig_op.py` (`health.assessment == at_risk`) |
| 02 | steward run, mark delivered, archive, each with its receipt; `connection.list` never checked | `atlas-phase9-steward.json` (4 op cases) | covered (op) |
| 02 | the Connections face: "never checked" at 1440 and 393 | none | **gap → `case.p9.connections.never_checked_face`** (red on main) |
| 03 | F1 callers, F3 steward counts, F7 RECEIPTS | excluded (`excluded.p9.room_face_callers_and_receipts`: glass) | covered by glass, excluded with a reason |
| 03 | F10 Steward verb, F11 update words, the delivery row | `room_steward_verb.owned`, `update_list.head_updates`, `update.delivered_row` | covered (face) |
| 03 | the delivery's durable outcome as the face's twin | none named as its `.op` | **gap → `case.p9.update.delivered_row.op`** (reads the receipt with its actor) |
| 04 | status word, columns, sort verb, row menu | the four `list_*` cases | covered; selection contrast and 12 px excluded with a reason (glass) |
| 07 | the grant face at 1440 and 393 | none (story 07 shipped no atlas case) | **gap → `case.p9.grant.project_allowed`** (new capability) |
| 07 | the grant's durable outcome and receipt (HTTP only, in no MCP palette) | none | **gap → `case.p9.grant_route.project_allowed`** |
| 07 | DESK reads DESK (red on main: ALL) | none | **gap → `case.p9.grant.desk_reads_desk`** (red on main) |
| 07 | agent refused without a grant, runs with it, revoke, expiry | none | not an atlas case: the rig speaks only with the owner's token. Excluded (`excluded.p9.agent_side_grant`), fenced by `test_philo9_project_grant*.py` with a real PROJECT credential |

## The counts (at this commit)

| File | Cases | Face | Op / route | Runs (1440 + 393 + headless) |
|---|---|---|---|---|
| `atlas.json` | 85 | — | — | 136 |
| `atlas-phase3.json` | 36 | — | — | 58 |
| `atlas-phase7.json` | 27 | 9 | 18 | 36 |
| `atlas-phase8.json` | 19 | 14 | 5 | 33 |
| `atlas-phase9.json` | 13 (8 + 5 new) | 11 | 2 | 24 |
| `atlas-phase9-steward.json` | 4 | 0 | 4 | 4 |
| total | 184 | | | 291 |

## The reruns (on this branch = merged main `79fdee3c` + story 05's atlas; `--engine none`, every run its own hub and HOME)

- **Phase 9, 28 runs, serial:** 28 of 28 pass (`assets/story-05-shots/p9-merged/runs.tsv`; capture 17:52:51Z). Every face case passes at 1440 and 393; the 6 op/route cases pass headless.
- **Phase 7 and Phase 8, 69 runs, serial:** 69 of 69 pass (36 + 33; `p78-merged/runs.tsv`; capture 18:08:57Z). A first parallel pass at load 18–23 had `case.p8.delete_twice.both_gone` at 1440 BLOCKED by its in-window guard (the guard held the late gesture back, as designed); `case.p9.list_status.shown` BLOCKED twice at load 22 on the first-use gate check. Both passed serially. The parallel pass is not the evidence.
- **The base atlas and Phase 3 (194 runs), before and after Phase 9:** the same instrument (this branch's rig and atlas files) on an export of `294632c0` (main just before story 01's merge; built from its own web source and run with its own package) and on merged main. 109 pass→pass, 76 blocked→blocked, 6 fail→fail, 1 not_applicable→not_applicable. One case flipped each way: `case.closure.chain.s5_next_day_brief_more_opened` (pass→blocked at 1440, blocked→pass at 393). Three more attempts per product: merged main 2 of 6 runs pass, `294632c0` 3 of 6 pass, each block on the same wait (`[data-testid=arrival-brief-more]` or the summary text), so it is an inherited timing flake, not a Phase 9 regression (`base-flake-s5-more/`). `base_diff.py` exits 1 on that one row by construction; the capture is kept as is. The 76 blocked and 6 failed runs are the same rows before and after (rig mechanisms not built, for example boundary substitutions; a stale assignment request shape). They are the base atlas's own history, not this phase's.

## The equivalence (face ↔ its twin, one build)

| Durable outcome | Browser (face) | Twin | Same values | Receipt with actor |
|---|---|---|---|---|
| Mark delivered, To Priya | `case.p9.update.delivered_row` pass ×2 | `case.p9.update.delivered_row.op` (MCP) pass; story 02's `mark_delivered_receipted` pass | recipient `Priya` (fenced); one delivery row whose `operation_id` is the mark's | `kernel.receipt.read`: `project.mark_update_delivered`, succeeded, `actor_kind` owner |
| Allow run and publish on a project | `case.p9.grant.project_allowed` pass ×2 (the route's 200 and the owner's receipt read on the face's own call; the ledger reads LIVE) | `case.p9.grant_route.project_allowed` (HTTP; the grant has no MCP tool by the charter) pass | the same route, identity and LIVE state (fenced) | `/api/kernel/read`: `project.delegation.grant`, succeeded, owner, target the project |
| Never checked | `case.p9.connections.never_checked_face` pass ×2 (face + `GET /api/connections`) | story 02's `case.p9.connections.never_checked` (MCP `connection.list`) pass | github `never_checked`, no check time | a read: no operation, no receipt (the op case asserts none) |
| Steward run, archive | excluded (face: F3 glass) | story 02's op cases pass | — | receipts read in the op cases |

The api ↔ MCP equivalence of every durable outcome AND every refusal is the stories' own fences, rerun here on merged main: `test_philo9_compat.py`, `test_philo9_room_contract.py`, `test_philo9_mark_delivered.py`, `test_philo9_delivery_record.py`, `test_philo9_project_grant.py`, `test_philo9_steward_admission.py`, `test_philo9_rig_op.py`, `test_philo9_02_rig_op.py` (177 tests), inside the 424 passed of capture 17:51:45Z. No Phase 9 atlas case is a refusal case; the refusals' equivalence is in those fences, not in the atlas. **Real and replayed:** every atlas run here is `--engine none`; no case declares a provider replay, so no replayed run exists to keep apart.

## Red on main (the story 05 cases on `1f332bc3`, main before stories 02, 03, 07; capture 18:24:42Z)

| Case | 1440 | 393 | Reading |
|---|---|---|---|
| `case.p9.grant.desk_reads_desk` | **fail** | **fail** | the wire: 0 rows match `{identity: desk-agent, palette: DESK}` (it reads `ALL`); the row's token reads `ALL` (observation text) |
| `case.p9.connections.never_checked_face` | **fail** | **fail** | the chip reads `SIGN IN`; the list probed on read (`owner_action_required`, a check time stamped) |
| `case.p9.grant.project_allowed` | blocked | blocked | no `Projects` Disclosure: a new capability, no red claimed |
| `case.p9.grant_route.project_allowed` | blocked (headless) | — | the route does not exist on main: never counted as a red |
| `case.p9.update.delivered_row.op` | blocked (headless) | — | `project.mark_update_delivered` does not exist on main: never counted as a red |

The two reds are for defects stories 02 and 07 already recorded red with their glass; these atlas reds corroborate them and claim nothing new.

## Unknown / not done

- The agent side of the grant is not an atlas case (the rig has no agent principal; rig work, excluded with the reason).
- `docs/generated/openapi.json` was stale on main (above); regenerated here. Not traced: which story's merge left it stale.

## Proof

### Captured run — 2026-09-28T17:51:45Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06
........................................................................ [ 84%]
................................................................         [100%]
424 passed in 46.78s
m1 (23): RED - 7 failed, 36 passed in 0.49s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_case_reference_inside_the_atlas_resolves-atlas-phase9.json]', 'FAILED te
m2 (27): RED - 2 failed, 41 passed in 0.45s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_face_cases_carry_both_ruled_viewports-atlas-phase9.json]', 'FAILED tests/unit/
m3 (31): RED - 1 failed, 42 passed in 0.44s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_admitted_write_twin_reads_its_receipt_with_its_actor']
m4 (36): RED - 1 failed, 42 passed in 0.42s; ['FAILED tests/unit/test_philo9_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m5 (40): RED - 1 failed, 42 passed in 0.41s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m6 (44): RED - 1 failed, 42 passed in 0.39s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
m7 (50): RED - 1 failed, 42 passed in 0.43s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_desk_face_case_crosses_the_gate_first-atlas-phase9.json]']
m8 (54): RED - 2 failed, 41 passed in 0.46s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_api_step_exists_in_the_generated_openapi[atlas-phase9.json]', 'FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read
8 red, 0 missed
```

### Captured run — 2026-09-28T17:52:51Z

- **Command:** `env SHOTS=1 zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p9-merged 1 docs/internal/philo/graph/atlas-phase9.json docs/internal/philo/graph/atlas-phase9-steward.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06; load { 5.76 6.22 8.38 }
✓ built in 4.73s
28 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p9-merged
atlas-phase9.json	case.p9.list_status.shown	1440	pass	21	5.54	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
atlas-phase9.json	case.p9.list_status.shown	393	pass	15	7.10	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
atlas-phase9.json	case.p9.list_columns.in_view	1440	pass	22	6.70	predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
atlas-phase9.json	case.p9.list_columns.in_view	393	pass	15	7.41	predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
atlas-phase9.json	case.p9.list_sort.zone_pressed	1440	pass	22	7.68	predicate: aria-pressed='true', wanted 'true'
atlas-phase9.json	case.p9.list_sort.zone_pressed	393	pass	15	9.48	predicate: aria-pressed='true', wanted 'true'
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	1440	pass	21	8.41	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	393	pass	14	13.82	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
atlas-phase9.json	case.p9.room_items.late_row	1440	pass	9	12.30	predicate: 'DAYS LATE' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 668, 'y': 361, 'w': 125, 'h': 18}
atlas-phase9.json	case.p9.room_items.late_row	393	pass	9	10.94	predicate: 'DAYS LATE' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 31, 'y': 571, 'w': 125, 'h': 18}
atlas-phase9.json	case.p9.update_list.head_updates	1440	pass	10	9.87	predicate: 'UPDATES 1' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 43, 'y': 167, 'w': 71, 'h': 18}
atlas-phase9.json	case.p9.update_list.head_updates	393	pass	9	9.19	predicate: 'UPDATES 1' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 531, 'w': 71, 'h': 18}
atlas-phase9.json	case.p9.update.delivered_row	1440	pass	10	8.08	predicate: 'Priya' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 274, 'w': 770, 'h': 26}
atlas-phase9.json	case.p9.update.delivered_row	393	pass	10	7.43	predicate: 'Priya' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 348, 'w': 363, 'h': 72}
atlas-phase9.json	case.p9.room_steward_verb.owned	1440	pass	10	13.21	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 731, 'y': 432, 'w': 68, 'h': 24}
atlas-phase9.json	case.p9.room_steward_verb.owned	393	pass	10	11.96	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 300, 'y': 350, 'w': 68, 'h': 24}
atlas-phase9.json	case.p9.grant.project_allowed	1440	pass	10	10.88	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-8e553fb147c9 answered 200, wanted 200 (body sha256 aadd2a5f70f2); respons
atlas-phase9.json	case.p9.grant.project_allowed	393	pass	10	9.90	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-7a9ab5aba923 answered 200, wanted 200 (body sha256 a7e135da0eb2); response 
atlas-phase9.json	case.p9.grant_route.project_allowed	op	pass	3	9.05	predicate: GET /api/settings/remote answered 200 with one row {'identity': 'sweep-runner', 'project_delegations.0.project_id': 'proj-b4121b0ddb9e', 'project_delegations.0.
atlas-phase9.json	case.p9.grant.desk_reads_desk	1440	pass	10	9.05	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in vie
atlas-phase9.json	case.p9.grant.desk_reads_desk	393	pass	10	8.19	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in view
atlas-phase9.json	case.p9.connections.never_checked_face	1440	pass	9	7.39	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 131, 'y': 190, 'w': 137, 'h': 18} | protocol_
atlas-phase9.json	case.p9.connections.never_checked_face	393	pass	9	6.41	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 24, 'y': 231, 'w': 137, 'h': 18} | protocol_rea
atlas-phase9.json	case.p9.update.delivered_row.op	op	pass	3	6.29	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.delivered_to holds; observe_at updates.0.delive
atlas-phase9-steward.json	case.p9.steward.run_receipted	op	pass	3	6.29	predicate: all 9 facts hold: observe_at run.state holds; observe_at operation_id holds; observe_at receipt.outcome holds; the trigger receipt holds; op read #0 (kernel.r
atlas-phase9-steward.json	case.p9.update.mark_delivered_receipted	op	pass	3	5.94	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.operation_id holds; observe_at 
atlas-phase9-steward.json	case.p9.project.archive_receipted	op	pass	3	5.94	predicate: all 5 facts hold: observe_at is_archived holds; the trigger success holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (ke
atlas-phase9-steward.json	case.p9.connections.never_checked	op	pass	3	5.63	predicate: all 4 facts hold: the trigger tools holds; the trigger tools holds; the trigger operation_id is absent; observe_at tools holds
TOTAL 28 runs: 28 pass, 0 not pass
```

### Captured run — 2026-09-28T18:08:57Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p78-merged 1 docs/internal/philo/graph/atlas-phase7.json docs/internal/philo/graph/atlas-phase8.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06; load { 5.80 4.32 5.78 }
✓ built in 4.25s
69 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p78-merged
atlas-phase7.json	case.p7.zone_create.visible	1440	pass	19	5.42	predicate: 'Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26}
atlas-phase7.json	case.p7.zone_create.visible	393	pass	20	8.10	predicate: 'Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26}
atlas-phase7.json	case.p7.zone_file.note_in_zone	1440	pass	10	8.52	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 98, 'h': 18}
atlas-phase7.json	case.p7.zone_file.note_in_zone	393	pass	11	7.81	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 98, 'h': 18}
atlas-phase7.json	case.p7.zone_file.refile_moves	1440	pass	12	7.17	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 109, 'h': 18}
atlas-phase7.json	case.p7.zone_file.refile_moves	393	pass	12	6.70	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 109, 'h': 18}
atlas-phase7.json	case.p7.zone_unfile.note_leaves	1440	pass	10	6.27	predicate: '+ Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 170}
atlas-phase7.json	case.p7.zone_unfile.note_leaves	393	pass	10	6.27	predicate: '+ Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 431, 'w': 347, 'h': 170}
atlas-phase7.json	case.p7.kb_create.visible	1440	pass	11	6.46	predicate: 'New Knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 145, 'w': 382, 'h': 26}
atlas-phase7.json	case.p7.kb_create.visible	393	pass	11	5.94	predicate: 'New Knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 123, 'w': 363, 'h': 26}
atlas-phase7.json	case.p7.kb_member.add_and_remove	1440	pass	10	5.40	predicate: '+ Atlas knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 137}
atlas-phase7.json	case.p7.kb_member.add_and_remove	393	pass	10	5.09	predicate: '+ Atlas knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 464, 'w': 347, 'h': 137}
atlas-phase7.json	case.p7.decision_status.review_list	1440	pass	12	4.76	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 302, 'w': 928, 'h': 54}
atlas-phase7.json	case.p7.decision_status.review_list	393	pass	11	4.14	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 383, 'w': 369, 'h': 103}
atlas-phase7.json	case.p7.decision_supersede.successor_visible	1440	pass	9	3.81	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 56}
atlas-phase7.json	case.p7.decision_supersede.successor_visible	393	pass	9	3.83	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 449, 'w': 363, 'h': 112}
atlas-phase7.json	case.p7.decision_delete.gone	1440	pass	34	3.68	predicate: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 748, 'w': 138, 'h': 27}
atlas-phase7.json	case.p7.decision_delete.gone	393	pass	25	6.81	predicate: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 628, 'w': 138, 'h': 27}
atlas-phase7.json	case.p7.zone_create.visible.op	op	pass	3	7.53	predicate: all 5 facts hold: observe_at directory.id holds; observe_at directory.name holds; observe_at directory.parent_id holds; op read #0 (zone.list) <root> holds; the trig
atlas-phase7.json	case.p7.zone_file.note_in_zone.op	op	pass	3	7.01	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.zone_file.refile_moves.op	op	pass	4	7.01	predicate: all 16 facts hold: observe_at <root> holds; op read #0 (zone.members) <root> holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read
atlas-phase7.json	case.p7.zone_unfile.note_leaves.op	op	pass	3	6.53	predicate: all 17 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.re
atlas-phase7.json	case.p7.kb_create.visible.op	op	pass	3	6.32	predicate: all 4 facts hold: observe_at id holds; observe_at name holds; op read #0 (kb.list) <root> holds; the trigger operation_id is absent
atlas-phase7.json	case.p7.kb_member.add_and_remove.op	op	pass	3	6.32	predicate: all 15 facts hold: observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.op
atlas-phase7.json	case.p7.decision_status.review_list.op	op	pass	3	6.14	predicate: all 9 facts hold: observe_at status holds; observe_at id holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.decision_supersede.successor_visible.op	op	pass	3	6.14	predicate: all 6 facts hold: observe_at status holds; observe_at superseded_by holds; op read #0 (decision.read) id holds; op read #0 (decision.read) deleted h
atlas-phase7.json	case.p7.decision_supersede.receipt.op	op	pass	3	5.73	predicate: all 9 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observ
atlas-phase7.json	case.p7.decision_delete.gone.op	op	pass	3	5.35	predicate: all 9 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1
atlas-phase7.json	case.p7.decision_create.receipt.op	op	pass	3	5.35	predicate: all 7 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_a
atlas-phase7.json	case.p7.zone_file.refused_unknown_zone.op	op	pass	3	5.16	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0
atlas-phase7.json	case.p7.kb_member.refused_bad_ref.op	op	pass	3	5.16	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.rece
atlas-phase7.json	case.p7.decision_status.refused_invalid.op	op	pass	3	4.91	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.p7.decision_delete.refused_unknown.op	op	pass	3	4.91	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.j1.first_words_keep_as_note.kept.op	op	pass	3	4.75	predicate: all 5 facts hold: observe_at id holds; observe_at body_markdown holds; observe_at title holds; op read #0 (note.list) <root> holds; the trigger operation_i
atlas-phase7.json	case.j11.write_a_thought.window_open.op	op	pass	3	4.75	predicate: all 3 facts hold: observe_at thought.id holds; observe_at thought.working_note.id holds; the trigger operation_id is absent
atlas-phase7.json	case.j11.thought_keep.kept.op	op	pass	3	4.45	predicate: all 4 facts hold: observe_at id holds; observe_at body_markdown holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_create.second_unnamed	1440	pass	31	4.45	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 d6f02f4912cd) | protocol_reads: GET /api/directories answered 200 with on
atlas-phase8.json	case.p8.zone_create.second_unnamed	393	pass	17	5.27	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 594c0efd6558) | protocol_reads: GET /api/directories answered 200 with one
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	1440	pass	38	5.35	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 c82bd38c88f3) | protocol_reads: GET /api/directories answered 200 w
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	393	pass	23	7.34	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 235398b43be8) | protocol_reads: GET /api/directories answered 200 wi
atlas-phase8.json	case.p8.zone_rename.list	1440	pass	25	7.13	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 297, 'w': 53, 'h': 24} | protocol_reads: GET /api/dir
atlas-phase8.json	case.p8.zone_rename.list	393	pass	14	7.19	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 469, 'w': 90, 'h': 38} | protocol_reads: GET /api/direct
atlas-phase8.json	case.p8.zone_rename.name_taken_list	1440	pass	24	6.94	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 339, 'w': 112, 'h': 18} | protocol_reads
atlas-phase8.json	case.p8.zone_rename.name_taken_list	393	pass	14	8.39	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 498, 'w': 112, 'h': 18} | protocol_reads: G
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	1440	pass	30	8.51	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1208, 'y': 167, 'w': 112, 'h': 18} | protocol_rea
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	393	pass	20	9.34	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 14, 'y': 315, 'w': 112, 'h': 18} | protocol_reads: 
atlas-phase8.json	case.p8.zone_rename.f2_row	1440	pass	17	9.08	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y':
atlas-phase8.json	case.p8.zone_rename.f2_row	393	pass	12	8.95	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 29
atlas-phase8.json	case.p8.chair.no_new_zone	1440	pass	9	8.31	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 73, 'w': 382, 'h': 44}
atlas-phase8.json	case.p8.chair.no_new_zone	393	pass	9	7.41	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 51, 'w': 363, 'h': 44}
atlas-phase8.json	case.p8.list_delete.gone	1440	pass	36	6.90	predicate: all_of: protocol_reads: GET /api/decisions/decision_006112cbcf67 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900
atlas-phase8.json	case.p8.list_delete.gone	393	pass	24	7.36	predicate: all_of: protocol_reads: GET /api/decisions/decision_2a1ce1a1fd8e answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} 
atlas-phase8.json	case.p8.list_delete.undo	1440	pass	29	12.18	predicate: all_of: protocol_reads: GET /api/decisions/decision_3c3f50e840de answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 1440, 'he
atlas-phase8.json	case.p8.list_delete.undo	393	pass	15	10.96	predicate: all_of: protocol_reads: GET /api/decisions/decision_d4b1b1103674 answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 393, 'heig
atlas-phase8.json	case.p8.list_delete.long_list_393	1440	pass	35	10.01	predicate: all_of: protocol_reads: GET /api/decisions/decision_41eefcf445db answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'he
atlas-phase8.json	case.p8.list_delete.long_list_393	393	pass	23	11.33	predicate: all_of: protocol_reads: GET /api/decisions/decision_1c045c940fa7 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'heig
atlas-phase8.json	case.p8.delete_twice.both_gone	1440	pass	43	10.92	predicate: all_of: protocol_reads: GET /api/decisions/decision_c27a569967f7 answered 404; GET /api/decisions/decision_af019cc65e3b answered 404 | readable_text: 'Removal co
atlas-phase8.json	case.p8.delete_twice.both_gone	393	pass	29	12.53	predicate: all_of: protocol_reads: GET /api/decisions/decision_d0af3dd821ea answered 404; GET /api/decisions/decision_4c467014e6b4 answered 404 | readable_text: 'Removal com
atlas-phase8.json	case.p8.delete_then_leave.gone	1440	pass	27	10.91	predicate: all_of: protocol_status: DELETE /api/decisions/decision_c36e490ad7f3 answered 200, wanted 200 (body sha256 766359e22f3d) | protocol_reads: GET /api/decisions/dec
atlas-phase8.json	case.p8.delete_then_leave.gone	393	pass	18	10.25	predicate: all_of: protocol_status: DELETE /api/decisions/decision_90d4e34cb884 answered 200, wanted 200 (body sha256 dc555afae025) | protocol_reads: GET /api/decisions/deci
atlas-phase8.json	case.p8.chair.delete_withheld	1440	pass	22	9.25	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26} | attr
atlas-phase8.json	case.p8.chair.delete_withheld	393	pass	16	9.02	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26} | attr_equ
atlas-phase8.json	case.p8.decision_heads.hidden	1440	pass	10	8.06	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 94} | text_absent: 
atlas-phase8.json	case.p8.decision_heads.hidden	393	pass	10	7.75	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 439, 'w': 363, 'h': 122} | text_absent: 'CO
atlas-phase8.json	case.p8.zone_create.second_unnamed.op	op	pass	3	7.21	predicate: all 3 facts hold: observe_at <root> holds; observe_at <root> holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_rename.list.op	op	pass	3	6.71	predicate: all 3 facts hold: observe_at directory.id holds; observe_at directory.name holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_rename.name_taken_list.op	op	pass	3	6.25	predicate: all 3 facts hold: the trigger error holds; the trigger existing_name holds; observe_at directory.name holds
atlas-phase8.json	case.p8.list_delete.gone.op	op	pass	3	6.25	predicate: all 7 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (ke
atlas-phase8.json	case.p8.delete_twice.both_gone.op	op	pass	3	5.91	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
TOTAL 69 runs: 69 pass, 0 not pass
```

### Captured run — 2026-09-28T18:24:42Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/red_main.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
base = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
✓ built in 4.39s
case.p9.grant.project_allowed 1440 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant.project_allowed 393 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant_route.project_allowed op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'grant_op': no value at 'operation_id' in the response of PUT /api/settings/remote/delegations/sweep-runner/projects/proj-b2e4c4d92528
case.p9.grant.desk_reads_desk 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.grant.desk_reads_desk 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.connections.never_checked_face 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.connections.never_checked_face 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.update.delivered_row.op op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'mark_op': no value at 'operation_id' in the decoded response of operation 'project.mark_update_delivered'
```

### Captured run — 2026-09-28T18:27:47Z

- **Command:** `python3 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/base_diff.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
  76  before blocked         after blocked
   1  before blocked         after pass
   6  before fail            after fail
   1  before not_applicable  after not_applicable
   1  before pass            after blocked
 109  before pass            after pass
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 1440: pass -> blocked
     before: predicate: 'Keep summary retrieval on the local desk' in observe_at text
     after:  BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 393: blocked -> pass
     before: BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
     after:  predicate: 'Keep summary retrieval on the local desk' in observe_at text
194 runs; 1 pass before and not after
```

### Captured run — 2026-09-28T18:30:07Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 21b3b50712fde932b6e59418a7e26e1ae3c61203

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:6> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:7> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:8> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:9> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:10> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:11> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:12> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:13> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:14> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:15> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:16> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:17> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:17> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:18> .venv/bin/python scripts/philo_openapi_reference.py --check
OpenAPI: 572 paths
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:18> echo 'rc=0'
rc=0
```
