# Evidence - HSEGHS001HS104-143-04

- **Story:** HSEGHS001HS104-143-04 - Assignment Store and Resolver
- **Status:** done
- **Date:** 2026-08-21

## Outcome

Story 04 adds the one hub-local `InferenceAssignment@1` authority. Sparse
assignment heads select an immutable, ordered profile chain at invocation,
subject, capability, group, or global precedence; the first defined chain wins
whole and is never concatenated, filtered, or substituted.

Set, Use default, and starter commands are narrow-CAS, idempotent transactions.
Clears retain a monotonic tombstone generation, preventing absent-state ABA.
Receipts reconstruct committed effects from immutable rows and return fresh
current truth, so response replay cannot forge or stale the owner projection.

## Truth and safety

- Chains are unique, contiguous, nonempty, and bounded to four entries.
- Compatibility is server-derived from the canonical capability registry,
  verified profile/deployment revisions, exact result-schema claims, context,
  modality, and canonical boundary evidence. Readiness and capacity remain
  repair/admission facts rather than structural save blockers.
- Legacy v1 and v2 profiles can share a chain without rewriting v1 bytes;
  legacy labels use the privacy-safe Story 03 adapter.
- Group/global assignments retain heterogeneous whole chains and project exact
  per-capability issues. Tool requirements fail closed until Story 09.
- Normalized profile references and canonical JSON are exact verified mirrors;
  malformed, cross-bound, or tampered state returns a named integrity refusal.
- The owner summary remains exactly global plus six canonical groups under
  registry growth. Unknown owner groups become a blocking global issue.
- Seed adoption no longer silently routes models. Migration markers prove exact
  durable assignment effects without cutting over product families owned by
  Stories 07, 08, and 10.
- Assignment, command, and migration buckets are hub-local and hostile sync
  refuses them.

## Verification

### Integrated authority, registry, schema, API/MCP adjacency, and censuses

```text
pytest <Story 04 integrated matrix>
186 passed in 40.73s
```

### Final hostile-audit gate

```text
pytest assignments + surface census + capability census + schema policy
42 passed in 19.40s
```

### Static hygiene

```text
ruff check <changed Story 04 Python files>
All checks passed!

git diff --check
# clean
```

## Review result

Independent counsel returned **RATIFY** after direct forgery, cross-binding,
corrupt migration, illegal SQL hybrid, malformed material, registry-growth,
legacy privacy, starter CAS, policy-intersection, and replay tests passed.

### Captured run — 2026-08-22T05:43:13Z

- **Command:** `/bin/zsh -lc PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q tests/unit/test_phase143_inference_assignments.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_db_schema_policy.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 679ce6fb02680cc385061125e29e24df675c78ee

```text
..........................................                               [100%]
42 passed in 19.24s
```
