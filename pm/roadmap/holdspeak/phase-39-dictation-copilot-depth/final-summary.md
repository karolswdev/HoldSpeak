# Phase 39 — Final Summary

- **Phase opened:** 2026-06-05
- **Phase closed:** 2026-06-05
- **Chunks shipped:** 9 (grew 7 → 9 mid-flight on user requests)

## Goal — was it met?

Original goal:

> Phase 18 built the intelligent-typing substrate; Phase 19 made it trustworthy
> for daily use. Phase 39 makes the copilot **deeper and self-improving**: the
> rewrite gets a refinement pass, the pipeline **learns from corrections** within
> a session, target detection gains a model-assisted fallback, and project-doc
> suggestions gain a quality gate so they stop repeating what's already written —
> all made observable. The DIR-01 invariant is unchanged: **off by default;
> always typeable; pipeline-disabled byte-identical; no real LLM/network call in
> the default suite.**

**Yes.** All four depth features shipped, opt-in and default-byte-identical, and
were proven firing together against a real LLM endpoint:

- **Multi-pass rewriting** — [evidence-01](./evidence-story-01.md)
- **Correction memory** — [evidence-02](./evidence-story-02.md)
- **Model-assisted target detection** — [evidence-03](./evidence-story-03.md)
- **Suggestion quality gate** — [evidence-04](./evidence-story-04.md)
- **Depth telemetry** — [evidence-05](./evidence-story-05.md)
- **Documentation** — [evidence-06](./evidence-story-06.md)
- **Real `.43` e2e** — [evidence-08](./evidence-story-08.md)
- **All-features showcase + public doc + Mermaid** — [evidence-09](./evidence-story-09.md)

The headline before/after (same dictation, Phase-18/19 single-pass vs Phase-39
multi-pass) is in [`evidence/before_after.md`](./evidence/before_after.md): the
depth pass refines and **tightens** the task (1483 → 1430 chars) rather than
bloating it. The all-features run (rough 446-char ramble → a precise,
project-grounded coding task with the correction nudge, model-assisted target,
and KB injection all firing) is in
[`evidence/dictation_enrichment_demo.txt`](./evidence/dictation_enrichment_demo.txt).

## Exit criteria — final state

- [x] `ProjectRewriter` runs `rewrite_passes` (default 1, byte-identical),
      latency-budget-gated, fail-open-to-best-draft — [evidence-01](./evidence-story-01.md).
- [x] Bounded session correction store nudges routing; default byte-identical;
      no secrets, no DB — [evidence-02](./evidence-story-02.md).
- [x] Opt-in LLM target fallback below the heuristic threshold; override wins;
      off ⇒ byte-identical — [evidence-03](./evidence-story-03.md).
- [x] Suggestion dedup vs the existing doc + dismissal-no-recur + consolidation
      helper — [evidence-04](./evidence-story-04.md).
- [x] `GET /api/dictation/readiness` `depth` block: per-stage p50/p95 + budget
      guidance + multi-pass + correction state — [evidence-05](./evidence-story-05.md).
- [x] `docs/INTELLIGENT_TYPING_GUIDE.md` documents every knob; doc-guards green
      — [evidence-06](./evidence-story-06.md).
- [x] Real spoken→enriched e2e over a `.hs` fixture, gated/auto-skip, passing
      live on `.43` — [evidence-08](./evidence-story-08.md).
- [x] `.43` dogfood + before/after captured; `final-summary.md`; README → done
      — this file + `evidence/before_after.md`.
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout
      (closed at **2186 passed, 16 skipped**); pipeline-disabled byte-identical;
      no new default LLM/network call.

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| HS-39-01 | Multi-pass rewriting | feef203 | 2026-06-05 |
| HS-39-02 | Correction memory (session learning) | ad0d6fa | 2026-06-05 |
| HS-39-03 | Model-assisted target detection | 3c4d9de | 2026-06-05 |
| HS-39-08 | Real spoken→enriched dictation e2e + demo | 0ff7c3f | 2026-06-05 |
| HS-39-09 | Dictation copilot showcase (all features + doc + Mermaid) | 736e22b | 2026-06-05 |
| HS-39-04 | Project-doc suggestion quality gate | 70f2bf5 | 2026-06-05 |
| HS-39-05 | Pipeline depth telemetry | 1c76b41 | 2026-06-05 |
| HS-39-06 | Documentation | 71e9cd0 | 2026-06-05 |
| HS-39-07 | Closeout + final-summary | (this commit) | 2026-06-05 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | Consolidation UI wiring | The `consolidate_suggestions` helper is shipped + tested; the live store holds one suggestion per project, so accumulate-then-fold needs a list-shaped store + a control | Phase 40 / DIR-02 candidate |
| — | Decode-time enum constraint for model-assisted target | The runtime's constrained `classify` is block-shaped; the fallback validates the enum at parse and degrades — decode-time constraint is a refinement | DIR-02 candidate |
| — | Cross-session persistent correction memory | Kept in-process/session-scoped by design | DIR-02, gated on dogfood showing it's too forgetful |

## Surprises and lessons

- **The per-pipeline ring buffer resets every `build_pipeline`.** Both the
  dry-run and live paths rebuild the pipeline per utterance, so DIR-F-009's ring
  never accumulates. HS-39-05 added a session telemetry store fed via `on_run` —
  budget that pattern (server-hosted session store + `on_run`) for any
  cross-utterance dictation state.
- **Correction memory makes routing robust even when the classifier fails.** The
  openai-compatible `classify` isn't constrained-decoded, so it routinely
  returns un-parseable JSON on the homelab endpoint — and the post-classify
  correction nudge rescued routing anyway. A genuinely useful emergent property,
  surfaced in the demo panel.
- **Multi-pass tightens, it doesn't bloat.** The before/after shows the refine
  pass producing a *shorter*, cleaner task — the value is refinement, not length.
- **PMO hook discipline paid off.** Trying to amend HS-39-08's shipped evidence
  was blocked by the orphan-evidence check; splitting the all-features showcase
  into HS-39-09 was the correct, honest move (phase grew 8 → 9).

## Handoff to Phase 40

- **What's now available:** an opt-in, observable, self-improving dictation
  copilot (multi-pass · session memory · model-assisted target · suggestion
  quality gate · depth telemetry), a reusable `scripts/dictation_enrichment_demo.py`,
  a gated real-endpoint e2e (`tests/e2e/test_dictation_enrichment_e2e.py`), a
  `ledgerline` fixture project, and a public showcase doc.
- **Contract/canon changes:** `DictationPipelineConfig` gained `rewrite_passes`,
  `corrections_enabled`, `target_detect_llm_enabled`, `target_detect_llm_below`;
  `BuildResult` gained `runtime`; `WebContext` gained `corrections` + `telemetry`;
  new routes `GET/POST /api/dictation/corrections` and the readiness `depth` block.
- **Read first:** `docs/DICTATION_COPILOT.md`, `docs/INTELLIGENT_TYPING_GUIDE.md`
  §10, and this phase's `current-phase-status.md`.
- **Phase-40 candidates (user picks):** DIR-02 (new backends / cloud router /
  persistent cross-session memory / consolidation UI / decode-time enum
  constraint / a self-hosted CI runner for the gated e2e), **or** pivot to the
  long-deferred **Release & Dogfood** / **Growth** directions.

## Final asset / test posture

- Full suite: **2186 passed, 16 skipped** (`--ignore=tests/e2e/test_metal.py`).
- New dictation tests this phase: multi-pass (5+4) · corrections (9+5+4+2) ·
  model-assisted (8+2) · suggestion gate (8+2) · telemetry (5+3+1) · the gated
  real-endpoint e2e (all-features assertions).
- Default pipeline-off path **byte-identical** to pre-Phase-39; the default suite
  makes **no real LLM/network call** (all fakes); the real e2e auto-skips in
  hosted CI.
- New config knobs all **off by default**.
