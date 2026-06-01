# HS-28-01 — Synthesis per-type renderer registry (behavior-preserving)

- **Project:** holdspeak
- **Phase:** 28
- **Status:** backlog
- **Depends on:** HS-27-04 (the fourth custom body — the trigger to refactor)
- **Unblocks:** HS-28-02, HS-28-03, HS-28-04
- **Owner:** unassigned

## Problem

`synthesize_meeting_artifacts` (`holdspeak/plugins/synthesis.py`) chooses an
artifact body via a hand-written `if mermaid / elif action_items / elif decisions
/ elif requirements / else` chain, with a parallel set of `if`s appending
`structured_json` keys. That was fine at one custom body; it's now four, and this
phase adds three more. The in-file TODO already calls for this:

> "once a third custom body lands, extract a per-artifact-type renderer registry
> instead of branching here."

Pay it down **before** adding ADR / milestone / risk bodies, so each new plugin
plugs in by registering a renderer instead of extending two parallel chains.

## Scope

### In

- Introduce a per-`artifact_type` renderer registry in `synthesis.py`: a mapping
  (or small dataclass) from `artifact_type` → a function that, given the canonical
  plugin output + the precomputed `title` / `summary` / `source_lines`, returns the
  `body_markdown` **and** the extra `structured_json` keys for that type.
- Port the four existing custom bodies (`diagram`, `action_items`, `decisions`,
  `requirements`) and the default body into the registry, **byte-for-byte**.
- The dispatch site becomes: look up the renderer for `artifact_type` (default
  renderer if none), call it, merge its `structured_json` keys.
- Keep the existing helper functions (`_action_item_line`, `_decision_body`,
  `_requirements_body`, etc.) — the registry calls them.

### Out

- Any change to artifact *content*, ordering, hashing, dedupe, or lineage.
- New artifact types (those are HS-28-02..04).
- Touching the web render (this is a synthesis-internal refactor).

## Acceptance criteria

- [ ] A renderer registry exists; the dispatch chain is replaced by a registry
      lookup + default fallback.
- [ ] Every existing synthesis test passes **unchanged** — especially the
      byte-for-byte guards (`test_artifact_synthesis_diagram.py`): diagram,
      action_items, decisions, requirements, and the legacy default body are all
      identical to before.
- [ ] Full sweep green.

## Test plan

- `uv run pytest -q tests/unit/test_artifact_synthesis_diagram.py` — must pass with
  **no edits** to the test file (the proof the refactor preserved behavior).
- Full sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Simplest viable shape: `dict[str, Callable[[Ctx], tuple[str, dict]]]`. A
  dataclass is fine too; don't over-engineer.
- The default renderer is just the `### {title}\n\n{summary}\n\n{source_lines}`
  body with no extra structured keys — the current `else` branch.
- This is a pure refactor: if any existing test needs editing to pass, the refactor
  changed behavior — stop and fix the refactor, don't edit the test.
