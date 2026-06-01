# Phase 16 — First Real Plugin (`mermaid_architecture`): Final Summary

**Opened:** 2026-05-08 (scaffolded) · first ship 2026-05-10 (HS-16-01).
**Closed:** 2026-06-01.
**Chunks shipped:** 5 / 5 (HS-16-01 … HS-16-05).

## Goal — was it met?

> Land the first real, LLM-backed analysis plugin on HoldSpeak's plugin
> substrate, end-to-end: meeting transcript → Mermaid diagram → reviewable
> artifact rendered as a live diagram in the web UI. Prove the plugin contract,
> deferred queue, capability gating, artifact synthesis, and web rendering
> compose for a real (not-stub) plugin.

**Met.** The full path is live: transcript → LLM (`resolve_intel_provider`) →
parsed/validated Mermaid → `diagram` artifact (`structured_json.mermaid` +
fenced body) → inline SVG in `/history`. Every substrate layer the goal named
(contract, deferred queue, `"llm"` capability gate, synthesis body, web render)
was exercised by a real plugin rather than a stub.

## Exit criteria (re-run against evidence)

- [x] Real `MermaidArchitecturePlugin` registered in place of the stub — HS-16-01 (`evidence-story-01.md`).
- [x] `test_mermaid_architecture_plugin.py` green (≥5 cases; 16 shipped) — HS-16-01.
- [x] `test_plugin_host_llm_capability.py` green, both branches — HS-16-02 (`evidence-story-02.md`, 8 cases).
- [x] `test_artifact_synthesis_diagram.py` green; non-diagram bodies byte-for-byte — HS-16-03 (`evidence-story-03.md`, 3 cases).
- [x] Integration pipeline: transcript → diagram artifact in DB — HS-16-01.
- [x] Manual: Mermaid renders as SVG, not raw text — HS-16-04 (`evidence-story-04.md`, real-Chrome screenshots).
- [x] RFC annotated with shipped/stub status + "Appendix A" — HS-16-05 (this commit).
- [x] No regressions: full sweep green (1902 passed, 13 skipped).
- [x] `final-summary.md` records calibration data — this file (below).

## Stories shipped

| ID | Story | Evidence |
|---|---|---|
| HS-16-01 | Real `mermaid_architecture` plugin (LLM call + parse + structured output) | evidence-story-01.md |
| HS-16-02 | LLM capability gate wired at host instantiation | evidence-story-02.md |
| HS-16-03 | Diagram-aware artifact body in `synthesize_meeting_artifacts` | evidence-story-03.md |
| HS-16-04 | Web: render `mermaid` artifacts as inline SVG via mermaid.js | evidence-story-04.md |
| HS-16-05 | RFC reality-check + phase exit (this summary) | — |

**Stories cut / deferred:** none.

## Calibration — `mermaid_architecture` parse-success

Light, post-hoc closeout baseline (3 transcripts × available configs × 3 runs
each). Raw output: `evidence/calibration.txt`. "Valid" = the plugin returned a
`mermaid` block whose first token is a known Mermaid diagram keyword.

| Config | heavy | mixed | low | avg runtime | avg confidence |
|---|---|---|---|---|---|
| **local Q6** — `.43:8080`, Qwen3.5-9B-UD-Q6_K_XL | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | ~1–3.6 s | 1.00 |
| **local Q4** — `127.0.0.1:8081`, Qwen3.5-9B-Q4_K_M | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | ~28–30 s | 0.00 |

**Reading:** on the **Q6** endpoint the plugin is reliable across all three
densities — 100% parse-success, sub-4s, max confidence. The **Q4** endpoint
fails every time **and** is ~10× slower: it's a reasoning-style build that emits
its chain-of-thought into `reasoning_content` and leaves the message `content`
empty until it exhausts `max_tokens`, so `_chat_completion_text` sees no fenced
block. This is a content-extraction mismatch, not a diagram-quality cliff —
hence `mermaid_architecture` stays **✅ shipped** (it's reliable on the configured
default), with the caveat: **prefer ≥Q6 / a non-reasoning build, or add
`reasoning_content` fallback extraction (phase 17)** before recommending smaller
or reasoning-style local models.

**Configs not tested:** cloud (real OpenAI / `gpt-5-mini`) — no API key on this
remote machine; documented gap, not a blocker (the self-hosted OpenAI-compatible
path is the configured default and is exercised above).

## Surprises and lessons

- **The `$OPENAI_API_KEY` foot-gun.** `resolve_intel_provider("cloud", …)`
  required a key even for a self-hosted, key-less llama.cpp endpoint, which would
  have left `mermaid_architecture` permanently blocked on the actual dev setup.
  Fixed mid-phase (commit `7f03008`) so a custom `base_url` doesn't require a key.
- **Quant matters for structured output.** The Q6 endpoint produced clean,
  parseable Mermaid; the Q4 endpoint leaks chain-of-thought into the message
  `content` (empty `content` + populated `reasoning_content`), which depresses
  parse-success. See the calibration table. Recommendation: prefer ≥Q6 (or a
  reasoning-aware extraction) for diagram quality; revisit content extraction in
  phase 17 if the cheaper quant must be supported.
- **`?raw` script injection breaks bare imports.** `history-app.js` is run via
  `new Function(rawString)`, so a dynamic `import('mermaid')` inside it isn't
  bundler-resolvable. The fix — a `window.__loadMermaid` code-split loader in the
  real module script — is the pattern any future lazy npm dep on these pages must
  follow.
- **Looking at the render caught a real bug.** mermaid injects its own "syntax
  error" bomb SVG into the DOM on failure even when the throw is caught;
  `suppressErrorRendering: true` was needed. A pure unit test would have missed it.

## Handoff to phase 17

- **What's now possible:** the end-to-end pattern (LLM call → parse/validate →
  structured output → synthesis body → web render) is proven on a real plugin.
  The remaining twelve `_BUILTIN_PLUGIN_DEFS` stubs can each be flipped to real
  by re-using it — no new substrate work.
- **Canon changed:** `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` now carries a
  reality-status table for all thirteen plugins and **Appendix A** ("what
  'shipped' means"). Read it first; it is the bar for phase 17.
- **Read first:** this summary, then `evidence-story-0{1..4}.md`, then the
  `mermaid_architecture.py` plugin as the reference implementation.
- **Open quality question for 17:** content extraction on reasoning-style models
  (the Q4 leak) — decide whether to read `reasoning_content` as a fallback or to
  recommend ≥Q6 / cloud for artifact plugins.

## Asset / test posture

- Net-new code: the real plugin (`holdspeak/plugins/builtin/mermaid_architecture.py`),
  the capability helper (`resolve_llm_capability` in `intel.py`), the diagram
  branch in `synthesis.py`, and the web render path (`history.astro` +
  `history-app.js` + pinned `mermaid@11.15.0`).
- Tests added across the phase: ~28 cases (16 plugin unit + 1 pipeline integration
  [HS-16-01], 8 capability [HS-16-02], 3 synthesis-diagram [HS-16-03]) plus the
  extended history bundle-marker assertions [HS-16-04].
- Full suite at close: **1902 passed, 13 skipped** (`--ignore=tests/e2e/test_metal.py`).
