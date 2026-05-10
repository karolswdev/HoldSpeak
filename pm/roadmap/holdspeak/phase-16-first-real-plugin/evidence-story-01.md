# HS-16-01 — Evidence

- **Status:** done (2026-05-10)
- **Story:** [story-01-mermaid-architecture-plugin.md](./story-01-mermaid-architecture-plugin.md)

## What landed

- `holdspeak/plugins/builtin.py` → `holdspeak/plugins/builtin/`
  package (preserves the public surface: `DeterministicPlugin`,
  `register_builtin_plugins`, `_BUILTIN_PLUGIN_DEFS`, plus the new
  `MermaidArchitecturePlugin` and `_extract_mermaid_block` helper).
- `holdspeak/plugins/builtin/mermaid_architecture.py` defines
  `MermaidArchitecturePlugin`:
  - `id="mermaid_architecture"`, `version="0.1.0"`,
    `kind="artifact_generator"`, `execution_mode="deferred"`,
    `required_capabilities=["llm"]`.
  - `__init__(intel_call=...)` — DI'd LLM call so unit tests don't
    need a real model. Default factory lazily constructs a
    `MeetingIntel` and caches it on the plugin instance.
  - `run(context)` reads `transcript`, `active_intents`, `tags`,
    `project_name`/`project`, builds a strict 2-message prompt,
    calls the intel callable, parses + validates one fenced
    ```mermaid block.
- `_extract_mermaid_block(text)` returns `(block_body, kind)` for
  the first valid fenced ```mermaid block. `kind` is one of
  `flowchart`, `graph`, `sequenceDiagram`, `classDiagram`,
  `erDiagram`, `stateDiagram` (canonicalised from the first
  non-empty line). Validates per-kind minimum structure (at least
  one connector + ≥ 2 distinct identifiers for `flowchart`/`graph`;
  at least one `participant` and one message for
  `sequenceDiagram`; etc.). Returns `None` on any failure.
- `register_builtin_plugins(host)` branches: `mermaid_architecture`
  → `MermaidArchitecturePlugin()`, all other twelve IDs continue to
  register as `DeterministicPlugin` stubs.

## Output shape contract

Success path:

```python
{
    "summary": "<one-line English summary>",
    "mermaid": "<inner Mermaid block, no fences>",
    "diagram_kind": "<flowchart|graph|sequenceDiagram|classDiagram|erDiagram|stateDiagram>",
    "confidence_hint": 1.0,
    "active_intents": ["<intent>", ...],
}
```

Failure path (no fence, malformed fence, unknown kind, structure
gate failed, intel call raised, empty transcript):

```python
{
    "summary": "<reason string>",
    "confidence_hint": 0.0,
    "active_intents": ["<intent>", ...],
    # `mermaid` key intentionally absent — HS-16-03's renderer
    # branches on its presence.
}
```

The `mermaid` value is the inner block body. HS-16-03's synthesis
splice will wrap it back in ```mermaid fences when rendering
`body_markdown`.

## Test results

```
$ /home/karol/.platformio/penv/bin/uv run --extra test pytest -q \
    tests/unit/test_mermaid_architecture_plugin.py
................                                                         [100%]
16 passed in 0.06s

$ /home/karol/.platformio/penv/bin/uv run --extra test pytest -q \
    tests/integration/test_mermaid_architecture_pipeline.py
.                                                                        [100%]
1 passed in 0.91s

$ /home/karol/.platformio/penv/bin/uv run --extra test pytest -q \
    --ignore=tests/e2e/test_metal.py
1569 passed, 5 skipped in 118.47s (0:01:58)
```

## Test counts

- Pre-story baseline (HEAD = `b96b39d` "phase 16 scaffold"): 1552
  passing.
- Post-story: 1569 passing. Net delta: +17 = 16 new unit cases
  (parametrize multiplies 7 functions to 16 cases) + 1 new
  integration case.
- 5 skipped — pre-existing skips for optional deps (scipy, llama-cpp
  with model files, mlx, etc.). Unchanged by this story.

## Pre-existing test that needed adjustment

`tests/unit/test_web_runtime.py::test_runtime_meeting_control_callbacks_are_wired`
asserted that every plugin run in a `route_preview` response had
status in `{"success", "deduped"}`. With HS-16-01,
`mermaid_architecture` declares `required_capabilities=["llm"]`;
the test fixture's `PluginHost` does not enable the `llm`
capability, so the plugin run now legitimately comes back as
`status="blocked"` (the host's documented behaviour for
capability-gated plugins). Loosened the assertion to accept
`{"success", "deduped", "blocked"}` with an inline comment
referencing HS-16-01. HS-16-02 is the story that wires
`enabled_capabilities={"llm"}` at the production-host
instantiation; in this fixture it remains intentionally absent
because the fixture has no LLM provider available.

## Out-of-scope (deferred to follow-up stories)

- Real LLM-call plumbing through `MeetingIntel` runs end-to-end in
  this story only via the DI'd stub. Real local/cloud calibration
  is HS-16-05.
- `enabled_capabilities` wiring at the host instantiation site
  belongs to HS-16-02. Until that ships, every running production
  configuration sees `mermaid_architecture` as `blocked` — which is
  the safest default state.
- `synthesize_meeting_artifacts` does not yet splice the
  `output["mermaid"]` value into `body_markdown`; HS-16-03 owns
  that branch. The artifact's `structured_json` carries
  `summary`, `plugin_id`, etc. but not the `mermaid` key yet.
- Web view still renders the body as raw markdown. HS-16-04 adds
  mermaid.js and the inline-SVG renderer.

## Files touched

- `holdspeak/plugins/builtin.py` — deleted (moved into package).
- `holdspeak/plugins/builtin/__init__.py` — created.
- `holdspeak/plugins/builtin/mermaid_architecture.py` — created.
- `tests/unit/test_mermaid_architecture_plugin.py` — created.
- `tests/integration/test_mermaid_architecture_pipeline.py` — created.
- `tests/unit/test_web_runtime.py` — one-line assertion loosened
  (see "Pre-existing test that needed adjustment").
- `pm/roadmap/holdspeak/phase-16-first-real-plugin/current-phase-status.md`
  — story row + "Last updated" + "Where we are" + exit-criteria
  checkboxes for the HS-16-01 lines.
- `pm/roadmap/holdspeak/phase-16-first-real-plugin/story-01-mermaid-architecture-plugin.md`
  — header status + acceptance-criteria checkboxes flipped.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
