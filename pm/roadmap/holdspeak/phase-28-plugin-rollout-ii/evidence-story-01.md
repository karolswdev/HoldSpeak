# HS-28-01 Evidence — Synthesis per-type renderer registry

**Date:** 2026-06-01.
**Story:** [story-01-renderer-registry.md](./story-01-renderer-registry.md).

## What shipped

`holdspeak/plugins/synthesis.py` — replaced the hand-branched body chain
(`if mermaid / elif action_items / elif decisions / elif requirements / else`)
plus its parallel `structured_json`-key `if`s with a **renderer registry**:

- `_RenderContext(output)` — the canonical plugin output handed to a renderer.
- `_compose_body(title, summary, source_lines, block)` — the single shared body
  template. `block=None` → the legacy default body; a non-empty block →
  `### title / summary / block / source_lines`. Both forms are byte-for-byte the
  pre-registry output.
- Four renderers (`_render_diagram`, `_render_action_items`, `_render_decisions`,
  `_render_requirements`), each returning `(inner_block, extra_structured_keys)`
  or `None` to fall back. Logic ported verbatim (same `isinstance`/non-empty
  guards, same `_action_item_line` / `_decision_body` / `_requirements_body`
  calls, same key-insertion order for decisions/open_questions).
- `_ARTIFACT_RENDERERS: dict[str, renderer]` keyed by `artifact_type`.
- The dispatch site is now: look up the renderer, call it, `_compose_body(...)`,
  then `structured_json.update(extra)`. ~75 lines of branching → ~10.

This is purely internal to synthesis; content, ordering, hashing, dedupe, and
lineage are untouched. Adding a new artifact body is now: write a renderer +
register it (no dispatch edits) — exactly what HS-28-02..04 need.

Equivalence argument: `artifact_type` is unique per plugin, and in the old chain
each `*_value` was gated on `artifact_type == "..."`, so at most one branch ever
fired for a given artifact — identical to a registry keyed by `artifact_type`.

## Tests

The proof is the byte-for-byte guard suite passing **with no edits**:

```bash
git diff --stat tests/unit/test_artifact_synthesis_diagram.py   # (empty — file untouched)
uv run pytest -q tests/unit/test_artifact_synthesis_diagram.py  # 6 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py               # 1939 passed, 14 skipped
```

`ruff check holdspeak/plugins/synthesis.py` → **All checks passed!**

## Acceptance criteria

- [x] A renderer registry exists; the dispatch chain is a registry lookup + default fallback.
- [x] Every existing synthesis test passes unchanged (diagram, action_items,
      decisions, requirements, legacy default body all byte-for-byte identical).
- [x] Full sweep green.

## Result

The Phase-27-flagged synthesis debt is paid down before three new artifact bodies
land. `adr` / `milestone_plan` / `risk_register` (HS-28-02..04) now plug in as
renderers.
