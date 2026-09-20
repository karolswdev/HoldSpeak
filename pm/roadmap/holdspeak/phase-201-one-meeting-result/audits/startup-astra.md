# HS-201-07 — lane A startup identity proof

Astra session: `01a0bbc3-9bbd-7513-a76d-f6cc139fae2d`.

The startup ownership seam prints the already captured backend commit,
frontend build, and DB path in one line. It performs no new identity discovery.
The owner sitting remains lane B work; story 07 remains open.

## Red before the line

Command: `HOME=$(mktemp -d) uv run --extra dev pytest -q
tests/unit/test_hs201_startup_identity.py`.

```text
F                                                                        [100%]
=================================== FAILURES ===================================
______ test_startup_line_uses_the_captured_commit_build_and_database_path ______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8748/test_startup_line_uses_the_cap0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1083d4180>
capsys = <_pytest.capture.CaptureFixture object at 0x1084ca510>

    def test_startup_line_uses_the_captured_commit_build_and_database_path(
        tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """The boot line reports the same identity that the runtime captured."""
        database_path = tmp_path / "holdspeak.db"
        bundle = tmp_path / "_built"
        bundle.mkdir()
        (bundle / runtime_identity.BUILD_STAMP_NAME).write_text(
            json.dumps({"build_id": "frontend-build-201"}), encoding="utf-8"
        )
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", database_path)
        monkeypatch.setattr(runtime_identity, "built_dir", lambda: bundle)
        monkeypatch.setenv("HOLDSPEAK_BACKEND_REVISION", "backend-commit-201")
        runtime_identity.reset_runtime_identity()
    
        class Runtime(DatabaseOwnershipMixin):
            runtime_started_at = datetime(2026, 9, 19, 12, 0, 0)
    
            def __init__(self) -> None:
                self.owns_database = None
    
        runtime = Runtime()
        try:
            runtime._capture_identity_and_claim()
            identity = runtime_identity.current_runtime_identity()
            output = capsys.readouterr().out
        finally:
            release_database()
            runtime_identity.reset_runtime_identity()
    
>       assert output.splitlines() == [
            "HoldSpeak runtime identity: "
            f"backend_commit={identity.backend_revision} "
            f"frontend_build={identity.frontend_build} "
            f"database_path={identity.database_path}"
        ]
E       AssertionError: assert [] == ['HoldSpeak r...holdspeak.db']
E         
E         Right contains one more item: 'HoldSpeak runtime identity: backend_commit=backend-commit-201 frontend_build=frontend-build-201 database_path=/privat...r/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8748/test_startup_line_uses_the_cap0/holdspeak.db'
E         Use -v to get more diff

tests/unit/test_hs201_startup_identity.py:45: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_startup_identity.py::test_startup_line_uses_the_captured_commit_build_and_database_path
1 failed in 0.14s
```

## Astra verification

Command: `HOME=$(mktemp -d) uv run --extra dev pytest -q
tests/unit/test_hs201_startup_identity.py tests/unit/test_phase200_runtime_identity.py`.

```text
.......................                                                  [100%]
23 passed in 0.98s
```

Actual startup-seam probe, isolated HOME: instantiate `DatabaseOwnershipMixin`
with `runtime_started_at=datetime.now()`, call `_capture_identity_and_claim()`,
then `release_database()` in `finally`. No web server, microphone, or background
loop is started by this probe. The commit/build below are the actual checkout
and generated bundle at probe time; the DB path is the temporary HOME.

```text
HoldSpeak runtime identity: backend_commit=fdc3fc45bccf2b3b995ae9f4d13cb58691717a75 frontend_build=0fe67be374a1cd63 database_path=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.gYdZcFwLBn/.local/share/holdspeak/holdspeak.db
```

## Handoff and unknown

No loop was shown unable to stay inactive, so no loop gate was added (Tenet 1).
The before/after job counts on the sitting DB, startup from main, owner restart,
real meeting, usefulness verdict, and typed dictation remain unobserved here.
Lane B owns those checks. This fixture is not evidence of the owner's sitting.


## Final startup verification after the three backend story commits

Isolated HOME, the same two named test files. The flushed startup line is
also present in the quiet full-suite product snapshot.

```text
tests/unit/test_hs201_startup_identity.py::test_startup_line_uses_the_captured_commit_build_and_database_path
tests/unit/test_phase200_runtime_identity.py::test_identity_carries_every_c1_field
tests/unit/test_phase200_runtime_identity.py::test_a_later_checkout_cannot_change_a_running_identity
tests/unit/test_phase200_runtime_identity.py::test_capture_is_idempotent_without_force
tests/unit/test_phase200_runtime_identity.py::test_public_dict_drops_path_and_pid
tests/unit/test_phase200_runtime_identity.py::test_database_identity_is_opaque_and_stable
tests/unit/test_phase200_runtime_identity.py::test_config_revision_moves_with_the_file
tests/unit/test_phase200_runtime_identity.py::test_matching_bundle_and_schema_produce_no_diagnosis
tests/unit/test_phase200_runtime_identity.py::test_stale_bundle_when_the_disk_moved_under_the_process
tests/unit/test_phase200_runtime_identity.py::test_stale_bundle_when_no_stamp_exists_at_all
tests/unit/test_phase200_runtime_identity.py::test_schema_mismatch_names_its_direction[1-SCHEMA AHEAD]
tests/unit/test_phase200_runtime_identity.py::test_schema_mismatch_names_its_direction[-1-SCHEMA BEHIND]
tests/unit/test_phase200_runtime_identity.py::test_two_runtimes_diagnosis_names_the_owner
tests/unit/test_phase200_runtime_identity.py::test_unknown_ownership_is_not_a_two_runtimes_finding
tests/unit/test_phase200_runtime_identity.py::test_identity_report_hides_details_on_the_ordinary_surface
tests/unit/test_phase200_runtime_identity.py::test_one_lock_is_exclusive_and_names_its_owner
tests/unit/test_phase200_runtime_identity.py::test_a_dead_claim_is_stale_and_reclaimable
tests/unit/test_phase200_runtime_identity.py::test_a_process_never_refuses_itself
tests/unit/test_phase200_runtime_identity.py::test_release_is_safe_when_never_held
tests/unit/test_phase200_runtime_identity.py::test_refusal_message_is_a_specific_diagnosis
tests/unit/test_phase200_runtime_identity.py::test_allow_unowned_reads_the_hatch
tests/unit/test_phase200_runtime_identity.py::test_only_the_database_owner_runs_the_sweeps
tests/unit/test_phase200_runtime_identity.py::test_two_real_processes_and_exactly_one_owns_the_database

23 tests collected in 0.12s
```

```text
.......................                                                  [100%]
23 passed in 1.09s
```
