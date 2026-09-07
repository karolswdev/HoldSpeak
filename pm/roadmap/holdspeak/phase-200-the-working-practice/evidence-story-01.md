# Evidence - HS-200-01

- **Story:** HS-200-01 - Establish the integration baseline and obligation map
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T18:00:41Z

- **Command:** `bash -c set -o pipefail; uv run python scripts/check_docs.py 2>&1 | tail -1; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py -p no:cacheprovider 2>&1 | tail -1; echo -n "baseline record bytes: "; wc -c < pm/roadmap/holdspeak/phase-200-the-working-practice/assets/baseline-2026-09-06.md | tr -d " "; grep -m1 -i "byte-identical" pm/roadmap/holdspeak/phase-200-the-working-practice/assets/baseline-2026-09-06.md | cut -c1-120; n=$(.githooks/dw check holdspeak 2>&1 | grep -c "phase-200" || true); echo "dw check phase-200 issues: $n"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 29b1327410119352d201853c8d34080d98e1b34c

```text
Documentation navigation: 37 files checked; local targets and Markdown headings resolve.
35 passed in 1.76s
baseline record bytes: 86659
**Result: the two runs are byte-identical (`diff` empty).** Both report
dw check phase-200 issues: 0
```
