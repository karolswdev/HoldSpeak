# PHILO-7-03 — round two: Muad'Dib's F2 and F3 paid (F4 recorded)

- **Story:** PHILO-7-03 The atlas for the desk; PR #663, branch `feat/philo-7-03-atlas`
- **Answers:** `checks/story-03-built-muaddib.md` (Muad'Dib's counsel on built, RATIFY-WITH-CONDITIONS, at `ca744702`)
- **Lane:** the Fedaykin lane (Opus 5.5). Astra's check is still owed (she returns 2026-09-26).
- **Date:** 2026-09-25
- **Why here:** `evidence-story-03.md` is locked by the story's done status; the corrections to it live in this record and in the phase status "Where we are".

## F2 — the equivalence run was weaker than "18/18" said. PAID.

- **(a) The delete identity was vacuous.** `_delete_face`/`_delete_op` returned `True` whatever they read. Now `scripts/philo7_pairs.py:153-181`:
  - face (`:153`): the id the setup minted is the id whose own read answers 404, and the list no longer holds it;
  - op (`:164`): the id is absent from `decision.list`, its own read refuses `not_found` naming it, and the READ delete receipt carries the delete's captured `operation_id` and names `decision:<id>` as target.
- **(b) The refusal leg was vacuous where the face sends nothing.** `:193` reads the face trigger's own captured network response. Where there is none, the row records `refusal_check: {status: not_applicable, reason, op_refused}` (`:234-242`), never "not refused". In both folders that is 6 of 18 pair-widths: `zone_create.visible`, `kb_create.visible` and `decision_supersede.successor_visible` at both widths (a Search fill; the write ran in setup). The other 12 read the trigger's own response (PUT/DELETE membership, DELETE decision, all 200). **One more disclosure:** for `decision_status.review_list` the checked response is `POST /api/brief/generate`, the trigger that makes the brief. The status write itself is a face click in SETUP, and its refusal and receipt are not read by the face pair (C1 in the counsel).
- **(c) The runs behind "18".** One headless `.op` run serves BOTH face widths of its pair (`op_run_shared_across_widths: true`, `:257`). The script now prints and stores the plain count (`:280`): **18/18 pair-widths equivalent, over 9 headless op runs (each shared by both widths) × 18 face runs; the refusal leg is not applicable on 6 of them.** Read the evidence file's "18/18 pair-widths" with that sentence.
- `pairs.json` is regenerated in both folders (`assets/story-03-shots/real-engine/pairs.json`, `assets/story-03-shots/replay-engine-none/pairs.json`). It is now `{summary, pairs}`, and every row carries `refusal_check` and `op_run_shared_across_widths`. The verdicts are unchanged: 18/18, `decision_delete.gone` face FAIL at both widths.
- **Fences:** `tests/unit/test_philo7_atlas.py:414` (`test_the_delete_identity_is_a_real_check`) and `:426` (`test_a_face_trigger_that_sends_nothing_is_not_a_refusal_check`).
- **Reds:** `docs/internal/philo/phase-7/atlas/reds/round-two-pairs-base.txt`, both tests run against a `git archive` of the pre-round-two `pairs.py`:
  - the delete fence is a real red: `assert True is False` (the old identity returned True for a listed, readable decision);
  - the second fails with `AttributeError … _face_trigger_response`. That is a missing symbol, which by the fence law is **NOT** a lawful red. It is disclosed as such. The vacuity it guards was shown instead by reading the pre-fix `pairs.json` (a `refusals_equal: true` row whose face side had no response).

## F3 — the evidence claimed actor checks the cases did not make. PAID.

- **Correction to `evidence-story-03.md:63`** (locked). The sentence "asserted by its own `operation_id`, operation name, state, actor and, where it names them, target and result" was FALSE at `ca744702`:
  - `case.p7.decision_supersede.receipt.op` and `case.p7.decision_create.receipt.op` asserted no actor;
  - the four refusal-receipt cases asserted no actor;
  - the supersede receipt did not assert the successor.

  From this round the sentence is TRUE: every receipt the atlas reads asserts `actor_kind: owner` AND `actor_identity: owner-session` from that same read.
- **Atlas (`docs/internal/philo/graph/atlas-phase7.json`).** 23 new facts, and no existing fact changed:
  - `case.p7.decision_supersede.receipt.op` (`:2517`) captures the successor from the same supersede with `capture_more: [{as: successor_id, path: id}]`. It asserts the READ receipt's `result_ref: decision:{successor_id}`, the old decision's `superseded_by: {successor_id}`, and the actor;
  - `case.p7.decision_create.receipt.op` (`:2772`) asserts the actor;
  - the four refusal cases assert the actor;
  - every other receipt read gains `actor_identity`; `actor_kind` was already there.
- **Rig (`scripts/graph_walk.py:4104-4119`).** `capture_more` captures further values from the same record, and a missing value blocks. The trigger's pre-fire placeholder check counts them as minted (`:4841`). The schema (`atlas.schema.json`, op step) declares the field.
- **Fences:**
  - `tests/unit/test_philo7_atlas.py:219` (`test_every_receipt_read_asserts_its_actor`, over EVERY receipt read in the file);
  - `:238` (`test_the_supersede_receipt_names_the_successor_the_write_returned`);
  - `tests/unit/test_philo_graph_atlas.py` (`test_named_pair_observations_bind_their_read_arguments`) now counts `capture_more` names as bound.
- **Reds:**
  - `reds/round-two-structural-pre.txt`: both new structural fences are red against the `ca744702` atlas. The actor fence names every receipt read that did not assert its actor; the successor fence finds no `capture_more`;
  - `reds/round-two-new-facts.md`: each of the 23 NEW facts, mutated ALONE (owner → agent, owner-session → another principal, the successor → a wrong id), runs its case through the real rig headless. **23/23 `fail`**, each with the assertion reading that names the fact. None is blocked.
- **Retained runs.** All 18 `.op` cases were re-run against the round-two atlas into BOTH folders: `real-engine` 18/18 pass, `replay-engine-none` 18/18 pass, 2.8–4.4 s. The round-one `.op` runs stay beside them; nothing is deleted. `pairs.py` reads the newest run per case.

## F4 — recorded

The 27 round-one mutation reds mutate the EXPECTATION, not the product. They prove each predicate discriminates; they do not prove a product regression turns a case red. **The mutation red for `case.p7.decision_delete.gone` proves nothing**, because that case already fails UNMUTATED on the face finding (the undo receipt drawn above the top edge). 26 of 27 are meaningful. The 23 round-two reds are of the same kind (expectation mutations) and every one of those cases passes unmutated.

## Counts and tests

- Atlas counts are unchanged by this round: `atlas.json` 85, `atlas-phase3.json` 36, `atlas-phase7.json` 27 (9 face, 18 `.op`), 148 in total.
- Scoped set: `HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_philo7_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo_graph_reference.py` → **152 passed** (148 + 4 new).

## Left as it was

- Astra's four untracked files under `docs/internal/philo/phase-7/atlas/` (`design.md`, `orientation.md`, `baseline-collect.txt`, `baseline-run.txt`) are untouched.
- C1, C2 and the F5 divergences remain Astra's rulings.

## Round three: the Astra-role check (Opus 5.5 stand-in), K1–K4 paid

- **Source:** `checks/story-03-built-astra-role-r1.md` (RATIFY-WITH-CONDITIONS). It rules **C1** (the narrower reading is lawful: reword the box, add no op cases) and **C2** (accept `atlas-phase7.json`).
- **Merge:** `origin/main` was merged into the branch first (merge commit `bb072063`, which brings #666's guard allow-list).
- **K1:** `tests/unit/test_graph_walk_calibration.py:272-274` expects the eight-action UI vocabulary, including `focus`. Red before the fix, on the merged tree: `Extra items in the left set: 'focus'`.
- **K2:** `tests/unit/test_evidence_scratch_guard.py:27` allow-lists `tests/unit/test_philo7_atlas.py` as a READER, beside `test_philo5_his_words.py`. Red before the fix, on the merged tree: `assert not ['tests/unit/test_philo7_atlas.py:30']`.
- **K3:** `docs/generated/api-reference.json` is regenerated (+15 lines: round two's fences named more routes). It showed `API reference drift` before. Every `scripts/philo_*.py --check` now exits 0 (api, boundary census, config, doctor, graph, openapi, repository census).
- **K4 (C1):** the story's acceptance box now reads "for each admitted write the NAMED cases fire". It names the unexercised admitted writes and their story 02 fence (`tests/unit/test_philo7_article_xi.py:87-91`, `_one`), and cites the ruling. The gate accepted the edit to the done story file.
- **Scoped run:** the five named files plus the guard plus the calibration fence give **216 passed**.
