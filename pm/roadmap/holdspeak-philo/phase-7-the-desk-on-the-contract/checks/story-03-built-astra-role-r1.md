# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — CHECK on built, PR #663

- Branch `feat/philo-7-03-atlas` @ `ae1c99a8`, worktree `/Users/karol/dev/tools/wt-philo-7-03` (read only).
- Every run: isolated `HOME=$(mktemp -d)`, `PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright`, output under my scratchpad. No full suite.
- Tree before and after: only Astra's four untracked files under `docs/internal/philo/phase-7/atlas/`. Unchanged. `git merge-tree --write-tree main HEAD` is clean.

## VERDICT

**RATIFY-WITH-CONDITIONS.** Do not merge until K1-K3 are paid and CI shows no branch-new red.

The atlas work is sound. I reproduced the counts, a passing face case, the delete FAIL, three `.op` receipt reads, the equivalence run and a new red. But the PR has **three branch-new reds** that nobody has reported. Two of them are in the PR's own CI. Main does not have them. Each is a one-line or one-command fix.

## FINDINGS

1. **Branch-new red: the rig's closed-vocabulary fence.** Round one added `focus` to `UI_ACTIONS` (`scripts/graph_walk.py:3759-3763`). The older fence `tests/unit/test_graph_walk_calibration.py:272` still asserts the old seven-action set.
   Repro: `HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=… uv run pytest -q tests/unit/test_graph_walk_calibration.py` → `1 failed, 61 passed`, `Extra items in the left set: 'focus'`.
   PR CI job 108279064618 fails on it. Main's CI (job 108288634169 @ `3d3f1748`) does not. The lane's scoped set did not include this rig fence.
2. **Branch-new red that stays after merge: the evidence scratch guard.** `tests/unit/test_philo7_atlas.py:30` builds a `pm/roadmap` path (it READS the phase status) and uses `tmp_path` for a DB. The guard flags it as a writer.
   Repro: `git merge-tree --write-tree main HEAD` → archive → run the merged guard → `RED … tests/unit/test_philo7_atlas.py:30`.
   Main's #666 allow-listed only `test_philo5_his_words.py`. Merging #663 as it is turns main red again. Fix: one allow-list line ("reads the phase status; writes only to tmp_path"), the #666 pattern.
3. **Branch-new red: API reference drift after round two.**
   Repro: `uv run python scripts/philo_api_reference.py --check` at `ae1c99a8` → `API reference drift: docs/generated/api-reference.json`. Regenerating in memory adds `tests/unit/test_philo7_atlas.py` as a test candidate on about 12 more routes. Round two's new fences name decision routes.
   PR CI "Documentation Navigation" fails on it (job 108279064661, head `ae1c99a8`). The claim "every `scripts/philo_*.py --check` exits 0" (evidence, and Muad'Dib's reproduction 7) was true at `ca744702` and is false at `ae1c99a8`.
4. **Counts hold.** atlas 85 (7 `.op`) + phase3 36 (12 `.op`) + phase7 27 (18 `.op`) = 148. `git diff main...HEAD -- atlas.json atlas-phase3.json web holdspeak` is empty.
5. **Passing face case reproduced.** `graph_walk.py run --atlas …/atlas-phase7.json --case case.p7.zone_file.note_in_zone --brain astra --viewport 393 --engine none` → `VERDICT: pass`, `'Filed · Atlas zone' is readable … rect {x:33,y:403,w:98,h:18}`. `after.png` shows the note pullout with "Filed · Atlas zone" and the zone chip checked.
6. **The delete FAIL is the face, and the hub deleted.** Same command, `case.p7.decision_delete.gone` @393 → `VERDICT: fail`. `initial_feedback.hit_test.rect {x:9,y:-12,w:372,h:27}`, `in_viewport:false`, top samples `owned:false`. Hub: `GET /api/decisions/decision_08c8… 404 decision_not_found`, `GET /api/decisions 200 {'decisions': []}`. PR #665 (open, `fix/delete-receipt-offscreen`) touches `WorldStage.tsx`/`useUndoReceipt.ts`. It is not on main, so the case fails, as it should.
7. **Three `.op` receipt reads reproduced (headless, `/api/mcp`).**
   - `case.p7.decision_supersede.receipt.op` → pass, 9 facts. The read receipt has `target_ref decision:decision_d599…`, `result_ref decision:decision_8dfe…` (a different id, the captured `successor_id`), `actor_identity owner-session`, `principal_kind owner`, and the old decision reads `superseded_by` = the successor.
   - `case.p7.zone_file.refile_moves.op` → pass, 16 facts, `restarts: [restart_hub]`. Both filings' receipts are read, and `result_ref` names two different zones.
   - `case.p7.kb_member.refused_bad_ref.op` → pass, 8 facts. Receipt `state: refused`, actor owner-session, `mcp_refused` on the trigger.
8. **Equivalence reproduced.** `scripts/philo7_pairs.py <folder>` on both retained folders produces JSON identical to each retained `pairs.json`. Summary: "18/18 pair-widths equivalent, over 9 headless op runs (each shared by both widths) x 18 face runs; the refusal leg is not applicable on 6". The 6 are `zone_create`, `kb_create` and `decision_supersede` at both widths. The delete identity is a real check (`scripts/philo7_pairs.py:153-181`): 404 by the minted id, not listed, `not_found` naming the id, and the receipt's `operation_id` and `target_ref` matched.
9. **A new fact's red reproduced by me.** I mutated `case.p7.decision_supersede.receipt.op` `result_ref` to `decision:{decision_id}` in a scratch copy → `VERDICT: fail`, `fact #6 failed: … = 'decision:decision_6add…', wanted 'decision:decision_698e…'`. It is an assertion red, not a blocked one.
10. **Carriage refusals hide nothing the named cases need.** The rig blocks the non-canonical `ref` (`graph_walk.py`, kb member projection) and blocks `successor_id` on supersede (`_id_only`). grep: no atlas case uses `"ref"`, and `successor_id` appears only as a capture name. MCP `decision.supersede` carries `decision_id` only (`holdspeak/mcp/tools.py:430-434`). The successor is minted before admission (`holdspeak/services/desk_kernel.py:100-101`), so the `.op` fires the real admitted write. `OP_HTTP_ONLY` blocks HTTP-only ops by name (`graph_walk.py:920-922`). That is the reason `decision.status` over HTTP and `delegation.*` have no `.op`, which is lawful and stated.
11. **Scoped fences.** The five named files plus the guard: `1 failed, 153 passed` (the one failure is finding 2). `--collect-only tests/unit/test_philo7_atlas.py` → 26 tests: the evidence file's 22 plus round two's 4, disclosed in the round-two record. Story 02's `tests/unit/test_philo7_article_xi.py` → `73 passed in 53.24s`.

## CONDITIONS (all before merge)

- **K1.** Update `tests/unit/test_graph_walk_calibration.py:272` to the eight-action set with `focus`. Keep the blocked-typo loop.
- **K2.** Allow-list `tests/unit/test_philo7_atlas.py` in `tests/unit/test_evidence_scratch_guard.py` as a READER, the #666 way. Rebase on or merge main first so both entries are there.
- **K3.** Run `scripts/philo_api_reference.py` (write) and commit `docs/generated/api-reference.json` (and `docs/API_REFERENCE.md` if it changes). Then every `scripts/philo_*.py --check` must exit 0.
- **K4 (wording, not blocking).** Put the C1 ruling below into the round-two record or the story Notes, so the ticked box says what was proved.

Proof of K1-K3: a PR CI run with Unit Tests failures equal to main's inherited set (playwright-browser and phase143-census) and a green Documentation Navigation.

## RULINGS

**C1 — the narrower reading is LAWFUL for story 03.** Amend the box wording (K4). Do not add the conditional op cases before merge, and do not add a follow-up story for them.

Reasons:
- **Tenet 1.** Each of those writes already has a real-hub fence in story 02. `tests/unit/test_philo7_article_xi.py` covers HTTP `decision.status` (`:169`), `zone.delete` (`:249`), kb create/update with `member_ids` or over an id, zone move by `parent_id` and by create over an id, the Thought tombstone on both transports, and the grant/revoke in `test_philo7_grant_lifecycle.py`. `_one` asserts exactly one operation of that name with a receipt (`:87-91`). I ran it: 73 passed. An atlas `.op` for each would prove the same thing a second time through a slower harness. That is safety ceremony with no new fact.
- **Tenet 3.** The atlas exists to prove what the owner does on the Desk and its twin. None of these writes has a face trigger in the named list. `decision.status` over HTTP and `delegation.*` are HTTP-only, and the rig blocks them by name.
- My parked design asked for the conditional cases. I withdraw that line. It was PROPOSED and never ratified, and the tenets outrank it.
- One gap remains: the atlas does not read a receipt for the owner's real click path (HTTP `decision.status` from the review-list setup). Story 02 covers it. If anyone later touches that route, add one `api`-then-`kernel.receipt.read` op case. Until then it is not owed.

**C2 — ACCEPT the new file `atlas-phase7.json`.**

Reasons:
- It follows the ratified precedent `atlas-phase3.json` (`extends: atlas.json`).
- It makes "no existing case replaced" machine-provable: the diff on the two old files is empty.
- It keeps the phase's cases in one file to review and count.
- My design's "existing two files" was an unratified proposal. Its intent, keeping every existing ID, is met more strongly by a new file. The story's "counts over both named files" is met: both are reported unchanged and the third is added.

## MISSED (ranked by owner cost)

1. **The three branch-new reds (K1-K3).** The owner would get a red main after merge (the guard stays red on the merged tree). Neither Muad'Dib's counsel nor round two found them. The lane's scoped set left out the older rig fence and the evidence guard, and round two did not rerun the generators.
2. **No face refusal case.** The "refusals" leg of equivalence reads only the success-side status on the face. The four refusal cases are op-only. That is acceptable (the Desk shows no refusal for these writes today), but "refusals equivalent" means "neither side refused", not "both refuse the same way".
3. **Product-side reds are absent (F4 kept).** All 27 + 23 mutation reds change the expectation, not the product. No run shows that a real regression, for example a kernel that stops writing the supersede `result_ref`, turns a case red. That is low cost for an atlas that records today's Desk.
4. **Re-run owed after #665.** When the delete receipt repair merges, `case.p7.decision_delete.gone` at 1440 and 393 must be re-run and seen to pass. That belongs to the #665 lane or story 04, not here.

## TUESDAY

Yes, indirectly. It gives the owner a repeatable proof that "file a note, see it in its zone, put a decision on the review list" works on his Desk and leaves a receipt. It also found a real face defect (the delete receipt off-screen) that #665 is already fixing.

## UNKNOWN

- I did not run any case at 1440 or with `--engine real`. I read those retained runs through `pairs.py` only.
- I did not re-run the other 15 face runs or 15 `.op` cases. I trust the retained observations for those, and `pairs.py` reproduces from them byte-identically.
- I did not run the full suite or the Integration/E2E CI jobs (both still pending on the PR).
- I did not verify the cause of the receipt drawn at y=-12 (Muad'Dib's UNKNOWN stands; #665 addresses it).
- I did not exercise the 393 list-view row-menu Delete. Main's #667 diagnostic says it does nothing; I did not reproduce that.
