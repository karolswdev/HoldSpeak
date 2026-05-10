# Evidence — HS-18-03 Web Cockpit for Intelligent Typing and Project Context

**Date:** 2026-05-10
**Status:** done

## What shipped

- Dictation Readiness now reports active target profile and Claude/Codex hook freshness alongside selected project, pipeline, blocks, Project KB, and runtime status.
- Project Context tab now surfaces the HS-18-02 write policy, flat `.hs_*` compatibility files, skipped-file warnings, truncation state, and canonical `.hs/` edit path.
- Saving a flat-derived context entry writes only the canonical `.hs/<name>` copy and leaves the flat compatibility file unchanged.
- Runtime tab exposes the project-aware rewrite stage toggle before dictation starts.
- Agent Hooks tab continues to show hook templates, latest captured hook status, captured agent-context banner, and external summary controls.

## Files touched

- `holdspeak/web_server.py`
- `holdspeak/agent_context.py`
- `web/src/pages/dictation.astro`
- `web/src/scripts/dictation-app.js`
- `holdspeak/static/_built/`
- `tests/integration/test_web_project_kb_api.py`
- `tests/integration/test_web_dictation_readiness_api.py`

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_agent_context.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_readiness_api.py
```

Result: `62 passed in 2.39s`.

```bash
cd web && npm run build
```

Result: Astro built 7 static pages successfully into `holdspeak/static/_built/`.

## Notes

- The browser UI edits only the canonical `.hs/` files. Flat `.hs_*` files are visible as read-only compatibility inputs.
- Skipped unsafe project context files are surfaced in the API/UI instead of silently disappearing.
- Manual browser clicking remains useful before phase exit, but HS-18-03 acceptance is covered by API assertions, static bundle marker assertions, and the web build.
