# Shared collection read truth

Status: implemented; hold for SHIP. Root owns integration and the done call.

The Operate walk found an accepted Workbench Add followed by HTTP 503 from
`/api/workbenches`. The aggregate refresh replaced the known Workbench bucket
with the loader's initial empty bucket, and the window lost its source object.
This fails Tenet 3 (help the owner complete the job) and Tenet 7 (keep the
architect's working material available).

## Repair and authority

`web/src/desk/api.ts:126` adds optional per-kind `transientFailures` metadata.
The existing failure path marks network/unknown read exceptions and `ApiError`
with HTTP status at least 500 (`api.ts:744`). It keeps the existing unreachable
status, ranked first failure, error text, and HTTP 401 sign-in text.

`web/src/desk/store/dataSlice.ts:196` retains the latest store bucket for those
classified transient reads. A successful empty collection remains authoritative.
HTTP 4xx refusals do not gain retention. Existing write-version and rollback
fences remain in the ordinary merge path.

Root authorized the loader field after the initial inspection found that
`unreachable` alone includes HTTP 401/403. The first failure cannot safely
classify all collections: an earlier HTTP 503 can coexist with a later HTTP
403. The repair uses each collection's own classification.

Owned files:

- `web/src/desk/api.ts`
- `web/src/desk/store/dataSlice.ts`
- `web/src/desk/__tests__/loadAllOutage.test.ts`
- `web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx`
- This record.

## Focused proof

The initial run reproduced all three new retention regressions on the prior
merge behavior: 3 failed, 7 existing write/rollback tests passed. Log:
`.tmp/deep-usability/shared-read-red.log`.

The final scoped run names both existing test files and uses isolated HOME,
Node 22, and the machine lock through the phase wrapper:

```sh
.venv/bin/python .tmp/deep-usability/locked.py shared-read-green --web node node_modules/vitest/vitest.mjs run src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/loadAllOutage.test.ts --maxWorkers=2 --reporter=verbose
```

Store regressions cover multiple known Workbenches through HTTP 503, an ordinary
saved Decision through a read exception, HTTP 401/403 clearing, mixed first-ranked
HTTP 503 plus later HTTP 403, and recovery to authoritative empty data. The same
file retains its seven existing write/version/rollback tests. Loader regressions
cover network and unknown exceptions, per-kind mixed HTTP 503/403 classification,
and HTTP 401 sign-in text. Verbose output names every collected case.

Final run result: 2 files passed, 16 tests passed, exit 0, 2.26 seconds after
the machine lock became available. Log:
`.tmp/deep-usability/shared-read-green.log`.

```text
Test Files  2 passed (2)
     Tests  16 passed (16)
  Duration  2.26s (transform 1.02s, setup 191ms, import 1.40s, tests 652ms, environment 548ms)
```

## Proof limits

This repair covers collection buckets in `items`. It does not change separate
profile/project summary/model fields, held-object detail reads, or the intentional
empty Coder result when its companion is off. No visual composition changes;
the Operate lane and root own the real Workbench replay and its screenshots.
No owner state, model, microphone, terminal, or external delivery was used.
No staging or commit.
