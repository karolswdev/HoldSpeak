# Evidence - PHILO-8-03 (held as `assets/story-03-proof.md` until the story flips done; then it moves to `evidence-story-03.md`)

- **Story:** PHILO-8-03 - The atlas cases and the closing proof
- **Status:** in-progress (the delete cases run on merged main after #672 merges, and the owner reviews the rehearsal shots; neither has happened)
- **Date:** 2026-09-26

## Summary

- **Built (branch `feat/philo-8-03-atlas`, from main `ce772ef9`):** `docs/internal/philo/graph/atlas-phase8.json` (19 cases: 14 face at 1440 and 393, 5 `.op`; 3 states; 1 clock; 2 exclusions) — the case table and the decisions are in `docs/internal/philo/phase-8/atlas/README.md`. The rig `scripts/graph_walk.py` 1.4.0 → 1.5.0: `button: "right"` on `click`/`click_role`; the predicates `protocol_reads` and `all_of`; a trigger's `then` steps. Schemas: `atlas.schema.json` (`p8`, `button`, `then`, the two kinds), `graph.schema.json` (the two kinds). Fences: `tests/unit/test_philo8_atlas.py` (new), `tests/unit/test_philo_graph_atlas.py` (op siblings 39 → 44; `zone.update`). The closing rehearsal driver `scripts/philo8_rehearsal.py`. `docs/generated/api-reference.json` regenerated. The Phase 7 atlas: three state anchors re-anchored (below).
- **Where the product runs came from.** Two `git archive` builds in the lane's scratchpad, each with `uv sync --extra test` and a real `npm ci --ignore-scripts && npm run build`, and this branch's rig and atlas copied in: **main before the repair `267f692a`** (the charter merge) and **the #672 head `b65107f5`** (main `ce772ef9` + story 02: stories 01 A+B, 04 (a) and 02 together — the phase build until #672 merges). Every run: `scripts/graph_walk.py run --engine none` (no case calls a model), one real hub per run on its own fresh HOME (the rig's `Hub`), a fresh Chromium profile, `--brain muaddib`. The owner's HOME and DB were not touched.
- **Machine load.** The owner's machine carried sibling lanes (load 10–34 during this story). The load average at each run's start is in each folder's `runs.tsv`. The three cases that live inside the 8 s window were first written with the second act as the trigger. Under load 20–35 the rig's before-capture (settle, preconditions, hub reads, a 2x screenshot) outlasted the window: main PASSED `case.p8.delete_twice.both_gone` and `case.p8.delete_then_leave.gone` at 1440 (the timer had committed the first delete), and the phase build FAILED `case.p8.list_delete.undo` at 393 (the Undo came after the commit, 404). All three are now ONE gesture: the first act is the trigger, the rest is its `then`, and the receipt is read pending right before the second act (fenced: `test_an_in_window_case_is_one_gesture`). Two phase runs were also `blocked` at load 31–35 when the right-click did not land in 10 s (`click_role … Timeout 10000ms`, the menu open in `blocked.png`); the right-click now waits 25 s. The superseded runs are not retained as verdicts; they are recorded here.

## Every new case, both builds

`assets/story-03-shots/main-267f692a/` and `assets/story-03-shots/phase-b65107f5/` — one folder per run with its `observation.json` (the rig's full record: provenance incl. the atlas sha256, setup, preconditions, before, trigger and its `then`, the trigger's own response, after, the reading) and the shots as JPEG (converted from the rig's 2x PNG by `sips`, 70 %, 1600 px, to keep the tree small; the main runs keep `after` only). `runs.tsv` in each folder: case, width, verdict, duration, the load average at the start, the reading. `python3 docs/internal/philo/phase-8/atlas/verdicts.py <folder>` prints the verdicts from the observations.

| Case | Width | main `267f692a` (before the repair) | phase build `b65107f5` |
|---|---|---|---|
| `case.p8.zone_create.second_unnamed` | 1440 | **fail** 93s (load1=12.22) | **pass** 51s (load1=19.57) |
| `case.p8.zone_create.second_unnamed` | 393 | **fail** 76s (load1=20.67) | **pass** 20s (load1=26.53) |
| `case.p8.zone_create.second_unnamed_floor` | 1440 | **fail** 90s (load1=24.22) | **pass** 56s (load1=26.75) |
| `case.p8.zone_create.second_unnamed_floor` | 393 | **fail** 75s (load1=23.04) | **pass** 30s (load1=25.37) |
| `case.p8.zone_rename.list` | 1440 | **fail** 80s (load1=28.25) | **pass** 39s (load1=22.51) |
| `case.p8.zone_rename.list` | 393 | **fail** 63s (load1=24.95) | **pass** 23s (load1=24.78) |
| `case.p8.zone_rename.name_taken_list` | 1440 | **fail** 82s (load1=18.58) | **pass** 38s (load1=25.85) |
| `case.p8.zone_rename.name_taken_list` | 393 | **fail** 66s (load1=32.31) | **pass** 17s (load1=28.25) |
| `case.p8.zone_rename.name_taken_floor` | 1440 | **fail** 84s (load1=34.16) | **pass** 52s (load1=27.11) |
| `case.p8.zone_rename.name_taken_floor` | 393 | **fail** 57s (load1=32.97) | **pass** 25s (load1=26.22) |
| `case.p8.zone_rename.f2_row` | 1440 | **fail** 42s (load1=30.10) | **pass** 31s (load1=23.99) |
| `case.p8.zone_rename.f2_row` | 393 | **fail** 35s (load1=25.63) | **pass** 20s (load1=29.40) |
| `case.p8.chair.no_new_zone` | 1440 | **fail** 25s (load1=23.68) | **pass** 11s (load1=30.57) |
| `case.p8.chair.no_new_zone` | 393 | **fail** 24s (load1=19.27) | **pass** 12s (load1=32.16) |
| `case.p8.delete_twice.both_gone` | 1440 | **blocked** 47s (load1=26.68) | **pass** 48s (load1=30.98) |
| `case.p8.delete_twice.both_gone` | 393 | **fail** 63s (load1=21.55) | **pass** 28s (load1=27.38) |
| `case.p8.delete_then_leave.gone` | 1440 | **fail** 59s (load1=24.29) | **pass** 28s (load1=25.82) |
| `case.p8.delete_then_leave.gone` | 393 | **fail** 47s (load1=25.70) | **pass** 16s (load1=22.97) |
| `case.p8.chair.delete_withheld` | 1440 | **fail** 51s (load1=23.72) | **pass** 21s (load1=19.27) |
| `case.p8.chair.delete_withheld` | 393 | **fail** 42s (load1=22.85) | **pass** 16s (load1=17.73) |
| `case.p8.decision_heads.hidden` | 1440 | **fail** 32s (load1=21.22) | **pass** 10s (load1=14.96) |
| `case.p8.decision_heads.hidden` | 393 | **fail** 30s (load1=16.40) | **pass** 10s (load1=15.47) |
| `case.p8.zone_create.second_unnamed.op` | op | — | **pass** 3s (load1=15.43) |
| `case.p8.zone_rename.list.op` | op | — | **pass** 3s (load1=15.43) |
| `case.p8.zone_rename.name_taken_list.op` | op | — | **pass** 3s (load1=14.84) |
| `case.p8.delete_twice.both_gone.op` | op | — | **pass** 3s (load1=14.93) |
| `case.p8.list_delete.gone` | 1440 | **fail** 67s (load1=16.55) | **pass** 37s (load1=15.21) |
| `case.p8.list_delete.gone` | 393 | **fail** 56s (load1=16.37) | **pass** 24s (load1=18.81) |
| `case.p8.list_delete.undo` | 1440 | **fail** 50s (load1=18.67) | **pass** 36s (load1=19.17) |
| `case.p8.list_delete.undo` | 393 | **fail** 36s (load1=20.76) | **pass** 19s (load1=21.47) |
| `case.p8.list_delete.long_list_393` | 1440 | **fail** 69s (load1=20.11) | **pass** 36s (load1=20.76) |
| `case.p8.list_delete.long_list_393` | 393 | **fail** 57s (load1=21.12) | **pass** 23s (load1=20.11) |
| `case.p8.list_delete.gone.op` | op | — | **pass** 4s (load1=14.93) |

**On main `267f692a`: 27 of 28 face runs FAIL with an assertion reading (the outcome absent: the second create answers 409; no field, no chip; 200 where 404 is owed; no DELETE after the face change; the empty heading present); 1 is `blocked`, not failed: `case.p8.delete_twice.both_gone` at 1440, three attempts at load 26–31, each time the gesture (select B over the spatial Floor) outlasted A's 8 s window on main, so the rig refused to press B's Delete outside the window (`blocked.jpg`: "Removal committed"). Its 393 run on main fails (the hub keeps an object). On the phase build `b65107f5`: 28 of 28 PASS.** The five `.op` siblings pass headless on the phase build (the rows marked `op`). The two-delete fence at both widths on main is also red in story 02's glass (`docs/internal/philo/phase-8/one-delete/red-main-two-deletes-serial.txt`, PR #672). The main atlas file differs from the final one only in the list and in-window cases that were rewritten during the story; each run records the sha256 of the atlas it read (the list delete cases on main ran on the final file).

## The 27 Phase 7 cases on the phase build

`assets/story-03-shots/phase7-on-b65107f5/` (the Phase 7 atlas with only its three re-anchored lines changed; no case changed).

| Case | Width | Verdict | Duration | Load | Reading |
|---|---|---|---|---|---|
| `case.p7.zone_create.visible.op` | op | **pass** | 4s | load1=19.12 | predicate: all 5 facts hold: observe_at directory.id holds; observe_at directory.name holds; observe_at directory.parent_id holds; op read #0 (zone.list) <root> holds; the trigger operation_id is abse |
| `case.p7.zone_file.note_in_zone.op` | op | **pass** | 3s | load1=19.75 | predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operat |
| `case.p7.zone_file.refile_moves.op` | op | **pass** | 6s | load1=19.75 | predicate: all 16 facts hold: observe_at <root> holds; op read #0 (zone.members) <root> holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (kernel.receipt.read) o |
| `case.p7.zone_unfile.note_leaves.op` | op | **pass** | 4s | load1=20.75 | predicate: all 17 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operat |
| `case.p7.kb_create.visible.op` | op | **pass** | 3s | load1=20.75 | predicate: all 4 facts hold: observe_at id holds; observe_at name holds; op read #0 (kb.list) <root> holds; the trigger operation_id is absent |
| `case.p7.kb_member.add_and_remove.op` | op | **pass** | 4s | load1=21.89 | predicate: all 15 facts hold: observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read # |
| `case.p7.decision_status.review_list.op` | op | **pass** | 3s | load1=21.98 | predicate: all 9 facts hold: observe_at status holds; observe_at id holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.n |
| `case.p7.decision_supersede.successor_visible.op` | op | **pass** | 4s | load1=21.98 | predicate: all 6 facts hold: observe_at status holds; observe_at superseded_by holds; op read #0 (decision.read) id holds; op read #0 (decision.read) deleted holds; the trigger receipt.target_ref hold |
| `case.p7.decision_supersede.receipt.op` | op | **pass** | 3s | load1=22.94 | predicate: all 9 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_ki |
| `case.p7.decision_delete.gone.op` | op | **pass** | 3s | load1=23.83 | predicate: all 9 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (kernel.receipt.read) ob |
| `case.p7.decision_create.receipt.op` | op | **pass** | 4s | load1=23.83 | predicate: all 7 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_ki |
| `case.p7.zone_file.refused_unknown_zone.op` | op | **pass** | 3s | load1=24.16 | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_ |
| `case.p7.kb_member.refused_bad_ref.op` | op | **pass** | 4s | load1=22.54 | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_ |
| `case.p7.decision_status.refused_invalid.op` | op | **pass** | 3s | load1=22.54 | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_ |
| `case.p7.decision_delete.refused_unknown.op` | op | **pass** | 4s | load1=23.70 | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_ |
| `case.j1.first_words_keep_as_note.kept.op` | op | **pass** | 3s | load1=24.77 | predicate: all 5 facts hold: observe_at id holds; observe_at body_markdown holds; observe_at title holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent |
| `case.j11.write_a_thought.window_open.op` | op | **pass** | 3s | load1=24.77 | predicate: all 3 facts hold: observe_at thought.id holds; observe_at thought.working_note.id holds; the trigger operation_id is absent |
| `case.j11.thought_keep.kept.op` | op | **pass** | 4s | load1=25.43 | predicate: all 4 facts hold: observe_at id holds; observe_at body_markdown holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent |
| `case.p7.zone_create.visible` | 1440 | **pass** | 27s | load1=31.92 | predicate: 'Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26} |
| `case.p7.zone_create.visible` | 393 | **pass** | 22s | load1=34.10 | predicate: 'Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26} |
| `case.p7.zone_file.note_in_zone` | 1440 | **pass** | 10s | load1=30.58 | predicate: 'Filed · Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 98, 'h': 18} |
| `case.p7.zone_file.note_in_zone` | 393 | **pass** | 10s | load1=29.16 | predicate: 'Filed · Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 98, 'h': 18} |
| `case.p7.zone_file.refile_moves` | 1440 | **pass** | 13s | load1=26.08 | predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 109, 'h': 18} |
| `case.p7.zone_file.refile_moves` | 393 | **pass** | 13s | load1=25.01 | predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 109, 'h': 18} |
| `case.p7.zone_unfile.note_leaves` | 1440 | **pass** | 10s | load1=22.37 | predicate: '+ Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 170} |
| `case.p7.zone_unfile.note_leaves` | 393 | **pass** | 10s | load1=21.06 | predicate: '+ Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 431, 'w': 347, 'h': 170} |
| `case.p7.kb_create.visible` | 1440 | **pass** | 12s | load1=21.61 | predicate: 'New Knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 145, 'w': 382, 'h': 26} |
| `case.p7.kb_create.visible` | 393 | **pass** | 11s | load1=21.88 | predicate: 'New Knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 123, 'w': 363, 'h': 26} |
| `case.p7.kb_member.add_and_remove` | 1440 | **pass** | 10s | load1=23.45 | predicate: '+ Atlas knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 137} |
| `case.p7.kb_member.add_and_remove` | 393 | **pass** | 11s | load1=22.54 | predicate: '+ Atlas knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 464, 'w': 347, 'h': 137} |
| `case.p7.decision_status.review_list` | 1440 | **pass** | 12s | load1=23.68 | predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 302, 'w': 928, 'h': 54} |
| `case.p7.decision_status.review_list` | 393 | **pass** | 11s | load1=25.60 | predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 383, 'w': 369, 'h': 103} |
| `case.p7.decision_supersede.successor_visible` | 1440 | **pass** | 9s | load1=23.76 | predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 56} |
| `case.p7.decision_supersede.successor_visible` | 393 | **pass** | 9s | load1=25.66 | predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 449, 'w': 363, 'h': 112} |
| `case.p7.decision_delete.gone` | 1440 | **pass** | 39s | load1=24.89 | predicate: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 748, 'w': 138, 'h': 27} |
| `case.p7.decision_delete.gone` | 393 | **pass** | 28s | load1=29.02 | predicate: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 628, 'w': 138, 'h': 27} |

27 of 27 pass (9 face cases at 1440 and 393, 18 `.op`), including `case.p7.decision_delete.gone` at both widths (it failed in Phase 7 story 03 before #665).

## The reds: one mutation per case

`docs/internal/philo/phase-8/atlas/mutate_atlas8.py.txt` writes the atlas with every case's expected result mutated ONCE (the wrong field value, the old defect's hub answer, the wrong words, a refused receipt); `assets/story-03-shots/mutations/` holds the runs on the phase build (face cases at 1440, `.op` headless). Each must FAIL by assertion, never block. These mutate the expectation, not the product: the product reds are the 28 main runs above.

| Case | Width | Verdict | Duration | Load | Reading |
|---|---|---|---|---|---|
| `case.p8.zone_create.second_unnamed` | 1440 | **fail** | 78s | load1=18.56 | predicate: all_of part input_value: value is 'New zone 2', wanted 'New zone 3' |
| `case.p8.zone_create.second_unnamed_floor` | 1440 | **fail** | 82s | load1=20.77 | predicate: all_of part input_value: value is 'New zone 2', wanted 'New zone 3' |
| `case.p8.zone_rename.list` | 1440 | **fail** | 67s | load1=22.03 | predicate: all_of part protocol_reads: GET /api/directories: 0 row(s) at 'directories' match {'name': 'Platform 2'}; exactly one is required |
| `case.p8.zone_rename.name_taken_list` | 1440 | **fail** | 60s | load1=29.14 | predicate: all_of part readable_text: 'NOT SAVED' NOT in observe_at text |
| `case.p8.zone_rename.name_taken_floor` | 1440 | **fail** | 69s | load1=26.27 | predicate: all_of part readable_text: 'NOT SAVED' NOT in observe_at text |
| `case.p8.zone_rename.f2_row` | 1440 | **fail** | 44s | load1=22.85 | predicate: all_of part input_value: value is 'Inbox', wanted 'Inbox 2' |
| `case.p8.chair.no_new_zone` | 1440 | **fail** | 25s | load1=21.76 | predicate: 'New Zone' NOT in observe_at text |
| `case.p8.list_delete.gone` | 1440 | **fail** | 69s | load1=17.57 | predicate: all_of part protocol_reads: GET /api/decisions/decision_436e59672b72 answered 404, wanted 200 |
| `case.p8.list_delete.undo` | 1440 | **fail** | 54s | load1=21.89 | predicate: all_of part protocol_reads: GET /api/decisions/decision_502760a35002 answered 200, wanted 404 |
| `case.p8.list_delete.long_list_393` | 1440 | **fail** | 68s | load1=30.79 | predicate: all_of part protocol_reads: GET /api/decisions/decision_9fb3a1dd37e8 answered 404, wanted 200 |
| `case.p8.delete_twice.both_gone` | 1440 | **fail** | 81s | load1=24.88 | predicate: all_of part protocol_reads: GET /api/decisions/decision_ecbaf5478f61 answered 404, wanted 200 |
| `case.p8.delete_then_leave.gone` | 1440 | **fail** | 52s | load1=28.09 | predicate: all_of part protocol_reads: GET /api/decisions/decision_ff5632e53820 answered 404, wanted 200 |
| `case.p8.chair.delete_withheld` | 1440 | **fail** | 43s | load1=18.95 | predicate: all_of part protocol_reads: GET /api/decisions/decision_ec67fb82301d answered 200, wanted 404 |
| `case.p8.decision_heads.hidden` | 1440 | **fail** | 30s | load1=21.78 | predicate: all_of part readable_text: 'CONSEQUENCES' NOT in observe_at text |
| `case.p8.zone_create.second_unnamed.op` | op | **fail** | 35s | load1=25.12 | predicate: fact #1 failed: observe_at <root> holds no row matching {'id': 'dir_587088e1d315', 'name': 'New zone 3'} |
| `case.p8.zone_rename.list.op` | op | **fail** | 34s | load1=27.40 | predicate: fact #1 failed: observe_at directory.name = 'Platform', wanted 'Platform 2' |
| `case.p8.zone_rename.name_taken_list.op` | op | **fail** | 34s | load1=21.63 | predicate: fact #1 failed: the trigger existing_name = 'Inbox', wanted 'Inbox 2' |
| `case.p8.list_delete.gone.op` | op | **fail** | 35s | load1=17.65 | predicate: fact #4 failed: op read #1 (kernel.receipt.read) objects.0.receipt.state = 'succeeded', wanted 'refused' |
| `case.p8.delete_twice.both_gone.op` | op | **fail** | 35s | load1=14.75 | predicate: fact #7 failed: op read #1 (kernel.receipt.read) objects.0.receipt.state = 'succeeded', wanted 'refused' |

## The closing rehearsal (exit 6)

`assets/story-03-shots/rehearsal-b65107f5/` — `scripts/philo8_rehearsal.py` on the phase build `b65107f5` (a `git archive` copy; main `ce772ef9` + story 02): one real hub (the rig's `Hub`, its own process, a fresh isolated HOME), one Chromium page per width (1440x900, 393x852, 2x), the six jobs in order on the list, the hub read back after each job (`rehearsal.json`, which also records the load average and zero page errors at both widths). A rehearsal, not a sitting. **For the owner's review before merge; it is re-run on merged main after #672 merges.**

| Width | Job | What the face showed | The hub, read back after the job | Shots |
|---|---|---|---|---|
| 1440 | two unnamed zones | list; the second field reads 'New zone 2' | new zones: ['New zone', 'New zone 2'] | `1440-1-second-zone-field.png` |
| 1440 | rename where he is | list; Enter in the row | zones now: ['New zone', 'Platform 1440'] | `1440-2-renamed-in-row.png` |
| 1440 | list delete, no Undo | 'Removed Rehearsal keep 1440\nUndo\n07s' then 'Removal committed' | Rehearsal keep 1440: 404 | `1440-3a-list-delete-pending.png`, `1440-3b-list-delete-committed.png` |
| 1440 | list delete with Undo | 'Restored Rehearsal undo 1440'; the row still listed after the window: True | Rehearsal undo 1440 (after the window): 200 | `1440-4a-list-undo-restored.png`, `1440-4b-list-undo-after-window.png` |
| 1440 | two deletes in one window | after B: 'Removed Rehearsal B 1440\nUndo\n08s' | Rehearsal A 1440: 404; Rehearsal B 1440: 404 | `1440-5a-two-deletes-b-pending.png`, `1440-5b-two-deletes-committed.png` |
| 1440 | delete, then a face change | list -> Chair inside the window | Rehearsal leave 1440: 404 | `1440-6a-delete-pending-before-leaving.png`, `1440-6b-on-the-chair.png` |
| 393 | two unnamed zones | list; the second field reads 'New zone 3' | new zones: ['New zone 2', 'New zone 3'] | `393-1-second-zone-field.png` |
| 393 | rename where he is | list; Enter in the row | zones now: ['New zone 2', 'Platform 393'] | `393-2-renamed-in-row.png` |
| 393 | list delete, no Undo | 'Removed Rehearsal keep 393\nUndo\n08s' then 'Removal committed' | Rehearsal keep 393: 404 | `393-3a-list-delete-pending.png`, `393-3b-list-delete-committed.png` |
| 393 | list delete with Undo | 'Restored Rehearsal undo 393'; the row still listed after the window: True | Rehearsal undo 393 (after the window): 200 | `393-4a-list-undo-restored.png`, `393-4b-list-undo-after-window.png` |
| 393 | two deletes in one window | after B: 'Removed Rehearsal B 393\nUndo\n08s' | Rehearsal A 393: 404; Rehearsal B 393: 404 | `393-5a-two-deletes-b-pending.png`, `393-5b-two-deletes-committed.png` |
| 393 | delete, then a face change | list -> Chair inside the window | Rehearsal leave 393: 404 | `393-6a-delete-pending-before-leaving.png`, `393-6b-on-the-chair.png` |

Notes for the reviewer: at 393 the first zone job made "New zone 2" and "New zone 3" because the 1440 leg (same hub) had left "New zone" and renamed "New zone 2" to "Platform 1440": the free name is the lowest free number, by the hub's rule. In `1440-1-second-zone-field.png` the field shows "New zone 2" but the text is not drawn as selected (the story 01 fences assert the selection right after New Zone; this driver closes the palette first). Observed in the shot only; not examined.

## Counts at the branch commit

| File | main `ce772ef9` | this branch |
|---|---|---|
| `docs/internal/philo/graph/atlas.json` | 85 | 85 |
| `docs/internal/philo/graph/atlas-phase3.json` | 36 | 36 |
| `docs/internal/philo/graph/atlas-phase7.json` | 27 | 27 (three state anchors re-anchored; no case changed) |
| `docs/internal/philo/graph/atlas-phase8.json` | — | 19 (14 face, 5 `.op`) |
| total | 148 | 167 |

## The rig and the fences

- `scripts/graph_walk.py` 1.5.0; both calibrations still OK on this branch (`calibrate --headless`: 6/6; `calibrate` with a page: 6/6, "RIG 1.5.0 calibration: OK").
- `tests/unit/test_philo8_atlas.py`: the two predicates (pass, fail, unsent read, missing read, blocked shapes, headless), the right-click (reaches the page as a right-click; a button the rig cannot press is blocked), `then` (ui steps only), the atlas file (the named ids, both widths, `.op` pairs, exclusions, readable face checks, hub reads on every delete case, the in-window gestures), and 17 general fences of `tests/unit/test_philo_graph_atlas.py` applied to this file (16 parametrized, plus the OpenAPI route check) (they read `atlas.json` only by default).
- `docs/internal/philo/graph/atlas-phase7.json`: `test_every_source_reference_lands_on_its_symbol[atlas-phase7.json]` was RED on main `ce772ef9` (`verbRegistry.ts:204 no longer holds 'id: "desk.new-zone"'`, and 160, 547): story 01 moved the lines. Re-anchored to 220, 176, 568.
- Generators: `docs/generated/api-reference.json` regenerated; every `scripts/philo_*.py --check` exits 0 (captured below); `philo_graph_validate.py docs/generated/graph.json` OK.

## What waits on #672 (and on the owner)

- The delete cases (`case.p8.list_delete.*`, `case.p8.delete_twice.both_gone`, `case.p8.delete_then_leave.gone`, `case.p8.chair.delete_withheld`) re-run on MERGED main; the state anchors in `atlas-phase8.json` re-checked (the builder re-anchors: `docs/internal/philo/phase-8/atlas/build_atlas8.py.txt`).
- The closing rehearsal re-run on merged main; the owner reviews the shots. Then this story flips done and `final-summary.md` gets its CLOSED line.
- Codex Astra's check on this PR.

## Proof

### Captured run — 2026-09-26T22:20:40Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ctzLx0igcW uv run pytest -q -p no:cacheprovider tests/unit/test_philo8_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo7_atlas.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo_graph_reference.py tests/unit/test_evidence_scratch_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c73086c4c51abc8f2ec5959152e6595bff736dc

```text
........................................................................ [ 34%]
........................................................................ [ 69%]
...............................................................          [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: "\(" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\("? A raw string is also an option.
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
207 passed, 2 warnings in 17.13s
```

### Captured run — 2026-09-26T22:21:06Z

- **Command:** `bash -c for s in api_reference boundary_census config_reference council_check doctor_reference graph_reference openapi_reference repository_census; do HOME=$(mktemp -d) uv run python scripts/philo_$s.py --check >/dev/null 2>&1; echo "philo_$s --check exit $?"; done; HOME=$(mktemp -d) uv run python scripts/philo_graph_validate.py docs/generated/graph.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c73086c4c51abc8f2ec5959152e6595bff736dc

```text
philo_api_reference --check exit 0
philo_boundary_census --check exit 0
philo_config_reference --check exit 0
philo_council_check --check exit 0
philo_doctor_reference --check exit 0
philo_graph_reference --check exit 0
philo_openapi_reference --check exit 0
philo_repository_census --check exit 0
OK docs/generated/graph.json
```

### Captured run — 2026-09-26T22:21:20Z

- **Command:** `python3 docs/internal/philo/phase-8/atlas/verdicts.py pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/main-267f692a pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase-b65107f5 pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase7-on-b65107f5 pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/mutations`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c73086c4c51abc8f2ec5959152e6595bff736dc

```text
## pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/main-267f692a  (28 runs)
case.p8.zone_create.second_unnamed | 1440 | fail | 92.0s | - | predicate: all_of part protocol_status: POST /api/directories answered 409, wanted 201 (body sha256 8b06698a05e0)
case.p8.zone_create.second_unnamed | 393 | fail | 75.8s | - | predicate: all_of part protocol_status: POST /api/directories answered 409, wanted 201 (body sha256 8b06698a05e0)
case.p8.zone_create.second_unnamed_floor | 1440 | fail | 90.4s | - | predicate: all_of part protocol_status: POST /api/directories answered 409, wanted 201 (body sha256 8b06698a05e0)
case.p8.zone_create.second_unnamed_floor | 393 | fail | 74.0s | - | predicate: all_of part protocol_status: POST /api/directories answered 409, wanted 201 (body sha256 8b06698a05e0)
case.p8.zone_rename.list | 1440 | fail | 80.0s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.zone_rename.list | 393 | fail | 62.7s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.zone_rename.name_taken_list | 393 | fail | 65.4s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.zone_rename.name_taken_floor | 1440 | fail | 83.4s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.zone_rename.name_taken_floor | 393 | fail | 57.3s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.zone_rename.f2_row | 1440 | fail | 41.6s | - | predicate: all_of part input_value: no form control at '.desk-listmode input.desk-zone-rename' (its value cannot be read)
case.p8.zone_rename.f2_row | 393 | fail | 34.4s | - | predicate: all_of part input_value: no form control at '.desk-listmode input.desk-zone-rename' (its value cannot be read)
case.p8.chair.no_new_zone | 1440 | fail | 25.2s | - | predicate: the named text scope is absent or hidden
case.p8.chair.no_new_zone | 393 | fail | 24.0s | - | predicate: the named text scope is absent or hidden
case.p8.list_delete.gone | 1440 | fail | 66.6s | - | predicate: all_of part protocol_reads: GET /api/decisions/decision_80059f33fc09 answered 200, wanted 404
case.p8.list_delete.gone | 393 | fail | 55.9s | - | predicate: all_of part protocol_reads: GET /api/decisions/decision_c86d88557db2 answered 200, wanted 404
case.p8.list_delete.undo | 1440 | fail | 49.8s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.list_delete.undo | 393 | fail | 35.8s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.list_delete.long_list_393 | 1440 | fail | 68.1s | - | predicate: all_of part protocol_reads: GET /api/decisions/decision_1975ace42ca6 answered 200, wanted 404
case.p8.list_delete.long_list_393 | 393 | fail | 57.0s | - | predicate: all_of part protocol_reads: GET /api/decisions/decision_a4ce513e336e answered 200, wanted 404
case.p8.delete_twice.both_gone | 393 | fail | 62.7s | - | predicate: all_of part protocol_reads: GET /api/decisions/decision_d055cd595f67 answered 200, wanted 404
case.p8.delete_then_leave.gone | 1440 | fail | 58.8s | - | predicate: all_of part protocol_status: no trigger response was recorded; `protocol_status` reads the status of the trigger's own call
case.p8.delete_then_leave.gone | 393 | fail | 46.4s | - | predicate: all_of part protocol_status: no trigger response was recorded; `protocol_status` reads the status of the trigger's own call
case.p8.chair.delete_withheld | 1440 | fail | 51.5s | - | predicate: all_of part readable_text: 'Open the Floor or the list' NOT in observe_at text
case.p8.chair.delete_withheld | 393 | fail | 41.7s | - | predicate: all_of part readable_text: 'Open the Floor or the list' NOT in observe_at text
case.p8.decision_heads.hidden | 1440 | fail | 31.4s | - | predicate: all_of part text_absent: 'CONSEQUENCES' PRESENT at observe_at
case.p8.decision_heads.hidden | 393 | fail | 29.9s | - | predicate: all_of part text_absent: 'CONSEQUENCES' PRESENT at observe_at
case.p8.zone_rename.name_taken_list | 1440 | fail | 82.2s | - | predicate: all_of part readable_text: the named text scope is absent or hidden
case.p8.delete_twice.both_gone | 1440 | blocked | 46.6s | - | BLOCKED: ui step wait_for on '.undo-receipt.is-pending' failed: TimeoutError: Locator.wait_for: Timeout 3000ms exceeded. Call log:   - waiting for locator(".undo-receipt.is-pending").first to be visible 

## pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase-b65107f5  (33 runs)
case.p8.zone_create.second_unnamed | 1440 | pass | 51.4s | - | predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 508e33e7db8b) | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New zone'}; GET /api/directories answered 200
case.p8.zone_create.second_unnamed | 393 | pass | 19.5s | - | predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 2dab480104ca) | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New zone'}; GET /api/directories answered 200
case.p8.zone_create.second_unnamed_floor | 1440 | pass | 55.8s | - | predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 5b5a47a89780) | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New zone'}; GET /api/directories answered 200
case.p8.zone_create.second_unnamed_floor | 393 | pass | 29.5s | - | predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 bc011c2af431) | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New zone'}; GET /api/directories answered 200
case.p8.zone_rename.list | 1440 | pass | 39.3s | - | predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 280, 'w': 53, 'h': 24} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'Platfo
case.p8.zone_rename.list | 393 | pass | 22.5s | - | predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 364, 'w': 53, 'h': 24} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'Platform
case.p8.zone_rename.name_taken_list | 1440 | pass | 37.4s | - | predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 322, 'w': 112, 'h': 18} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New
case.p8.zone_rename.name_taken_list | 393 | pass | 16.6s | - | predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 394, 'w': 112, 'h': 18} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New z
case.p8.zone_rename.name_taken_floor | 1440 | pass | 52.2s | - | predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1208, 'y': 167, 'w': 112, 'h': 18} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'Ne
case.p8.zone_rename.name_taken_floor | 393 | pass | 24.5s | - | predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 14, 'y': 315, 'w': 112, 'h': 18} | protocol_reads: GET /api/directories answered 200 with one row {'name': 'New z
case.p8.zone_rename.f2_row | 1440 | pass | 30.8s | - | predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 196, 'w': 389, 'h': 36}
case.p8.zone_rename.f2_row | 393 | pass | 19.7s | - | predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 220, 'w': 122, 'h': 36}
case.p8.chair.no_new_zone | 1440 | pass | 11.0s | - | predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 73, 'w': 382, 'h': 44}
case.p8.chair.no_new_zone | 393 | pass | 11.5s | - | predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 51, 'w': 363, 'h': 44}
case.p8.delete_twice.both_gone | 1440 | pass | 47.9s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_a585b580f486 answered 404; GET /api/decisions/decision_74c117f85e7e answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height':
case.p8.delete_twice.both_gone | 393 | pass | 28.2s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_59daf656bebe answered 404; GET /api/decisions/decision_b88b85b3d739 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 
case.p8.delete_then_leave.gone | 1440 | pass | 28.3s | - | predicate: all_of: protocol_status: DELETE /api/decisions/decision_e034bc8d856f answered 200, wanted 200 (body sha256 dc9a8cb432ca) | protocol_reads: GET /api/decisions/decision_e034bc8d856f answered 404
case.p8.delete_then_leave.gone | 393 | pass | 16.0s | - | predicate: all_of: protocol_status: DELETE /api/decisions/decision_e5680dbc9f3c answered 200, wanted 200 (body sha256 3825f093e844) | protocol_reads: GET /api/decisions/decision_e5680dbc9f3c answered 404
case.p8.chair.delete_withheld | 1440 | pass | 20.4s | - | predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26} | attr_equals: aria-disabled='true', wanted 'true' | protocol_
case.p8.chair.delete_withheld | 393 | pass | 16.3s | - | predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26} | attr_equals: aria-disabled='true', wanted 'true' | protocol_rea
case.p8.decision_heads.hidden | 1440 | pass | 9.5s | - | predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 94} | text_absent: 'CONSEQUENCES' absent at observe_at
case.p8.decision_heads.hidden | 393 | pass | 9.4s | - | predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 439, 'w': 363, 'h': 122} | text_absent: 'CONSEQUENCES' absent at observe_at
case.p8.zone_create.second_unnamed.op | op | pass | 3.1s | - | predicate: all 3 facts hold: observe_at <root> holds; observe_at <root> holds; the trigger operation_id is absent
case.p8.zone_rename.list.op | op | pass | 3.1s | - | predicate: all 3 facts hold: observe_at directory.id holds; observe_at directory.name holds; the trigger operation_id is absent
case.p8.zone_rename.name_taken_list.op | op | pass | 3.1s | - | predicate: all 3 facts hold: the trigger error holds; the trigger existing_name holds; observe_at directory.name holds
case.p8.list_delete.gone.op | op | pass | 3.1s | - | predicate: all 7 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (kernel.receipt.read) objects.0.operation.name holds; 
case.p8.delete_twice.both_gone.op | op | pass | 3.1s | - | predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; op read #0 (ker
case.p8.list_delete.gone | 1440 | pass | 36.6s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_2b228a1683f5 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 788, 'w': 138, 'h': 27}
case.p8.list_delete.gone | 393 | pass | 23.9s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_2888f0429f12 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 668, 'w': 138, 'h': 27}
case.p8.list_delete.undo | 1440 | pass | 35.9s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_be2f7c7c73fc answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 621, 'y': 788, 'w': 198,
case.p8.list_delete.undo | 393 | pass | 19.0s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_93a3482d4066 answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 98, 'y': 668, 'w': 198, '
case.p8.list_delete.long_list_393 | 1440 | pass | 35.5s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_2d16bde3753f answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 788, 'w': 138, 'h': 27}
case.p8.list_delete.long_list_393 | 393 | pass | 23.0s | - | predicate: all_of: protocol_reads: GET /api/decisions/decision_d24d5e3504a1 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 668, 'w': 138, 'h': 27}

## pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase7-on-b65107f5  (36 runs)
case.p7.zone_create.visible.op | op | pass | 3.6s | - | predicate: all 5 facts hold: observe_at directory.id holds; observe_at directory.name holds; observe_at directory.parent_id holds; op read #0 (zone.list) <root> holds; the trigger operation_id is absent
case.p7.zone_file.note_in_zone.op | op | pass | 3.2s | - | predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (ke
case.p7.zone_file.refile_moves.op | op | pass | 5.8s | - | predicate: all 16 facts hold: observe_at <root> holds; op read #0 (zone.members) <root> holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (kernel.receipt.read) objects.0.operation.name holds;
case.p7.zone_unfile.note_leaves.op | op | pass | 3.2s | - | predicate: all 17 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (ke
case.p7.kb_create.visible.op | op | pass | 3.1s | - | predicate: all 4 facts hold: observe_at id holds; observe_at name holds; op read #0 (kb.list) <root> holds; the trigger operation_id is absent
case.p7.kb_member.add_and_remove.op | op | pass | 3.7s | - | predicate: all 15 facts hold: observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) object
case.p7.decision_status.review_list.op | op | pass | 3.1s | - | predicate: all 9 facts hold: observe_at status holds; observe_at id holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.
case.p7.decision_supersede.successor_visible.op | op | pass | 3.2s | - | predicate: all 6 facts hold: observe_at status holds; observe_at superseded_by holds; op read #0 (decision.read) id holds; op read #0 (decision.read) deleted holds; the trigger receipt.target_ref holds; the trigger operation_id ho
case.p7.decision_supersede.receipt.op | op | pass | 3.1s | - | predicate: all 9 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0
case.p7.decision_delete.gone.op | op | pass | 3.2s | - | predicate: all 9 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (kernel.receipt.read) objects.0.operation.name holds; 
case.p7.decision_create.receipt.op | op | pass | 3.6s | - | predicate: all 7 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0
case.p7.zone_file.refused_unknown_zone.op | op | pass | 3.1s | - | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0.receipt.actor_ide
case.p7.kb_member.refused_bad_ref.op | op | pass | 3.2s | - | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0.receipt.actor_ide
case.p7.decision_status.refused_invalid.op | op | pass | 3.1s | - | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0.receipt.actor_ide
case.p7.decision_delete.refused_unknown.op | op | pass | 3.1s | - | predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.receipt.actor_kind holds; observe_at objects.0.receipt.actor_ide
case.j1.first_words_keep_as_note.kept.op | op | pass | 3.1s | - | predicate: all 5 facts hold: observe_at id holds; observe_at body_markdown holds; observe_at title holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent
case.j11.write_a_thought.window_open.op | op | pass | 3.1s | - | predicate: all 3 facts hold: observe_at thought.id holds; observe_at thought.working_note.id holds; the trigger operation_id is absent
case.j11.thought_keep.kept.op | op | pass | 3.2s | - | predicate: all 4 facts hold: observe_at id holds; observe_at body_markdown holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent
case.p7.zone_create.visible | 1440 | pass | 27.0s | - | predicate: 'Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26}
case.p7.zone_create.visible | 393 | pass | 22.3s | - | predicate: 'Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26}
case.p7.zone_file.note_in_zone | 1440 | pass | 9.8s | - | predicate: 'Filed · Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 98, 'h': 18}
case.p7.zone_file.note_in_zone | 393 | pass | 9.8s | - | predicate: 'Filed · Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 98, 'h': 18}
case.p7.zone_file.refile_moves | 1440 | pass | 12.3s | - | predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 109, 'h': 18}
case.p7.zone_file.refile_moves | 393 | pass | 12.5s | - | predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 109, 'h': 18}
case.p7.zone_unfile.note_leaves | 1440 | pass | 9.3s | - | predicate: '+ Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 170}
case.p7.zone_unfile.note_leaves | 393 | pass | 9.8s | - | predicate: '+ Atlas zone' is readable in viewport {'width':
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-26T22:21:29Z

- **Command:** `python3 -c 
import json,glob,collections,sys
for d in sys.argv[1:]:
    c=collections.Counter(); 
    for f in sorted(glob.glob(d+'/*/observation.json')):
        r=json.load(open(f)); c[r['verdict']]+=1
        if r['verdict']!='pass' and 'mutations' not in d and 'main-' not in d: print('  NOT PASS', r['case_id'], r['viewport'])
        if 'main-' in d and r['verdict']!='fail': print('  NOT FAIL', r['case_id'], r['viewport'], r['verdict'])
    print(d.rsplit('/',1)[1], dict(c))
 pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/main-267f692a pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase-b65107f5 pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/phase7-on-b65107f5 pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/mutations`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c73086c4c51abc8f2ec5959152e6595bff736dc

```text
  NOT FAIL case.p8.delete_twice.both_gone 1440 blocked
main-267f692a {'fail': 27, 'blocked': 1}
phase-b65107f5 {'pass': 33}
phase7-on-b65107f5 {'pass': 36}
mutations {'fail': 19}
```
