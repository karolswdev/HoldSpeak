# PHILO-3-02 — implementation briefs

**2026-09-23 ratified continuation:** The owner said "Ratify, build it" on the corrected canvas, published at https://claude.ai/artifact/KnASxYRZc4UXkAiFU1z5zX. Fresh Luna workers own disjoint Arrival, detail projection, and actual-atlas repair paths; Astra owns serial rig execution, full suites and delivery. The shared recovery job projection rides the existing detail response to keep the Chair within three HTTP reads per refresh. No acceptance criterion changes.

**Earlier 2026-09-23 checkpoint:** [Muad'Dib's recorded check](checks/summary-design-muaddib.md) authorizes the install correction first, then queue notifications. Corrected canvas boards go to the owner through Muad'Dib. Arrival implementation waits for the owner's ratification. The later recovery projection and atlas briefs below remain held for that continuation. [Design](summary-design.md), [story](story-02-see-and-find-the-summary.md), [lane record](summary-lane-record.md).

**Checkpoint:** install `794f07ff` and queue `a28c19f9` are committed and verified with the focused proofs in the lane record. Do not repeat those implementation tasks. The corrected canvas, synthetic WAV and failure reply are retained; the remaining briefs describe work after the owner ratifies the face.

All workers: `gpt-5.6-luna`, `xhigh`, `fork_turns=none`. Worktree `/Users/karol/dev/tools/wt-philo-3-02`, branch `feat/philo-3-02-summary`. Read TWO-BRAINS first, then AGENTS, CLAUDE, the story, authority and checked design. Anchors below are from `7ce95358`; verify each before editing. Workers implement the checked design and do not widen it. The council's deferred list and sibling stories are do-not-touch.

Use an isolated HOME for every test/product run. Never the owner's desk, keychain, microphone or native keyboard. No full suite or `tests/e2e/test_metal.py`; only the scoped tests below. Main owns hubs and closure walks unless explicitly handed the single-hub lane. No git verbs that move/clean trees, no restores, staging, evidence capture, status flips, contracts or commits. **HOLD FOR SHIP**. Astra owns delivery.

Before changing a seam, collect and run its new fence against the pre-fix product; retain the actual failure. Test the real producer and wire fields, not a double that invents the state being checked. Change words and their fences together. Fence rendered transitions and retain receipts across every branch. A sample calibration does not replace actual atlas cases. Reports carry exact changed paths, test collection, before/after run tails and limits.

## D2 first, serialized

Own `pyproject.toml`, `uv.lock` and only the install-guide lines necessary for the checked installation choice. Existing reproduction and probes live in `docs/internal/philo/phase-3/summary/install-d2/`. The base-install client probe already fails. After the checked change, repeat the same documented install in a new separate venv and retain package identity plus the same executable assertion. Do not use the development/test extras to prove the public install. Astra commits this correction before other product changes.

## Queue and recovery

Own `holdspeak/intel_queue.py`, `holdspeak/services/meeting_intel_service.py`, any narrowly necessary post-commit notification in `holdspeak/db/intel.py`, and new `tests/unit/test_philo3_summary_queue.py`. All frontend files, atlas/harness, fixtures, package/docs install files and roadmap files are do-not-touch.

The existing composition notification is `holdspeak/runtime/composition.py::notify_desk_changed` (~343); import completion already uses it (`meeting_service.py` ~282–289). Deferred processing is `_process_bound_intel_job` (~384–666). Announce running and committed retry/terminal/success changes; final notification must follow the receipt needed by Arrival. The real claim refusal path must announce a durable changed row too. Do not create a second event protocol or new polling conductor.

**Later continuation, not this queue commit:** extend the existing recovery job projection (~207–223) with real current-leaf error/retry facts already read by `list_jobs` (~69–74). A retry remains a retry when its scheduled time is due; no parsing of prose to infer it. Preserve truthful failure cause within the existing provider-content boundary. Do not leak raw provider content through generic receipts.

Focused checks: new queue fence, `tests/unit/test_phase200_intel_drain.py`, `tests/unit/test_intel_queue.py`, `tests/unit/test_meeting_deferred_admission.py` relevant admission/settlement cases. Mint admitted jobs through real production queue/service code, substitute only the provider boundary, and inspect the persisted state/receipt at notification time. Explicit success, retry, terminal failure and claim refusal cases.

## Arrival

Own `web/src/desk/chair/ChairHome.tsx`, a small adjacent detail-read hook if needed, `web/src/desk/api.ts`, `web/src/lib/primitives.ts`, and focused tests adjacent to the Arrival tests. Existing summary/transcript components may be composed; do not redesign or change their global grammar without returning to Astra. Backend, atlas/harness, package files, canvas and roadmap are do-not-touch.

Anchors: meeting rows ~1935–2042; headline ~628; Run ~736–775; wire adapter ~435–459. Use the existing three visible meeting IDs, existing detail and recovery routes, and the desk refresh signal. Ignore stale detail responses. Keep the length, transcript, summary, cause and actual receipt in their owning row. Keep planned host beside Run. Reuse SurfaceLedgerRow children, MeetingSummarySlab and TranscriptWell; all verbs are library Buttons. Read-error state must not masquerade as empty content. Follow the checked 1440/393 boards.

Focused checks: new `web/src/desk/chair/arrivalSummaryCompletion.test.tsx`; `arrivalSummaryRun.test.tsx`; `__tests__/drainerBadge.test.tsx`; `web/src/desk/__tests__/deskChangedRefresh.test.tsx`; adapter coverage if changed. The completion fence must use production wire shape and drive the bus/store refresh through rendered Arrival; assert imported text/length, actual host and summary, retry/failed cause/headline, branch transitions, and stale-read handling. Pin the existing Node 22 binary in PATH; the environment's Homebrew Node is broken. No build/shot may be called a real hub observation.

## Actual atlas and rig

Own `scripts/graph_walk.py`, the relevant `case.j4.*`–`case.j7.*` entries of `docs/internal/philo/graph/atlas.json`, any required schema additions, synthetic fixture/provenance/reply files, and narrow harness/atlas tests. Product files, other atlas case families, sealed pass JSON/Markdown, sibling stories and roadmap are do-not-touch.

Use the prepared 34.67525-second synthetic WAV and its source/manifest. Prefer the real existing transcription path; a new transcription replay adapter is not authorized by this brief. Recording/microphone atlas cases remain explicitly outside lawful rig reach. J4 import completion, J5 disclosure, J6 states/results and J7 persistence are the closure cases.

Repair the async wait, duplicate Run, missing reply, covered phone control and weak restart predicates. Prefer a bounded polling option on the existing check/API vocabulary to a new step kind when it expresses the job. Do not misuse the heartbeat scheduler clock for import completion. Keep one Run admission per completion chain. Summary and actual-host predicates scope the Arrival row. The restart comparison reads `/api/meetings/{meeting_id}`'s `intel.summary` and receipt; `/api/intel/summary` is queue counts and cannot prove summary equality. Preserve restart pid/home/db evidence and selected before/after content in the observation.

The real LAN engine is `http://192.168.1.43:8080` (Qwen3.6-35B expected; record observed identity). A failure reply is a named, retained provider-boundary substitution and must be labelled as such, never a planted finished DB row. Completion/usefulness use the real summary. The expected fact matrix is in the synthetic source; report every omission.

Focused checks: `tests/unit/test_philo_graph_atlas.py`, `tests/unit/test_graph_walk_calibration.py`, and new narrowly scoped rig tests needed by the changed operations. Provide pre-fix failures first. Main runs actual cases serially through DW capture and owns observation/shot inspection; workers do not claim the sample atlas closes A2.
