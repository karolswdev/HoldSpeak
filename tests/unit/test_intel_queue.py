"""Unit tests for deferred-intel queue worker lifecycle."""

from __future__ import annotations

import time
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import holdspeak.intel_queue as intel_queue_module


def test_worker_start_and_stop(monkeypatch) -> None:
    calls = []

    def fake_drain(
        model_path=None,
        *,
        provider="local",
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url=None,
        cloud_reasoning_effort=None,
        cloud_store=False,
        retry_base_seconds=30,
        retry_max_seconds=900,
        retry_max_attempts=6,
        include_scheduled=False,
        max_jobs=None,
    ):
        _ = (
            provider,
            cloud_model,
            cloud_api_key_env,
            cloud_base_url,
            cloud_reasoning_effort,
            cloud_store,
            retry_base_seconds,
            retry_max_seconds,
            retry_max_attempts,
            include_scheduled,
        )
        _ = max_jobs
        calls.append(model_path)
        return 0

    monkeypatch.setattr(intel_queue_module, "drain_intel_queue", fake_drain)
    monkeypatch.setattr(
        intel_queue_module,
        "get_database",
        lambda: SimpleNamespace(
            get_intel_queue_summary=lambda: SimpleNamespace(
                total_jobs=0,
                queued_jobs=0,
                running_jobs=0,
                failed_jobs=0,
                queued_due_jobs=0,
                scheduled_retry_jobs=0,
                next_retry_at=None,
            )
        ),
    )

    worker = intel_queue_module.start_intel_queue_worker(model_path="model.gguf", poll_seconds=1.0)
    time.sleep(0.02)
    worker.stop(timeout=1.0)

    assert calls
    assert worker.model_path == "model.gguf"
    assert worker.poll_seconds == 5.0
    assert worker.is_alive() is False


def test_compute_retry_delay_seconds_uses_exponential_backoff() -> None:
    assert intel_queue_module._compute_retry_delay_seconds(1) == 30
    assert intel_queue_module._compute_retry_delay_seconds(2) == 60
    assert intel_queue_module._compute_retry_delay_seconds(3) == 120
    assert intel_queue_module._compute_retry_delay_seconds(20) == 900


def test_retry_or_fail_job_requeues_before_max_attempts() -> None:
    calls = {"retry": [], "fail": [], "history": []}

    class _FakeDb:
        def retry_intel_job(self, meeting_id, error, *, retry_at, attempt, max_attempts):
            calls["retry"].append((meeting_id, error, retry_at, attempt, max_attempts))

        def fail_intel_job(self, meeting_id, error):
            calls["fail"].append((meeting_id, error))

        def record_intel_job_attempt(self, meeting_id, *, attempt, outcome, error=None, retry_at=None):
            calls["history"].append((meeting_id, attempt, outcome, error, retry_at))

    job = SimpleNamespace(meeting_id="meeting-1", attempts=2)
    intel_queue_module._retry_or_fail_job(_FakeDb(), job, "Deferred intel failed: timeout")

    assert len(calls["retry"]) == 1
    assert calls["retry"][0][0] == "meeting-1"
    assert calls["retry"][0][3] == 2
    assert calls["retry"][0][4] == intel_queue_module.RETRY_MAX_ATTEMPTS
    assert calls["fail"] == []
    assert calls["history"][0][2] == "scheduled_retry"


def test_retry_or_fail_job_marks_failed_after_max_attempts() -> None:
    calls = {"retry": [], "fail": [], "history": []}

    class _FakeDb:
        def retry_intel_job(self, meeting_id, error, *, retry_at, attempt, max_attempts):
            calls["retry"].append((meeting_id, error, retry_at, attempt, max_attempts))

        def fail_intel_job(self, meeting_id, error):
            calls["fail"].append((meeting_id, error))

        def record_intel_job_attempt(self, meeting_id, *, attempt, outcome, error=None, retry_at=None):
            calls["history"].append((meeting_id, attempt, outcome, error, retry_at))

    job = SimpleNamespace(meeting_id="meeting-1", attempts=intel_queue_module.RETRY_MAX_ATTEMPTS)
    intel_queue_module._retry_or_fail_job(_FakeDb(), job, "Deferred intel failed: timeout")

    assert calls["retry"] == []
    assert len(calls["fail"]) == 1
    assert "after" in calls["fail"][0][1]
    assert calls["history"][0][2] == "terminal_failure"


def test_compute_failure_rate_percent() -> None:
    assert intel_queue_module._compute_failure_rate_percent(total_jobs=0, failed_jobs=0) == 0.0
    assert intel_queue_module._compute_failure_rate_percent(total_jobs=10, failed_jobs=3) == 30.0


def test_failure_alert_hysteresis_triggers_once_per_incident(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = None
    worker.failure_alert_webhook_header_value = None
    worker._failure_alert_above_since = None
    worker._failure_alert_sent = False

    webhook_calls = []
    monkeypatch.setattr(worker, "_post_failure_alert_webhook", lambda **kwargs: webhook_calls.append(kwargs))

    summary_high = SimpleNamespace(
        total_jobs=10,
        queued_jobs=4,
        running_jobs=0,
        failed_jobs=6,
        queued_due_jobs=2,
        scheduled_retry_jobs=2,
        next_retry_at=None,
    )
    summary_low = SimpleNamespace(
        total_jobs=10,
        queued_jobs=6,
        running_jobs=0,
        failed_jobs=1,
        queued_due_jobs=4,
        scheduled_retry_jobs=1,
        next_retry_at=None,
    )

    t0 = datetime(2026, 1, 1, 12, 0, 0)
    worker._update_failure_alert_state(summary_high, now=t0)
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=4))
    assert webhook_calls == []

    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=5))
    assert len(webhook_calls) == 1
    assert webhook_calls[0]["event"] == "triggered"

    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=8))
    assert len(webhook_calls) == 1

    worker._update_failure_alert_state(summary_low, now=t0 + timedelta(minutes=9))
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=10))
    worker._update_failure_alert_state(summary_high, now=t0 + timedelta(minutes=15))
    assert len(webhook_calls) == 3
    assert [call["event"] for call in webhook_calls] == ["triggered", "resolved", "triggered"]


def test_post_failure_alert_webhook_posts_json_payload(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = "X-HoldSpeak-Token"
    worker.failure_alert_webhook_header_value = "secret-token"

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return b"ok"

    def _fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = request.data.decode("utf-8")
        captured["header"] = request.headers.get("X-holdspeak-token")
        return _Resp()

    monkeypatch.setattr(intel_queue_module.urlrequest, "urlopen", _fake_urlopen)

    summary = SimpleNamespace(
        total_jobs=3,
        queued_jobs=2,
        running_jobs=0,
        failed_jobs=1,
        queued_due_jobs=1,
        scheduled_retry_jobs=1,
        next_retry_at=datetime(2026, 1, 1, 12, 5, 0),
    )
    now = datetime(2026, 1, 1, 12, 0, 0)
    worker._post_failure_alert_webhook(summary=summary, failure_rate_percent=33.3, now=now)

    assert captured["url"] == "https://example.test/hook"
    assert captured["timeout"] == intel_queue_module.RETRY_FAILURE_WEBHOOK_TIMEOUT_SECONDS
    assert captured["header"] == "secret-token"
    payload = json.loads(captured["body"])
    assert payload["type"] == "intel_queue_failure_alert"
    assert payload["event"] == "triggered"
    assert "triggered_at" in payload
    assert payload["queue"]["failed_jobs"] == 1


def test_post_failure_alert_webhook_resolved_payload(monkeypatch) -> None:
    worker = intel_queue_module.IntelQueueWorker.__new__(intel_queue_module.IntelQueueWorker)
    worker.failure_alert_percent = 50.0
    worker.failure_alert_hysteresis_seconds = 300.0
    worker.failure_alert_webhook_url = "https://example.test/hook"
    worker.failure_alert_webhook_header_name = None
    worker.failure_alert_webhook_header_value = None

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return b"ok"

    def _fake_urlopen(request, timeout):
        _ = timeout
        captured["body"] = request.data.decode("utf-8")
        return _Resp()

    monkeypatch.setattr(intel_queue_module.urlrequest, "urlopen", _fake_urlopen)

    summary = SimpleNamespace(
        total_jobs=5,
        queued_jobs=4,
        running_jobs=0,
        failed_jobs=0,
        queued_due_jobs=2,
        scheduled_retry_jobs=1,
        next_retry_at=None,
    )
    above_since = datetime(2026, 1, 1, 12, 0, 0)
    now = datetime(2026, 1, 1, 12, 12, 0)
    worker._post_failure_alert_webhook(
        summary=summary,
        failure_rate_percent=0.0,
        now=now,
        event="resolved",
        above_since=above_since,
    )

    payload = json.loads(captured["body"])
    assert payload["type"] == "intel_queue_failure_alert"
    assert payload["event"] == "resolved"
    assert payload["resolved_at"] == now.isoformat()
    assert payload["above_since"] == above_since.isoformat()
