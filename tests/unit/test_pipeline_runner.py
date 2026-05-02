"""HS-13-06 — pipeline manifest + dependency-graph runner tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.connector_pack_loader import (
    RegisteredPack,
    SOURCE_FIRST_PARTY,
    SOURCE_USER,
    _validate_pipeline_graph,
)
from holdspeak.connector_runtime import (
    NotAPipelineError,
    PipelineRunner,
    UnknownPipelineError,
)
from holdspeak.connector_sdk import (
    ConnectorManifestError,
    ConsumesEntry,
    validate_manifest,
)
from holdspeak.db import MeetingDatabase, reset_database


# ──────────────────────── Manifest validation ────────────────────────


def _pipeline_manifest(**overrides):
    base = {
        "id": "test_pipeline",
        "label": "Test pipeline",
        "version": "0.1.0",
        "kind": "pipeline",
        "capabilities": ["annotations"],
        "permissions": [
            "read:activity_annotations",
            "write:activity_annotations",
        ],
        "consumes": [
            {"pack_id": "gh", "output_kind": "annotations"},
        ],
    }
    base.update(overrides)
    return base


def _producer_manifest(**overrides):
    base = {
        "id": "test_producer",
        "label": "Test producer",
        "version": "0.1.0",
        "kind": "candidate_inference",
        "capabilities": ["candidates"],
        "permissions": ["read:activity_records"],
    }
    base.update(overrides)
    return base


def test_pipeline_manifest_round_trips():
    manifest = validate_manifest(_pipeline_manifest())
    assert manifest.kind == "pipeline"
    assert manifest.consumes == (
        ConsumesEntry(pack_id="gh", output_kind="annotations"),
    )
    again = validate_manifest(manifest.to_payload())
    assert again == manifest


def test_pipeline_requires_non_empty_consumes():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(_pipeline_manifest(consumes=[]))
    codes = {e.code for e in exc_info.value.errors}
    assert "pipeline_requires_consumes" in codes


def test_non_pipeline_must_not_declare_consumes():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(
            _producer_manifest(
                consumes=[{"pack_id": "gh", "output_kind": "annotations"}]
            )
        )
    codes = {e.code for e in exc_info.value.errors}
    assert "consumes_only_on_pipeline" in codes


def test_pipeline_must_declare_matching_read_permissions():
    bad = _pipeline_manifest(permissions=["write:activity_annotations"])
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(bad)
    codes = {e.code for e in exc_info.value.errors}
    assert "pipeline_missing_read_permission" in codes


def test_consumes_rejects_unknown_output_kind():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(
            _pipeline_manifest(
                consumes=[{"pack_id": "gh", "output_kind": "rocket_fuel"}]
            )
        )
    assert any(
        e.code == "unknown_output_kind" for e in exc_info.value.errors
    )


def test_consumes_rejects_duplicate_entries():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(
            _pipeline_manifest(
                consumes=[
                    {"pack_id": "gh", "output_kind": "annotations"},
                    {"pack_id": "gh", "output_kind": "annotations"},
                ]
            )
        )
    assert any(
        e.code == "duplicate_consumes_entry" for e in exc_info.value.errors
    )


def test_freshness_must_be_non_negative_int():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(_pipeline_manifest(pipeline_freshness_seconds=-5))
    assert any(
        e.code == "must_be_non_negative" for e in exc_info.value.errors
    )


# ────────────────────── Cross-pack validation ───────────────────────


def _registered(manifest_dict, source=SOURCE_FIRST_PARTY) -> RegisteredPack:
    manifest = validate_manifest(manifest_dict)
    module = SimpleNamespace(MANIFEST=manifest)
    return RegisteredPack(
        manifest=manifest, source=source, module=module, file_path=None
    )


def test_pipeline_with_unknown_consumes_id_is_rejected():
    pipeline = _registered(
        _pipeline_manifest(
            id="ghost_pipe",
            consumes=[{"pack_id": "no_such_pack", "output_kind": "annotations"}],
        ),
        source=SOURCE_USER,
    )
    surviving, errors = _validate_pipeline_graph((pipeline,))
    assert surviving == ()
    assert len(errors) == 1
    assert errors[0].code == "unknown_consumed_pack"
    assert errors[0].pack_id == "ghost_pipe"


def test_pipeline_cycle_is_rejected():
    pipe_a = _registered(
        _pipeline_manifest(
            id="pipe_a",
            consumes=[{"pack_id": "pipe_b", "output_kind": "annotations"}],
        )
    )
    pipe_b = _registered(
        _pipeline_manifest(
            id="pipe_b",
            consumes=[{"pack_id": "pipe_a", "output_kind": "annotations"}],
        )
    )
    surviving, errors = _validate_pipeline_graph((pipe_a, pipe_b))
    assert {p.manifest.id for p in surviving} == set()
    assert {e.code for e in errors} == {"pipeline_cycle"}
    assert {e.pack_id for e in errors} == {"pipe_a", "pipe_b"}


def test_self_referential_pipeline_is_rejected_as_cycle():
    pipe = _registered(
        _pipeline_manifest(
            id="self_loop",
            consumes=[{"pack_id": "self_loop", "output_kind": "annotations"}],
        )
    )
    surviving, errors = _validate_pipeline_graph((pipe,))
    assert surviving == ()
    assert any(e.code == "pipeline_cycle" for e in errors)


def test_acyclic_pipeline_chain_survives():
    producer = _registered(_producer_manifest(id="prod"))
    pipe_a = _registered(
        _pipeline_manifest(
            id="pipe_a",
            consumes=[{"pack_id": "prod", "output_kind": "candidates"}],
            permissions=[
                "read:activity_meeting_candidates",
                "write:activity_annotations",
            ],
        )
    )
    pipe_b = _registered(
        _pipeline_manifest(
            id="pipe_b",
            consumes=[{"pack_id": "pipe_a", "output_kind": "annotations"}],
        )
    )
    surviving, errors = _validate_pipeline_graph((producer, pipe_a, pipe_b))
    assert errors == ()
    assert {p.manifest.id for p in surviving} == {"prod", "pipe_a", "pipe_b"}


# ─────────────────────────── Runner ─────────────────────────────────


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _producer_pack(*, pack_id: str, run_callable=None) -> RegisteredPack:
    manifest = validate_manifest(
        _producer_manifest(id=pack_id, capabilities=["annotations"])
    )
    module = SimpleNamespace(MANIFEST=manifest)
    if run_callable is not None:
        module.run = run_callable
    return RegisteredPack(
        manifest=manifest, source=SOURCE_FIRST_PARTY, module=module, file_path=None
    )


def _pipeline_pack(
    *,
    pack_id: str,
    consumes_ids: list[str],
    run_callable=None,
    freshness: int = 300,
) -> RegisteredPack:
    manifest = validate_manifest(
        _pipeline_manifest(
            id=pack_id,
            consumes=[{"pack_id": cid, "output_kind": "annotations"} for cid in consumes_ids],
            pipeline_freshness_seconds=freshness,
        )
    )
    module = SimpleNamespace(MANIFEST=manifest)
    if run_callable is not None:
        module.run = run_callable
    return RegisteredPack(
        manifest=manifest, source=SOURCE_FIRST_PARTY, module=module, file_path=None
    )


def test_plan_returns_topological_order_with_target_last(db):
    runs: list[str] = []

    def make_runner(name):
        def _run(_db, **_kwargs):
            runs.append(name)
        return _run

    upstream = _producer_pack(pack_id="up_a", run_callable=make_runner("up_a"))
    upstream_b = _producer_pack(pack_id="up_b", run_callable=make_runner("up_b"))
    pipeline = _pipeline_pack(
        pack_id="pipeline_target",
        consumes_ids=["up_a", "up_b"],
        run_callable=make_runner("pipeline_target"),
    )

    runner = PipelineRunner(db, registry=(upstream, upstream_b, pipeline))
    order = runner.plan("pipeline_target")
    assert order[-1] == "pipeline_target"
    assert set(order) == {"up_a", "up_b", "pipeline_target"}


def test_plan_unknown_id_raises(db):
    runner = PipelineRunner(db, registry=())
    with pytest.raises(UnknownPipelineError):
        runner.plan("nope")


def test_plan_non_pipeline_raises(db):
    pack = _producer_pack(pack_id="prod", run_callable=lambda _db: None)
    runner = PipelineRunner(db, registry=(pack,))
    with pytest.raises(NotAPipelineError):
        runner.plan("prod")


def test_run_executes_each_step_and_records_runs(db):
    """Real first-party packs (`gh.run`, `jira.run`,
    `calendar.run`) all record their own `connector_runs` rows
    via `db.record_connector_run` at completion. The runner
    relies on that contract — fake packs in this test mirror
    it so the assertion below holds."""
    fired: list[str] = []

    def make_runner(name):
        def _run(database, **_kwargs):
            fired.append(name)
            now = datetime(2026, 5, 2, 12, 0, 0)
            database.record_connector_run(
                connector_id=name,
                started_at=now,
                finished_at=now,
                succeeded=True,
            )
        return _run

    upstream = _producer_pack(pack_id="up", run_callable=make_runner("up"))
    pipeline = _pipeline_pack(
        pack_id="pipe",
        consumes_ids=["up"],
        run_callable=make_runner("pipe"),
    )

    runner = PipelineRunner(db, registry=(upstream, pipeline))
    result = runner.run("pipe")

    assert result.succeeded is True
    assert [s.pack_id for s in result.steps] == ["up", "pipe"]
    assert all(s.status == "ran" for s in result.steps)
    assert fired == ["up", "pipe"]
    # Each pack records its own row at completion — the runner's
    # contract is "do not double-record on success".
    assert len(db.list_connector_runs(connector_id="up")) == 1
    assert len(db.list_connector_runs(connector_id="pipe")) == 1


def test_run_skips_fresh_upstream(db):
    """A successful upstream run within the freshness window
    causes the runner to skip re-running it."""
    fired: list[str] = []

    def make_runner(name):
        def _run(_db, **_kwargs):
            fired.append(name)
        return _run

    upstream = _producer_pack(pack_id="up_fresh", run_callable=make_runner("up_fresh"))
    pipeline = _pipeline_pack(
        pack_id="pipe_fresh",
        consumes_ids=["up_fresh"],
        run_callable=make_runner("pipe_fresh"),
        freshness=300,
    )

    # Seed a recent successful run for the upstream so the
    # pipeline runner sees it as fresh.
    now = datetime(2026, 5, 2, 10, 0, 0)
    db.record_connector_run(
        connector_id="up_fresh",
        started_at=now - timedelta(seconds=10),
        finished_at=now - timedelta(seconds=5),
        succeeded=True,
    )

    runner = PipelineRunner(
        db, registry=(upstream, pipeline), now=lambda: now
    )
    result = runner.run("pipe_fresh")

    assert result.succeeded is True
    statuses = {s.pack_id: s.status for s in result.steps}
    assert statuses["up_fresh"] == "skipped_fresh"
    assert statuses["pipe_fresh"] == "ran"
    # Upstream run was NOT invoked.
    assert "up_fresh" not in fired
    # Upstream's existing run row is intact; no new one added.
    assert len(db.list_connector_runs(connector_id="up_fresh")) == 1


def test_run_does_not_skip_target_on_freshness(db):
    """Freshness governs upstream re-runs only — the target
    pipeline always runs, even if its previous run is fresh."""
    fired: list[str] = []

    def make_runner(name):
        def _run(_db, **_kwargs):
            fired.append(name)
        return _run

    upstream = _producer_pack(pack_id="up2", run_callable=make_runner("up2"))
    pipeline = _pipeline_pack(
        pack_id="pipe2",
        consumes_ids=["up2"],
        run_callable=make_runner("pipe2"),
        freshness=300,
    )
    now = datetime(2026, 5, 2, 10, 0, 0)
    db.record_connector_run(
        connector_id="pipe2",
        started_at=now - timedelta(seconds=5),
        finished_at=now - timedelta(seconds=4),
        succeeded=True,
    )

    runner = PipelineRunner(db, registry=(upstream, pipeline), now=lambda: now)
    result = runner.run("pipe2")
    assert "pipe2" in fired
    assert result.succeeded is True


def test_run_aborts_on_failed_step(db):
    """A step whose `run` raises is reported as `failed` and
    aborts the pipeline; later steps are not executed."""
    def _bad_run(_db, **_kwargs):
        raise RuntimeError("upstream blew up")

    upstream = _producer_pack(pack_id="up_bad", run_callable=_bad_run)
    pipeline = _pipeline_pack(
        pack_id="pipe_bad",
        consumes_ids=["up_bad"],
        run_callable=lambda _db, **_kwargs: None,
    )

    runner = PipelineRunner(db, registry=(upstream, pipeline))
    result = runner.run("pipe_bad")
    assert result.succeeded is False
    assert [s.pack_id for s in result.steps] == ["up_bad"]
    assert result.steps[0].status == "failed"
    assert "upstream blew up" in (result.steps[0].error or "")
    # The failure is also recorded in connector_runs.
    [row] = db.list_connector_runs(connector_id="up_bad")
    assert row.succeeded is False


def test_run_reports_missing_runner_when_pack_has_no_run_callable(db):
    """An upstream pack with no fresh successful run AND no
    `run` callable cannot proceed — the pipeline aborts with a
    `missing_runner` step error."""
    upstream = _producer_pack(pack_id="up_no_run")  # no run_callable
    pipeline = _pipeline_pack(
        pack_id="pipe_stuck",
        consumes_ids=["up_no_run"],
        run_callable=lambda _db, **_kwargs: None,
    )

    runner = PipelineRunner(db, registry=(upstream, pipeline))
    result = runner.run("pipe_stuck")
    assert result.succeeded is False
    assert result.steps[0].status == "missing_runner"


def test_first_party_packs_expose_run_callables():
    """gh / jira / calendar packs all carry a `run(db)` entry
    point that pipelines can dispatch to. Firefox is event-
    driven and intentionally omits one."""
    from holdspeak.connector_packs import (
        calendar_activity,
        firefox_ext,
        github_cli,
        jira_cli,
    )

    assert callable(getattr(github_cli, "run", None))
    assert callable(getattr(jira_cli, "run", None))
    assert callable(getattr(calendar_activity, "run", None))
    assert getattr(firefox_ext, "run", None) is None
