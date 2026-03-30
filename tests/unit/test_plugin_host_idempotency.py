from __future__ import annotations

from holdspeak.plugins.host import PluginHost, build_idempotency_key


class CountingPlugin:
    id = "counter"
    version = "1.0.0"

    def __init__(self) -> None:
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        self.calls += 1
        return {"calls": self.calls}


def test_build_idempotency_key_is_deterministic() -> None:
    key_one = build_idempotency_key(
        meeting_id="m-1",
        window_id="w-1",
        plugin_id="p-1",
        transcript_hash="hash-123",
    )
    key_two = build_idempotency_key(
        meeting_id="m-1",
        window_id="w-1",
        plugin_id="p-1",
        transcript_hash="hash-123",
    )
    key_three = build_idempotency_key(
        meeting_id="m-1",
        window_id="w-2",
        plugin_id="p-1",
        transcript_hash="hash-123",
    )

    assert key_one == key_two
    assert key_one != key_three


def test_duplicate_plugin_run_returns_deduped_result() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    plugin = CountingPlugin()
    host.register(plugin)

    first = host.execute(
        "counter",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="hash-123",
    )
    second = host.execute(
        "counter",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="hash-123",
    )

    assert first.status == "success"
    assert second.status == "deduped"
    assert second.deduped is True
    assert second.output == first.output
    assert plugin.calls == 1


def test_allow_duplicate_forces_new_execution() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    plugin = CountingPlugin()
    host.register(plugin)

    first = host.execute(
        "counter",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="hash-123",
    )
    second = host.execute(
        "counter",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="hash-123",
        allow_duplicate=True,
    )

    assert first.status == "success"
    assert second.status == "success"
    assert first.output != second.output
    assert plugin.calls == 2
