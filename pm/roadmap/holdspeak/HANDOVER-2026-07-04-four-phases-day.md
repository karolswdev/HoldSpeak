# Handover — 2026-07-04 — the four-phases day

One session, owner-steered throughout ("keep adding value" → "2, please" → "next
move"): **the Equilibrium build finished (Phases 22 + 23 opened and fully built),
the first whole-product dogfood run was recorded (Phase 67 closed), and its headline
finding was fixed and re-proven the same day (Phase 80 opened and closed).** Nine
PRs merged (#236–#244), every merge gated on the conclusion JSON in a separate call.
This is the map: what shipped, the findings ledger, the traps, what remains.

## Where main stands

- **Main is green at `88e852e`** (Phase 80 merge). Working tree clean — the
  long-standing untracked `dogfood/repos/questline/src/lib/` finally landed (#243).
- Merged today: #236 (P23 open + 23-04 sync integrity), #237 (23-03 readiness
  panel), #238 (23-05 docs + storage rider), #239 (P22 open, survey-corrected),
  #240 (22-01 graph serializer + golden pin), #241 (22-03 web linear builder —
  **went red once**, see traps), #242 (22-04 cross-surface run), #243 (P67 dogfood
  closeout + the recorded run), #244 (P80 artifacts for the archive).
- Suites at last runs: full `swift test` **445/8-skip/0-fail**; the Python
  batteries around every touched module green; CI green on all nine PRs
  post-heal.

## Track 1 — THE EQUILIBRIUM BUILD IS COMPLETE (mobile, Phases 18–23)

- **Phase 23 (mesh-safe storage): fully built, gate staged.** Survey-corrected
  open (23-01/02 pre-paid by Wave 4, recorded with fresh runs). 23-04 completed
  the 10-kind sync round-trip matrix + brought `SERIALIZATION-CONTRACT.md` §11 to
  the shipping wire + corrected the stale "lossy manual_context" finding
  (Phase 77 fixed it) and golden-pinned the fields cross-language. 23-03 gave the
  Wave-4 schema safety a face: `StoreHealthProbe` + `SetupStatus.sections` (the
  hub's doctor block was being dropped) + the READINESS section in Settings +
  the typed `.tooNew` banner — live-proven incl. a real seeded `user_version=7`
  store rendered amber and left byte-intact.
- **Phase 22 (the graph travels): fully built, gate staged.** The survey KILLED a
  false memory (the Wave-2 "web authors a graph" claim had no code) and caught a
  producer hole (`BPNode` had no `runs_on`). 22-01: the shipping v1 canvas saves a
  real linear Blueprint → desk `WorkflowRecord` → DeskSync; the language boundary
  is golden-pinned (Swift-ENCODED fixtures fed byte-for-byte into `linearize()` by
  `test_blueprint_graph_conformance.py`; regen with
  `HS_REGEN_BLUEPRINT_FIXTURES=1`). 22-03: the web desk is the second producer
  (in-world step builder; iPad provenance presented read-only, never stripped;
  the run `warning` finally rendered). 22-04: `runWorkflow` on the iPad hub path
  (result type `HubWorkflowRunResult` — see traps) + the crown test
  (Swift fixture → sync push → hub run) — **live-proven on real metal**: the
  iPad-authored graph ran on the hub against `.43`, the card wearing
  Cloud · your desktop with the standup's actual decision extracted.
- **THE ONE OWNER COUCH SESSION NOW CLOSES FIVE PHASES: 18, 19, 21, 22, 23.**
  Same hub + `.43` pre-flight (`~/run-qwythos-vision.sh`, never `-intel`):
  `HSM-18-06-WALK.md` (W1–W5) · `HSM-19-07-WALK.md` (W1–W6) ·
  `HSM-21-WALK-RIDER.md` (H1–H3) · `HSM-22-WALK-RIDER.md` (G1–G2) ·
  `HSM-23-WALK-RIDER.md` (R1 + optional R2). Roughly half an hour total.

## Track 2 — the dogfood run + the same-day fix (desktop)

- **Phase 67 closed (#243):** `dogfood/results/2026-07-04.md` — all 63 protocol
  checks driven headless against the real `.43` Qwythos endpoint: **40 PASS /
  14 PARTIAL / 1 FAIL / 8 SKIP-for-glass** (mic wake word, native HUD, live
  diarization, capture-path spoken symbols are the owner's glass items). What
  proved spectacular: the grounded rewriter (rambling → a brief citing LL-118 +
  every `.hs/memory.md` invariant + acceptance criteria), a real actuator execute
  byte-equal into a local receiver with the credential never stored, the learning
  loop teaching live, cadence 5/5, isolation held. The run also hardened its own
  harness (repos gained `.holdspeak/blocks.yaml`; `setup.sh` gained the missing
  `project-rewriter` stage; CONTRIBUTING now points at the harness).
- **Phase 80 closed (#244), the F-05 fix:** `holdspeak/meeting_plugins.py` —
  `run_meeting_plugin_chain` (score → route → standalone `PluginHost` → one
  full-transcript window + runs + synthesized artifacts, DB-backed idempotency on
  the transcript hash). Wired into the deferred-intel processor (gated on
  `intent_router_enabled`; router-off imports byte-identical, test-locked) and
  `intel --reroute` (executes now). Re-proven on the same sandbox: the
  zero-artifact arch import → **4 artifacts** (a real accepted ADR, a mermaid
  flowchart, requirements, project association); the delivery reroute → 10.

## The findings ledger (the follow-on worklist, `dogfood/results/2026-07-04.md`)

- **F-05 — FIXED (Phase 80, same day).**
- **F-10 (MED, open):** the project-rewriter fabricates a plausible task from an
  EMPTY utterance (grounded in `.hs` context alone) — needs an empty-input guard.
- **F-01 (LOW, systemic, open):** `/theater/theaterorb.png` 404s on every
  theater-bearing page.
- Small opens: F-03 `dictation blocks ls/show` don't cwd-detect (need
  `--project .`; dry-run does detect), F-04 `hs import` exits 0 on error, F-07
  tier-1 pipeline-off never journals, F-08 the blocks docs example pairs
  `mode: append` with a `{raw_text}` template (doubles the text; use `replace`),
  F-12 no srt export choice, F-11 protocol wording vs the ratified Phase-61
  slack-approval design, F-06 the dogfood env defaults name the retired Qwen3.5
  model (override with `DOGFOOD_INTEL_MODEL`).

## Outstanding (ranked, headless-buildable)

1. **Release prep for v0.4.0** — the CHANGELOG `[Unreleased]` is rich (the whole
   Equilibrium wave + readiness panel + graph bridge + F-05 fix), and the dogfood
   record makes it an honest cut. Prep only: the tag IS the publish (Phase 65
   rule) and stays the owner's button. Consider folding the small findings
   (F-01/F-04/F-10) in first.
2. **Phase 17 — Agent Sync** ("the coder on your desk", the owner's explicit
   vision). FIRST MOVE: rescue the uncommitted `holdspeak-mobile/desk-parity`
   branch (the CoderSession contract + DioCoderSession UI live there); then
   17-02 (hooks capturing real Claude/Codex sessions into the hub) is pure
   desktop work, provable against a live session.
3. **The small-findings basket** (F-10 guard, the theater orb, exit codes,
   blocks cwd-detect) — a half-day sweep.
4. Watch items: `db/core.py` (guard-named), the
   `test_replay_after_target_correction_changes_routing` flake.

## Traps (this session's additions to the standing list)

- **The HS-72-02 api-surface lock fires on new WEB call sites too**, not just
  Swift. #241 went red on Unit Tests for exactly this; the conclusion-JSON gate
  caught it pre-merge (the #233 lesson working as designed). Heal:
  `uv run python scripts/gen_api_surface.py` on the same PR/commit.
- **SPM modules hide App-target name collisions.** `swift test` green while the
  gen-copy app build is red = check for duplicate type names (the engine already
  owned `WorkflowRunResult`; the client type became `HubWorkflowRunResult`). The
  gen-copy build is the arbiter for App-visible names.
- **`intel_queue` binds `get_database` at module level** — patch
  `holdspeak.intel_queue.get_database`, not `holdspeak.db.get_database` (the
  Phase-63 patch-target rule; noted in `test_meeting_plugins.py`'s fixture).
- **Sim demo branches need `SIMCTL_CHILD_HS_CLASSIC_HOME=1`** in addition to
  their own `HS_DEMO_*` flag (they live in the classic-home body).
- **`simctl spawn defaults read` does NOT see the app container's plist** —
  read `$(simctl get_app_container ...)/Library/Preferences/<bundle>.plist`
  directly; spawn `defaults write` DOES work for pairing.
- **Never `uv run` from inside a dogfood mock repo** — uv builds a venv INTO the
  fixture (it happened; cleaned).
- **A fresh scratch hub fronts the `/welcome` wizard** — mark
  `db.milestones.mark(FIRST_DICTATION_SUCCESS)` in proof hubs. The hub config
  file is JSON despite the `.yaml` name.
- **The owner runs his own `holdspeak web` instances** (one since Jul 1, one
  launchd-parented). Never kill a listener without checking its `HOME=` marker
  for `dogfood`.
- **PMO hook: an evidence-story file may only ship in the commit that flips its
  story to done** (orphan-evidence check) — docs-half commits ship without one
  (the 21-05 pattern); phases that track stories in the status table (67, 80)
  need no story files at all.
- **`Blueprint.graphJSONValue()` must decode with a PLAIN `JSONDecoder`** — the
  snake_case-converting decoder would mangle the already-snake_case wire keys.
- **Ternary `Color` vs `LinearGradient` needs `AnyShapeStyle`** on both arms
  (`Sig.topHairline` is a gradient).

## Where things live

- Phase 22/23: `pm/roadmap/holdspeak-mobile/phase-2{2,3}-*/` (evidence +
  screenshots + riders). Phase 67/80: `pm/roadmap/holdspeak/phase-{67,80}-*/`.
- The recorded run + findings: `dogfood/results/2026-07-04.md` (committed past
  the results gitignore as exit evidence; future runs stay ignored).
- Memory (Claude's): `project_equilibrium_program` (the whole mobile program
  state incl. 22/23), `project_phase67_dogfood_closed` (the run, the ledger,
  the harness re-run gotchas, the F-05 fix note).
