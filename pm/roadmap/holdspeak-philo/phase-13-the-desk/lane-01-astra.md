# PHILO-13-01 — Astra lane record, r2

**Status:** DRAFT — UNCHECKED — awaiting Muad'Dib. Story 01 stays in-progress; B2 stays held.

LANE: Data + truth, Phase 13 story 01 (B0). Local worktree `/Users/karol/dev/tools/wt-philo-13-b0-r2`, branch `feat/philo-13-b0-r2`; target PR #726 updates remote branch `feat/philo-13-astra`. Product base `27b915538`; walked revision `c7073f9ca` with this lane's Atlas/rig edits present.

OUTCOME: Paid Muad'Dib's signed C1–C6 conditions on #726. H-B0a and H-B0b remain present: the Phase 13 Astra Atlas validates, its own count is fenced, the shared `.op` count filters only `atlas-phase13-*`, and shared semantic guards still read both Phase 13 files. All nine real atlas cases ran once per viewport against the final Atlas hash. The selected table records 4 predicate passes and 14 fail/blocked results, with visible product reds and rig limits separated. No product face was changed.

PROOF:

- Worktree-local `uv sync --extra test` and `cd web && npm ci` completed; Node 22.21.0 from the existing nvm install was used because Homebrew Node could not load `libllhttp.9.3.dylib`.
- Focused collection: 139 tests. Focused run: **139 passed in 3.70s**, with isolated HOME and the existing Playwright cache selected explicitly. Exact output is in [the focused capture](assets/story-01-walks/r2-focused-output-pass.txt). No full suite or metal tests ran.
- `test_phase13_shared_semantic_guards_show_red_then_green` exercises actual Phase 13 atlas copies through the shared semantic validator and rejects broken words, bindings and semantics before the final Atlas passes. The final Spatial label was observed as `IDENTITY`; the Atlas word and exact fence changed together before the final walks.
- The [five-column run index](walks-01-astra.md) links all 18 observations and their screenshots. Every selected observation records final Atlas SHA `4ab5c4449f6ef0f2996327719dfc574a398952110cd3340153ec8f9df9d34236`, an isolated DB under that run's HOME, and native touch at 393. The [manifest](assets/story-01-walks/manifest.json) records the preserved run artifacts' SHA-256 values.
- The real inputs include Calendar's upload route, a repository fixture with the `build_roadmaps_router` seam disclosed in each repository-backed case, `/api/chains`, agent-hook ingestion, `/api/directories` with both world probes, and a real Sequence opened through Spatial.

LEDGER: [Findings and homes](findings-01-astra.md). The highest owner costs are: Chain/Coder Close leaves Dock records; Roadmap's identity fails at both widths; Repository content is off-screen on desktop; Delivery windows are covered on phone; the Directory context menu does not select its real Zone; Calendar exposes a machine code. The Dossier zero counters and Terminal footer overflow remain visible outside their narrower passing predicates. Info opens through Spatial and displays `IDENTITY`; its remaining results are observation-bound limits, not product reds.

AMENDMENTS: Applied every signed #726 condition without changing the ratified scope: the five-column table; Calendar refusal lifecycle; Zone through Directory and Info through Spatial; corrected F1 language; seam disclosure in every repository-backed case; the C5 B2 gate and post-#725 F1 re-walk; and Astra ownership of shared `atlas.schema.json` and `scripts/graph_walk.py`, with face-lane changes by named handoff. The initial isolated pytest command missed the external browser cache; the final captured run selected the existing cache explicitly and passed. The draft-branch results do not satisfy the “on main” acceptance criterion. Do not flip Story 01 or create canonical `evidence-story-01.md` before its remaining gate evidence exists.

UNKNOWN: The cases have not been rerun on merged `main`; #725 is open, so the post-#725 Chain/Coder re-walk remains pending; B0 has not run on B2's head; B0-F2 must still pass there. The engine-none Calendar runs prove the genuine refusal but not a successful vision-backed review. The Info observations exceed or miss rig hit-test bounds despite the correct rendered content. No owner-desk sitting or real send is claimed.
