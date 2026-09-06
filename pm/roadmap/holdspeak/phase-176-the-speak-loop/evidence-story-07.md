# Evidence - HS-176-07

- **Story:** HS-176-07 - The docs (the Speak Loop in the guide; the correction flow in the architecture)
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T15:48:25Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_docs_navigation.py tests/unit/test_product_language.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_mcp_sidecar_doc_drift.py -p no:cacheprovider 2>&1 | tail -1; HOME=$T uv run python scripts/check_docs.py 2>&1 | tail -1; HOME=$T PUPPETEER_CACHE_DIR=/Users/karol/.cache/puppeteer npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_mermaid_renders.py -p no:cacheprovider 2>&1 | tail -1; ls docs/assets/speak-loop/ | tr '\n' ' '; echo; grep -c '' docs/USER_GUIDE.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 200c26298586fc20e3b40e33a6906bf0e129406f

```text
51 passed in 3.66s
Documentation navigation: 37 files checked; local targets and Markdown headings resolve.
2 passed in 82.90s (0:01:22)
journal-row-open-1440.png journal-stream-1440.png learned-1440.png speak-applied-1440.png speak-taught-1440.png speak-teach-row-1440.png 
2486
```
