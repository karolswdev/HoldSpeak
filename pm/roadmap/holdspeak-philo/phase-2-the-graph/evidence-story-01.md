# Evidence - PHILO-2-01

- **Story:** PHILO-2-01 - The rulebook and the state atlas
- **Status:** done
- **Date:** 2026-09-22

## Proof

### Captured run — 2026-09-22T22:42:39Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.aLP1V3aBvD PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1577cf551608d1fbb429cbbb048c6e91d26598eb

```text
....................................................                     [100%]
52 passed in 45.92s
```

### Captured run — 2026-09-22T23:15:01Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.BxZwyj6ZKB PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 49704aa94cc6ac569c37845b1f3cd9cc3de09835

```text
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 95.37s (0:01:35)
```

### Captured run — 2026-09-23T00:12:11Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Rr2GNDsm7D PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e332786740a5e10ab853fc0f509270ff2fea5932

```text
........................................................................ [ 61%]
........................................F.F..                            [100%]
=================================== FAILURES ===================================
_ test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle] __

case_id = 'case.j1.first_words_continue_later.idle'
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-171/test_the_rig_drives_the_real_a0')

    @pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
    def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
        want_verdict, names, why = ATLAS_FENCE[case_id]
        record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                          out=tmp_path, engine="none")
    
        assert record["verdict"] == want_verdict, (
            f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
        assert record["complete"] is True
        assert record["provenance"]["revision"]
        assert (tmp_path / record["run_id"] / "observation.json").exists()
    
        if want_verdict == "blocked":
            # a named block: the record says WHAT could not be reached
            blocked = [n for n in record["notes"] if n.startswith("BLOCKED:")]
>           assert blocked, record["notes"]
E           AssertionError: ["predicate: BLOCKED: observe_at not present ('section.desk-first-words'); an absence inside a scope that does not exi...D, not failed: the rig gathered the whole run (setup, before, trigger, wait, after) but no verdict is earned from it.']
E           assert []

tests/e2e/test_graph_walk_smoke.py:84: AssertionError
__ test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face] __

case_id = 'case.j9.shade_receipt_open.rhythm_face'
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-171/test_the_rig_drives_the_real_a2')

    @pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
    def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
        want_verdict, names, why = ATLAS_FENCE[case_id]
        record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                          out=tmp_path, engine="none")
    
>       assert record["verdict"] == want_verdict, (
            f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
E       AssertionError: case.j9.shade_receipt_open.rhythm_face: the case's setup never crosses the first-value gate, so the Desk memory door does not exist when setup step 2 clicks it
E         [
E           "predicate: windows after: ['Rhythm']"
E         ]
E       assert 'pass' == 'blocked'
E         
E         - blocked
E         + pass

tests/e2e/test_graph_walk_smoke.py:75: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle]
FAILED tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]
2 failed, 115 passed in 148.79s (0:02:28)
```

### Captured run — 2026-09-23T00:17:38Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.j3Ak3GCEyw PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e332786740a5e10ab853fc0f509270ff2fea5932

```text
........................................................................ [ 61%]
.............................................                            [100%]
117 passed in 128.79s (0:02:08)
```
