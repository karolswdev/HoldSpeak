# Evidence — HS-19-02 Web Review Flow for Suggested `.hs/` Updates

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-19-02](./story-02-web-suggestion-review.md)

## What changed

- Added validated project documentation suggestion endpoints:
  - `GET /api/dictation/project-doc-suggestion`
  - `POST /api/dictation/project-doc-suggestion/apply`
  - `POST /api/dictation/project-doc-suggestion/dismiss`
- Persisted the latest valid suggestion from dictation dry-run stage metadata per project root.
- Added explicit apply/dismiss behavior; apply writes only validated `.hs/{memory,decisions,handoffs,workflows,issues}/lower-dash-slug.md` paths.
- Added a Project Context review panel that displays suggestion path, rationale, and editable content.
- Rebuilt the Astro frontend into `holdspeak/static/_built/`.

## Validation

```bash
npm run build
```

Result: passed from `web/`.

```bash
.venv/bin/pytest -q tests/unit/test_project_doc_suggestions.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_assembly.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
```

Result: `63 passed in 2.70s`.

## Notes

- Suggestions remain proposals only. HoldSpeak still does not silently write project documentation.
- Dismiss clears the in-memory latest suggestion and does not touch disk.
- A later dry-run for the same project with no suggestion clears the stale review panel.
