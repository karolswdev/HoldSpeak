# Evidence - HS-150-05

- **Story:** HS-150-05 - The record book
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T22:17:55Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_docs.py 2>/dev/null || HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4fb5a367939b7671392150bb1c2fd6266639d399

```text

no tests ran in 0.00s
..........................                                               [100%]
26 passed in 1.00s
```

## Orchestrator triage — 2026-08-29

- The captured guard run above is UNFILTERED — 26/26 including
  test_mcp_tool_count_claims_match_registry. The builder had
  deselected that guard as "pre-existing (docs claim 138, registry
  has 140)" — the SEVENTH builder attribution miss of the era, and
  the third by arithmetic: story 01 added exactly two MCP tools
  (people.owner_alias.link/.unlink), 138 + 2 = 140, entirely this
  arc's. Docs claims updated 138 → 140 (docs/README.md,
  docs/MCP_SIDECAR.md ×2) by the orchestrator; the guard passes
  unfiltered.
- Spot-read against the shipped code: the PEOPLE_INTEGRATION second
  FULFILLED association mirrors the first rule-by-rule (gesture ×2
  surfaces, P2 naming its holder, reserved strings by name,
  read-time-only projection, inference still forbidden); USER_GUIDE
  labels verified verbatim (map…, Everyone, Owner aliases, Generate
  your brief, Add to 1:1 agenda, Open person, People sidecar
  unavailable); the SECURITY/PEOPLE_SECURITY persisted-boundary
  paragraphs state exactly what the walk rig proves on glass.
- Root README pitch honestly untouched per the story's own scope.
