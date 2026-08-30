# Evidence - HS-150-01

- **Story:** HS-150-01 - The owner gesture (aliases + resolution + delegated_at)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T21:30:59Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$HOME/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_owner_gesture.py tests/unit/test_people_service.py tests/unit/test_people_mcp.py tests/unit/test_people_calendar_link.py tests/unit/test_follow_through_service.py tests/unit/test_people_brief.py tests/unit/test_people_routes.py tests/unit/test_people_no_leaks.py tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6bfbbd6cc76c00814513c33b97aa950eefcc4737

```text
........................................................................ [ 36%]
........................................................................ [ 73%]
.....................................................                    [100%]
197 passed in 28.53s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder: 197 focused re-run and read (their 141
+ the schema guard). The upsert CASE guard read line-by-line —
owner AND delegated_at guarded in one atomic statement, INSERT
passes None (fresh extraction never stamps, honest null), the
counsel pair proven both directions verbatim. The alias machinery
is the calendar_links clone as ruled (P2 naming the holder at all
transports; reserved me/remote/you refused; casefold in memory,
never logged).

**The SIXTH attribution near-miss, caught pre-suite:** the builder
changed the schema and reported "no guard failures" — but the
canonical-snapshot guard (tests/unit/test_db.py:1734, NOT the
policy file) was never in their selection and WAS red. The
orchestrator regenerated the fixture — and in doing so REPRODUCED
the recorded regen gotcha exactly (a bash-heredoc double-escaped
the \\s+ regex into a no-op; the memory note warned of this
precise trap): fixed via a script file with the correct regex,
74/74 green. The fixture regen rides this commit. Lesson sharpened:
schema-touching briefs must name tests/unit/test_db.py in the
verification list explicitly.
