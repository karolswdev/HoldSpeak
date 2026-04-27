"""Unit tests for shared plugin activity context."""

from __future__ import annotations

from datetime import datetime

from holdspeak.activity_context import ActivityContextProvider, build_activity_context
from holdspeak.db import MeetingDatabase
from holdspeak.plugins.host import PluginHost


class _CapturePlugin:
    id = "capture"
    version = "1.0"

    def __init__(self) -> None:
        self.context = {}

    def run(self, context):
        self.context = dict(context)
        return {"activity_seen": "activity" in context}


def test_build_activity_context_serializes_recent_records(tmp_path):
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    db.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://example.atlassian.net/browse/HS-805",
        title="HS-805 shared context",
        visit_count=2,
        last_seen_at=datetime(2026, 4, 26, 12, 0),
        entity_type="jira_ticket",
        entity_id="HS-805",
    )

    bundle = build_activity_context(db=db, limit=5).to_dict()

    assert bundle["records"][0]["entity_type"] == "jira_ticket"
    assert bundle["records"][0]["entity_id"] == "HS-805"
    assert bundle["entity_counts"] == {"jira_ticket": 1}
    assert bundle["domain_counts"] == {"example.atlassian.net": 1}
    assert bundle["source_counts"] == {"safari": 1}
    assert bundle["refreshed"] is False


def test_activity_context_provider_can_refresh_once(tmp_path):
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    calls = []

    def importer(**kwargs):
        calls.append(kwargs)
        kwargs["db"].upsert_activity_record(
            source_browser="firefox",
            url="https://miro.com/app/board/uXjVContext/",
            title="Context board",
            entity_type="miro_board",
            entity_id="uXjVContext",
        )
        return []

    provider = ActivityContextProvider(db=db, refresh=True, refresh_once=True, importer=importer)

    first = provider({})
    second = provider({})

    assert len(calls) == 1
    assert first["activity"]["refreshed"] is True
    assert second["activity"]["refreshed"] is False
    assert second["activity"]["records"][0]["entity_type"] == "miro_board"


def test_plugin_host_injects_activity_context_for_any_plugin(tmp_path):
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/12",
        title="PR 12",
        entity_type="github_pull_request",
        entity_id="openai/codex#12",
    )
    plugin = _CapturePlugin()
    host = PluginHost(
        default_timeout_seconds=0.5,
        context_providers=[ActivityContextProvider(db=db, refresh=False)],
    )
    host.register(plugin)

    result = host.execute(
        "capture",
        context={"active_intents": ["delivery"]},
        meeting_id="m1",
        window_id="w1",
        transcript_hash="abc",
    )

    assert result.status == "success"
    assert result.output == {"activity_seen": True}
    assert plugin.context["activity"]["records"][0]["entity_id"] == "openai/codex#12"
