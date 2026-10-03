# PR #757 — Astra single-pass check

DRAFT — UNCHECKED, awaiting Muad'Dib's confirmation of the atlas correction and closing recommendation.
Astra session: `01a10318-6b05-7153-8ed7-d820c6df362f`; 2026-10-03.
Reviewed product head: `210b9f33240d9a5d7281cf1e5744daa8c18c39e5`.
Worktree: `/Users/karol/dev/tools/wt-philo-13-pr757-astra`.
The caller pre-authorized mechanical corrections and requested one check plus one confirmation.

VERDICT: RATIFY-WITH-CONDITIONS — the scoped fixes are verified; story 01 closes only after the B2/main evidence below.

FINDINGS:

1. Zone's original actual case fails at both widths on the PR head: 1440 reaches the named window at 32.019 s and records the late result at 33.753 s against 20 s; 393 has the correct accessible name and nine owned hit points but no title in its window text. The preserved runs are in [1440](../assets/pr757-astra/zone-before-1440/) and [393](../assets/pr757-astra/zone-before-393/). Correction: 40 s lifecycle bound; exact `aria-label` AND readable `Drop items here`; desktop title remains visible after reopen. This repairs the case without waiving Tenets 3 and 6.
2. A bare attribute predicate would accept an occluded window. `scripts/graph_walk.py:1983` only checks identity; `:1838` also checks visibility, viewport and hit ownership. The corrected conjunction retains those guards and the real producer, close, reload and reopen path.
3. The supplied 14/18 table is predicate coverage, not 14 healthy product outcomes. Roadmap still says `Roadmap not found` (B0-F4; Tenet 3); Calendar still exposes `no_vision_model_assigned` (B0-F6; Tenet 4). Delivery Dossier and Terminal remain covered at 393 (B0-F2; Tenets 3 and 6). [Preserved supplied observations](../assets/pr757-astra/supplied-table/) retain their original provenance: dirty `ecb4e0f1`, not this PR head.

CONDITIONS: Story 01 remains in-progress. Before closing, the integrated B2-head rerun must cover all nine cases at both widths and show B0-F2 green; B2's merge record must cite B0's merged commit, its runs and the closing evidence. Main-run evidence, canonical `evidence-story-01.md` and the paired status flip still have to ship. Outside-B2 defects may remain only with named open homes under the signed C5 ruling.

MISSED: The table can conceal product failures behind predicate passes. B0-F4's former C4 home is already done; draft BACKLOG B0-L4 keeps the remaining wrong-identity defect open. Calendar stays in B0-L1. A merge event alone is not the B2 gate.

TUESDAY: The corrected Zone case proves the ordinary open, close and return path; Roadmap's useful content and the two phone Delivery returns are not yet demonstrated usable by this check.

UNKNOWN: Final integrated #747 behavior and owner observation on the real desk were not exercised. Runs use isolated HOMEs and real local hubs, with no microphone or owner's DB.

## Lane record

LANE: PHILO-13-01 / PR757 atlas correction; branch `fix/philo-13-pr757-astra`, delivered to PR #757.
OUTCOME: built — both pre-authorized atlas corrections and their fences; no story flip and no merge.
PROOF: Focused collection contains 177 cases; Python selection passes 172; Dock and first-use glass pass 5; focused Vitest files pass 8; full web suite passes 3,217 with zero branch-new. Final actual Zone cases pass at 1440 (30.803 s) and 393 native touch (17.139 s), with all nine hit points owned at both widths. See the exact receipts below.
LEDGER: (a) Zone title predicate and lifecycle bound are stale harness assumptions, corrected together with their fences. (b) No branch-new face defect identified in the scoped check; B0-F2 remains B2's gate, F4 is retained in draft B0-L4, F6 remains B0-L1. The full Python run is red (59 failures, 4 errors); all 63 nodes have named follow-up homes in the [failure ledger](../assets/pr757-astra/failure-ledger.md). Fifteen unmatched failures reproduce on the exact main parent; 37 names recur from the older C3 ledger without a fresh cause comparison. No flake classification claimed.
AMENDMENTS: Zone completion 20 → 40 s, with 6.247 s margin over the observed 33.753 s lifecycle; accessible identity plus readable content replaces title text at the shared window scope. Owner may overrule at the sitting.
UNKNOWN: Full Python has 59 failures and 4 errors; attribution limits and named follow-ups are in the failure ledger. Integrated B2-head proof and owner observation remain unverified here.

## Scoped source check

`web/src/desk/floorMenu.ts:81` uses the real canonical `qualifiedRef` (`api.ts:128` maps directory to zone). `components/dock.css:643` removes the sticky More gadget from snap targeting. `RepoWindow.tsx:188` and `RoadmapWindow.tsx:83` compose the existing `desk-pullout` class that supplies fixed positioning. `tests/e2e/test_hs202_first_use_smoke.py:329` and `:421` select the menu element after C5 made its compact accessible name depend on the open group. `holdspeak/db/meetings.py:1282` is the actual `delete_meeting` definition named by the repaired source anchor. No new product defect was found in this bounded review. The eight Vitest tests and all five glass tests pass; source checks alone are not the glass proof.

Two Luna workers were requested at `gpt-5.6-luna` / `xhigh`: one reviewed the atlas contract and one reviewed the face diff and ran the focused Vitest selection. Astra made the diagnosed harness edit and verified the actual observations and images. Neither worker changed product code, staged or committed.

## Verification receipts

| Proof | Result | Receipt |
|---|---|---|
| Collected scoped Python and glass cases | 177 | [collection](../assets/pr757-astra/focused-collect.txt) |
| Updated case fence against original atlas | 1 failed, 31 passed; original predicate rejected | [red fence](../assets/pr757-astra/atlas-fence-red.txt) |
| Five-file Python selection, including three shared fences | 172 passed | [Python](../assets/pr757-astra/focused-python-green.txt) |
| Dock More/swipe/into-view touch plus first use at both widths | 5 passed | [glass](../assets/pr757-astra/focused-glass.txt) |
| Two new scoped Vitest files | 8 passed | [names and output](../assets/pr757-astra/focused-vitest.txt) |
| Full web baseline | 3,217 passed; zero branch-new | [web](../assets/pr757-astra/web-baseline.txt) |
| Full Python suite, Metal excluded | 13,926 passed; 59 failed; 117 skipped; 4 xfailed; 4 errors | [output](../assets/pr757-astra/full-python.txt), [failure ledger](../assets/pr757-astra/failure-ledger.md) |
| Main-parent focused failure comparison | 12 same-cause failures, 2 passed | [output](../assets/pr757-astra/baseline-unit-run.txt) |
| Main-parent Dock/gadget comparison | 3 same-cause failures, 2 editor-rail passes | [collection](../assets/pr757-astra/baseline-glass-collect.txt), [failure excerpts and tail](../assets/pr757-astra/baseline-glass-run-tail.txt) |
| Atlas hash, isolated DB, revision and hit ownership | final runs match current atlas | [provenance](../assets/pr757-astra/case-provenance.txt) |

| Actual Zone case | Verdict | Observation | Shot |
|---|---|---|---|
| Original, 1440 | fail: 20 s bound exceeded | [observation](../assets/pr757-astra/zone-before-1440/20261003T185031Z-case.p13.directory.zone-astra-1440/observation.json) | [after](../assets/pr757-astra/zone-before-1440/20261003T185031Z-case.p13.directory.zone-astra-1440/after.png) |
| Original, 393 touch | fail: title absent from window text | [observation](../assets/pr757-astra/zone-before-393/20261003T185142Z-case.p13.directory.zone-astra-393/observation.json) | [after](../assets/pr757-astra/zone-before-393/20261003T185142Z-case.p13.directory.zone-astra-393/after.png) |
| Corrected, 1440 | pass, 30.803 s | [observation](../assets/pr757-astra/zone-final-1440/20261003T185855Z-case.p13.directory.zone-astra-1440/observation.json) | [after](../assets/pr757-astra/zone-final-1440/20261003T185855Z-case.p13.directory.zone-astra-1440/after.png) |
| Corrected, 393 touch | pass, 17.139 s | [observation](../assets/pr757-astra/zone-final-393/20261003T190052Z-case.p13.directory.zone-astra-393/observation.json) | [after](../assets/pr757-astra/zone-final-393/20261003T190052Z-case.p13.directory.zone-astra-393/after.png) |

The before/after PNGs were read by Astra. Original runs report clean `210b9f332`; corrected runs report the same product revision plus dirty atlas/tests/records. The atlas SHA256 in both final observations is `c563c8828e89406c880c3a9fd172491ffb8c678589cc00b20a34c249924195e4`. Product files and the rig are unchanged from the reviewed head. The independent check does not promote the supplied dirty `ecb4e0f1` table into exact-head proof, nor claim a new 18/18 run.

Commands used an installed Node 22 (`PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH`) because the default Homebrew Node failed to load libllhttp. `uv sync --extra dev --extra test` built this worktree's frontend. Every pytest invocation had a fresh HOME; browser tests used `PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright`. The full Python run also used `npm_config_cache=/Users/karol/.npm`. The excluded metal test was never run.

```text
uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/e2e/test_philo13_01_dock_tap_glass.py tests/e2e/test_hs202_first_use_smoke.py
uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py
uv run --extra dev pytest -q tests/e2e/test_philo13_01_dock_tap_glass.py tests/e2e/test_hs202_first_use_smoke.py
uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 1440 --engine none --out .tmp/pr757/zone-final-1440
uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 393 --engine none --out .tmp/pr757/zone-final-393
uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py
uv run python scripts/check_web_baseline.py --run
```

## Full-suite limits

The full suite is not green. No scoped case failed in the full run. The [failure ledger](../assets/pr757-astra/failure-ledger.md) names all 63 failing/error nodes and their follow-up homes. Twelve failures reproduce with the same causes on main parent `2e4b446c4`; the prior C3 ledger accounts for 37 recurring names, with no new claim that each current cause was compared. Two cancellation tests pass on the main parent once; this is not flake proof. The focused main-parent glass run reproduces both Dock species failures and the G2 resize failure with the same assertions (3 failed, 2 editor-rail cases passed). Eleven nodes remain unclassified, including the two cancellation tests and nine glass errors/failures. These are disclosed maintenance outcomes, not silently accepted green results. #747 was still open at head `dca2c128e063e6bdfa6c4b57b9d0e238c3b28d2a` at the final metadata check; its integrated behavior was not run.
