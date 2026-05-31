# Phase 16 — First real synthesizer: `mermaid_architecture`

**Status:** paused 2026-05-31 (HS-16-01 shipped 2026-05-10; HS-16-02..05 remain backlog). Paused to reflect reality — work moved on to phases 17–24 with only 1/5 stories shipped, so the headline feature (diagrams visible end-to-end) is not yet wired. Resume to land HS-16-02 (LLM capability gate) onward; sequence to be decided relative to phases 25/26.

This phase is the first time HoldSpeak's plugin substrate produces a
real, LLM-backed analysis artifact. The host, router, deferred queue,
artifact persistence, and meeting-detail UI already exist (phases 1–13).
What's missing is a `run()` that does more than echo a transcript
snippet.

We pick `mermaid_architecture` (already registered as a stub in
`holdspeak/plugins/builtin.py:48`, already routed in the `architect`
profile and the `architecture` intent chain in
`holdspeak/plugins/router.py:25,32`, already mapped to
`artifact_type="diagram"` in `holdspeak/plugins/synthesis.py:16`)
because the substrate is already wired end-to-end for it; the only
gap is the plugin class itself, an artifact-type-aware body
renderer, and a Mermaid-capable web view.

The other twelve `DeterministicPlugin` stubs in `builtin.py` stay as
stubs. They get flipped to real implementations in follow-on phases
once the pattern this phase establishes is proven.

## Source canon (phase-scoped)

- `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — RFC. Will be reality-checked
  in HS-16-05 (this phase) so the doc stops claiming twelve plugins
  are real when only one is.
- `holdspeak/plugins/host.py` — `HostPlugin` Protocol + `PluginHost`
  (capability gates, deferred-queue, idempotency). The plugin built
  here conforms to that Protocol; no new contract.
- `holdspeak/plugins/router.py` — already routes
  `mermaid_architecture` for `architect` profile + `architecture`
  intent. No router changes needed in this phase.
- `holdspeak/plugins/synthesis.py` — already maps the plugin to
  `artifact_type="diagram"`. Gets the diagram-specific body renderer
  in HS-16-03.
- `holdspeak/intel.py` — existing local-llama-cpp + cloud OpenAI
  provider abstraction (`resolve_intel_provider`). The plugin uses it;
  no new provider stack.
- `holdspeak/web_server.py:2928` — artifact API endpoint, already
  exists. Mermaid renders in the web view (HS-16-04) without new API
  surface.

## Where to look first when this phase opens

- `pm/roadmap/holdspeak/phase-16-first-real-plugin/current-phase-status.md`
  — goal, scope, exit criteria.
- `holdspeak/plugins/builtin.py` — current stub registration.
  Replacement scope is HS-16-01.
- `holdspeak/intel.py:183` (`resolve_intel_provider`) — the LLM call
  shape the plugin will use.
- `web/src/` — the Astro source root for HS-16-04 (mermaid.js
  integration on the artifact-detail surface).
