# Evidence - HS-149-05

- **Story:** HS-149-05 - The record book
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T19:21:53Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit -k doc`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0a8bd28f698fb38f350fdee97dc7908847faffb8

```text
........................................................................ [ 55%]
.........................................................                [100%]
129 passed, 5748 deselected in 3.95s
```

## Orchestrator triage note (2026-08-29)

Verified: PEOPLE_INTEGRATION.md now records the calendar-series
link as the contract's first FULFILLED deliberate association with
each of the seven rules itemized against shipped evidence; the
USER_GUIDE People section quotes every label verbatim (spot-read);
PEOPLE_SECURITY's two stale claims updated; SECURITY.md judged
correctly untouched (its encrypted-payload claim already covers
the link). The builder's deliberate non-claims are all correct.

**The FIFTH attribution miss, caught by arithmetic:** the builder
called the MCP tool-count guard failure "pre-existing (135 vs
138)" — but 149 added EXACTLY three tools (calendar.link/unlink +
one_on_one.brief); the failure was branch-new fallout of stories
02+04, invisible to a docs-only stash-compare. Guard-owner duty
discharged: docs/README + MCP_SIDECAR counts updated 135→138; all
129 doc guards green. The guard-owner law now has five scars.
