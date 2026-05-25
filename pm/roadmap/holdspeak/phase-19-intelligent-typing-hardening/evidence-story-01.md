# Evidence — HS-19-01 Local LLM Project Documentation Suggestions

**Date:** 2026-05-10
**Status:** done

## What shipped

- Added `holdspeak/project_doc_suggestions.py` with a safe proposal contract for narrow `.hs/.../*.md` documentation updates.
- Suggestions are parsed from local runtime output and validated before use.
- Allowed target paths are restricted to:
  - `.hs/memory/*.md`
  - `.hs/decisions/*.md`
  - `.hs/handoffs/*.md`
  - `.hs/workflows/*.md`
  - `.hs/issues/*.md`
- Secret-looking content and broad/unsafe paths are rejected.
- `ProjectRewriter` now appends a "Context preservation suggestion" for Codex/Claude target profiles when the local runtime returns a valid suggestion.
- Generic targets do not receive suggestions.
- No file writes were added. The product contract remains: HoldSpeak proposes; user/agent writes.

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_project_doc_suggestions.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_assembly.py
```

Result: `17 passed in 0.10s`.

## Notes

- Invalid model output, `NO_SUGGESTION`, runtime failure, unsupported runtime, unsafe target paths, and secret-looking content all fail open to no suggestion.
- This story intentionally does not add the web apply/dismiss flow; that is HS-19-02.
