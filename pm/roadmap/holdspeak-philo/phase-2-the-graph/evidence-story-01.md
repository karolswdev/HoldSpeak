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

### Captured run — 2026-09-23T01:00:12Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.2LICz00p2N PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 43805c4689301bb9874eb96082871300f518cc31

```text
..................F.......................F............................. [ 54%]
...........................................................              [100%]
=================================== FAILURES ===================================
___________________ test_atlas_validates_against_its_schema ____________________

atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/48: Additional properties are not allowed ('trigger_route' was unexpected)
E       assert not [<ValidationError: "Additional properties are not allowed ('trigger_route' was unexpected)">]

tests/unit/test_philo_graph_atlas.py:131: AssertionError
___________ test_every_case_validates_against_the_graph_case_schema ____________

atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}
graph_case_schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...hilo/graph.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_every_case_validates_against_the_graph_case_schema(
        atlas: dict, graph_case_schema: dict
    ) -> None:
        """Every atlas case must be a legal graph case, so the generator can join them.
    
        No exemption: the atlas case definition IS the graph's, so every case that
        validates against one validates against the other.
        """
        validator = Draft202012Validator(
            {"$schema": "https://json-schema.org/draft/2020-12/schema",
             "$ref": "#/$defs/case", "$defs": graph_case_schema["$defs"]}
        )
        problems: list[str] = []
        for case in atlas["cases"]:
            for error in validator.iter_errors(case):
                path = list(error.absolute_path)
                if path[:3] == ["expected", "predicate", "kind"]:
                    continue
                if path[:1] == ["expected"] and case["applicability"] != "applicable":
                    # An unreachable case is never fired, so it has no expected
                    # RESULT to structure -- only a reason. graph.schema.json
                    # already makes `trigger` conditional on applicability (its
                    # allOf); `expected` needs the same treatment. Until it does,
                    # this is the one shape the two schemas disagree on, and the
                    # disagreement is NAMED here, never hidden.
                    assert case.get("reason"), f"{case['id']} has neither predicate nor reason"
                    continue
                problems.append(f"{case['id']}: {'/'.join(str(p) for p in path)}: {error.message}")
>       assert not problems, "\n".join(problems[:20])
E       AssertionError: case.j10.arrival_generate_again.same_day_idempotent: : Additional properties are not allowed ('trigger_route' was unexpected)
E       assert not ["case.j10.arrival_generate_again.same_day_idempotent: : Additional properties are not allowed ('trigger_route' was unexpected)"]

tests/unit/test_philo_graph_atlas.py:530: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema
FAILED tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
2 failed, 129 passed in 336.44s (0:05:36)
```

### Captured run — 2026-09-23T01:06:44Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.liluxUDDYH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py tests/e2e/test_graph_walk_smoke.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 43805c4689301bb9874eb96082871300f518cc31

```text
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 341.07s (0:05:41)
```
