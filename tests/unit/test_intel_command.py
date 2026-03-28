from __future__ import annotations

from datetime import datetime
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
