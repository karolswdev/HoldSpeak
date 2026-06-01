# HS-28-03 Evidence — `milestone_planner` (real run)

**Date:** 2026-06-01.
**Story:** [story-03-milestone-planner.md](./story-03-milestone-planner.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/milestone_planner.py`) — real
`MilestonePlannerPlugin` (`kind="synthesizer"`, deferred,
`required_capabilities=["llm"]`). Phase-16 pattern: strict prompt → fenced
```json → `_extract_milestones` parses `{"milestones": [{name, target,
deliverables, dependencies}]}`. `target` is null-coerced (`TBD`/`?`/`none` →
null); `deliverables` / `dependencies` are sanitized string lists (empty allowed).
A milestone needs a name. Success when ≥1 milestone; else the clean failure shape.
Uses `build_configured_meeting_intel` (honours `.43`).

**Registration:** `_REAL_PLUGINS` maps `milestone_planner` → the real class
(**6 real plugins now, 8 stubs**). **No routing ripple** — already on the
`delivery` chains as a stub.

**Synthesis** (registry): `_milestone_body` (per milestone: `**name** — target`
then Deliverables / Dependencies lines) + `_render_milestones` registered under
`"milestone_plan"`. Other bodies unchanged.

**Web render** (`history.astro` + `history-app.js`): `milestonesFor(artifact)` +
a `.milestone-artifact` block — per milestone a name + target pill + Deliverables
/ Dependencies lines, from `structured_json`. Fallback `x-show` excludes
milestones. `(cd web && npm run build)` clean.

## Tests

- `tests/unit/test_milestone_planner_plugin.py` (11 cases): attributes, success +
  targets, missing-target → null, milestone-without-name dropped, empty →
  failure, unparseable → failure, no-transcript, provider-exception,
  `_extract_milestones` edge cases, registrar, capability-blocked.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): `milestone_plan` body +
  structured key; byte-for-byte default-body guard still passes.

```bash
uv run pytest -q tests/unit/test_milestone_planner_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_intent_dispatch.py   # 25 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                # 1965 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

```
summary: 2 milestone(s); 2 with a target date.
 - Private Beta | end of Q3 | deliv: ['auth', 'billing integration'] | deps: ['API contract frozen']
 - GA | Q4 | deliv: ['mobile app', 'load testing finished'] | deps: ['Private Beta completed']
```

## Live evidence (spoken e2e, extended)

`tests/e2e/test_spoken_meeting_e2e.py` now runs **six** real plugins and asserts
the `milestone_plan` artifact + `.milestone-artifact .milestone-record` render.
Refreshed `evidence/spoken_meeting_artifacts.png` shows all six artifacts from the
natural conversation.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed (artifacts: action_items, adr, decisions, diagram, milestone_plan, requirements)
```

## Result

Six real plugins now. **Next: HS-28-04** (`risk_heatmap`), then HS-28-05 (close).
