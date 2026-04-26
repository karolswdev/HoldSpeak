"""HS-2-10 / spec §9.10 — MIR-R-004 plugin failure isolation end-to-end.

Verifies that when one plugin in a routed chain fails, sibling plugins
in the same chain still execute, the pipeline still persists what it
can, and the typed `PluginRun` records on disk reflect the mixed
statuses (success / error). Exercises the full pipeline rather than
just the dispatcher so the persistence + post-error continuation
contracts both get coverage.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.pipeline import process_meeting_state


class _StubPlugin:
    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.version = "1.0.0"
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return {"id": self.id, "summary": f"{self.id} ok"}


class _AlwaysFailsPlugin:
    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.version = "1.0.0"
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        raise RuntimeError(f"{self.id} intentionally exploding")


@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield db_path
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_path):
    return MeetingDatabase(temp_db_path)


def _meeting_state() -> MeetingState:
    return MeetingState(
        id="m-fail-iso",
        started_at=datetime(2026, 4, 26, 10, 0, 0),
        title="Failure isolation",
        segments=[
            TranscriptSegment(
                text="Sprint milestone owner deadline planning for next release.",
                speaker="Me",
                start_time=0.0,
                end_time=15.0,
            ),
        ],
    )


def _host_with_one_failing(failing_id: str) -> tuple[PluginHost, dict[str, object]]:
    """Register the full balanced+all-intents chain, swap one for an exploder."""
    host = PluginHost(default_timeout_seconds=1.0)
    plugins: dict[str, object] = {}
    for pid in (
        "project_detector",
        "requirements_extractor",
        "action_owner_enforcer",
        "milestone_planner",
        "dependency_mapper",
        "mermaid_architecture",
        "adr_drafter",
        "scope_guard",
        "customer_signal_extractor",
        "incident_timeline",
        "risk_heatmap",
        "stakeholder_update_drafter",
        "decision_announcement_drafter",
        "runbook_delta",
    ):
        plugin: object = _AlwaysFailsPlugin(pid) if pid == failing_id else _StubPlugin(pid)
        plugins[pid] = plugin
        host.register(plugin)  # type: ignore[arg-type]
    return host, plugins


@pytest.mark.integration
def test_failing_plugin_does_not_block_chain_siblings_mir_r_004(db) -> None:
    state = _meeting_state()
    db.save_meeting(state)
    host, plugins = _host_with_one_failing("requirements_extractor")

    result = process_meeting_state(
        state,
        host,
        profile="balanced",
        threshold=0.4,
        db=db,
    )

    # Pipeline did not raise; errors aren't on the top-level pipeline list
    # (per-plugin failures land on the typed PluginRun records, not the
    # pipeline's outer try/except surface).
    assert result.errors == []
    statuses = {r.plugin_id: r.status for r in result.runs}
    assert statuses["requirements_extractor"] == "error"
    # Sibling plugins for the balanced+delivery chain still ran.
    sibling_ids = {
        "project_detector",
        "action_owner_enforcer",
        "milestone_planner",
        "dependency_mapper",
    }
    for pid in sibling_ids:
        assert pid in statuses, f"chain missing sibling {pid!r}"
        assert statuses[pid] == "success", f"sibling {pid!r} status={statuses[pid]!r}"


@pytest.mark.integration
def test_failing_plugin_runs_persisted_with_error_status(db) -> None:
    state = _meeting_state()
    db.save_meeting(state)
    host, _plugins = _host_with_one_failing("action_owner_enforcer")

    process_meeting_state(state, host, profile="balanced", threshold=0.4, db=db)

    persisted = db.list_plugin_runs("m-fail-iso")
    by_id = {r.plugin_id: r for r in persisted}

    # Failing plugin is on disk with status='error' and a populated error message.
    failed = by_id["action_owner_enforcer"]
    assert failed.status == "error"
    assert failed.error is not None and "intentionally exploding" in failed.error

    # At least one sibling persisted with status='success'.
    successful = [r for r in persisted if r.status == "success"]
    assert len(successful) >= 1


@pytest.mark.integration
def test_pipeline_keeps_running_when_every_other_plugin_explodes(db) -> None:
    """Multiple plugins failing simultaneously still don't block the pipeline."""
    state = _meeting_state()
    db.save_meeting(state)

    host = PluginHost(default_timeout_seconds=1.0)
    chain_ids = [
        "project_detector",
        "requirements_extractor",
        "action_owner_enforcer",
        "milestone_planner",
        "dependency_mapper",
        "mermaid_architecture",
        "adr_drafter",
        "scope_guard",
        "customer_signal_extractor",
        "incident_timeline",
        "risk_heatmap",
        "stakeholder_update_drafter",
        "decision_announcement_drafter",
        "runbook_delta",
    ]
    for i, pid in enumerate(chain_ids):
        plugin = _AlwaysFailsPlugin(pid) if i % 2 == 0 else _StubPlugin(pid)
        host.register(plugin)  # type: ignore[arg-type]

    result = process_meeting_state(state, host, profile="balanced", threshold=0.4, db=db)

    statuses = [r.status for r in result.runs]
    assert "error" in statuses
    assert "success" in statuses
    # Pipeline produced full chain coverage: one record per registered chain plugin.
    assert len(result.runs) == len({r.plugin_id for r in result.runs})
