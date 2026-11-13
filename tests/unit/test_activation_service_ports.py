"""Moved setup work retains failed baselines and content-free source receipts."""
from contextlib import closing
from types import SimpleNamespace

from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.watch_service import WatchService
from tests.watch_seed import seed_watch

OWNER = Principal(PrincipalKind.OWNER, "activation")


def test_activated_watches_keep_a_failed_baseline_pending_and_continue(tmp_path):
    with closing(Database(tmp_path / "watches.db")) as db:
        for name in ("failed", "ready"):
            seed_watch(db, watch_id=name, connector_id="gh", query_kind="pull_requests",
                       query={"repository": f"acme/{name}"})
            db.automations.update_watch_spec(name, baseline_state="stale")

        def fetch(principal, **kwargs):
            if kwargs["query"]["repository"] == "acme/failed":
                raise RuntimeError("provider unavailable")
            return [{"number": 3, "state": "open", "title": "Three"}]

        service = WatchService(db, snapshot_fetcher=fetch)
        service.baseline_activated(OWNER, [{}, {"watch_id": "failed"}, {"watch_id": "ready"}])
        failed = db.automations.get_watch("failed")
        ready = db.automations.get_watch("ready")
        assert failed["baseline_state"] == "pending"
        assert ready["baseline_state"] == "established"
        assert ready["snapshot"]
        assert db.automations.list_events() == []


def test_refresh_sources_supplies_only_enabled_identities_and_https_hosts():
    def source(id, url, enabled=True):
        return SimpleNamespace(id=id, url=url, enabled=enabled)

    config = SimpleNamespace(calendar=SimpleNamespace(sources=[
        source("private", "https://user:secret@calendar.example/private?token=secret"),
        source("file", "/tmp/calendar.ics"), source("bad", "https://["),
        source("disabled", "https://disabled.example", False),
    ]))
    conductor = CalendarIngestConductor(config_loader=lambda: config)
    assert conductor.refresh_sources() == [
        {"source_id": "private", "host": "calendar.example"}, {"source_id": "file"},
        {"source_id": "bad", "host": ""},
    ]


def test_thread_event_tap_detaches_without_replacing_a_newer_tap():
    from holdspeak.services.thread_service import ThreadService

    service = object.__new__(ThreadService)
    sent, first, second = [], [], []
    service._broadcast = lambda kind, data: sent.append((kind, data)) or "sent"
    detach_first = service.tap_events(lambda kind, data: first.append((kind, data)))
    detach_second = service.tap_events(lambda kind, data: second.append((kind, data)))
    assert service._broadcast("text", "one") == "sent"
    detach_first()
    assert service._broadcast("text", "two") == "sent"
    detach_second()
    assert service._broadcast("text", "three") == "sent"
    assert sent == [("text", "one"), ("text", "two"), ("text", "three")]
    assert first == [("text", "one")]
    assert second == [("text", "one"), ("text", "two")]
