# PHILO-7-03 — Muad'Dib's counsel on built

- **Story:** PHILO-7-03 The atlas for the desk
- **PR:** #663, branch `feat/philo-7-03-atlas`, checked at `ca744702` (build `e3a32308`), base `f6695090`
- **Checker:** Muad'Dib (Opus 5.5 counsel lane). This is Muad'Dib's counsel, NOT Astra's check. Astra is out of quota until 2026-09-26 20:50; the owner ruled "build on; Astra checks on return". The PR stays OPEN for Astra's check whatever this verdict says.
- **Date:** 2026-09-25

## VERDICT

**RATIFY-WITH-CONDITIONS** — MERGE when Astra agrees.

The build does what the story asks and reports it honestly. Every claim below was reproduced, not read. The one face FAIL (`case.p7.decision_delete.gone`) is a real defect of the Desk today, recorded as a FAIL and not waived; that is the lawful outcome under the story's Out clause ("a case records what the Desk shows today"). The conditions are rulings Astra owes on two scope readings, not rework.

## What was reproduced

1. **Counts.** At `ca744702`: `atlas.json` 85 (7 `.op`), `atlas-phase3.json` 36 (12 `.op`), `atlas-phase7.json` 27 (18 `.op`, 9 face) = 148. `git diff main...HEAD -- docs/internal/philo/graph/atlas.json docs/internal/philo/graph/atlas-phase3.json` is empty: no existing case changed. No file under `web/` or `holdspeak/` changed (face Out clause held).
2. **The focused fences.** `HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_philo7_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo_graph_reference.py` → `148 passed in 15.33s`. `--collect-only tests/unit/test_philo7_atlas.py` → 22 tests.
3. **The delete FAIL is the FACE.** `uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase7.json --case case.p7.decision_delete.gone --brain muaddib --viewport 393 --engine none --out <scratch>` (isolated HOME) → `VERDICT: fail terminal=settled`, 56.8 s. `initial_feedback.hit_test.rect = {x: 9, y: -12, w: 372, h: 27}`, `in_viewport: false`. The hub DID delete: `after.api_reads` `GET /api/decisions/{id}` → 404, `GET /api/decisions` → `[]`. The retained four runs agree (1440: `x: 1056, y: -12`; 393: `x: 9, y: -12`; 3 of 9 hit points unowned; hub 404 in each). Source: `web/src/desk/gl/WorldStage.tsx:245-250` (`position: fixed; right: 12; bottom: 12`), `web/src/desk/hooks/useUndoReceipt.ts:43` (committed phase 1.2 s). Observation, not cause: the right edge lands at viewport − 12 (1428 at 1440) but the bottom edge lands at y = 15, so the box's bottom is measured from something about 27 px from the top, not from the viewport bottom.
4. **Equivalence.** `uv run python scripts/philo7_pairs.py <folder> --out <scratch>` on both retained folders → 18 `equivalent`, exit 0, output byte-identical (JSON-normalised) to each retained `pairs.json`.
5. **Real-engine vs replay.** All 36 real-engine observations record `engine_identity.status 200` from `http://192.168.1.43:8080/v1/models`; all 36 in `replay-engine-none` record `null`. Both folders: 18 `.op` pass, 16 face pass, 2 face fail (the delete, both widths).
6. **Reds.** `reds/rig-carriage-base.txt`: 5 red + 1 green against a `git archive` of the base rig. `reds/atlas-mutations.md` + `atlas-mutations-run.log`: 27 runs, 27 `VERDICT: fail`, each with an assertion reading.
7. **Generators.** Every `scripts/philo_*.py` that takes `--check` exits 0 at the branch (7 scripts: api, boundary census, config, doctor, graph, openapi, repository census).
8. **Not on the face.** `grep supersedeDecision web/src` → only its definition at `web/src/desk/api.ts:259`; `web/src/desk/verbRegistry.ts` has no supersede verb; `web/src/desk/pullouts/DecisionPullout.tsx:125-134` renders "Supersedes …" / "Superseded by …" as navigation only; `:142-166` (the footer) has Copy, Dictate about this, Edit — no Delete. The record holds.
9. **Tree.** After my runs `git status --short` in the worktree shows only Astra's four untracked files (below); nothing under `pm/roadmap/holdspeak/`.

## Rulings on the questions asked

- **(2) The delete FAIL.** Recorded as a FAIL in the evidence table, the phase row, the README stamp and the mutation note. Not waived, not re-expected to pass. Lawful.
- **(5) "real-engine" as a label.** RULED honest as the rig's MODE label (`--engine real`, `engine_mode: real`), because the evidence says in plain words "No case here calls a model … never an inference". It would NOT be honest as a claim of inference; nothing in the records makes that claim. The `--engine none` folder is named `replay-engine-none` and the evidence says it is not a provider-fixture replay. Lawful.
- **(6) The base-rig refusal-capture red.** `test_a_refusal_receipt_is_captured_from_the_refusal_only_when_asked` goes red on the base rig through a `Blocked` raised by the base rig's own capture code on a real hub's real refusal. That is the behaviour absent, not an import failure or a missing symbol. RULED a real red (for a new capability, not a defect).
- **(7) Carriage coverage.** No loss. `kb.member.add/remove` still execute faithfully through the canonical `resource_ref` (mapped to the tool's `ref`; `test_the_canonical_reference_is_carried` asserts the sent arguments and the response). Only the NON-canonical `ref` key is refused by name. `decision.supersede`: every transport carries `decision_id` only (MCP `holdspeak/mcp/tools.py:431-435`, HTTP `holdspeak/web/routes/decisions.py:110`); the successor id is minted before admission (`holdspeak/services/desk_kernel.py:100-101`). So the `.op` supersede with `decision_id` alone IS the real admitted write. No existing case in `atlas.json` / `atlas-phase3.json` used `ref` or `successor_id` (grep empty).
- **(8) readable_text.** All nine face predicates are `readable_text`; the delete FAIL is itself the proof that the check reads viewport and hit points, not containment.
- **(10) `dirty=True`.** `scripts/graph_walk.py:317` sets `dirty = bool(git status --porcelain)`, which counts untracked files. The four untracked files are Astra's (`docs/internal/philo/phase-7/atlas/design.md` "Status: PROPOSED … Author: Astra", `orientation.md` "Owner: Astra", `baseline-collect.txt`, `baseline-run.txt`). Leaving them untracked is RIGHT: they are her work product, and committing them would publish a PROPOSED design under this story. Park them; Astra commits or retires them on return. Never delete.

## FINDINGS

| # | Severity | Finding | Reproduction |
|---|---|---|---|
| F1 | face defect (recorded, not this story's to fix) | The delete undo receipt is drawn above the top edge at both widths; "Removal committed" is never readable. | See "What was reproduced" 3. Filed in `pm/roadmap/holdspeak/BACKLOG.md` "PHILO-7-03 follow-ups". |
| F2 | minor, equivalence strength | (a) `_delete_face`/`_delete_op` return identity `True` unconditionally (`scripts/philo7_pairs.py:148-160`), so the identity leg of the delete pair is vacuous. (b) The refusals leg (`:174-176`, `:214`) reads the face trigger's network status; for `zone_create`, `kb_create` and `decision_supersede` the face trigger is a Search fill with no network response, so `status 0` → "not refused" is vacuous there (the write happened in setup). (c) The nine `.op` pair siblings ran ONCE each; each run serves both widths, so "18/18 pair-widths" rests on 9 op runs + 18 face runs. All three are true as written; none changes a verdict. | `jq '.[].engine' pairs.json`; `trigger_response_capture.chosen` is empty in the three face observations named. |
| F3 | minor, evidence wording | `evidence-story-03.md:63` says each receipt is asserted by "operation_id, operation name, state, actor and, where it names them, target and result". `case.p7.decision_supersede.receipt.op` and `case.p7.decision_create.receipt.op` assert no `actor_kind`; the supersede receipt's `result_ref` (the successor) is not asserted. | `atlas-phase7.json:2469`, `:2691` (the `facts` lists). |
| F4 | note | The 27 mutation reds mutate the EXPECTATION (the wrong words, the wrong id), not the product. They prove each predicate discriminates; they do not prove a product regression turns the case red. The delete's mutation proves nothing extra (disclosed in `atlas-mutations.md`). 26 of 27 are meaningful. Acceptable for an atlas that records today's Desk. | `reds/atlas-mutations.md` |
| F5 | note, process | Astra's `design.md` is marked "PROPOSED — Muad'Dib's check required before implementation"; the lane built without that check (Astra's lane died on quota). Two divergences from it: (a) the cases are in a NEW `atlas-phase7.json`, where her design said "Mint cases in the existing two atlas files" (the lane followed the `atlas-phase3.json` `extends` precedent); (b) her design said "Cover the admission table's conditional placement effects as operation cases"; the lane left them out (disclosed under "Left out"). | `docs/internal/philo/phase-7/atlas/design.md` (untracked) |

## CONDITIONS (for Astra's check; none is rework I require)

- **C1.** Astra rules the acceptance reading "for each admitted write (the admission table)". The lane met it as "each admitted write the named cases fire". Admitted rows with no atlas receipt read: `decision.status` over HTTP (its MCP twin `decision.update` is read), `zone.delete`, `kb.create`/`kb.update` with members or id, `zone.update` with `parent_id`, `zone.create` with `directory_id`, the Thought-note delete, `delegation.grant`/`revoke`. Story 02's unit fences cover them. Either amend the box wording to the narrower reading (Tenet 1 favours this) or add the op cases in a follow-up. Her own design asked for the conditional ones.
- **C2.** Astra accepts or reverses the new-file placement (`atlas-phase7.json`, F5a).
- **C3.** PAID in this commit: the three face findings are filed in `pm/roadmap/holdspeak/BACKLOG.md` "PHILO-7-03 follow-ups".

## MISSED (by the lane, small)

- F2 and F3 above. Neither is worth a round on its own; fold into whatever touches the file next.
- The face case `case.p7.decision_status.review_list` proves the brief's review row after a status change made by a face click in SETUP; its trigger is `POST /api/brief/generate`. The status write's own receipt (HTTP `decision.status`) is not read anywhere in the atlas (C1).

## UNKNOWN

- Why the fixed wrapper's bottom resolves about 27 px from the top (a containing block other than the viewport is the likely class; not verified).
- Whether the rig, polling at 0.5 s (`scripts/graph_walk.py:2399`), would catch the 1.2 s "Removal committed" phase once the receipt is on-screen. Likely, not run.
- The 393 list view's row-menu Delete (`web/src/desk/components/DeskListView.tsx:332`, `objectMenuEntries`) having no listener: read from code by the lane, not exercised by the lane or by me. UNVERIFIED.
