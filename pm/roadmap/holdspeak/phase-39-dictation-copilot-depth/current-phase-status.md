# Phase 39 — Dictation Copilot Depth

**Status:** IN PROGRESS (2/7 stories). Opened 2026-06-05. Direction chosen by
the user (feature work over Release/First-Run and Growth; track "Dictation
Copilot depth" over Actuators III and Artifact→action bridges).

**Last updated:** 2026-06-05 (**HS-39-02 done** — correction memory (session
learning). New `holdspeak/plugins/dictation/corrections.py` `CorrectionStore`
(bounded ring, thread-safe, gist-only + secret-rejected), owned by
`MeetingWebServer` and shared with the live `WebRuntime`. Capture/list routes
`POST/GET /api/dictation/corrections`. A deterministic post-classify nudge in
`IntentRouter` reinforces/redirects toward a similar recent correction;
`target_profile.apply_target_correction` biases detection (manual override
always wins). Gated behind default-off `corrections_enabled` and threaded
through `assembly.build_pipeline` + the dry-run helper + the live path; empty
store or flag-off ⇒ byte-identical. Suite **2157 passed, 15 skipped** (+25);
touched files ruff-clean. Next: HS-39-03 model-assisted target detection.)

**Earlier 2026-06-05** (**HS-39-01 done** — multi-pass rewriting.
`DictationPipelineConfig.rewrite_passes` (default 1, validated 1–5);
`ProjectRewriter` runs a draft → critique → refine loop, latency-budget-gated
against `max_total_latency_ms` (an extra pass is skipped before it would
breach the budget) and **fails open to the best successful draft** on a refine
failure so multi-pass never regresses below single-pass. Per-pass timing +
counts on `StageResult.metadata` (surfaced verbatim by the dry-run). Wired
through `assembly.build_pipeline`. Default (`rewrite_passes=1`) byte-identical;
suite **2132 passed, 15 skipped** (+9); touched files ruff-clean. Next:
HS-39-02 correction memory.)

## Goal

Phase 18 built the intelligent-typing substrate; Phase 19 made it
**trustworthy for daily use** (safe `.hs/*.md` suggestions, latency/fallback
telemetry, target-profile override, a real OpenAI-compatible endpoint
dogfood). Phase 19's own handoff named the next work: *"compatibility and
quality, not more UI knobs — prompt quality checks, latency budgets, and real
daily dogfood,"* and left three things **still experimental**: suggestion
quality under long noisy sessions, automatic target detection on
Wayland/terminals, and prompt quality.

Phase 39 makes the copilot **deeper and self-improving**: the rewrite gets a
refinement pass, the pipeline **learns from corrections** within a session,
target detection gains a model-assisted fallback, and project-doc suggestions
gain a quality gate so they stop repeating what's already written — all made
observable.

The DIR-01 invariant is unchanged and load-bearing throughout:

> The pipeline is **off by default**; every new behavior is opt-in; any stage
> failure short-circuits to the original (post-`TextProcessor`) text — **the
> utterance is always typeable**; with the pipeline disabled, behavior is
> **byte-identical** to pre-Phase-39.

## Scope

### In

- **Multi-pass rewriting (HS-39-01).** `ProjectRewriter` gains an optional
  draft → self-critique → refine loop behind a new `rewrite_passes` config
  (default `1` ⇒ byte-identical). Latency-budget-aware: an extra pass is
  skipped when it would breach `max_total_latency_ms`. Dry-run surfaces each
  pass.
- **Correction memory — session learning (HS-39-02).** A bounded, thread-safe
  in-process correction store. When a user corrects a wrong intent/profile or
  rejects a rewrite (via the dry-run / web surface), the router prompt + the
  match threshold get a **session-scoped** nudge for similar utterances. Off
  by default; bounded ring; never persists secrets; no DB schema change.
- **Model-assisted target detection (HS-39-03).** When heuristic target-profile
  confidence is below a threshold, an **opt-in** LLM classification refines the
  profile (still overridable; manual override always wins). Closes Phase 19's
  "automatic detection unreliable on Wayland/terminals" gap without brittle
  per-app automation rules.
- **Project-doc suggestion quality gate (HS-39-04).** Before proposing a
  `.hs/*.md` update, dedup against the existing doc (skip if already
  ~covered); track accept/reject so a dismissed suggestion does not recur;
  optional consolidation of suggestions from the last N utterances into one
  update. Closes Phase 19's "suggestion quality under long noisy sessions."
- **Pipeline depth telemetry (HS-39-05).** Per-stage latency quantiles
  (p50/p95) + budget guidance, multi-pass attribution, and correction-store
  visibility surfaced on `GET /api/dictation/readiness`. Makes the new depth
  observable.
- **Documentation (HS-39-06).** Dedicated docs story:
  `docs/INTELLIGENT_TYPING_GUIDE.md` (+ any guide/MODELS touchpoints) documents
  every new knob (multi-pass, correction memory, model-assisted detection,
  quality gate, telemetry); doc drift-guard + link-check green.
- **Closeout (HS-39-07).** Real dogfood against the `.43` OpenAI-compatible
  endpoint; a before/after on a messy dictation session; `final-summary.md`;
  README phase row → done; HANDOVER refresh.

### Out

- **New LLM backends** beyond the existing `mlx` / `llama_cpp` /
  `openai_compatible` — a DIR-02 question.
- **Cloud router fallback** — DIR-02.
- **Cross-utterance windowing / rolling context** beyond the bounded,
  session-scoped correction store (no persistent learning, no DB writes).
- **Silent project-memory writes** — a suggestion still requires explicit
  apply (Phase 19 posture unchanged).
- **Per-app automation rules** for target profile — manual override + the
  model-assisted fallback are the chosen path (Phase 19 decision upheld).
- **Reworking the meeting-side MIR pipeline** — DIR and MIR stay independent
  (shared contracts only).

## Exit criteria (evidence required)

- [x] `ProjectRewriter` runs `rewrite_passes` passes (default 1); `passes=1`
      output is byte-identical to pre-Phase-39; an extra pass is skipped when
      it would breach `max_total_latency_ms`; dry-run shows each pass.
      (HS-39-01) — [evidence-story-01](./evidence-story-01.md)
- [x] A bounded correction store nudges routing within a session; default (no
      corrections) leaves routing byte-identical; the store never persists
      secrets and adds no DB schema. (HS-39-02) —
      [evidence-story-02](./evidence-story-02.md)
- [ ] Below-threshold heuristic confidence triggers the opt-in LLM
      target-profile fallback; manual override still wins; with the fallback
      off, detection is byte-identical. (HS-39-03)
- [ ] A proposed `.hs/*.md` update that ~duplicates the existing doc is
      suppressed; a dismissed suggestion does not recur in the session;
      consolidation can fold N utterances into one update. (HS-39-04)
- [ ] `GET /api/dictation/readiness` reports per-stage p50/p95 + budget
      guidance + multi-pass + correction-store state. (HS-39-05)
- [ ] `docs/INTELLIGENT_TYPING_GUIDE.md` documents every new knob; no live doc
      contradicts the shipped surface; doc-guards + link-check green. (HS-39-06)
- [ ] `.43` endpoint dogfood captured; before/after on a messy session;
      `final-summary.md`; README → done. (HS-39-07)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout;
      with `dictation.pipeline.enabled=false` the typing path is byte-identical
      to pre-Phase-39; no new default network/LLM call. (all)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-39-01 | Multi-pass rewriting | done | [story-01-multi-pass-rewriting.md](./story-01-multi-pass-rewriting.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-39-02 | Correction memory (session learning) | done | [story-02-correction-memory.md](./story-02-correction-memory.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-39-03 | Model-assisted target detection | backlog | [story-03-model-assisted-target-detection.md](./story-03-model-assisted-target-detection.md) | — |
| HS-39-04 | Project-doc suggestion quality gate | backlog | [story-04-suggestion-quality-gate.md](./story-04-suggestion-quality-gate.md) | — |
| HS-39-05 | Pipeline depth telemetry | backlog | [story-05-pipeline-depth-telemetry.md](./story-05-pipeline-depth-telemetry.md) | — |
| HS-39-06 | Documentation | backlog | [story-06-documentation.md](./story-06-documentation.md) | — |
| HS-39-07 | Closeout + final-summary | backlog | [story-07-closeout.md](./story-07-closeout.md) | — |

## Where we are

**HS-39-02 done (2026-06-05).** Correction memory (session learning) shipped.
New `corrections.py` `CorrectionStore` (bounded ring, thread-safe, gist-only,
secret-rejected via the new public `looks_like_secret`) is owned by
`MeetingWebServer` and shared with the live `WebRuntime` (`server.dictation_corrections`),
exposed on `WebContext.corrections`. `POST/GET /api/dictation/corrections`
capture + list (route-table invariant updated 26→28). Consumption is a
**deterministic post-classify nudge**: `IntentRouter` reinforces/redirects to a
similar recent correction's *known* block (confidence floor 0.85, Jaccard
similarity ≥ 0.5); `target_profile.apply_target_correction` biases detection
(manual override always wins). All gated behind default-off `corrections_enabled`,
threaded through `assembly.build_pipeline`, the dry-run helper, and the live
`_maybe_run_dictation_pipeline`; empty/flag-off ⇒ byte-identical. 25 new tests
(store/intent/target/config/route+dry-run); suite 2157/15. **Next: HS-39-03**
model-assisted target detection.

**HS-39-01 done (2026-06-05).** Multi-pass rewriting shipped. `rewrite_passes`
(default 1, validated 1–5) on `DictationPipelineConfig`; `ProjectRewriter` now
loops draft → critique → refine via a new `_default_refine_prompt_builder`,
gating each extra pass on the projected pipeline budget
(`max_total_latency_ms`) and failing open to the best successful draft on a
refine failure/empty/over-budget result. New metadata keys
(`rewrite_passes_configured`/`rewrite_passes_run`/`rewrite_pass_ms`/
`rewrite_budget_skipped`) flow through the dry-run serializer unchanged.
`assembly.build_pipeline` constructs the rewriter with the configured passes +
budget. Default path byte-identical (5 new rewriter tests + 4 config tests);
suite 2132/15. **Next: HS-39-02** correction memory (session learning).

**Scaffolded (2026-06-05).** Recon done against the live code: the
dictation pipeline is a clean, modular `holdspeak/plugins/dictation/` package
(executor `pipeline.py`, `assembly.build_pipeline`, three built-in stages
`intent_router` / `kb_enricher` / `project_rewriter`, backend-agnostic
`runtime.py` with `mlx` / `llama_cpp` / `openai_compatible`), with the web
surface under `web/routes/dictation/` (intents/agent/project_docs/blocks/kb/
pipeline) and config at `holdspeak/config.py` (`DictationPipelineConfig`,
`LLMRuntimeConfig`). All seams the phase needs already exist:

- **Rewrite seam (HS-39-01):** `ProjectRewriter.run()` calls
  `runtime.rewrite(prompt, …)` once; a refine loop wraps that call —
  `rewrite_passes` is a new `DictationPipelineConfig` field, default 1.
- **Correction seam (HS-39-02):** the dry-run / web surface already round-trips
  intent + target; a session-scoped store on `WebRuntime` + a prompt nudge in
  `intent_router` / `target_profile` is additive.
- **Target seam (HS-39-03):** `target_profile.detect_active_target_profile()`
  returns a confidence; a sub-threshold LLM fallback slots in behind a flag.
- **Suggestion seam (HS-39-04):** `project_doc_suggestions.suggest_project_doc_update()`
  already validates path + content; a dedup/recurrence gate wraps it.
- **Telemetry seam (HS-39-05):** `PipelineRun.stage_results[i].elapsed_ms` is
  already captured per stage; `/api/dictation/readiness` is the surface.

**Pickup order:** HS-39-01 (multi-pass — the headline depth feature) →
HS-39-02 (correction memory — the learning feature) → HS-39-03/04 (quality,
independent) → HS-39-05 (telemetry, depends on 01/02 for the new fields) →
HS-39-06 (docs, after the surface is stable) → HS-39-07 (closeout). Keep the
pipeline **off by default** so the typing path stays byte-identical, and keep
the default suite free of any real LLM/network call (inject fake runtimes).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Multi-pass blows the latency budget on real hardware | Medium | `rewrite_passes` default 1; an extra pass is skipped when it would breach `max_total_latency_ms`; dry-run attributes per-pass latency | A warm 2-pass rewrite consistently exceeds the budget on the reference Mac |
| Correction memory degrades routing instead of helping | Medium | Off by default; bounded ring; session-scoped (no persistence); default path byte-identical; unit-tested that no-corrections ⇒ unchanged scores | Corrections measurably worsen classification on the dry-run set |
| Model-assisted detection adds latency / wrong guesses | Medium | Opt-in + only fires below the heuristic threshold; manual override always wins; degrades to the heuristic on any failure | The fallback overrides a correct heuristic or adds perceptible lag |
| Suggestion dedup suppresses genuinely new content | Low-Med | Conservative similarity gate + the existing explicit apply/dismiss; a suppressed suggestion is logged in the dry-run trace | A useful suggestion is silently dropped |
| Default behavior drifts (pipeline-off no longer byte-identical) | High if careless | Every feature gated behind a default-off flag; a standing "pipeline disabled ⇒ byte-identical" regression assertion | The typing path changes with the pipeline disabled |
| A real LLM/network call lands in the default suite | Medium | Inject fake runtimes/clients; real-endpoint runs opt-in + skipped in CI | CI makes a real `/v1/chat/completions` or model-load call |

## Decisions made (this phase)

- 2026-06-05 — **Direction = Dictation Copilot depth** — user pick (feature
  work) over Release/First-Run and Growth; then over Actuators III and
  Artifact→action bridges.
- 2026-06-05 — **Full 7-story phase** (multi-pass · correction memory ·
  model-assisted detection · suggestion quality gate · telemetry · docs ·
  closeout) — user pick over a lean 5-story cut.
- 2026-06-05 — **Correction memory is session-scoped + in-process only** (no DB,
  no persistence) — keeps the DIR-01 "stateless utterance" posture mostly
  intact, bounds blast radius, and avoids a secret-bearing on-disk store.
- 2026-06-05 (HS-39-01) — **Refine-pass failure fails open to the best draft**,
  not to raw input — a blip on an *extra* pass must never make multi-pass output
  worse than single-pass. Only a *first*-pass (draft) failure short-circuits to
  the stage input, as before.
- 2026-06-05 (HS-39-01) — **Budget gate projects the next pass at the last
  pass's cost** (`elapsed + last_pass_ms > budget` ⇒ skip) — simple,
  deterministic, and testable with an injected clock; no per-pass measurement
  gate.
- 2026-06-05 (HS-39-01) — **`rewrite_passes` capped at 5** — a typo can't fan
  out into a runaway per-utterance LLM loop.
- 2026-06-05 (HS-39-02) — **Correction nudge is a deterministic post-classify
  step, not a prompt hint** — keeps "no similar correction ⇒ byte-identical"
  exact and the nudge unit-testable with a fake runtime.
- 2026-06-05 (HS-39-02) — **Store hosted on `MeetingWebServer`, shared with
  `WebRuntime`** — the routes only see the server's `WebContext`; the live path
  reaches the same instance via `self.server.dictation_corrections`. One store
  per session; literal placement deviates from "on WebRuntime".
- 2026-06-05 (HS-39-02) — **Target corrections key on the utterance gist**, not
  a window/app signature — one matching mechanism; a hints-signature key is a
  later refinement if dogfood shows it's needed.

## Decisions deferred

- **Should correction memory ever persist across sessions?** — trigger: real
  dogfood (HS-39-07) shows the session-scoped store is too forgetful —
  default: stays in-process only; persistence is a DIR-02 candidate.
- ~~**Multi-pass critique prompt — generic vs target-profile-specific?**~~ —
  **resolved HS-39-01 (2026-06-05):** one generic self-critique/refine prompt
  (`_default_refine_prompt_builder`) that still carries the project + target
  directive (but drops the agent-reply lines to keep the model focused on
  improving the draft); injectable via the `refine_prompt_builder` constructor
  seam.
- **Telemetry persistence (quantiles across restarts)?** — trigger: HS-39-05 —
  default: in-memory ring only (mirrors the existing recent-runs buffer).
