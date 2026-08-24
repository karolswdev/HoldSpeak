# HANDOVER — Story HS-143-08 (FINAL, 2026-08-24: STORY DONE)

FINAL revision. Story 08 is DONE: all six phases (A-F) complete and
ratified, the story flipped with captured full-suite evidence
(evidence-story-08.md: 6475 passed / zero branch-new). Twenty-one
gate commits on `feat/hs143-08-meeting-adoption`. NOT PUSHED — push +
PR only on the owner's word. Next actionable story: 09 (tool
routing). This file remains as the arc's historical index; the
per-phase counsel records and the Phase F cleanup plan in `assets/`
are the canon.

## 1. Way of working (the standing law for this arc)

- **Orchestration:** `docs/internal/ORCHESTRATION.md` (Muad'Dib method).
  Orchestrator decides/briefs/verifies, never writes product code;
  authors PMO docs directly. Model order for THIS arc (owner carve-out,
  2026-08-22): **workers = Terra** (`model: terra` on general-purpose
  agents), **counsel = Sol**. Default opus-worker rule resumes after
  Story 08.
- **OWNER'S BAR — hard, twice-reasserted, once HARD-OVERRULED into law
  (2026-08-24):** the product always runs YOLO mode. Findings count
  ONLY when a normal product action reproduces damage. Crash-window /
  sleep-resume / takeover-race / adversarial scenarios are LEDGER NOTES
  by default, even when a probe reproduces them. **Counsel loops
  hard-cap at ONE ruling round + at most ONE fix round, then
  RATIFY-WITH-NOTES and ship.** The five-round C1 loop is the
  never-again example. State this bar verbatim in every counsel brief.
- **Worker proofs construct PRODUCTION objects.** Decorating a fake
  with the attribute under test is this story's named sin — caught
  twice (C2 disabled-plugins fake host; a wake test faking
  `loaded=True`). Reject reports that do it.
- **Commit lane:** workers NEVER stage/commit. Orchestrator stages by
  explicit path, `.githooks/dw contract new --story HS-143-08`, flip
  boxes honestly, commit. Every commit passes the DW gate. NO PUSH
  until the arc is ratified AND the owner agrees (GitHub Actions
  minutes are out by owner order — CI is never consulted; verification
  is local-only).
- **Sweep discipline:** full suite only on a quiet tree, always
  `HOME=$(mktemp -d) ... uv run --python 3.13.11 pytest -q -n auto
  --ignore=tests/e2e/test_metal.py` with
  `PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright`
  and `npm_config_cache=$HOME_REAL/.npm`. **Pin 3.13.11** — a bare
  `uv sync` grabs Python 3.14 and its results were discarded once.
  Triage every sweep against
  `assets/story-08-inherited-failure-baseline.txt` (the 72-name main
  baseline at `89d232f3`; ~70 of them reproduce here — they are
  INHERITED, not ours). Anything not in that list: serial ×2 to split
  flake from real. Known recurring xdist load flakes (each proven
  serial-green ≥2×): workbench deadline-expiry, device-recording-tick
  sender-exception, refinement-coordinator recovers-owner /
  reciprocal-stop, jira/github enablement, conductor
  deadline-persisted, delivery-campaign, glass e2es.
- **Gotchas:** failed/killed glass e2e runs CLOBBER the six phase-141
  chair PNGs — `git checkout -- pm/roadmap/holdspeak/phase-141.../story-05a/`
  after sweeps, never commit them. Background suite runs were
  externally killed ~5× this session at random points — just relaunch;
  completed runs are trustworthy. Census/snapshot regens are the LAST
  act of any worker round (anchors move with every edit).

## 2. What is DONE and COMMITTED (eighteen gate commits)

Branch `feat/hs143-08-meeting-adoption`, all on top of main `89d232f3`.

1. `a581bc1e` — full-suite stabilization: the owed sweep found 148
   failures → 70 inherited + 78 branch-new; all 78 classified a/b/c and
   repaired (3 real regressions; a suite-wide readiness-pollution leak
   killed; `intel_token` retirement completed).
2. `88d9e52c` — C1 checkpoint round 1 fixes (retry-lineage glass lies,
   refusal spin-forever, per-bookmark budgets, reserved→promote
   successors, census registration).
3. `c8296959` — round 2 (receipt→promotion crash scan, legacy/V3 stable
   handoff identity, bookmark_id-keyed publication).
4. `63bf3d88` — round 3 STRUCTURAL: durable executor lease (bearer
   token + epoch + 15s heartbeat, stale-only takeover CAS).
5. `32b730e1` — round 4: the epoch fences EVERY durable effect;
   fail-closed heartbeat; reconcile-not-reexecute takeover.
6. `c8b4fba9` — round 5 + **C1 CHECKPOINT CLOSED BY OWNER AUTHORITY**
   (takeover recovery scoped per-execution; owner ended the loop:
   "stop spinning wheels on edge cases").
7. `f3546f8d` — **C2**: installed plugins ride the routed queue
   (frozen ID/revision/schema members, runtime-string planning dead,
   non-model gates pre-child, inner-output semantics).
8. `dab3c8b2` — C2 counsel fix: the owner's Disabled-plugins setting is
   honored in production. **C2 CLOSED.**
9. `4381a820` — **C3**: Stop-handoff provider (reserve-inert primitive
   adopted; unknown terminals stay reserved + auto fresh local re-run
   per owner ruling, ledger-not-UI).
10. `35dfa709` — C3 counsel fix: reserved handoffs fenced from generic
    Retry/Skip ("Skip meant run it anyway"); Stop cancel signals
    backgrounded (800ms worst→16.31ms measured); unsettled-handoff
    index. **C3 CLOSED — PHASE C STRUCTURALLY COMPLETE.**
11. **Phase D slice 1** (the commit carrying this handover revision) —
    speech capture on the router: atomic routed capture admission for
    owner + wake sessions, routed transcription adapter on frozen
    members (actual-audio identity, `ProviderIndeterminate` timeouts),
    one bounded P=1 preload member, egress badge from ALL frozen route
    legs (missing route refuses). Plus the five counsel rulings
    implemented: speech LOCAL-ONLY (`allowed_boundaries=("local",)` at
    capability + every policy; non-local legs refused at admission;
    remote transport LEDGERED); `wake-capture@1` + derived
    `speech.preload@1` member (cold-MLX wake proven with a REAL
    unloaded `_MlxTranscriber`, the `loaded=True` fake retired);
    `wake_capture_revision` binds in the immutable parent snapshot
    only (generic evidence schema untouched); the two migration
    markers COUPLE into one cutover switch (bundled parent's legacy
    provider fallthrough refuses); faster-whisper constructor load =
    ratified local-only exception (LEDGERED). Density-guard breach
    closed by moving `_frozen_session_transcriber` to
    `transcriber_state.py` (census anchors regenerated). Committed
    `9489ec96`.
12. **Phase D slice 2** (the commit carrying this handover revision) —
    the pre-session warm rides the router: the sole parentless
    startup/background warm entrance freezes the exact capability-only
    owner `speech.transcribe` assignment + derives the SERVICE
    `speech.preload` route in ONE transaction (fixed basis
    `local-model-preload:assigned-speech-route`, amendment 2) before
    any construction; frozen stop rules + frozen-only MLX
    candidate/stage walk (amendment 3); warm reuse gated on
    deployment-revision + durable successful preload receipt
    (amendment 4; Meeting reuse aligned); denied/failed warm DEFERS to
    first lawful transcription (the sweep-caught escaping
    admission-error regression fixed by bounding deferral at the
    admission seam; warm-on-start test moved onto a real production
    admission path). New proof file
    tests/unit/test_phase143_speech_lifecycle_adoption.py (8 lifecycle
    cases). Committed `5aadd02a`.
13. **Phase D counsel fix round** (the commit carrying this handover
    revision) — Sol's capped post-commit pass (record in the counsel
    file) found two ordinary-path defects, both fixed: D1 default cold
    wake was DEAD (pinned-on default pipeline vs closed wake policy;
    old proof masked it by disabling the pipeline) → wake-capture@1
    authorizes the routed wake pipeline tail (amendment 8-bis), routed
    provider execution resolves its frozen deployment, new proof runs
    ordinary cold wake with default pipeline ON to the configured wake
    output; D2 deferred faster-whisper warm lied forever as "warming"
    → deferral settles to not_loaded, proven on the production runtime.
    **PHASE D RATIFIED-WITH-NOTES — CLOSED.** Committed `0fdd2d44`.
14. **Phase E design + slice 1 Rails** (the commit carrying this
    handover revision) — design ruled (Sol RATIFY-WITH-AMENDMENTS,
    E1-E3 in-file: sentinel conversion, refusal-recording seam,
    override retirement; only Rails is true background SERVICE work,
    cadence/decision/delivery are OWNER request-time drafts). Slice 1:
    sealed rails-observer@1 policy, rails.observer-batch parent kind,
    batch-hash one-member bundle (replay-safe journal/egress), E2 seam
    record_pre_route_refusal on the bundle service, E1 sentinel
    migration (rails-observer-route-assignments family). Three real
    defects caught by orchestrator probes/guards, fixed in-round:
    reconcile now REBUILDS kernel_parent_runs on kind-vocabulary drift
    (existing DBs refused new parent kinds; proof vs old-shape DB);
    trusted_child persists a declared non-generic SERVICE authority
    basis (was overwritten by the generic basis); stale one-path spine
    rig repaired. Sweep 6453/zero branch-new — ELEVEN inherited
    baseline failures now pass on this branch. Committed `dd1ef120`.
15. **Phase E slices 2-4** (the commit carrying this handover
    revision) — the three OWNER drafts routed via the shared
    services/inference_owner_draft.py one-member-bundle module:
    cadence next-action (deterministic fallback on refusal), decision
    promotion (no artifact on refusal), delivery PR review
    (non-posting, diff-hash replay). E2 terminal refusal receipts on
    every pre-route refusal; E3 override retirement
    (inference_request_target_override_retired, receipt-backed).
    Successful draft parent receipts retain the artifact ID. One
    stale rig migrated to assignment authority. **ALL FOUR PHASE E
    ADOPTERS ARE ROUTED.** Committed `abe4bb63`.
16. **Phase E counsel fix round** (the commit carrying this handover
    revision) — Sol's capped pass found four receipt-truth defects,
    all fixed (record: assets/story-08-phase-e-counsel.md): E-F1
    migrated Rails sentinel executable (locator preserved, first-use
    exception for the exact migrated revision, readiness bootstraps
    on first load; sweep catch folded in: migration gates on an
    ENABLED observer, deployment capability-owned active=0 + excluded
    from generic setup projection + marker-replay repair — it briefly
    hijacked current_thought_deployment); E-F2 refusal identities in
    their own namespace (pre-route-refusal: + sha256 of
    schema/command/reason; never returns a non-refusal receipt);
    E-F3 durable Rails journal carries one [egress: <boundary>]
    badge = widest frozen boundary; E-F4 known terminal outcomes
    persist (failed stays failed; only dispatch uncertainty is
    indeterminate). **PHASE E RATIFIED-WITH-NOTES — CLOSED.**

Counsel records (verbatim, with orchestrator dispositions):
`assets/story-08-c1-checkpoint-counsel-round1.md` (5 rounds + owner
close), `assets/story-08-c2-counsel.md`, `assets/story-08-c3-counsel.md`,
`assets/story-08-phase-d-counsel.md` (the five slice-1 rulings; brief
with verified file:line evidence in
`assets/story-08-phase-d-rulings-brief.md`),
`assets/story-08-audit-stream-notes.md` (owner-side code-review stream
findings + dispositions). Verification ledger sweep section:
`assets/story-08-tranche-ac-verification-ledger.md`.

Last clean sweep (Phase E ratified tree): **6470 passed / 51 failed /
zero branch-new** — 48 inherited + 3 known xdist flakes serial-green
×2; the branch now FIXES a dozen-odd inherited failures. From 6314
passing at the restart-session start.

## 3. Rulings RESOLVED (2026-08-24) and open ledger

The three formerly-blocked items and both review-stream findings were
verified against the tree (all five CONFIRMED) and ruled by Sol in the
single capped round — full record with required proofs:
`assets/story-08-phase-d-counsel.md`; binding texts = design
amendments 7–11. All five implemented in the slice-1 commit.

Open LEDGER entries from the ruling (future work, not defects):
1. **Remote speech transport** — mesh/private-network speech execution
   needs an explicit audio transport + semantic adapter before the
   local-only boundary can widen; until then non-local speech legs are
   refused at admission.
2. **Faster-whisper constructor seam** — model load is
   constructor-inseparable (library API); ratified local-only
   exception per amendment 11.

Standing flake ledger candidates (each serial-green ≥2×): workbench
deadline-expiry, device-recording-tick sender-exception, refinement
reciprocal-stop, jira/github enablement, conductor deadline-persisted,
sigkill process-input, github-enrichment preview.

## 4. What REMAINS for Story 08

1. Phase F — migration cleanup (legacy authority removal; the design's
   compatibility cutover; the deferred lexical-punctuation stance
   stays future/non-assignable).
2. Story 08 close: full-suite sweep, `dw evidence capture` of the real
   verification, story flip to done WITH evidence in the same commit,
   phase-status/README cadence updates.
3. Then Stories 09–14 remain for the phase (tools, agents/workbenches,
   HTTP/MCP sync, Model Library UI, Assignments UI, chaos glass) — not
   this handover's scope.
4. Push + PR ONLY when the owner says so.

## 5. The final outcome (what "done" means)

Every model invocation in HoldSpeak — Ask, Thoughts, meetings (live +
deferred + plugins), speech (dictation, wake, rewrite), and the
background adopters — flows through ONE sealed router: frozen route
plans, ordered assignments with a durable fallback controller, one
admitted child + one terminal receipt per physical call, honest egress
badges derived from frozen routes, and a Model Library / Assignments
owner experience where setup never silently rewrites a job. On a tired
Tuesday the owner records, stops, sleeps the laptop, clicks whatever
button is in front of them — and the status glass never lies, no work
is silently lost or doubled, and disabled things stay disabled.
