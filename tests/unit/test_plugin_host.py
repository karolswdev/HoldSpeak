from __future__ import annotations

import time

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.host import PluginHost


class EchoPlugin:
    id = "echo"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {"echo": context.get("text", "")}


class FailingPlugin:
    id = "failing"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        raise RuntimeError("boom")


class SlowPlugin:
    id = "slow"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        sleep_seconds = float(context.get("sleep_seconds", 0.1))
        time.sleep(sleep_seconds)
        return {"slept": sleep_seconds}


class HeavyPlugin:
    id = "heavy"
    version = "1.0.0"
    execution_mode = "deferred"

    def __init__(self) -> None:
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return {"processed": bool(context), "calls": self.calls}


def test_plugin_host_register_and_execute_success() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    host.register(EchoPlugin())

    result = host.execute(
        "echo",
        context={"text": "hello"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "success"
    assert result.plugin_id == "echo"
    assert result.output == {"echo": "hello"}
    assert result.deduped is False


def test_plugin_host_returns_error_for_plugin_exception() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    host.register(FailingPlugin())

    result = host.execute(
        "failing",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "error"
    assert result.error is not None
    assert "RuntimeError" in result.error


def test_plugin_host_returns_timeout_for_slow_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.01)
    host.register(SlowPlugin())

    result = host.execute(
        "slow",
        context={"sleep_seconds": 0.2},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "timeout"
    assert result.error is not None
    assert "Timed out" in result.error


def test_plugin_host_chain_isolates_failure_and_continues() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    host.register(FailingPlugin())
    host.register(EchoPlugin())

    results = host.execute_chain(
        ["failing", "echo"],
        context={"text": "next"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert len(results) == 2
    assert results[0].plugin_id == "failing"
    assert results[0].status == "error"
    assert results[1].plugin_id == "echo"
    assert results[1].status == "success"
    assert results[1].output == {"echo": "next"}


def test_builtin_plugins_register_and_execute() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    registered = register_builtin_plugins(host)
    assert "requirements_extractor" in registered
    assert "incident_timeline" in registered

    result = host.execute(
        "requirements_extractor",
        context={
            "transcript": "Architecture proposal with trade-offs and dependencies.",
            "active_intents": ["architecture"],
        },
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="hash-1",
    )
    assert result.status == "success"
    assert result.output is not None
    assert result.output["plugin_id"] == "requirements_extractor"
    assert result.output["token_count"] > 0


def test_plugin_host_defers_heavy_plugins_through_queue() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    plugin = HeavyPlugin()
    host.register(plugin)

    queued = host.execute(
        "heavy",
        context={"text": "large context"},
        meeting_id="m-queue",
        window_id="w-001",
        transcript_hash="hash-queue",
    )
    assert queued.status == "queued"
    assert plugin.calls == 0
    assert queued.output is not None
    assert queued.output["deferred"] is True

    queued_again = host.execute(
        "heavy",
        context={"text": "large context"},
        meeting_id="m-queue",
        window_id="w-001",
        transcript_hash="hash-queue",
    )
    assert queued_again.status == "deduped"
    assert plugin.calls == 0

    deferred = host.list_deferred_runs(meeting_id="m-queue")
    assert len(deferred) == 1
    assert deferred[0].plugin_id == "heavy"
    assert deferred[0].meeting_id == "m-queue"

    processed = host.process_next_deferred_run()
    assert processed is not None
    assert processed.status == "success"
    assert plugin.calls == 1

    assert host.list_deferred_runs() == []
    metrics = host.get_metrics()
    assert metrics["queued"] == 1
    assert metrics["deduped"] == 1
    assert metrics["success"] == 1
