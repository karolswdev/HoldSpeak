"""PERF-HUB 2026-10-28: the three desk reads stay fast on a big event log.

The owner: "I open a window and often need to wait 2-3 seconds. Even on
local". On his desk ``pipeline_events`` held 1.39 M rows, and three reads
scanned it on every needs-you, settings and projections read (the Room's
receipts by ``method``, the remote hosts and the remote origins by
``origin``). The two indexes in ``holdspeak/db/schema.py`` turn those scans
into searches; the routes also run their work off the event loop.

This fence boots the real hub (``MeetingWebServer`` + ``TestClient``) on a
database seeded with 300,000 synthetic pipeline events (all inside the last
30 days, few remote) and holds each read under 300 ms. The budget is
generous: it fences a table scan, not the machine. At 50,000 rows a scan
still answered in under 100 ms, so the fence could not fail; at 300,000 the
reads without the two indexes take longer than the budget.
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_desk_needs_you import _boot  # noqa: E402

BUDGET_S = 0.300
EVENTS = 300_000
READ_METHODS = ("list_meetings", "board", "proposal_needs", "people_store_state", "room")


def _seed_events(db, project_ids: list[str]) -> None:
    now = time.time()
    rows = []
    for i in range(EVENTS):
        pid = project_ids[i % len(project_ids)]
        method = READ_METHODS[i % len(READ_METHODS)] if i % 50 else "update_project"
        origin = "remote" if i % 10_000 == 0 else "local"
        rows.append((
            uuid.uuid4().hex, now - (EVENTS - i) * 5.0, "ProjectService", method,
            "owner", "owner", f'{{"project_id": "{pid}", "n": {i}}}', "{}",
            0.5, origin, "100.64.0.9" if origin == "remote" else "",
        ))
    with db._connection() as conn:
        conn.executemany(
            "INSERT INTO pipeline_events (event_id, timestamp, service, method, "
            "principal_kind, principal_identity, args_summary, result_summary, "
            "duration_ms, origin, caller) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _timed(hub, path: str) -> float:
    started = time.perf_counter()
    response = hub.client.get(path)
    elapsed = time.perf_counter() - started
    assert response.status_code == 200, response.text
    return elapsed


def test_desk_reads_stay_under_budget_on_a_big_event_log(hub) -> None:
    project_ids = []
    for name in ("Atlas", "Beacon", "Cobalt", "Delta", "Ember", "Fjord", "Garnet", "Harbor"):
        response = hub.client.post("/api/projects", json={"name": name})
        assert response.status_code in (200, 201), response.text
        project_ids.append(response.json()["project"]["id"])
    _seed_events(hub.db, project_ids)
    with hub.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM pipeline_events").fetchone()[0] >= EVENTS

    paths = ("/api/desk/needs-you?fresh=1", "/api/settings/hub", "/api/desk/projections")
    for path in paths:  # the first read of each warms imports and caches
        _timed(hub, path)
    # Best of three: a parallel run loads the machine; a scan is slow every time.
    slow = {path: round(min(_timed(hub, path) for _ in range(3)), 3) for path in paths}
    assert all(seconds < BUDGET_S for seconds in slow.values()), slow

