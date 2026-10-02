# PHILO-13-01 — Astra lane record

**Status:** DRAFT — UNCHECKED — awaiting Muad'Dib.

LANE: Data + truth, Wave 1; PHILO-13-01 B0. Worktree `/Users/karol/dev/tools/wt-philo-13-astra`; branch `feat/philo-13-astra`; base `27b915538`. No PR yet.

OUTCOME: Partial. H-B0a/b are implemented and verified. The atlas currently contains one real Zone operation case, with the lane count fence. The legacy count excludes only Phase 13 files; all shared semantic guards still see them. The opt-in `ui-by-viewport` rig adapter supplies native mouse at 1440 and native touch at 393. The nine face walks remain pending; B0 stays in progress and B2 stays gated.

PROOF:

- Worktree-local `uv sync --extra test`, `npm ci`, and web production build passed. No node_modules symlink. Node 22.21.0 is selected from the existing nvm installation because Homebrew Node fails to load `libllhttp.9.3.dylib`.
- Before changes: 98 shared atlas tests collected and passed in 1.92 s. Raw [collection](assets/story-01-handoffs/b0-shared-before-collect.txt) and [run](assets/story-01-handoffs/b0-shared-before-run.txt).
- Astra verification: **136 tests collected; 136 passed in 2.02 s**, covering the shared atlas, the Phase 13 atlas, the new rig adapter and existing select/press behavior. [Actual DW captures](assets/story-01-handoffs/captured-runs.md) include exact commands, collection and output.
- A deliberately broken Phase 13 case changed its durable observation to `zone.create`. The existing shared operation test failed with `observation re-fires 'zone.create'`. Restoring the original atlas byte-for-byte passed. Both executions are captured above. The separate mutation fence also rejects an unbound producer ID.
- Actual `graph_walk.py run`, one case/one isolated hub: `case.p13.directory.zone_window.op` **pass**. [Unmodified observation](assets/story-01-handoffs/zone-operation/observation.json): real `zone.create` returned `dir_5dcfcd48acda`; `zone.read` and `zone.list` returned that row; all four expected facts held. Initial feedback satisfied at 0.913 s; terminal settled at 0.915 s. Revision `27b915538`, dirty with this uncommitted lane work. DB path verified under the rig's temporary HOME. Original output: `.tmp/graph-walk/philo-13-01/handoff-zone-op/20261002T014424Z-case.p13.directory.zone_window.op-astra-1440/`.
- Native browser listeners in focused adapter tests observed mouse and touch pointer types, including touchstart/touchend at 393. These are adapter tests, not the nine actual face walks. This preparatory operation case is headless; no face shots are claimed.
- `dw check holdspeak-philo` and `git diff --check` passed. No full suite, per the dispatch's law 26. No metal tests or real sends.

LEDGER:

- (b, corrected before commit) The first count edit accidentally excluded Phase 13 from the semantic loop. Astra caught it; the final code filters a separate count only. The shared-operation mutant above proves the correction.
- (b, corrected before commit) The rig edit moved the Phase 11 source anchor. The touch implementation keeps `_op_step` at line 4685; the unchanged shared source guard passes.
- Verification input correction: the unfinished Zone face case targeted a nonexistent palette row. The real palette uses `zone:<id>` and navigates into it; it does not open the Zone window. That candidate is parked at `.tmp/philo-13-astra/zone-face-candidate.json` pending a real door sequence. It is not committed as a runnable or passed case.
- Source findings to exercise in B0: Calendar review needs vision extraction; Roadmap has no production `openRoadmapWindow` caller; Coder/Terminal need actual session producers. These are source findings, not observed runtime verdicts.
- Gate bookkeeping: the charter's six-column table was readable by `dw context` but rejected by `dw story status` (`render.py` requires five cells). Proposal IDs were retained in the Story labels; the standard status command then succeeded. No acceptance or ownership changed.

AMENDMENTS: None. The dispatch's scoped-tests-only instruction overrides older full-suite guidance. B0 remains in progress. Its DW captures are archived under assets for this preparatory commit; `evidence-story-01.md` remains pending the story's closing commit, as the gate forbids adding that file without a done flip.

UNKNOWN: The nine actual face paths and 1440/393 screenshots, behavior on merged main, and Muad'Dib's built check remain unverified. This handoff does not release B2's merge gate.
