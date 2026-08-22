# Evidence - HSEGHS001HS104-143-05

- **Story:** HSEGHS001HS104-143-05 - Frozen Route Plans
- **Status:** done
- **Date:** 2026-08-22

## Outcome

Story 05 adds the one canonical, hub-local `InferenceRoutePlan@1` authority.
Every parent can now resolve one ordered assignment chain from a single SQLite
snapshot and freeze exact capability, assignment, profile, binding, deployment,
boundary, context-support, operation-policy, and retry-policy evidence before
execution. Later mutable changes affect only the next parent.

The private `OperationAdmittedRouteRequestPlan@1` retains frozen eligibility
and exact admitted/context/serialized-request hashes without persisting owner
material. Executable evidence is accepted only from a composition-registered,
revision-bound provider that can reconstruct its independent durable source.
Until an adopting product story registers that owner, executable planning
refuses rather than trusting caller-authored hashes.

## Truth and safety

- Pure resolution performs one read transaction and no write, network, scan,
  probe, model load, or readiness mutation; the measured warmed four-leg p95 is
  below 10 ms.
- Freeze commands are atomic and idempotent. Persisted effect IDs are derived
  from the command and canonical request, so replay cannot be repointed to a
  different valid route or operation plan.
- Historical reads reconstruct canonical payloads against normalized legs,
  immutable assignment/profile/binding/deployment material, and frozen
  capability/retry definitions rather than current mutable heads or registry.
- Disabled or unavailable configured legs remain in the route and are frozen
  as named preflight-unavailable operation legs; they are never filtered.
- The v1 adapter is read-only and content-free. It performs no path, environment,
  liveness, or readiness observation and refuses capabilities its legacy
  language-only evidence cannot prove.
- Route-leg evidence does not mint a physical-attempt ordinal. Story 06 owns
  durable attempt reservation and retry/fallback advancement.
- Route, command, authority, normalized-leg, and private request-plan buckets
  are hub-local; hostile sync import refuses them.
- Plans and projections contain no prompt, Note, transcript, credential,
  private endpoint, or local path.

## Verification

### Dedicated adversarial route-plan suite

```text
pytest tests/unit/test_phase143_inference_route_plans.py
16 passed in 3.64s
```

### Integrated Phase 143 authority, profile, assignment, schema, and census matrix

```text
pytest <Story 05 integrated matrix>
168 passed in 42.82s
```

### Independent hostile-audit gate

```text
pytest <counsel route/profile/assignment/schema/census matrix>
83 passed
```

### Static hygiene

```text
ruff check <changed Story 05 Python files>
All checks passed!

git diff --check
# clean
```

## Review result

Independent counsel returned **RATIFY** after direct tests for copied-valid
command-pointer substitution, recomputed route and operation-plan forgeries,
cross-bound assignment/profile/binding/deployment evidence, malformed or
missing admission providers, provider-source tamper, closed DTOs, identity
collisions, legacy capability overclaim, restart, deletion dependency, privacy,
and hostile sync.

### Captured run — 2026-08-22T06:33:09Z

- **Command:** `env PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q tests/unit/test_phase143_inference_route_plans.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9350cf95a0777ca0ceff67f7edc4749f2e3e61a7

```text
................                                                         [100%]
16 passed in 2.49s
```
