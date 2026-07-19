# Evidence - HS-100-05

- **Story:** HS-100-05 - B1: the vocabulary guard
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T13:52:50Z

- **Command:** `uv run pytest -q tests/unit/test_web_vocabulary_guard.py tests/unit/test_intel_command.py tests/unit/test_intel_package.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4a39e69bf482f1b4c74f00633077fb473b6a14a

```text
...............                                                          [100%]
15 passed in 0.50s
```

## Summary of proof

- **tests/unit/test_web_vocabulary_guard.py**: scans every web/src
  string literal + JSX text that reads as prose for canon-banned
  vocabulary (intel → intelligence, persona → agents) and absolute
  filesystem paths. Shrink-only allowlist frozen with today's SEVEN
  offender files (Agents/Settings stories burn it to zero; B8 asserts
  empty). Both-ways pattern proof included, like the voice guard.
- **The trace-C refusal fixed at its two backend sources**
  (intel/providers.py, intel/engine.py): "Intel model not found:
  /Users/…" → "No language model on this hub. Pick one in Settings
  under Intelligence." — names the fix, leaks nothing; pinned by
  test_backend_refusal_names_its_fix.
- Intel-adjacent suites green (341 passed).
