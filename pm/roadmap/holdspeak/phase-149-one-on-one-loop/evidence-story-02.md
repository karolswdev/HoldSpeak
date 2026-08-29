# Evidence - HS-149-02

- **Story:** HS-149-02 - The link (encrypted series link + resolution)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T18:35:10Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$HOME/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_people_calendar_link.py tests/unit/test_people_service.py tests/unit/test_people_routes.py tests/unit/test_people_mcp.py tests/unit/test_people_no_leaks.py tests/unit/test_people_store.py tests/unit/test_people_policy.py tests/unit/test_honest_keystore.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5032b00c69e1787ec856cc6ef161751d69d41988

```text
........................................................................ [ 65%]
......................................                                   [100%]
110 passed in 2.14s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: the resolve seam read
line-by-line (readiness-guarded with "unavailable" DISTINCT from
no-match; exceptions degrade to unavailable, never to a lying
empty; input hygiene); the P1 refusal carries the holder by name at
all three transports (service exception / HTTP 409 / MCP isError);
calendar_links flow through the EXISTING _shared_relationship and
_grounding_bundle visibility paths (shared_intent-class relationship
metadata, the project_refs precedent — the counsel's F-family
concerns land in story 04 where the brief tool is born). The
schema grep pin makes the 138 law mechanical. Every People test
runs through the story-01 seam, spy-confirmed. 71 focused re-run
and read by the orchestrator (the builder's full 119 recorded in
the capture). Deviation ruling: the closed-catalogue MCP test
extension (+2 tool names) is the test's PURPOSE, not a weakening —
accepted.
