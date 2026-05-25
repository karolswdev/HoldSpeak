# Evidence — HS-19-04 Target Profile Override and Refinement

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-19-04](./story-04-target-profile-override.md)

## What changed

- Added persisted `dictation.pipeline.target_profile_override`.
- Supported override values:
  - `auto`
  - `codex_cli`
  - `claude_code`
  - `terminal_shell`
  - `browser`
  - `editor`
  - `chat`
- Added target-profile helper support for manual overrides.
- Dry-run and readiness now apply the persisted override.
- Live dictation now applies the persisted override before building the utterance activity context.
- Added a Dictation Runtime cockpit selector plus reset-to-auto button.
- Settings API validates and persists the override.

## Validation

```bash
npm run build
```

Result: passed from `web/`.

```bash
.venv/bin/pytest -q tests/unit/test_target_profile.py tests/unit/test_controller.py tests/unit/test_dictation_telemetry.py tests/unit/test_project_doc_suggestions.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_assembly.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py tests/integration/test_web_project_kb_api.py
```

Result: `113 passed in 4.15s`.

```bash
git diff --check
```

Result: passed.

## Notes

- `auto` preserves existing active-window detection behavior.
- Manual override sets target profile source to `override` with confidence `1.0`.
- No per-app automation rules were added.
