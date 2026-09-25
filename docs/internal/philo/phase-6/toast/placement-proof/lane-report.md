# PHILO-6-03 placement — Astra lane report

LANE: `/Users/karol/dev/tools/wt-philo-6-03`, `feat/philo-6-03-placement`, forked from `d8f608c812e540678ed3f945156aeeccc46d795a`. Product and atlas workers were `gpt-5.6-luna`, `xhigh` ([model record](luna-models.json)). No main-checkout edits. The exact four-line ChairHome patch is isolated in gated commit `d1e355f2`; lane A reconciles it.

OUTCOME: The ratified placement is built and the six actual surface walks pass. Published as [PR #649](https://github.com/karolswdev/HoldSpeak/pull/649). Build commit `c6aafa8e` passed the full gate (7/7 boxes, one story); the separate ChairHome commit is `d1e355f2`. No merge is authorized. Main advanced during this build: lane A merged as PR #646 (`e64114df`). PR #649 is open but reports five conflicts: `docs/internal/philo/graph/atlas.json`, `docs/generated/graph.json`, `docs/generated/boundary-candidates.json`, this project README, and the Phase 6 status file. The read-only merge preflight auto-merges ChairHome and the atlas tests; no combined-tree test or glass result is claimed. Muad’Dib’s integration and counsel remain before merge. [Raw merge preflight](merge-preflight.txt). The actual calling Muad'Dib's counsel on the built PR remains before merge; any Astra-invoked Claude check is labelled separately.

PROOF:

| Story box | Evidence |
| --- | --- |
| Zero counts omitted; numeric facts unchanged | Inherited merged lane-B proof: `../zero/red-origin-behavior.txt` (3 failed / 6 controls passed), `../zero/dw-validation.md` (13 passed). This build preserves the card strings, library Buttons and numeric producer. |
| Canvas ratified before build | Owner ratification `38cf713a`, merged in fork `d8f608c8`; boards `../shots/`. These are canvas fixtures; the runs below are the actual product. |
| Built placement, red before fix | [Archive rendered red](red-rendered.txt): 8 failed, 10 controls passed. Real `publishAftercare` and actual ChairHome, SurfaceWindowHost and DeskListView hosts. Arrival geometry red and six greens below; computed position is `static` in every slot. |
| ChairHome lane law | Only the exact `../chairhome.patch`; gated `d1e355f2`, [slot validation](slot-validation.md). No other ChairHome change in this lane. |
| Rendered appearance and dismissal, both widths | `aftercarePlacement.test.tsx` parameterizes the real ChairHome at 1440/393, publishes through the real signal producer, checks unchanged words, then clicks the real Dismiss Button and asserts card removal and empty slot. Phone tests also cover same-signal re-render, new card after dismissal, desktop no-scroll, and a focused field. Real Dismiss observations at both widths below also fence the slot hidden and CaptureBar 9/9 after the card leaves. |
| Actual rig, all surfaces and widths | Six rows below. Each uses real import, summary admission, drainer and durable meeting read; only the provider reply is replayed at the declared boundary. Each probe is armed before the producer trigger. No owner HOME or desk DB is used. |

| Case / width | Run and after-shot | Unobscured samples | Scroll calls; movement | Durable meeting |
| --- | --- | --- | --- | --- |
| arrival / 1440 | [20260925T052913Z-case.philo603.toast.arrival-astra-1440](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/after.png) | card 9/9; summary 9/9; capture 9/9 | 0; Δ0 px | `7d79b346` ready / succeeded |
| arrival / 393 | [20260925T052820Z-case.philo603.toast.arrival-astra-393](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/after.png) | card 9/9; summary 9/9; capture 9/9 | 1; Δ501 px | `0cc74979` ready / succeeded |
| meetings_window / 1440 | [20260925T052045Z-case.philo603.toast.meetings_window-astra-1440](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052045Z-case.philo603.toast.meetings_window-astra-1440/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052045Z-case.philo603.toast.meetings_window-astra-1440/after.png) | card 9/9; Meetings headline 9/9 | 0; Δ0 px | `ddccdd8e` ready / succeeded |
| meetings_window / 393 | [20260925T051937Z-case.philo603.toast.meetings_window-astra-393](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051937Z-case.philo603.toast.meetings_window-astra-393/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051937Z-case.philo603.toast.meetings_window-astra-393/after.png) | card 9/9; Meetings headline 9/9 | 1; Δ0 px | `54b561f6` ready / succeeded |
| floor_list / 1440 | [20260925T052727Z-case.philo603.toast.floor_list-astra-1440](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052727Z-case.philo603.toast.floor_list-astra-1440/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052727Z-case.philo603.toast.floor_list-astra-1440/after.png) | card 9/9; list header 9/9 | 0; Δ0 px | `6b66e90a` ready / succeeded |
| floor_list / 393 | [20260925T052207Z-case.philo603.toast.floor_list-astra-393](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052207Z-case.philo603.toast.floor_list-astra-393/observation.json) · [shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052207Z-case.philo603.toast.floor_list-astra-393/after.png) | card 9/9; list header 9/9 | 1; Δ0 px | `58a720a9` ready / succeeded |

Two earlier passes in `final/` are superseded for closure: `20260925T051357Z-case.philo603.toast.arrival-astra-393` and `20260925T051652Z-case.philo603.toast.arrival-astra-1440` lack the later declared Dismiss step. They remain as raw history; only the six table rows above are the closure set.

Each linked directory also retains `before.png`. Astra inspected the before/after pair for each of these six closure rows and the initial and terminal readings. All six observations are complete; terminal state is settled within 30 seconds. Provenance records `d1e355f2` with `dirty: true`, the actual frontend bundle and an isolated `graph-walk-home-*` database; these are pre-commit build observations, not falsely labelled clean-HEAD runs.

The phone Arrival scroll moves the reading position, as ratified: one `scrollIntoView` at 210 ms, three native scroll events, scrollTop 0 → 501. The real capture bar is 138 px high. Card `(12,381.296875,369,180)` ends at 561.296875; capture starts at 573. Summary and card do not intersect. The generated BRIEF row moves offscreen and does not intersect the card; it was 9/9 visible before the trigger. On desktop, summary, capture and BRIEF remain 9/9 visible with zero scroll calls. Window/list phone slots start visible, so their one nearest-scroll call causes no movement. These are calls to the card slot, not inferred from screenshot framing.

The final six closure runs disable the unrelated heartbeat scheduler (`scheduler_thread: false`); the real intelligence drainer remains active. The final Arrival reads initially report summary geometry absent, then settle with the summary present in about 1.5 seconds. No first-frame summary-readability claim is made. Each primary scroll probe is sealed before the separate Dismiss interaction.

Dismiss at 1440: [20260925T052913Z-case.philo603.toast.arrival-astra-1440](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/observation.json) · [dismissed shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/dismissed.png). The card is absent from the DOM, the slot is present, empty and hidden, and the CaptureBar owns 9/9 points at `{'x': 256, 'y': 758, 'w': 928, 'h': 74}`. Astra viewed the before, after and dismissed shots.

Dismiss at 393: [20260925T052820Z-case.philo603.toast.arrival-astra-393](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/observation.json) · [dismissed shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/dismissed.png). The card is absent from the DOM, the slot is present, empty and hidden, and the CaptureBar owns 9/9 points at `{'x': 12, 'y': 573, 'w': 369, 'h': 138}`. Astra viewed the before, after and dismissed shots.

Browser scope is Chromium only. [Astra-invoked built check](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/story-03-placement-astra-invoked-claude.md) C1 is paid by that explicit boundary; C2 is paid by the two Dismiss observations above. The review’s blanket Safari assertion is corrected in that record using the official Safari 27 release notes. Older engines without anchoring and a frontmost non-surface pullout remain ledgered limits.

Clearance is scoped to the active face. The open Meetings window covers the Arrival backdrop at 393; that hidden CaptureBar records 0/9 and is not claimed readable. The card does not intersect its rectangle. The foreground Meetings headline is 9/9. Floor list has no Arrival summary, capture or BRIEF; its header is 9/9. No all-points claim is made for absent or offscreen scopes.

The pre-fix `git archive origin/main` is pinned by [baseline.json](baseline.json). It has its own installed dependencies and original frontend build. Only the new tests, atlas and rig were overlaid. Archive observations have no git checkout, so their empty revision field is resolved by this pinned archive provenance, not passed off as a clean branch.

Archive Arrival run `20260925T044503Z-case.philo603.toast.arrival-astra-393` fails the absent slot fence: old card `fixed`, `(16,568,361,180)`; summary `(16,612.296875,361,90)` is 0/9, real capture `(12,573,369,138)` is 6/9. The card intersects both. Archive Meetings run `20260925T045541Z-case.philo603.toast.meetings_window-astra-393` fails the missing window slot. Archive Floor run `20260925T050903Z-case.philo603.toast.floor_list-astra-393` fails the missing list slot. All three retain real intel-ready / succeeded reads. The baseline's focused rendered controls pass; missing imports or unknown symbols are not counted as reds.

Verbatim result lines (ANSI removed only; full logs remain linked):

Archive rendered red, exit 1 ([raw](red-rendered.txt)):

```text
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 8 ⎯⎯⎯⎯⎯⎯⎯
 Test Files  1 failed | 1 passed (2)
      Tests  8 failed | 10 passed (18)
```

Focused frontend, exit 0 ([raw](final-focused-run.txt)):

```text
 Test Files  3 passed (3)
      Tests  30 passed (30)
```

Final Python atlas/rig/architecture, exit 0 ([raw](final-python-run.txt)):

```text
104 passed in 4.40s
```

Untouched main scoped baseline, exit 1 ([raw](scoped-baseline.txt)):

```text
⎯⎯⎯⎯⎯⎯ Unhandled Errors ⎯⎯⎯⎯⎯⎯
TypeError: currentBucket is not iterable
 Test Files  30 passed (30)
      Tests  214 passed (214)
     Errors  1 error
```

Final broad scope, exit 1 ([raw](final-scoped-run.txt)):

```text
⎯⎯⎯⎯⎯⎯ Unhandled Errors ⎯⎯⎯⎯⎯⎯
TypeError: currentBucket is not iterable
 Test Files  32 passed (32)
      Tests  235 passed (235)
     Errors  1 error
```

Generated checks ([raw](generated-checks.txt)), final DW capture `2026-09-25T05:31:40Z`, exit 0:

```text
Architecture documentation checked (10 outputs).
Documentation coverage checked.
API reference checked
Boundary candidate census checked
philo_graph_reference.py --check: exit 0 (all graph rows checked; full console in .tmp/philo603/graph-check.txt)
```

Typecheck and Vite build passed. The first final-validation capture had 104 passing tests but failed the boundary-census drift check; regenerating its six shifted source-line references paid the drift. The later final capture is the green reference. No failed command is relabelled green.

LEDGER:

- Workbench: `dw check holdspeak-philo` passes after the CLI story flip (capture `2026-09-25T05:38:01Z`, exit 0). The repository-wide `dw check` exits 1 on six older `pm/roadmap/holdspeak/` errors; the pinned origin/main archive returns the same six ([raw baseline](dw-global-baseline.txt)). No file in that other roadmap changed.
- [Phase-local ledger](../../ledger.md): the inherited `arrivalSummaryRun.test.tsx` fixture omits kind buckets; a real refresh raises `TypeError: currentBucket is not iterable`. Untouched archive has 214 passing assertions and the same error ([raw baseline](scoped-baseline.txt)). Separate fixture repair is the follow-up; no unrelated product repair here.
- Spatial WebGL Floor deliberately keeps fixed placement. Run [20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393/observation.json) · [fallback shot](../../../../../../pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393/after.png) records computed `fixed`, card `(16,568,361,180)`, 9/9 card samples and zero scroll calls. The actual WebGL furniture is visible and the card covers some items. This is fallback evidence, not a no-overlap pass for spatial Floor. A future spatial placement canvas owns that repair.
- The first built Arrival run `20260925T045018Z` found the summary expanding after the sole scroll and moving the card under capture/dock. The correction scopes native scroll anchoring to the nonempty Arrival slot. The actual repeat `20260925T045707Z` proves the final layout; no timing sleep or repeated scroll was added.
- Diagnostic Floor runs at `050111Z` and `050229Z` were blocked by setup menu assumptions; `050406Z` failed because the setup menu remained open. The corrected recipe accepts the phone's existing list mode, closes the menu by an outside pointer-down, and fences the menu hidden before the trigger. These are not counted as product reds or greens.
- The initial archive attempt `043908Z` was stopped while its first draft had an excessive completion bound and a text-case mismatch. Its incomplete `not_run` record is retained; only the completed `044503Z` run is the Arrival red.

AMENDMENTS: No placement design or product string change. The latest build brief defines these three surface cases instead of the earlier phase-wide rehearsal for story closure; that broader rehearsal remains the integration lane's exit. The tiny native-anchor correction implements the already-ratified once-scroll when real summary content arrives asynchronously. Metadata, tests, atlas source anchors and generated views ship with the implementation.

UNKNOWN: PR merge is blocked on the five recorded conflicts against newly advanced main; the built branch itself is committed and its scoped proof complete. Global Workbench retains six baseline roadmap errors outside this lane. The broad scoped run exits 1 on the inherited fixture error, not a clean suite. No physical-phone or owner sitting is claimed. The live runs use Chromium at 393/1440 and a labelled summary-provider replay; real-provider quality is not verified by this lane. Spatial no-overlap, phase-wide closing rehearsal, lane-A reconciliation and actual Muad'Dib PR counsel remain outside this lane's completion.
