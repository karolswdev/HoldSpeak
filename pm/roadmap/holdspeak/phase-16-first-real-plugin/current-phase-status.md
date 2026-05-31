# Phase 16 — First real synthesizer: `mermaid_architecture`

**Last updated:** 2026-05-10 (HS-16-01 shipped — real `MermaidArchitecturePlugin` is live; HS-16-02..05 still pending).

## Goal

Land the first real, LLM-backed analysis plugin on HoldSpeak's plugin
substrate. The product outcome: when a meeting has architecture-flavored
content (or the user picks the `architect` profile), HoldSpeak generates
a Mermaid component / dataflow diagram as a reviewable artifact in the
meeting-detail UI, rendered as a live diagram (not just a code block).

The substrate goal: prove that the plugin contract, deferred queue,
capability gating, artifact synthesis, and web rendering compose
end-to-end for a real (not-stub) plugin. Once that's proven, the
remaining twelve stubs become a follow-on phase that re-uses this
pattern with no new substrate work.

## Scope

- **In:**
  - Real `MermaidArchitecturePlugin` class replacing the
    `DeterministicPlugin` stub for the `mermaid_architecture` plugin
    id. Conforms to the existing `HostPlugin` Protocol; declares
    `kind="artifact_generator"`, `execution_mode="deferred"`,
    `required_capabilities=["llm"]`.
  - LLM call via `holdspeak.intel.resolve_intel_provider` with a
    strict prompt: produce one fenced ```mermaid block plus a
    one-line summary; the plugin parses + validates the block.
  - Capability gate wiring at the `PluginHost` instantiation site so
    `"llm"` is added to `enabled_capabilities` iff an intel provider
    resolves successfully. On systems without an LLM the plugin is
    cleanly blocked (`status="blocked"`), not crashed.
  - Diagram-aware body rendering in
    `synthesize_meeting_artifacts`: when `artifact_type == "diagram"`
    and `output["mermaid"]` is present, the artifact's `body_markdown`
    contains a fenced ```mermaid block (plus title, summary, lineage
    footer). Other artifact types unchanged.
  - Mermaid.js integrated into the web bundle (`web/src/`) so artifact
    detail surfaces render the diagram inline rather than showing
    raw fenced text.
  - Tests (unit + integration) covering: success path, LLM-returns-
    garbage path, LLM-provider-missing path, deferred-queue path,
    end-to-end transcript-to-rendered-artifact.
  - `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` reality-check: mark
    `mermaid_architecture` as ✅ shipped, mark the other twelve
    plugins as ⚠️ stubs (DeterministicPlugin), add a one-paragraph
    appendix on "what 'shipped' means" in this RFC.

- **Out:**
  - Real `run()` for the other twelve stub plugins
    (`requirements_extractor`, `adr_drafter`,
    `action_owner_enforcer`, `milestone_planner`, etc.). Phase 17+.
    They stay as `DeterministicPlugin` stubs.
  - New plugin contracts, new artifact types, new persistence
    schema, new router rules. None needed; the substrate is wired.
  - "Plugin SDK" / external-plugin loading. RFC §"Phase 4" — out of
    scope for this phase.
  - Diagram editing in the web UI (read-only render only).
  - Multi-diagram outputs from a single plugin run. One diagram per
    run; if the LLM produces multiple fenced blocks, take the first
    valid one and ignore the rest.
  - Live-meeting hook (running the plugin during an active meeting
    on every intent transition). The plugin runs against
    saved-meeting transcripts only this phase. Live-meeting trigger
    is a separate decision once we see real latency / cost numbers.
  - Cross-network / AIPI-Lite-specific work — phase 15 owns that
    surface and is independent.

## Exit criteria (evidence required)

- [x] `holdspeak/plugins/builtin/mermaid_architecture.py` exists; the
  class conforms structurally to `HostPlugin` and is registered by
  `register_builtin_plugins` in place of the `DeterministicPlugin`
  stub. (HS-16-01, 2026-05-10)
- [x] `uv run pytest -q tests/unit/test_mermaid_architecture_plugin.py`
  green, ≥ 5 cases (success / parse-failure / provider-raises /
  output-shape / version+kind+capabilities). (HS-16-01: 16 cases
  green via parametrize; see evidence-story-01.md.)
- [ ] `uv run pytest -q tests/unit/test_plugin_host_llm_capability.py`
  green, both branches (provider-resolved → llm capability enabled;
  provider-missing → plugin blocked).
- [ ] `uv run pytest -q tests/unit/test_artifact_synthesis_diagram.py`
  green: a fake plugin run with `output["mermaid"]` produces a
  body containing exactly one fenced ```mermaid block; other
  artifact types' bodies are byte-for-byte unchanged.
- [x] `uv run pytest -q tests/integration/test_mermaid_architecture_pipeline.py`
  green: transcript with architecture cues → dispatch → run →
  synthesize → DB has an artifact with `artifact_type="diagram"`
  and a valid mermaid body. (HS-16-01, 1 case green; the body's
  fenced ```mermaid block is HS-16-03's responsibility — this test
  asserts artifact existence + type + plugin_id only.)
- [ ] Manual: open the meeting-detail page for that test artifact;
  the mermaid block renders as an SVG diagram, not raw text.
  Screenshot in HS-16-04's evidence file.
- [ ] `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` updated: §"Initial
  Built-In Plugins" annotated with shipped/stub status; appendix on
  "what 'shipped' means" added.
- [ ] No regressions: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  green at ≥ phase-14 baseline.
- [ ] `final-summary.md` records the LLM-quality calibration data
  (which models were tested, parse-failure rate observed) so phase
  17 has a baseline.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-16-01 | Real `mermaid_architecture` plugin (LLM call + parse + structured output) | done | [story-01-mermaid-architecture-plugin.md](./story-01-mermaid-architecture-plugin.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-16-02 | LLM capability gate wired at host instantiation | backlog | [story-02-llm-capability-gate.md](./story-02-llm-capability-gate.md) | — |
| HS-16-03 | Diagram-aware artifact body in `synthesize_meeting_artifacts` | backlog | [story-03-diagram-artifact-rendering.md](./story-03-diagram-artifact-rendering.md) | — |
| HS-16-04 | Web: render `mermaid` artifacts as inline SVG via mermaid.js | backlog | [story-04-web-mermaid-rendering.md](./story-04-web-mermaid-rendering.md) | — |
| HS-16-05 | RFC reality-check + phase exit (DoD, calibration, final summary) | backlog | [story-05-rfc-reality-check.md](./story-05-rfc-reality-check.md) | — |

## Where we are

**Paused 2026-05-31.** Only HS-16-01 of 5 stories shipped; work then moved on to
phases 17–24, leaving this phase open in name only. Critically, without HS-16-02
the `mermaid_architecture` plugin is `blocked` even where an LLM is available, so
the user-visible feature (a rendered diagram) does not yet work end-to-end. The
index was corrected from `in-progress` to `paused` to stop implying two phases
were active at once. Resume after Phase 25/26 or interleave by explicit decision;
the pickup below is unchanged.

HS-16-01 shipped 2026-05-10. `holdspeak/plugins/builtin.py` is now a
package; `holdspeak/plugins/builtin/mermaid_architecture.py` defines
the real `MermaidArchitecturePlugin` (LLM-backed, deferred,
`required_capabilities=["llm"]`). `register_builtin_plugins` now
returns the real class for `mermaid_architecture` and keeps the
twelve siblings on `DeterministicPlugin`. Unit + integration tests
landed; full regression sweep green at 1569 passing (was 1552
pre-story; +16 unit cases + 1 integration). One pre-existing
assertion in `tests/unit/test_web_runtime.py::
test_runtime_meeting_control_callbacks_are_wired` was loosened to
accept `blocked` alongside `success`/`deduped` — `blocked` is the
correct outcome when the plugin's `llm` capability isn't enabled
in a fixture, and HS-16-02 is the story that wires the capability
on at runtime.

Pickup: HS-16-02 — capability gate at `PluginHost(...)`
instantiation. Without it, `mermaid_architecture` is `blocked` in
real runtime configs that have a working LLM available, which
defeats the point of HS-16-01. After HS-16-02 the diagram artifact
will appear in the DB as a `diagram` artifact whose
`body_markdown` is still the generic synthesis body (HS-16-03's
job to splice the fenced block in), and the web view still shows
raw fenced text (HS-16-04's job).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| LLM output quality is unreliable on local models — small (7B) models produce broken Mermaid syntax often enough that the artifact's `confidence_hint` averages low and the user sees `needs_review` more than `draft` | medium | Strict prompt + post-hoc validation (reject if no fenced ```mermaid block, reject if < 2 nodes); calibrate against three model sizes (7B / 9B / 14B) and document in `final-summary.md`. Cloud provider as the recommended path; local as best-effort. | If parse-failure rate exceeds 40% on the calibration meetings on 9B+, demote `mermaid_architecture` to cloud-only and document. |
| Mermaid.js bundle size bloats the web build noticeably | low | Lazy-load mermaid.js only on artifact-detail routes that actually have a diagram artifact; do not include in the home / dictation bundles. | If gzip'd web bundle grows by > 80 KB after the integration, switch to a CDN script tag with SRI. |
| The deferred-queue path doesn't surface back to the user — they generate diagrams but never see when they're ready | medium | Existing artifact API + meeting-detail page already polls; verify in HS-16-01's integration test that a freshly-queued run becomes visible after `process_next_deferred_run`. | If polling cadence is wrong / deferred runs sit invisible, add a runtime-status counter and / or a manual "process queue" button (separate story). |
| Synthesis change breaks other artifact types' bodies (regression on `requirements`, `action_items`, etc.) | low | The change is a strict `if artifact_type == "diagram" and output["mermaid"]:` branch; default branch is byte-for-byte unchanged. Lock that with a test that diffs the body for a non-diagram artifact pre/post change. | If any existing artifact body changes shape, revert to the new branch only. |
| Cloud LLM cost surprise — `mermaid_architecture` runs on every meeting that touches the architect profile or architecture intent | low | Existing intel-queue + idempotency gate prevents re-runs of the same `(meeting_id, window_id, plugin_id, transcript_hash)`. Confidence gate plus deferred-queue means it doesn't fire on every transcript chunk. | If a single meeting's plugin runs exceed 10 cloud calls, gate the plugin behind an explicit user trigger ("Generate diagram") rather than auto-run. |

## Decisions made (this phase)

- 2026-05-08 — **Scope is one plugin, not all twelve.** Tight, demoable, validates the substrate end-to-end. The other twelve stubs flip in a follow-on phase. — author: PMO + agent.
- 2026-05-08 — **Slot as phase 16 (after phase 15).** Phase 14's exit explicitly handed off to phase 15 (cross-network); reversing that without a new trigger would be churn. — author: PMO + agent.
- 2026-05-08 — **`mermaid_architecture` over `adr_drafter` as the first.** Mermaid output is visually demoable in seconds; ADR is text-on-text and harder to "look at this!" — author: PMO + agent.
- 2026-05-08 — **`execution_mode="deferred"` from day one.** LLM calls are heavy and the deferred queue already exists. Inline execution (cheap-LLM, low-latency) can be revisited later if needed. — author: agent.
- 2026-05-08 — **Saved-meeting only this phase, not live-meeting hooks.** Real LLM latency + cost numbers should land before deciding whether to wire it into the meeting loop. — author: agent.

## Decisions deferred

- **Which LLM providers to officially recommend** — defer to HS-16-05's calibration. Trigger to revisit: HS-16-01 + HS-16-02 land and we have real parse-failure rates from at least three model sizes. Default if no decision: README documents both `local` and `cloud`, recommends `cloud` for diagram quality.
- **Auto-run vs explicit-trigger** — defer until the deferred-queue path proves out. Trigger: real users (the user) running real meetings and either wanting more diagrams or being surprised by them. Default: auto-run via the existing intent-routed pipeline.
- **Live-meeting checkpoint hook** — phase 17+. Trigger: the phase-16 substrate ships and the parse-failure rate is low enough that running the plugin on every active intent transition wouldn't drown the user in `needs_review` noise.
- **Whether to flip `requirements_extractor` next, `adr_drafter` next, or all twelve as a batch** — phase 17 plan. Trigger: HS-16-05 closes and we have an honest baseline of how long "make one stub real" takes. Default: pick the next one with the highest ratio of (user value) / (LLM-quality risk).
