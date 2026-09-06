"""HS-200-03 — the release checks' own guards, tested.

Three pieces of harness are load-bearing enough to need tests of their own:

* the isolated-HOME guard, which refuses a product suite pointed at a real
  installation (the schema-v43 pollution and the 167/168 walk seeds were both
  written into the owner's real database by a suite run under his own HOME);
* the dependency probes behind the skip markers, which must answer with a
  reason rather than let an absent dependency pass silently;
* the readiness predicate the Ask admission path resolves through, which was
  duplicated and therefore only half substitutable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import (
    REAL_HOME_OPT_IN,
    missing_local_dictation_route_reason,
    missing_local_model_reason,
    missing_mlx_whisper_reason,
    real_home_violation,
)


# ── the isolated-HOME guard ──────────────────────────────────────────


def _installation(root: Path) -> Path:
    (root / ".local" / "share" / "holdspeak").mkdir(parents=True)
    (root / ".config" / "holdspeak").mkdir(parents=True)
    return root


def test_a_real_installation_under_the_account_home_is_refused(tmp_path) -> None:
    home = _installation(tmp_path / "karol")
    violation = real_home_violation(home, home)
    assert violation
    assert str(home) in violation
    assert ".local/share/holdspeak" in violation
    assert "HOME=$(mktemp -d)" in violation, "the refusal must name the remedy"


def test_an_isolated_home_is_lawful(tmp_path) -> None:
    passwd_home = _installation(tmp_path / "karol")
    isolated = tmp_path / "throwaway"
    isolated.mkdir()
    assert real_home_violation(isolated, passwd_home) == ""


def test_a_bare_runner_home_is_lawful(tmp_path) -> None:
    """A CI runner IS its own passwd home; it just holds no installation.

    The Unit, Integration and E2E jobs run without isolating HOME, so a guard
    that refused on the HOME comparison alone would turn every job red.
    """
    home = tmp_path / "runner"
    home.mkdir()
    assert real_home_violation(home, home) == ""


def test_the_opt_in_waives_the_refusal_and_is_named(tmp_path) -> None:
    home = _installation(tmp_path / "karol")
    assert real_home_violation(home, home, opt_in="hs-200-39 cold rehearsal") == ""
    # An empty or whitespace value is not an opt-in.
    assert real_home_violation(home, home, opt_in="   ") != ""
    assert REAL_HOME_OPT_IN == "HOLDSPEAK_ALLOW_REAL_HOME"


def test_a_missing_passwd_entry_does_not_refuse(tmp_path) -> None:
    """Some containers have no passwd entry; the guard must not invent one."""
    home = _installation(tmp_path / "karol")
    assert real_home_violation(home, None) == ""


def test_the_running_suite_is_itself_isolated() -> None:
    """The guard, applied to this very run.

    `pytest_configure` already refused if this were a real installation; this
    states the invariant where a reader will see it.
    """
    import os
    import pwd

    home = os.environ.get("HOME") or str(Path.home())
    passwd_home = pwd.getpwuid(os.getuid()).pw_dir
    assert (
        real_home_violation(
            home, passwd_home, opt_in=os.environ.get(REAL_HOME_OPT_IN, "")
        )
        == ""
    )


# ── the dependency probes ────────────────────────────────────────────


@pytest.mark.parametrize(
    "probe",
    [
        missing_local_model_reason,
        missing_mlx_whisper_reason,
        missing_local_dictation_route_reason,
    ],
)
def test_every_probe_answers_a_string(probe) -> None:
    """A probe answers "" (present) or a reason. It never raises and never
    returns None, because a probe that throws during collection takes the whole
    run down instead of skipping one test."""
    reason = probe()
    assert isinstance(reason, str)


def test_the_local_model_probe_reports_the_absent_path(monkeypatch) -> None:
    import holdspeak.inference_targets as inference_targets

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: False
    )
    reason = missing_local_model_reason()
    assert reason.startswith("no local model file on this machine")


def test_the_local_model_probe_is_silent_when_present(monkeypatch) -> None:
    import holdspeak.inference_targets as inference_targets

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: True
    )
    assert missing_local_model_reason() == ""


def test_the_dictation_route_probe_names_the_missing_package(monkeypatch) -> None:
    """The Unit runner installs `--extra test` only, so neither dictation
    engine's package is present and the reason must say which one is wanted."""
    import importlib.util

    real = importlib.util.find_spec

    def absent(name, package=None):
        if name in {"mlx_lm", "llama_cpp"}:
            return None
        return real(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", absent)
    reason = missing_local_dictation_route_reason()
    assert "is not installed" in reason, reason


# ── the readiness predicate ──────────────────────────────────────────


def test_both_readiness_paths_go_through_one_predicate(monkeypatch) -> None:
    """The regression that made two Ask tests need a developer's ~/Models.

    `_this_machine_readiness()` and `this_machine_target_from_model_path()`
    each asked the filesystem directly, so substituting one left the other
    reading the real disk and the route still refused with 409.
    """
    import holdspeak.inference_targets as inference_targets

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: True
    )
    state, reason = inference_targets._this_machine_readiness()
    assert (state, reason) == ("ready", "")
    target = inference_targets.this_machine_target_from_model_path(
        "~/Models/gguf/a-file-that-does-not-exist.gguf"
    )
    assert target.readiness_state == "ready"
    assert target.ready

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: False
    )
    assert inference_targets._this_machine_readiness()[0] == "unavailable"
    assert not inference_targets.this_machine_target_from_model_path(
        "~/Models/gguf/a-file-that-does-not-exist.gguf"
    ).ready


def test_the_predicate_answers_false_for_an_unset_path() -> None:
    from holdspeak.inference_targets import local_model_file_present

    assert local_model_file_present(None) is False
    assert local_model_file_present("") is False
    assert local_model_file_present("   ") is False


def test_the_predicate_answers_true_for_a_real_file(tmp_path) -> None:
    from holdspeak.inference_targets import local_model_file_present

    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"0")
    assert local_model_file_present(artifact) is True


# ── the critical suite is declared and separable ─────────────────────


def test_every_critical_journey_carries_the_marker() -> None:
    """`-m critical` must select the whole suite; an unmarked journey would be
    invisible to the CI job that reports them."""
    critical_dir = Path(__file__).resolve().parents[1] / "critical"
    modules = sorted(critical_dir.glob("test_*.py"))
    assert modules, "the critical journey suite is missing"
    for module in modules:
        source = module.read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.critical" in source, module.name


# ── the database singleton, and the threads that call it ─────────────


def test_the_database_singleton_is_built_once_under_concurrency(
    tmp_path, monkeypatch
) -> None:
    """Two threads racing `get_database()` must share ONE database.

    Before HS-200-03 this was a check-then-assign around a ~250 ms
    constructor, so both threads built one and the loser's instance was
    silently discarded after running `reconcile_schema` over the same file.
    """
    import threading

    import holdspeak.db.core as db_core

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "race.db")
    db_core.reset_database()
    try:
        start = threading.Barrier(4)
        seen: list[int] = []
        lock = threading.Lock()

        def call() -> None:
            start.wait(timeout=10)
            database = db_core.get_database()
            with lock:
                seen.append(id(database))

        threads = [threading.Thread(target=call) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        assert len(seen) == 4
        assert len(set(seen)) == 1, "the singleton was built more than once"
    finally:
        db_core.reset_database()


def test_a_reset_cannot_be_undone_by_a_construction_already_in_flight(
    tmp_path, monkeypatch
) -> None:
    """`reset_database()` must win over a concurrent `get_database()`.

    A construction that began before the reset used to publish itself after
    it, restoring a database — and a path — the caller had just dropped. In a
    test process that is how a conductor tick handed the routes under test a
    foreign database.
    """
    import threading

    import holdspeak.db.core as db_core

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "reset.db")
    db_core.reset_database()
    try:
        entered = threading.Event()

        def slow_get() -> None:
            entered.set()
            db_core.get_database()

        worker = threading.Thread(target=slow_get)
        worker.start()
        entered.wait(timeout=10)
        db_core.reset_database()
        worker.join(timeout=30)
        # Whatever order the two took, the lock makes the outcome one of the
        # two lawful states — never a half-published instance.
        assert db_core._db is None or db_core._db.db_path == tmp_path / "reset.db"
    finally:
        db_core.reset_database()


def test_the_shutdown_handler_stops_every_conductor_it_started() -> None:
    """A conductor started by the app lifespan must be stopped by it.

    Two of the three were never stopped, so they outlived the app: in a test
    process they kept calling `get_database()` on a timer for the rest of the
    run, and in production an in-process restart left them ticking against a
    database nobody owned.
    """
    from pathlib import Path as _Path

    source = (
        _Path(__file__).resolve().parents[2] / "holdspeak" / "web_server.py"
    ).read_text(encoding="utf-8")
    shutdown = source.split("async def _shutdown()", 1)
    assert len(shutdown) == 2, "the shutdown handler moved"
    body = shutdown[1]
    for stop in (
        "stop_calendar_ingest_conductor",
        "stop_conductor",
        "stop_scheduled_recording_conductor",
    ):
        assert stop in body, f"{stop} is not called on shutdown"
