# HS-16-03 — Diagram-aware artifact body in `synthesize_meeting_artifacts`

- **Project:** holdspeak
- **Phase:** 16
- **Status:** done
- **Depends on:** HS-16-01
- **Unblocks:** HS-16-04, HS-16-05
- **Owner:** unassigned

## Problem

`synthesize_meeting_artifacts` (`holdspeak/plugins/synthesis.py:107`)
builds a generic `body_markdown` for every artifact:

```
### {title}

{summary}

- Source windows: ...
- Source plugin runs: ...
```

For most artifact types that's fine (the body is a description of
what the plugin produced). For `artifact_type="diagram"` it is not:
the user wants to see the diagram, not a paragraph about it. The
`MermaidArchitecturePlugin.run()` output (HS-16-01) carries a
`mermaid` key with the actual fenced block; synthesis needs to
splice it into `body_markdown` so the web layer (HS-16-04) has
something to render.

## Scope

- **In:**
  - Edit `synthesize_meeting_artifacts` in
    `holdspeak/plugins/synthesis.py`. After the existing
    `body_markdown` is computed, branch:
    - If `artifact_type == "diagram"` AND
      `canonical.output.get("mermaid")` is a non-empty string,
      replace `body_markdown` with:
      ```
      ### {title}

      {summary}

      ```mermaid
      {mermaid}
      ```

      - Source windows: ...
      - Source plugin runs: ...
      ```
      The `mermaid` value is inserted verbatim — the plugin is
      responsible for producing valid Mermaid syntax; synthesis
      does not re-validate.
    - Otherwise, leave `body_markdown` unchanged (current
      behavior).
  - Also expose `mermaid` in the artifact's `structured_json`
    payload under a top-level `mermaid` key when present, so the
    web view can read either the markdown or the structured shape.
    Keep the existing `summary`, `plugin_id`, `plugin_run_ids`,
    `window_ids`, `active_intents`, `run_count`, `dedupe_hash`
    keys exactly as they are.
  - Unit test:
    `tests/unit/test_artifact_synthesis_diagram.py`. Cases:
    1. A fake plugin run shaped like HS-16-01's success output
       produces a body containing exactly one fenced ```mermaid
       block, and the structured_json has the `mermaid` key.
    2. A fake plugin run with `output["mermaid"]` absent (parse
       failure shape from HS-16-01) produces the legacy body —
       no fenced block — and `structured_json["mermaid"]` is
       absent.
    3. Regression — a fake plugin run for a non-diagram artifact
       type (e.g., `requirements_extractor`) produces a body
       byte-for-byte equivalent to what `synthesize_meeting_artifacts`
       produced before the change. (Capture the pre-change body
       once via the existing
       `tests/unit/test_artifact_synthesis*.py` fixtures and
       assert equality.)
  - No public API changes to `ArtifactDraft`,
    `ArtifactSourceRef`, `record_artifact`, or the persistence
    layer. The `body_markdown` is just a different string for
    one artifact type.

- **Out:**
  - Web-side rendering — HS-16-04.
  - Body templating for the other artifact types — those stay
    untouched.
  - A pluggable per-artifact-type renderer registry. We hardcode
    the diagram branch with a `# TODO` referencing the
    follow-on phase that flips the other twelve plugins; once
    we have multiple custom renderers we extract.
  - Re-rendering existing artifacts in the DB. New runs produce
    the new body; old runs keep their old body (greenfield
    discipline).

## Acceptance criteria

- [x] When a plugin run has
  `artifact_type=="diagram"` AND `output["mermaid"]` is set, the
  resulting `ArtifactDraft.body_markdown` contains exactly one
  fenced ```mermaid block.
- [x] When `output["mermaid"]` is absent, `body_markdown` is
  identical to the pre-change output for the same input.
- [x] `structured_json["mermaid"]` is present iff
  `output["mermaid"]` was present in the canonical run.
- [x] `tests/unit/test_artifact_synthesis_diagram.py` runs ≥ 3
  cases green. (3 cases.)
- [x] No regression: existing
  `tests/unit/test_artifact_synthesis*.py` and
  `tests/integration/test_artifact_synthesis_pipeline.py` stay
  green; non-diagram bodies byte-for-byte identical (asserted). Full
  suite 1902 passed.

## Test plan

- Unit:
  `uv run pytest -q tests/unit/test_artifact_synthesis_diagram.py
  tests/unit/test_artifact_synthesis.py
  tests/unit/test_artifact_synthesis_persist.py`.
- Integration:
  `uv run pytest -q tests/integration/test_artifact_synthesis_pipeline.py`.
- Manual: not required (HS-16-04 owns visual verification).

## Notes / open questions

- The "byte-for-byte unchanged for non-diagram types"
  acceptance is the load-bearing one. If keeping that exactly
  is too brittle (e.g., we accidentally changed the order of a
  bullet), we may need to re-baseline the existing tests. If
  that happens, document why in the evidence file and update
  the existing tests in the same commit.
- The `mermaid` value goes into both `body_markdown` (for
  human / markdown consumers) and `structured_json` (for
  programmatic consumers like the web view). Some redundancy,
  but keeping the markdown self-contained means the artifact
  remains rendering-ready if you `cat` it without the JSON.
- We don't lint or sanitize the `mermaid` value here.
  Mermaid.js renders untrusted input client-side; the plugin
  upstream validates structure (HS-16-01). If a security
  concern emerges (e.g., link injection in a label), we add a
  pass in HS-16-04's renderer.
