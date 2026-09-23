# PHILO-3-02 — lane record

LANE: **PHILO-3-02 (A2)**. Owner Astra; design checker and counsel on built Muad'Dib. Worktree `/Users/karol/dev/tools/wt-philo-3-02`; branch `feat/philo-3-02-summary`. [PR #616 — PHILO-3-02: see and find the summary](https://github.com/karolswdev/HoldSpeak/pull/616). No merge before Muad'Dib's counsel on built.

OUTCOME: **built — technical completion; usefulness partial**. The owner ratified the corrected Arrival canvas on 2026-09-23 (“Ratify, build it”). Install, queue notification, bounded detail reads and the existing-row summary/transcript/receipt face are implemented. One Run brings the actual LAN host and summary back to Arrival; failed/retrying jobs retain their cause; summary/receipt/meeting identity survive the rig's restart. The synthetic input loses facts through ASR and summary generation; this does not close the owner's sitting or the phase exit.

PROOF:

- [Technical completion and exact run/shot paths](../../../../docs/internal/philo/phase-3/summary/technical-completion.md); [all 60 retained observations](../../../../docs/internal/philo/phase-3/summary/observations-index.md). All 20 actual J4–J7 cases at both widths are accounted for: 30 pass, 10 lawfully blocked. No blocked/native case is called a pass.
- Final 1440/393 live summary observations: `assets/story-02-shots/rig/final/20260923T191042Z-case.j6.run_summary.summary_text-astra-1440/` and `20260923T191150Z-case.j6.run_summary.summary_text-astra-393/`. Summary appears after one Run at 6.691/6.223 seconds, with actual host `192.168.1.43`. Both final raw summary hit tests own all nine samples. Engine identity: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf, llama.cpp. The earlier longer phone-summary overlap remains retained.
- Restart runs `20260923T171417Z` and `20260923T171510Z` retain different before/after PIDs, one DB path, and exact summary, receipt and meeting identity at both widths.
- [D2 base-install red/green](../../../../docs/internal/philo/phase-3/summary/install-d2/report.md), first gate commit `794f07ff`; [queue producer fences](../../../../docs/internal/philo/phase-3/summary/queue/report.md), `a28c19f9`; [detail wire](../../../../docs/internal/philo/phase-3/summary/detail/report.md); [rendered transition red/green](../../../../docs/internal/philo/phase-3/summary/arrival/final-proof.md). Words and their fences ship together. The WAV was added explicitly with `git add -f`; the provider failure reply lives in the tree.
- Final full `npm run check`: **306 files / 2,806 tests**, typecheck/build/bundle gate green. Full serial Python: **11,530 passed, 15 failed, 11 errors, 116 skipped, 4 xfailed**. All six lane failures and eleven calibration errors corrected: **144** rig/atlas/calibration and **19** copy/census/summary-glass focused tests pass; **11** rendered Arrival tests pass. Nine failures reproduced on fresh main remain inherited debt. [Complete a/b/c classification and raw tails](../../../../docs/internal/philo/phase-3/summary/integration/full-suite-classification.md). No full Python green or flake is claimed.
- [Paired DW captures](evidence-story-02.md), including actual rig invocations, the red full run, green final web/focused checks and the retained-observation audit. Main A4 and A1 integrated through the gate as `aac7544e` and `0ad59c04`; remote main remains `7b2c2b2a`.
- Closure commit `523ca6a37f8d2e76d509d0277f27bbfe0a550265`: `dw gate` passes with 7/7 boxes and one story flip; `dw verify origin/main..HEAD` passes (three commits). The feature branch is pushed and PR #616 is open. GitHub's connector refused creation with integration HTTP 403; the configured GitHub CLI file token completed it from an isolated HOME, without keychain access. [Counsel-on-built brief](checks/summary-built-muaddib-brief.md) remains pending.

LEDGER: [Every planted decision/owner/action mapped against output, including omissions](../../../../docs/internal/philo/phase-3/summary/usefulness.md). Maya becomes Mayyachan; SQLite is corrupted or omitted; Leo's test/Tuesday survive; Priya's named failure fence and before-ship timing are lost or replaced. Two inherited phone defects, stale legacy fixtures/selectors and the expired continuity fixture are named in the classification. Five sealed miscited anchors and fourteen subtype conflicts remain PHILO-2-07 debt. Manual retry proves admission/RESERVED, not eventual recovery. The full-suite evidence rewrites were restored only by reviewed explicit tracked paths; all A2 observations survive.

AMENDMENTS: **none**. No new Arrival verb, no attempt limit, no council scope expansion. A2's acceptance is technical completion plus an honest usefulness report; the owner's sitting remains a phase-exit requirement. The user explicitly ordered the closure/PR, followed by Muad'Dib's counsel on built.

UNKNOWN: **Muad'Dib's counsel on built and the owner's sitting are pending**. Native microphone recording was not exercised. Real LAN outage recovery was not exercised; failure/retry proof uses the retained provider-boundary reply. Complete planted-fact recovery is disproved by the retained output. The read-error correction has a rendered pre-fix failing fence; it is not presented as a separately walked native failure.

# Earlier checkpoint — retained history

LANE: PHILO-3-02. Owner Astra; checker Muad'Dib. Worktree `/Users/karol/dev/tools/wt-philo-3-02`. Branch `feat/philo-3-02-summary`, starting at `7ce95358`. No PR yet. Product commits, through the gate with zero story closures: `794f07ff` (install, first), `a28c19f9` (queue, second).

OUTCOME: in progress. The authorized install and queue seams are built and committed. The owner RATIFIED the corrected canvas on 2026-09-23 ("Ratify, build it"), published by Muad'Dib at https://claude.ai/artifact/KnASxYRZc4UXkAiFU1z5zX. **Arrival implementation and actual-atlas proof are authorized and under way.** [Design](summary-design.md), [recorded RATIFY-WITH-CONDITIONS](checks/summary-design-muaddib.md), [boards and the one owner question](assets/story-02-canvas/README.md). Astra owns this lane; Muad'Dib ratified these backend seams and required the owner decision before the face. No acceptance box is checked.

PROOF:

- **Install / D2:** the original documented base install produced `OpenAI=None` (assertion exit 1). Astra repeated the corrected install from fresh source, HOME and venv, with the ordinary web build enabled and no meeting/test/dev extra: `openai==3.19.0`, production client assertion exit 0, local model/speaker packages absent. The same produced-metadata fence fails against the old built package. Astra independently collected and passed **17** focused tests. [Report and complete raw output](../../../../docs/internal/philo/phase-3/summary/install-d2/report.md).
- **Queue:** Astra observed **4 pre-fix failures** on real service-admitted jobs, then independently collected and passed **77 tests** after the fix. Success, scheduled retry, terminal failure and real stale-assignment refusal announce the durable state through the existing composition seam, after the final receipt writes. [Report, collection and run](../../../../docs/internal/philo/phase-3/summary/queue/report.md).
- **Canvas:** eight boards at 1440×900 and 393×852, plus four phone footer views. Astra inspected all twelve PNGs and reran the retained capture: **8 boards / 12 shots pass**. Current bundled fonts loaded. The full title is readable; attempt/cause facts are below the row; no new Arrival Retry verb or attempt limit; planned host is beside Run, actual host is represented after it. Two phone row verbs and twelve footer targets pass nine-point hit ownership, with 44 px height and dock clearance. These are **static canvas observations, not product evidence**. [Manifest](assets/story-02-canvas/canvas.json), [validation](assets/story-02-canvas/validation.json), [Astra raw run](../../../../docs/internal/philo/phase-3/summary/canvas-astra-validation-raw.txt).
- **Fixtures:** one [synthetic source](../../../../tests/fixtures/philo3_architect_meeting.txt), [generated WAV](../../../../tests/fixtures/philo3_architect_meeting.wav) and [manifest](../../../../tests/fixtures/philo3_architect_meeting.json). Astra verified both hashes and the 16 kHz mono 16-bit PCM format, 34.67525 seconds. The WAV is staged explicitly with `git add -f`. The [failure reply](../../../../tests/fixtures/philo3_summary_failure_reply.json) is in the tree; the real rig `_ReplayIntel` and real `BoundMeetingAdapter` produce `provider_error_result` from it. [Fixture verification](../../../../docs/internal/philo/phase-3/summary/fixture-verification.txt), [exact future `reply` boundary contract](../../../../docs/internal/philo/phase-3/summary/failure-reply.md).
- **Existing baseline:** 38 backend and 12 frontend checks passed before implementation. The prior DW capture remains parked as [summary-baseline-capture.md](summary-baseline-capture.md), without an unfinished `evidence-story-02.md`. After repairing the local npm directory, the same 12 frontend checks pass again. [Baseline logs](../../../../docs/internal/philo/phase-3/summary/baseline/).
- **Technical completion:** package availability and the queue notification seam verified. Completed import, rendered Arrival transition, LAN execution and restart chain remain unverified.
- **Owner usefulness:** unverified. The canvas summary is an illustration based on the planted source, not model output. No planted-item recovery or owner's sitting is claimed.

LEDGER:

No existing test was weakened or updated to accept the queue change. Focused runs have no a/b/c fallout; no full-suite green or flake classification is claimed.

| Finding | Classification | Home / disposition |
| --- | --- | --- |
| Base install lacks endpoint model client | Existing install defect | Fixed by `794f07ff`; D2 raw evidence retained |
| Deferred queue omits desk notifications | Existing product defect | Fixed by `a28c19f9`; four real-producer red/green fences |
| Arrival omits persisted detail and truthful retry/cause | Existing product defect | PHILO-3-02 face continuation after owner ratification |
| Atlas import wait, duplicate Run, absent failure reply, weak restart evidence | Existing tooling debt | Failure artifact prepared; actual recipes and cases remain PHILO-3-02 continuation |
| Draft title, footer, token and verb defects | Canvas defects against Tenets 3–7 | Corrected boards supersede the parked drafts below; owner ratified on 2026-09-23 |
| Node 25 fails to load `libllhttp.9.3.dylib` | Existing environment defect | Use nvm Node 22; no machine-level repair |
| Worktree `npm ci` failed with `ENOTEMPTY` | Local dependency-directory problem, not classified as a flake | Complete failure retained; partial `web/node_modules` parked under `.tmp/philo3-node_modules-partial-20260923`; fresh npm ci succeeds, 12 frontend checks pass |
| First worker install omitted venv activation | Worker workflow error | Worktree development metadata was refreshed; excluded from D2 proof. Independent source/HOME/venv reproduction supplies decisive proof |
| Isolated counsel CLI lacked credentials | Resolved workflow error, not a verdict | Muad'Dib supplied the check from his own session; do not repeat that isolated-HOME CLI invocation |

AMENDMENTS: none. D1–D4, all A2 acceptance criteria, and the council's deferred list are unchanged. No story is done; no product face was built without the owner decision.

UNKNOWN: real LAN completion and engine identity at execution, completed import on the row, automatic rendered summary and actual-host arrival, truthful rendered retry/failure, actual J5 hit ownership at 393, restart equality, recovered planted facts, full-suite outcome, counsel on built and the owner's sitting.

## Earlier handoff to Muad'Dib — superseded by owner ratification

Publish [the corrected canvas README](assets/story-02-canvas/README.md) and its four paired state boards. It names one question: whether this corrected existing-row presentation is the face to build. The owner ratifies; Astra does not substitute counsel for that decision.

After ratification: implement the bounded visible-three detail reads and face; fence the rendered state transitions and keep receipts in every branch. Repair and run the actual J4/J5/J6/J7 cases serially through the rig and `dw evidence capture`, using the retained synthetic WAV and actual LAN engine. Use one Run, import-completion wait, the tree failure reply, and the rig restart step. Report technical completion and each planted decision/owner/action separately. Then run the full suites in a quiet tree, record Muad'Dib's counsel on built, flip PHILO-3-02 with its evidence, commit, push and create `PHILO-3-02: see and find the summary`.

The [worker briefs](summary-worker-briefs.md) carry the remaining seams. The proposed restart read of `/api/intel/summary` was rejected because it returns queue counts; compare `/api/meetings/{meeting_id}` summary and receipt. No new transcription-replay adapter is authorized. Do not treat the static boards or a sample atlas calibration as closure evidence.

## Parked first-draft canvas findings — Astra, 2026-09-23

These historical findings explain the correction. `assets/mockups/` stays parked and unratified; `assets/story-02-canvas/` is the current owner-review set.


The first draft had 10/11 px text, fictitious 4-minute/132-word counters and invented speaker labels; the worker corrected those to at least 12 px, the fixture values and generic full source text. Every board says DRAFT / UNCHECKED.

The corrected draft still needs a design correction before ratification/build:

1. The 1440 retry row reduces the meeting title to `Ar...` because of its repeated retry/attempt tokens. Keep the title readable; put attempt/cause facts in the existing below-row well. Tenets 3 and 7. Shot: `assets/mockups/summary-retrying.dc.png`.
2. The ready/retry/failed 393 boards place lower desk verbs behind the dock. The main meeting control is visible, but this is not full face compliance or live hit-ownership proof. Preserve the existing real shell/scroll behavior when correcting the canvas. Tenets 5 and 6. Shots: `summary-ready-phone.dc.png`, `summary-retrying-phone.dc.png`, `summary-failed-phone.dc.png`.
3. Faint text still uses the old `#767e8d`, while current `web/src/styles/tokens.css:93` is `#8b93a3`. Failure wells contain invented explanatory prose (for example, “The cause stays with this meeting.”); keep a concise, real cause and state facts. The exact audio duration should use the product's readable duration format rather than five decimal places. Tenets 4 and 5; UX-CANON A.3/C.
4. Retry/failed artboards add an Arrival Retry verb and invented `2/3` attempt limits. No new Arrival recovery verb or limit has been settled. Preserve the existing action path until the checked design explicitly settles it. These draft values are not queue evidence.

No worker validation transcript for the canvas is retained, so only Astra's visual/source findings above are verified here. The retained capture script creates screenshots; it is not an interaction/canon test. Real producer state, receipt correctness, pointer ownership, font contrast and built face behavior remain unverified.
