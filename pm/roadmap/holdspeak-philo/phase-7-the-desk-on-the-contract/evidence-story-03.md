# Evidence - PHILO-7-03

- **Story:** PHILO-7-03 - The atlas for the desk
- **Status:** done
- **Date:** 2026-09-25

## Proof

### Captured run — 2026-09-25T22:26:56Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.1gt9okwDlD PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q tests/unit/test_philo7_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo_graph_reference.py -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ba2821a68d6b150fb772b75f55a9752a7448a10

```text
........................................................................ [ 48%]
........................................................................ [ 97%]
....                                                                     [100%]
148 passed in 15.30s
```

## What was built (commit `e3a32308`)

- `docs/internal/philo/graph/atlas-phase7.json` (new, `extends` atlas.json, the per-phase precedent of `atlas-phase3.json`): 27 cases, 3 states, 1 clock, 1 exclusion.
- `scripts/graph_walk.py` rig 1.3.0 -> 1.4.0: the `op_facts` predicate (a conjunction over the durable `observe_at` read, the supplementary op `reads` and the trigger's own record; a missing, unsent or refused source FAILS; an empty list or a fact without a test is BLOCKED); `capture_from: refusal` (a refused admitted write's `operation_id`); `capture_match` on `api` captures (the desk seeds zones and a knowledge base on first load, so a face-made row is captured by its name, never by its position); the ui `focus` action and the `at_width` step field. Carriage repaired: `kb.member.add/remove` block the non-canonical `ref` (the `resource_ref`/`ref` collapse executed a DIFFERENT admitted write — Astra's probe, `docs/internal/philo/phase-7/atlas/red-kb-alias-probe.txt`); `decision.supersede` blocks `successor_id` (the MCP tool's closed schema cannot carry it; the rig answered a refusal the operation never gives).
- `scripts/philo7_pairs.py`: the equivalence run.
- `tests/unit/test_philo7_atlas.py` (22 tests), `tests/unit/test_philo_graph_atlas.py` (the op-sibling fence counts 21 -> 39 and learns the desk operations and `op_facts`), the two schemas (`op_facts`; job `p7`; ui `focus`/`at_width`; op `capture_from`; api `capture_match`), `docs/generated/api-reference.json` regenerated (the new test file names routes).

## Atlas counts at the branch commit

| File | base `f6695090` | branch `e3a32308` |
|---|---|---|
| `docs/internal/philo/graph/atlas.json` | 85 | 85 |
| `docs/internal/philo/graph/atlas-phase3.json` | 36 | 36 |
| `docs/internal/philo/graph/atlas-phase7.json` | — | 27 (9 face, 18 `.op`) |
| total | 121 | 148 |

No existing case was replaced or edited.

## Every case, both runs (durations measured by the lane's runner, one hub per invocation)

Folders: `assets/story-03-shots/real-engine/` (`--engine real`) and `assets/story-03-shots/replay-engine-none/` (`--engine none`, labelled REPLAY). The LAN engine answered: every real-engine run records `engine_identity` = `http://192.168.1.43:8080`, status 200, `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`. **No case here calls a model**: filing and deciding are deterministic, so the real-engine runs prove reachability plus the same deterministic outcomes, never an inference. The rig's `replayed` mode needs a case-declared provider reply; none of these cases has one, so the REPLAY folder is `--engine none` (no provider installed), not a provider fixture replay.

| Case | Width | Real engine | REPLAY (none) |
|---|---|---|---|
| case.p7.zone_create.visible | 1440 / 393 | pass 18.4s / pass 18.2s | pass 17.8s / pass 18.1s |
| case.p7.zone_file.note_in_zone | 1440 / 393 | pass 9.0s / pass 9.0s | pass 9.1s / pass 8.9s |
| case.p7.zone_file.refile_moves | 1440 / 393 | pass 10.4s / pass 10.4s | pass 10.3s / pass 10.4s |
| case.p7.zone_unfile.note_leaves | 1440 / 393 | pass 8.6s / pass 8.6s | pass 9.1s / pass 8.5s |
| case.p7.kb_create.visible | 1440 / 393 | pass 9.6s / pass 9.5s | pass 9.6s / pass 9.5s |
| case.p7.kb_member.add_and_remove | 1440 / 393 | pass 9.0s / pass 9.1s | pass 9.0s / pass 9.0s |
| case.p7.decision_status.review_list | 1440 / 393 | pass 9.9s / pass 9.8s | pass 9.9s / pass 9.8s |
| case.p7.decision_supersede.successor_visible | 1440 / 393 | pass 8.2s / pass 8.1s | pass 8.2s / pass 8.1s |
| case.p7.decision_delete.gone | 1440 / 393 | **FAIL** 64.1s / **FAIL** 56.9s | **FAIL** 63.6s / **FAIL** 56.6s |

Every `.op` case (headless, `/api/mcp` into the owning hub) passed in both folders, 2.8–4.4 s each: the nine `.op` siblings, `case.p7.decision_supersede.receipt.op`, `case.p7.decision_create.receipt.op`, the four refusal-receipt cases (`case.p7.zone_file.refused_unknown_zone.op`, `case.p7.kb_member.refused_bad_ref.op`, `case.p7.decision_status.refused_invalid.op`, `case.p7.decision_delete.refused_unknown.op`), and the note siblings `case.j1.first_words_keep_as_note.kept.op`, `case.j11.write_a_thought.window_open.op`, `case.j11.thought_keep.kept.op`. `case.p7.zone_file.refile_moves.op` restarts the real hub (same HOME, same port, no page) between the two filings and reads the first filing's receipt after the restart.

Every face predicate is `readable_text` (visible, in the viewport, all nine hit points owned). No face case reads or claims a receipt (fenced). Shots: `before.png`/`after.png` in each face run folder.

## Receipts read back (the `op` observations)

Each admitted write the `.op` cases fire has its receipt READ through `kernel.receipt.read` (`/api/mcp`, tool `kernel.receipt`) and asserted by its own `operation_id`, operation name, state, actor and, where it names them, target and result: `zone.file` (twice, one after a restart), `zone.unfile`, `kb.member.add`, `kb.member.remove`, `decision.update` (the status change over MCP; `decision.status` is HTTP only), `decision.supersede`, `decision.delete`, `decision.create`. Refusal receipts read back with `state: refused`: `zone.file` into an unknown zone (`not_found`), `kb.member.add` of an unqualified ref, `decision.update` with an invalid status (`invalid_value`), `decision.delete` of an unknown id (`not_found`). The exempt writes (`zone.create` and `kb.create` without id or members, `note.create`, the Thought save) are asserted to carry no `operation_id`.

## Equivalence (`scripts/philo7_pairs.py`, retained as `pairs.json` in each folder)

Durable outcome + identity relationships inside each run + refusals (neither side refused); never envelopes, never ids across hubs. 18/18 pair-widths `equivalent` in each folder, including `decision_delete.gone`, whose FACE verdict fails while the durable outcome (read refused `not_found`, not listed) is the same on both sides.

## Not on the face

- **The supersede ACTION.** `web/src/desk/api.ts:259` `supersedeDecision` has no caller; `web/src/desk/verbRegistry.ts` has no supersede verb; `DecisionPullout.tsx:125-134` only DISPLAYS "Supersedes <title>" / "Superseded by <id>". `case.p7.decision_supersede.successor_visible` therefore writes through `POST /api/decisions/{id}/supersede` in setup and proves what the Desk SHOWS (the successor opens by its own row and names the old decision, readable). This record does not waive story 04's shots.
- **The Floor's zones and objects** are a WebGL drawing; their DOM mirror `.desk-world-a11y` is clipped to 1px (`web/src/desk/desk.css:161-167`), so the Search row is the readable face for a made zone or knowledge base.

## Face findings (recorded, not fixed: this story changes no face)

1. **The delete receipt is drawn above the top edge.** After Delete on a selected decision, the undo receipt (`web/src/desk/gl/WorldStage.tsx:245-250`, `position: fixed; bottom: 12`) renders at rect `y=-12, h=27` at BOTH widths (`initial_feedback.hit_test` in the delete runs; 3 of 9 hit points off-screen). The `Removal committed` phase then lasts 1.2 s (`hooks/useUndoReceipt.ts:43`). The hub delete itself happened (`GET /api/decisions/{id}` 404, list lacks it). Cause not verified (a transformed ancestor is a guess, not a finding).
2. **New Zone from the Chair leaves no rename field.** The rename overlay lives only in the spatial `WorldStage`; on the Chair (the default face) the wait for `input.desk-zone-rename` timed out (first 1440 attempt, `.tmp` lane scratch). The case goes to the Floor first (`[data-testid=chair-floor-toggle]`).
3. **At 393 the Floor opens as a list** (`web/src/desk/store/types.ts:65-72`); the rename field and the delete listener exist only in the spatial view, so the 393 runs switch with Search > "Spatial view" (`at_width: 393` steps). Unverified by run: the list view's row-menu Delete (`DeskListView.tsx:332`) appears to have no listener (read from the code by the lane's research, not exercised).
4. **Deleting a decision needs a Floor selection** (keyboard: focus the world chip, Shift+Enter, then Delete); its pullout has no Delete (`DecisionPullout.tsx:142-166`).

## Fence law — the reds (`docs/internal/philo/phase-7/atlas/reds/`)

- `rig-carriage-base.txt`: the carriage fences against a `git archive` copy of the base rig (1.3.0) with the branch's test file: 5 red (the collapsed kb write EXECUTED `ref: note:other`; the supersede answered a schema refusal; the base rig cannot capture a refusal receipt — a named `Blocked`, not a missing symbol; the api capture took the whole list; the 393-only step ran at 1440), 1 green (`test_the_canonical_reference_is_carried`, a regression guard, not a fence).
- `atlas-mutations.md` + `atlas-mutations-run.log`: all 27 new cases run through the real rig with ONE deliberate mutation each (the wrong object's words on the face; a receipt asserted against the wrong operation id; the wrong identity) — 27/27 `fail` with an assertion reading, none blocked.
- The structural fence `test_every_captured_admitted_write_reads_its_receipt_by_its_own_id` was red on the lane's own draft (`case.p7.zone_unfile.note_leaves.op: zone.file {file_op} has no receipt read`) before the setup filing's receipt read was added.

## Generators

Every `scripts/philo_*.py --check` exits 0 at the branch (api reference regenerated first; it had drifted only by the new test file's name).

## Left out

- Conditionally admitted writes (`zone.create` with `directory_id`, `kb.create`/`kb.update` with members or id, `zone.update` with `parent_id`, `zone.delete`, the Thought-note delete) have no atlas case: they are not in the named list; story 02 fences them in unit tests.
- `case.j11.write_a_thought.create_refused` has no `.op` (excluded in the atlas with its reason: a browser-boundary interception, no durable outcome).
