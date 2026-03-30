from __future__ import annotations

import logging
import time

from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.router import get_router_counters, preview_route, reset_router_counters


class _SuccessPlugin:
    id = "success"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {"ok": bool(context)}


class _FailingPlugin:
    id = "failing"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        raise RuntimeError("boom")


class _SlowPlugin:
    id = "slow"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        time.sleep(float(context.get("sleep_seconds", 0.05)))
        return {"slept": True}


def test_router_counters_track_routed_and_dropped_windows() -> None:
    reset_router_counters()
    preview_route(
        profile="balanced",
        intent_scores={"architecture": 0.91},
        threshold=0.6,
    )
    preview_route(
        profile="balanced",
        intent_scores={"architecture": 0.11, "delivery": 0.2},
        threshold=0.6,
    )
    counters = get_router_counters()
    assert counters["routed_windows"] == 1
    assert counters["dropped_windows"] == 1


def test_plugin_host_metrics_count_success_error_timeout_and_deduped() -> None:
    host = PluginHost(default_timeout_seconds=0.01)
    host.register(_SuccessPlugin())
    host.register(_FailingPlugin())
    host.register(_SlowPlugin())

    first = host.execute(
        "success",
        context={"value": 1},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="h-1",
    )
    second = host.execute(
        "success",
        context={"value": 2},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="h-1",
    )
    failing = host.execute(
        "failing",
        context={},
        meeting_id="m-1",
        window_id="w-2",
        transcript_hash="h-2",
    )
    timeout = host.execute(
        "slow",
        context={"sleep_seconds": 0.2},
        meeting_id="m-1",
        window_id="w-3",
        transcript_hash="h-3",
    )

    assert first.status == "success"
    assert second.status == "deduped"
    assert failing.status == "error"
    assert timeout.status == "timeout"

    metrics = host.get_metrics()
    assert metrics["runs_total"] == 4
    assert metrics["success"] == 1
    assert metrics["deduped"] == 1
    assert metrics["error"] == 1
    assert metrics["timeout"] == 1
    assert metrics["blocked"] == 0


def test_plugin_host_structured_logs_include_fields_and_redact_secrets(caplog) -> None:
    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_SuccessPlugin())

    caplog.set_level(logging.INFO, logger="holdspeak.plugins.host")
    host.execute(
        "success",
        context={
            "active_intents": ["delivery"],
            "api_key": "sk-live-very-secret",
            "auth_token": "top-secret-token",
            "note": "safe-value",
        },
        meeting_id="m-99",
        window_id="w-07",
        transcript_hash="hash-99",
    )

    joined = "\n".join(record.message for record in caplog.records if record.name == "holdspeak.plugins.host")
    assert '"meeting_id":"m-99"' in joined
    assert '"window_id":"w-07"' in joined
    assert '"plugin_id":"success"' in joined
    assert '"intent_set":["delivery"]' in joined
    assert "sk-live-very-secret" not in joined
    assert "top-secret-token" not in joined
    assert '"redacted_keys":["api_key","auth_token"]' in joined
