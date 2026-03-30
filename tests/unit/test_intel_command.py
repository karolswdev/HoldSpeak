from __future__ import annotations

from datetime import datetime
import json
from types import SimpleNamespace

import holdspeak.commands.intel as intel_command
from holdspeak.db import IntelJob


def _meeting_cfg(model: str = "model.gguf") -> SimpleNamespace:
    return SimpleNamespace(
        intel_realtime_model=model,
        intel_provider="local",
        intel_cloud_model="gpt-5-mini",
        intel_cloud_api_key_env="OPENAI_API_KEY",
        intel_cloud_base_url=None,
        intel_cloud_reasoning_effort=None,
        intel_cloud_store=False,
        intel_retry_base_seconds=30,
        intel_retry_max_seconds=900,
        intel_retry_max_attempts=6,
    )


def test_run_intel_command_lists_jobs(monkeypatch, capsys) -> None:
    jobs = [
        IntelJob(
            meeting_id="meeting-1",
            status="queued",
            transcript_hash="abc123",
            requested_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 10, 0, 0),
            attempts=0,
            last_error=None,
            meeting_title="Quarterly Planning",
            started_at=datetime(2024, 1, 15, 9, 0, 0),
            intel_status_detail="Queued for later processing.",
        )
    ]

    class FakeDB:
        def list_intel_jobs(self, *, status=None, limit=20):
            assert status == "all"
            assert limit == 20
            return jobs

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())
    monkeypatch.setattr(
        intel_command,
        "Config",
        SimpleNamespace(load=lambda: SimpleNamespace(meeting=_meeting_cfg("model.gguf"))),
    )
    monkeypatch.setattr(intel_command, "get_intel_runtime_status", lambda *args, **kwargs: (True, None))

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=False,
            retry=None,
            retry_failed=False,
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "Runtime: ready" in captured.out
    assert "Quarterly Planning" in captured.out
    assert "[queued]" in captured.out


def test_run_intel_command_process_reports_runtime_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(intel_command, "get_database", lambda: object())
    monkeypatch.setattr(
        intel_command,
        "Config",
        SimpleNamespace(load=lambda: SimpleNamespace(meeting=_meeting_cfg("missing.gguf"))),
    )
    monkeypatch.setattr(
        intel_command,
        "get_intel_runtime_status",
        lambda *args, **kwargs: (False, "Intel model not found"),
    )

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=True,
            retry=None,
            retry_failed=False,
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "runtime unavailable" in captured.err.lower()


def test_run_intel_command_retry_failed_requeues_jobs(monkeypatch, capsys) -> None:
    jobs = [
        IntelJob(
            meeting_id="meeting-1",
            status="failed",
            transcript_hash="abc123",
            requested_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 10, 5, 0),
            attempts=1,
            last_error="Deferred intel failed",
        ),
        IntelJob(
            meeting_id="meeting-2",
            status="failed",
            transcript_hash="def456",
            requested_at=datetime(2024, 1, 16, 10, 0, 0),
            updated_at=datetime(2024, 1, 16, 10, 5, 0),
            attempts=2,
            last_error="Deferred intel failed",
        ),
    ]
    requeued: list[str] = []

    class FakeDB:
        def list_intel_jobs(self, *, status=None, limit=20):
            assert status == "failed"
            assert limit == 20
            return jobs

        def requeue_intel_job(self, meeting_id: str, *, reason: str | None = None) -> bool:
            assert reason == "Manual retry requested from CLI."
            requeued.append(meeting_id)
            return True

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=False,
            retry=None,
            retry_failed=True,
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert requeued == ["meeting-1", "meeting-2"]
    assert "Requeued 2 failed deferred-intel job(s)." in captured.out


def test_run_intel_command_process_retry_now_overrides_backoff(monkeypatch, capsys) -> None:
    drain_kwargs = {}

    class FakeDB:
        pass

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())
    monkeypatch.setattr(
        intel_command,
        "Config",
        SimpleNamespace(load=lambda: SimpleNamespace(meeting=_meeting_cfg("model.gguf"))),
    )
    monkeypatch.setattr(intel_command, "get_intel_runtime_status", lambda *args, **kwargs: (True, None))

    def _fake_drain(*args, **kwargs):
        _ = args
        drain_kwargs.update(kwargs)
        return 1

    monkeypatch.setattr(intel_command, "drain_intel_queue", _fake_drain)

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=True,
            retry=None,
            retry_failed=False,
            status="all",
            limit=20,
            max_jobs=3,
            retry_mode="retry-now",
        )
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "Processed 1 deferred-intel job(s)." in captured.out
    assert drain_kwargs["include_scheduled"] is True


def test_run_intel_command_route_dry_run_emits_route_json(monkeypatch, capsys) -> None:
    meeting = SimpleNamespace(
        id="meeting-42",
        title="Routing Review",
        tags=["Architecture", "Delivery"],
        segments=[
            SimpleNamespace(speaker="Me", text="We need an architecture decision record.", end_time=12.0),
            SimpleNamespace(speaker="Remote", text="Track delivery milestones and dependencies.", end_time=24.5),
        ],
        duration=24.5,
        transcript_hash=lambda: "hash-42",
    )

    class FakeDB:
        def get_meeting(self, meeting_id: str):
            assert meeting_id == "meeting-42"
            return meeting

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())
    monkeypatch.setattr(
        intel_command,
        "Config",
        SimpleNamespace(load=lambda: SimpleNamespace(meeting=_meeting_cfg("model.gguf"))),
    )

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=False,
            retry=None,
            retry_failed=False,
            route_dry_run="meeting-42",
            reroute=None,
            profile="architect",
            threshold=0.55,
            override_intents="delivery,comms",
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["success"] is True
    assert payload["mode"] == "dry_run"
    assert payload["meeting_id"] == "meeting-42"
    assert payload["route"]["profile"] == "architect"
    assert payload["route"]["override_intents"] == ["delivery", "comms"]


def test_run_intel_command_reroute_requires_profile(monkeypatch, capsys) -> None:
    class FakeDB:
        pass

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=False,
            retry=None,
            retry_failed=False,
            route_dry_run=None,
            reroute="meeting-42",
            profile=None,
            threshold=None,
            override_intents=None,
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert "requires `--profile`" in captured.err


def test_run_intel_command_reroute_persists_intent_window(monkeypatch, capsys) -> None:
    recorded_window: dict[str, object] = {}
    meeting = SimpleNamespace(
        id="meeting-77",
        title="Incident Triage",
        tags=["incident"],
        segments=[
            SimpleNamespace(speaker="Me", text="Investigate outage timeline.", end_time=8.0),
            SimpleNamespace(speaker="Remote", text="Draft stakeholder update.", end_time=16.0),
        ],
        duration=16.0,
        transcript_hash=lambda: "meeting-hash-77",
    )

    class FakeDB:
        def get_meeting(self, meeting_id: str):
            assert meeting_id == "meeting-77"
            return meeting

        def record_intent_window(self, **kwargs):
            recorded_window.update(kwargs)

    monkeypatch.setattr(intel_command, "get_database", lambda: FakeDB())
    monkeypatch.setattr(
        intel_command,
        "Config",
        SimpleNamespace(load=lambda: SimpleNamespace(meeting=_meeting_cfg("model.gguf"))),
    )

    rc = intel_command.run_intel_command(
        SimpleNamespace(
            process=False,
            retry=None,
            retry_failed=False,
            route_dry_run=None,
            reroute="meeting-77",
            profile="incident",
            threshold=0.65,
            override_intents="incident",
            status="all",
            limit=20,
            max_jobs=None,
        )
    )

    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["success"] is True
    assert payload["mode"] == "reroute"
    assert payload["persisted_window_id"] == "meeting-77:cli-reroute"
    assert recorded_window["meeting_id"] == "meeting-77"
    assert recorded_window["window_id"] == "meeting-77:cli-reroute"
    assert recorded_window["profile"] == "incident"
    assert recorded_window["override_intents"] == ["incident"]
    assert recorded_window["metadata"]["source"] == "cli_reroute"
