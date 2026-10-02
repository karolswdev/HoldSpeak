# PHILO-13-01 — Astra lane record, r3

**Status:** DRAFT — UNCHECKED — awaiting Muad'Dib. Story 01 remains in-progress; B2 stays gated.

LANE: Data + truth, Phase 13 story 01 (B0). Worktree `/Users/karol/dev/tools/wt-philo-13-b0-r2`, branch `feat/philo-13-b0-r2`; target PR #726 remote branch `feat/philo-13-astra`. Rebased onto `origin/main` after #729 merged (`aa6130db`); rebased onto origin/main at `0fc58fc6`.

OUTCOME: Paid Muad'Dib's signed r2 conditions R1–R6 and re-walked F1 after #725 merged. H-B0a/H-B0b remain intact. The PR is still DRAFT; Story 01 is still in-progress because the main/B2 gates are open.

PROOF:

- The focused selection collected 166 tests and passed **166 passed in 7.84s**. It includes `test_philo_graph_atlas.py`, `test_api_surface.py`, `test_philo_graph_reference.py`, `test_philo13_astra_atlas.py`, and `test_philo13_graph_walk.py`; collection and output are in [the focused evidence](assets/story-01-walks/r3/focused-collect.txt) and [the run tail](assets/story-01-walks/r3/focused-green.txt). No full suite ran.
- R1's two pre-fix-baseline fences each failed before correction (`DID NOT RAISE`) with the three standing files selected; they now read pinned commit `c7073f9c` rather than moving `HEAD`. See [red result 1](assets/story-01-walks/r3/r1-red-1.txt) and [red result 2](assets/story-01-walks/r3/r1-red-2.txt). The final 166-test run exercises their fixed forms.
- Captured pytest transcripts have trailing horizontal whitespace trimmed for the commit gate; assertion text and result counts are unchanged.
- Adding the three-state Dock-chip assertion exposed a stale adjacency fence: the first final selection failed only test_phase13_case_and_sibling_manifest_is_local (1 failed, 165 passed). The red is retained at [focused-fence-red.txt](assets/story-01-walks/r3/focused-fence-red.txt); the fence now requires the hidden receipt before a later reload, and the final 166-test selection is green.
- The Luna worker's C4 rounded-sheet regression failed before the probe change (**1 failed, 125 passed**) and passed after it (**126 passed**), using real Playwright at 393 px. C5's trigger regression failed before the lifecycle change (**1 failed, 125 passed**) because the record said `blocked`; the final 166-test selection passes the real-HTTP 404 mismatch as `fail`. Exact worker commands/tails are recorded in [the worker proof](assets/story-01-walks/r3/worker-red-green.md).
- Ten real atlas invocations ran one case per command with isolated HOME/TMPDIR and fresh output directories: Zone at 1440/393, Info at 1440/393, Calendar at 393, Roadmap at 393, and Chain/Coder at 1440/393. The [r3 run table](walks-01-astra.md) links all observations and shots. F7's target and hit probes match in both runs, touch uses native long-press, and Open is disabled; classify it as a product defect. Info passes under its evidence-based 75 s bound. The new probes remove the x=391 rig limit from Info, Calendar and Roadmap.
- Chain and Coder each pass with the added visible → hidden → visible Dock-chip transition around Close, reload and reopen. This directly re-walks F1 on #725's merged base.
- H-B0b still has one shared historical `== 69` count at `test_philo_graph_atlas.py:492`, filtered only for `atlas-phase13-*`; Astra's file has one computed `.op` count. Shared semantic guards still see both Phase 13 files. The final Atlas hash is recorded per observation in the r3 run directories.

LEDGER: [Current findings](findings-01-astra.md). F1 is cleared on the post-#725 head; F7 is a real disabled-Open defect for C7/story 17 or a named face-lane handoff; Info, Calendar and Roadmap no longer carry the affected 393 rig limit. Existing product reds remain: Roadmap identity, Calendar's `no_vision_model_assigned` string, delivery coverage/overflow and zero counters, and Repository content below the desktop viewport.

AMENDMENTS: Updated the phase status rows by content, preserving #727's H-A1 r3 fences, #728's H-A2 title-match ruling and source-reference outputs, and #729's H-A3. Kept the five-column status table and Astra ownership of `atlas.schema.json` and `scripts/graph_walk.py`. No face-owned files changed; no guard was deleted or weakened. PR #726 remains DRAFT and will carry the note `r3 — awaiting Muad'Dib`.

UNKNOWN: B0 has not merged to `main` and has not run on B2's head; the B2 merge record still needs the merged B0 commit, canonical `evidence-story-01.md`, reruns on B2's head, and F2 green. `engine=none` proves Calendar's real refusal, not a successful vision-backed run. The user has not sat at the desk.
