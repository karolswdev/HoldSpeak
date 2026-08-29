# Evidence - HS-147-06

- **Story:** HS-147-06 - The record book (docs)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T06:41:58Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_setup_status_doctor_drift.py -q && HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit -k "doc or drift" 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6bbd89896827383001ebe0185f804c183d991e99

```text
............................                                             [100%]
1 failed, 142 passed, 5665 deselected in 6.06s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: doc guards re-run and read (153
passed in the doc/drift/copy/language selection; the two failures are
the EXACT inherited baseline names test_product_copy +
test_product_language, and the stash-compare law was applied — the
violation LISTS are byte-identical between HEAD and the docs-bearing
tree, so zero branch-new violations hide inside them). Spot-read the
new USER_GUIDE "Arm an event for recording" section: labels quoted
verbatim from the shipped components, the honest-follow behavior in
user words, the origin line and its honest absence. The builder's
deliberate non-claims (SECURITY.md untouched — no new egress; no
doc-drift guard invented where none pins a false claim) are ruled
correct.
