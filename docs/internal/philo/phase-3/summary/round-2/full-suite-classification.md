# Round-two full-suite classification

The final quiet serial run on the integrated A2+A3 source completed with **12 failed, 11,559 passed, 116 skipped, 4 xfailed in 5678.77 s (exit 1)**. [Complete raw output](integration/full-python.raw.log), [DW capture receipt](integration/full-python.capture.txt). It ran `uv run --no-sync pytest -q --ignore=tests/e2e/test_metal.py` with an isolated HOME and Node 22; all workers held, one test/hub sequence, no parallel live walk and no product edits. No full Python green is claimed.

The final failure IDs and causes were compared with the prior independent archived-main reproduction at `7b2c2b2a`, [raw baseline](../integration/main-baseline-fallout.raw.log), and [original detailed classification](../integration/full-suite-classification.md). **The same nine inherited test IDs and causes recur, plus three lane expectation/probe failures described below. [Exact ID comparison](integration/failure-comparison.json)**. No failure is labelled (c), and no green-twice flake claim is made.

| Failure | a/b/c | Retained cause / follow-up home |
| --- | --- | --- |
| HS-170 `TestMeetingsGlass::test_meetings_face` | a, inherited | Fixture supplies actuator proposals while the facet needs action items. HS-170 fixture owner; keep producer setup truthful. |
| HS-200 attention `test_long_row_393` | a, inherited | Test scrolls window while Chair owns scrolling. Existing attention glass fixture; drive the actual container. |
| HS-200 preparation `test_running_then_kept_brief_with_claims_and_not_read[393]` | b, inherited | NOT INCLUDED does not expose its expected panel. Existing preparation/Disclosure follow-up. |
| HS-200 task resume `test_saved_ask_draws_the_ratified_unfinished_row[393]` | b, inherited | Composer covers the unfinished row's verb. Existing ProjectRoomCore/composer geometry follow-up. |
| HS-201 Thought `test_thought_note_is_one_clean_note[1440]` and `[393]` | a, inherited | Broad receipt selector matches both KEPT and filing lines after A4. Thought glass fixture owner; preserve checks of both receipts. |
| HS-201 Thought `test_thought_note_long_context_and_open_well_never_clip[1440]` and `[393]` | a, inherited | Same selector ambiguity before geometry. Same fixture follow-up. |
| Continuity `test_the_last_known_observation_survives_a_restart` | a, inherited | Hard-coded September 7 observation is outside the intentional 14-day retention horizon. Fixture clock follow-up; do not change product TTL. |

The six initial lane failures and eleven calibration errors from the first closure do not recur here. Round-two producer/recipe and A3 Python tests pass in the full run; rendered cause/refresh/fold fences pass in the full web check. Focused final run: **164 passed** ([collection](integration/focused.collect.raw.log), [raw](integration/focused.raw.log)). Scoped merged rig: **6 producer-clock tests + 62 calibration tests pass**, with actual collection/run output under `integration/rig-merge*`.

Final `npm --prefix web run check`: **307 files / 2,813 tests pass**, typecheck/build/token/architecture/bundle gates pass; [complete raw output](integration/full-web.raw.log). Desk JS 1,321,794 B; CSS 319,279 B; zero maps. The final build is the one used by the six integrated walks, index SHA `1cd6b691cb0828d1c31bd5bfa97507272c5d47ce884d633a646423a34911fcac`.

## Round-two fallout

Three additional failures were found in the final full run: the two legacy `test_phase200_intel_drain.py` retry/ceiling tests still required the removed `after 2 attempt(s)` wrapper in the displayed error field, and the older `test_the_summary_is_asked_for_disclosed_and_found_again` glass probe counted two Arrival transcript-fold buttons behind the Meetings window as overlaps (full log 1373–1420). The final trace and focused correction are recorded below; these are not labelled inherited.

All three are **(a), old test posture introduced into conflict by the lane's intentional words/fold change**. The glass probe now scopes facts, refusals, footer and verbs to the owning Meetings window; it checks bounding-rect intersection inside that window only. It does NOT test z-order or the topmost element at a point, so a verb from another layer (the aftercare panel, the dock, the Capture Bar) covering a Meetings refusal is no longer seen by this probe; that lost cross-layer coverage is ledgered in `deferred-ledger.md` (Muad'Dib, second counsel). It does not ignore a control by label. The queue fences read the real producer's rows and service projection, assert literal `PROVIDER FAILED`, and retain attempt ladder, backoff, terminal status, retry-history and no-survivor guarantees.

Fresh focused red: **two queue failures in 5.56 s** ([raw](integration/fallout-red-unit.raw.log)) and **one glass failure in 12.63 s** ([raw](integration/fallout-red-e2e.raw.log)). Worker collection: **22 tests** ([raw](integration/fallout-collect.raw.log)). The first scoped green is two queue tests and one glass case; Astra independently ran both complete scoped files after the final assertion-strengthening: **22 passed in 43.18 s (DW `2026-09-23T23:59:47Z`)**. [Independent capture/raw](integration/fallout-astra.raw.log). No product source changed after the full run or final web build. No second full Python green is claimed.

## Retained workflow errors and interruption

The first round-two serial run was deliberately interrupted after **106 passed, 69 skipped in 1247.51 s**, exit 2, because main advanced with A3 and PR #616 conflicted. [Raw partial output](full-python.pre-main-interrupted.raw.log) and [capture receipt](full-python.pre-main-interrupted.capture.txt) remain; they are not counted as a full result.

The first post-merge census used system Python without the project import; the corrected `uv run --no-sync python` census has zero new/removed/changed/stale/unread entries, plus the inherited five miscited anchors and fourteen subtype conflicts. The first worker calibration attempt lacked the browser-cache path under isolated HOME; the retained rerun has 62 passes. These are invocation errors, not product regressions or flakes. The first merged focused/web captures accurately show index `unknown` while the resolved conflicts awaited staging; final walks and the full run followed explicit conflict-path staging.

## Evidence preservation

The interrupted run rewrote 235 reviewed tracked evidence paths. They were restored only from successful explicit `git show HEAD:path` reads after backing up the test bytes; all pre-existing untracked bytes were checked unchanged. Three unrelated new shots were parked by explicit path. [Tracked receipt](partial-restored-tracked-evidence.json), [parked receipt](partial-parked-test-shots.json).

The completed run rewrote **503 explicit tracked evidence paths** (497 PNGs, five JSON files and one census Markdown record). Astra backed up the test bytes, read every committed path successfully before writing, and restored only reviewed ` M` paths. All **48 pre-existing untracked proof files** stayed byte-identical. Nine new unrelated shots were parked by explicit path. [Tracked receipt](integration/restored-tracked-evidence.json), [untracked proof hashes](integration/preserved-untracked-proof.json), [parked shots](integration/parked-unrelated-shots.json). The pre-full manifest has **130 unchanged files** and only the intentional paired-evidence append; the final web index hash is unchanged ([integrity record](integration/full-run-integrity.json)). Follow-up test-shot preservation is recorded separately below.

The focused follow-up rewrote **20 explicit tracked legacy PNG paths**. All twenty new shots are retained in [fallout-shots](integration/fallout-shots/) before restoration; **65 existing untracked files** stayed unchanged. [Path/hash receipt](integration/fallout-restored-tracked-evidence.json). Astra inspected both refusal and post-restart shots at 1440 and 393; the foreground Meetings controls are clear, and the Arrival folds sit behind the window. This controlled-provider restart fence is distinct from the retained real-LAN J7 atlas observations.

[Aftercare obstruction and ASR instability](deferred-ledger.md) remain separate inherited **b** owner costs, ledgered under the user's no-fix instruction. [Usefulness](usefulness.md) remains partial even though the technical round-two corrections pass.

## Post-push documentation check

CI on PR #616 at `4f5fd691` failed its generated boundary-census check ([job](https://github.com/karolswdev/HoldSpeak/actions/runs/35936854087/job/107435694324), [retained failure excerpt](integration/docnav-ci.failure.log)). The same check fails locally ([red](integration/docnav-boundary-reproduce.raw.log)). Regeneration corrects **eight source line numbers**: one in `web/src/desk/api.ts`, six in `ChairHome.tsx`, one in `web/src/lib/primitives.ts`. All **897 candidates**, excerpts, kinds, hashes and the snapshot identity remain unchanged. This is **(a), stale generated metadata**, corrected in this lane, not inherited debt or a product change.

The earlier full suite did not run this artifact-comparison CLI; its boundary unit test checks lexical patterns. The relevant existing unit test passes, and Astra now ran the **complete twelve-command Documentation Navigation CI sequence**, including nine navigation unittests, through DW capture **`2026-09-24T00:11:13Z`**, exit 0. [Complete raw output](integration/docnav-astra.raw.log), [capture receipt](integration/docnav-astra.capture.txt). No product or test source changed after the integrated build or the 22-test follow-up. Remote CI's next result remains separate from this local reproduction.

