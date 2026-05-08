# HS-16-01 — Real `mermaid_architecture` plugin (LLM call + parse + structured output)

- **Project:** holdspeak
- **Phase:** 16
- **Status:** ready
- **Depends on:** none
- **Unblocks:** HS-16-02, HS-16-03, HS-16-04, HS-16-05
- **Owner:** unassigned

## Problem

`mermaid_architecture` is registered as a `DeterministicPlugin` stub
(`holdspeak/plugins/builtin.py:48`) whose `run()` returns a snippet of
the input transcript. It is already routed by the `architect` profile
and the `architecture` intent
(`holdspeak/plugins/router.py:25,32`) and already maps to
`artifact_type="diagram"` in synthesis
(`holdspeak/plugins/synthesis.py:16`). The only thing missing for the
plugin to be real is a `run()` that calls an LLM, asks for a
component / dataflow diagram, parses + validates a single fenced
```mermaid block, and returns a structured output the existing
synthesis layer can consume.

This story builds the plugin class, the parse logic, and the unit +
integration tests. HS-16-02 (capability gate) and HS-16-03 (synthesis
body rendering) each ship under separate stories so the diff stays
focused.

## Scope

- **In:**
  - Convert `holdspeak/plugins/builtin.py` to a package
    `holdspeak/plugins/builtin/` with `__init__.py` re-exporting the
    existing public surface (`DeterministicPlugin`,
    `register_builtin_plugins`). Keep all existing imports working
    via the re-exports — do not break the existing
    `from .builtin import DeterministicPlugin, register_builtin_plugins`
    in `holdspeak/plugins/__init__.py`.
  - New file
    `holdspeak/plugins/builtin/mermaid_architecture.py` defining
    `MermaidArchitecturePlugin` with:
    - `id = "mermaid_architecture"`
    - `version = "0.1.0"`
    - `kind = "artifact_generator"`
    - `execution_mode = "deferred"`
    - `required_capabilities = ["llm"]`
    - `run(self, context: dict) -> dict` — reads
      `context["transcript"]` (and `active_intents`, `tags`,
      project metadata if present), builds a strict prompt asking
      for one fenced ```mermaid block plus a one-line summary,
      calls `holdspeak.intel.resolve_intel_provider(...)`, parses
      the response.
  - Parser:
    `_extract_mermaid_block(text: str) -> tuple[str, str] | None`.
    Returns `(diagram_text, diagram_kind)` for the first valid
    fenced ```mermaid block where `diagram_kind` is one of
    `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`, `erDiagram`,
    `stateDiagram` (extracted from the block's first non-empty line).
    Validates that the block has at least 2 nodes — for `flowchart` /
    `graph`, regex on `\b\w+\s*-->` and friends; for `sequenceDiagram`,
    at least one `participant` and one message line. Returns `None`
    on failure.
  - On parse success, `run()` returns
    `{"summary": str, "mermaid": str, "diagram_kind": str,
      "confidence_hint": float, "active_intents": list[str]}`
    where `confidence_hint` reflects parse confidence (1.0 if the
    block is well-formed, 0.7 if it parsed but had warnings).
  - On parse failure (no fenced block, malformed block, or LLM
    raised), `run()` returns
    `{"summary": "<reason>", "confidence_hint": 0.0,
      "active_intents": [...]}` — note the absence of the `mermaid`
    key. This is the contract HS-16-03's renderer keys off.
  - Registration: in
    `holdspeak/plugins/builtin/__init__.py`'s
    `register_builtin_plugins(host)`, when iterating
    `_BUILTIN_PLUGIN_DEFS`, branch: for
    `id == "mermaid_architecture"` register
    `MermaidArchitecturePlugin()`; for the other twelve, keep
    `DeterministicPlugin(id=..., kind=...)` as today.
  - Unit tests: new
    `tests/unit/test_mermaid_architecture_plugin.py` covering:
    1. Success path — mock `resolve_intel_provider` returns a
       known fenced ```mermaid block; `run()` returns the expected
       shape with `confidence_hint == 1.0`.
    2. Parse failure — provider returns text with no fenced block;
       `run()` returns the failure shape (`mermaid` key absent,
       `confidence_hint == 0.0`).
    3. Provider raises — `resolve_intel_provider` raises
       `MeetingIntelError`; `run()` catches and returns the
       failure shape (no host-level uncaught exception).
    4. Plugin attributes are correct (`id`, `version`, `kind`,
       `execution_mode`, `required_capabilities`).
    5. The plugin is registered in `register_builtin_plugins` —
       verify via `host.list_plugins()` that
       `"mermaid_architecture"` is present and is a
       `MermaidArchitecturePlugin` (`isinstance` check), not a
       `DeterministicPlugin`.
  - Integration test:
    `tests/integration/test_mermaid_architecture_pipeline.py`
    — runs end-to-end: build a `MeetingDatabase`-backed test
    fixture, dispatch a transcript with architecture cues, allow
    the deferred queue to drain (`host.process_next_deferred_run`),
    synthesize artifacts, assert the resulting `Artifact` has
    `artifact_type == "diagram"`, `structured_json["plugin_id"]
    == "mermaid_architecture"`, `confidence > 0.5` (synthesis
    averages confidence_hints; with our success path that yields
    1.0). The synthesis body assertion lives in HS-16-03; here we
    just assert artifact existence.
  - Mock the LLM via dependency injection in the plugin's
    constructor: `MermaidArchitecturePlugin(intel_provider=...)`.
    Default-construct from `resolve_intel_provider()` lazily on
    first call so tests can pass a stub.

- **Out:**
  - Capability gate at host instantiation — HS-16-02.
  - Diagram-aware artifact body rendering — HS-16-03.
  - Web mermaid rendering — HS-16-04.
  - Updates to `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — HS-16-05.
  - Real LLM calibration data (parse-failure rate by model size) —
    HS-16-05 collects it.
  - Multi-diagram outputs (more than one fenced block per run).
  - Diagram quality / nicer prompts — once the plumbing works, the
    prompt can be iterated separately.

## Acceptance criteria

- [ ] `holdspeak/plugins/builtin/` is a package; existing imports
  (`from holdspeak.plugins import register_builtin_plugins,
  DeterministicPlugin`) still work — proven by the existing test
  suite still being green after the package conversion.
- [ ] `holdspeak/plugins/builtin/mermaid_architecture.py` exports
  `MermaidArchitecturePlugin` with the documented attributes.
- [ ] `register_builtin_plugins(host)` registers
  `MermaidArchitecturePlugin` for `mermaid_architecture`;
  `host.get_plugin("mermaid_architecture")` returns a
  `MermaidArchitecturePlugin`, not a `DeterministicPlugin`.
- [ ] On parse success, `run()` output has keys exactly
  `{"summary", "mermaid", "diagram_kind", "confidence_hint",
   "active_intents"}` and the `mermaid` value contains a fenced
  block.
- [ ] On parse failure, `run()` output has `confidence_hint == 0.0`
  and the `mermaid` key is absent.
- [ ] `tests/unit/test_mermaid_architecture_plugin.py` runs ≥ 5
  cases green.
- [ ] `tests/integration/test_mermaid_architecture_pipeline.py` runs
  green and asserts a `diagram` artifact lands in the DB with
  `plugin_id == "mermaid_architecture"`.
- [ ] No regressions: existing
  `tests/unit/test_plugin_host*.py` and
  `tests/integration/test_artifact_synthesis_pipeline.py` stay
  green.

## Test plan

- Unit:
  `uv run pytest -q tests/unit/test_mermaid_architecture_plugin.py`.
- Integration:
  `uv run pytest -q tests/integration/test_mermaid_architecture_pipeline.py`.
- Regression sweep:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` — must stay
  at the phase-14 baseline counts or improve.
- Manual: not required for this story (HS-16-04 owns the visual
  manual check).

## Notes / open questions

- The plugin's `run()` has to be safe to call from the deferred
  queue's worker thread. `resolve_intel_provider` is already called
  from threads in the existing meeting-intel path, so this should
  be fine, but verify the local-llama-cpp path is not shared mutable
  state between concurrent runs. If it is, document and serialize
  via the existing dispatch lock.
- Prompt is intentionally simple in this story: "Given this meeting
  transcript and these tags, produce a single fenced ```mermaid
  block (component, dataflow, or sequence diagram) plus a one-line
  English summary on the line above the block." Prompt iteration is
  out of scope; HS-16-05 calibrates and documents.
- `_extract_mermaid_block` is regex-based, not a real Mermaid parser.
  We're checking "is this plausibly a Mermaid block with structure"
  not "is this valid Mermaid." The web view (HS-16-04) does the
  real validation by rendering with `mermaid.js`; if it fails to
  render we just show the fenced text with a warning, which the
  artifact's `needs_review` status already implies.
- Idempotency: the host's existing
  `build_idempotency_key(meeting_id, window_id, plugin_id,
  transcript_hash)` already prevents re-runs. No extra dedup
  needed in the plugin.
