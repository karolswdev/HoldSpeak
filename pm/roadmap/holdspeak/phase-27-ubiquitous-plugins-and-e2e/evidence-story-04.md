# HS-27-04 Evidence — `requirements_extractor` (real run)

**Date:** 2026-06-01.
**Story:** [story-04-requirements-extractor.md](./story-04-requirements-extractor.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/requirements_extractor.py`) — flips the
`DeterministicPlugin` stub to a real `RequirementsExtractorPlugin`
(`kind="synthesizer"`, deferred, `required_capabilities=["llm"]`). Phase-16
pattern: strict prompt → single fenced ```json → `_extract_requirements` parses a
`{"requirements": [{text, type}]}` object (fenced or bare; tolerates
string-or-object items). Each `type` is coerced to one of
`functional | non_functional | constraint | acceptance` via `_normalize_type`
(synonym table: `non-functional`/`NFR` → `non_functional`, `acceptance criteria`
→ `acceptance`, `constraints` → `constraint`; unknown → `functional`). Success
when ≥1 requirement; else the clean failure shape. Uses
`build_configured_meeting_intel` so it honours the `.43` config.

**Registration:** `_REAL_PLUGINS` maps `requirements_extractor` → the real class
(**4 real plugins now, 10 stubs**). Its `_BUILTIN_PLUGIN_DEFS` entry already
existed (net-new not required). **No routing ripple:** `requirements_extractor`
was already in the `balanced` and `architect` base chains as a stub, so the
dispatched chains are unchanged — no `test_intent_dispatch` / full-pipeline edits
needed.

**Synthesis** (`synthesis.py`): `_ARTIFACT_TYPE_BY_PLUGIN` already maps it to
`requirements`. Added a `requirements` body branch via `_requirements_body`
(grouped by type into `**Functional**` / `**Non-functional**` / `**Constraints**`
/ `**Acceptance criteria**` sections) + `structured_json["requirements"]`. The
branch only fires when a `requirements` list is present, so the byte-for-byte
legacy-body guard (which uses a `requirements_extractor` run *without* the key)
still passes. Other bodies byte-for-byte unchanged.

**Web render** (the HS-27-02 lesson applied up front): `history.astro` +
`history-app.js` render a `requirements` artifact as a typed list
(`requirementsFor` / `requirementTypeLabel`, each row a type chip + text) from
`structured_json` — never the raw `body_markdown`. The plain-text fallback
`x-show` now also excludes requirements. `(cd web && npm run build)` ran clean.

## Tests

- `tests/unit/test_requirements_extractor_plugin.py` (12 cases): attributes,
  success + classification, bare-string default, unknown-type fallback, empty →
  failure, unparseable → failure, no-transcript, provider-exception,
  `_extract_requirements` edge cases, `_normalize_type` synonyms, registrar
  returns the real class, host-blocked-without-capability.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): `requirements` grouped
  body + structured key, with group ordering asserted; the byte-for-byte
  non-custom-body guard still passes.
- **Two pre-existing tests updated (not silenced):** they used
  `requirements_extractor` as a representative *stub*, which is now real —
  `test_plugin_host.py::test_builtin_plugins_register_and_execute` and
  `test_mermaid_architecture_plugin.py::test_register_builtin_plugins_uses_real_class`
  now exercise a still-stub plugin (`incident_timeline`).

```bash
uv run pytest -q tests/unit/test_requirements_extractor_plugin.py tests/unit/test_artifact_synthesis_diagram.py   # 18 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                 # 1939 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

Direct plugin run against the live endpoint (real provider, no override):

```
summary: 4 requirement(s) (1 functional, 1 non-functional, 1 constraint, 1 acceptance).
confidence: 1.0
 - functional :: The system must let users export their billing history as a PDF.
 - non_functional :: Every page must load within 200 milliseconds.
 - constraint :: We must ship the gateway by Q3.
 - acceptance :: The export should pass WCAG AA contrast checks before we call it done.
```

## Live evidence (spoken e2e, extended)

`tests/e2e/test_spoken_meeting_e2e.py` now runs **all four** real plugins
(`mermaid_architecture`, `action_owner_enforcer`, `decision_capture`,
`requirements_extractor`) against real endpoints (macOS `say` → Whisper → MIR →
`.43` Q6 LLM → synthesis → web → Playwright). The script gained
requirement-flavored speech; the test asserts the `requirements` artifact and
that `.requirement-list .requirement-item` renders. Refreshed screenshot
`evidence/spoken_meeting_artifacts.png` shows the **Requirements Extractor**
artifact with FUNCTIONAL / NON-FUNCTIONAL / CONSTRAINT / ACCEPTANCE rows
alongside the diagram, decisions, and action-item checklist.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed (artifacts: action_items, decisions, diagram, requirements)
```

## Result

Four real ubiquitous plugins now flow end-to-end (transcript → LLM → artifact →
structured web render), all demonstrated by one spoken-meeting e2e. Phase 27 is
**4/5. Next: HS-27-05** to close — the RFC reality-status refresh (flip the four
plugins shipped this phase to ✅) + `final-summary.md`.
