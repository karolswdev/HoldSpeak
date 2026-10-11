#!/usr/bin/env python3
"""Record the hub's own steward answers for the Steward posture face tests (the test diet, 2026-10-11).

``web/src/features/project-room/steward/__tests__/StewardPosture.test.tsx``
replays these answers through a mocked ``apiFetch``. Every answer here comes
from the real hub (``MeetingWebServer`` through ``TestClient``) on an isolated
HOME and database: a Room with one overdue risk, a steward policy that allows
every effect that needs no network, and real runs. Nothing is typed by hand,
so no field the face reads can be invented (the SCAR LAW).

Run it again when the steward's answer shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_steward_fixture.py

It writes ``web/src/features/project-room/steward/__tests__/fixtures/steward.recorded.json``.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "features" / "project-room" / "steward" / "__tests__" / "fixtures" / "steward.recorded.json"

# The effects a run can take on an isolated hub with no network: refresh the
# sources, open a review, draft an update, file one Door item.
EFFECTS = ["refresh_sources", "create_proposals", "draft_update", "create_door_item"]


def _ok(response: Any) -> Any:
    assert response.status_code == 200, (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _run(hub: Any, project_id: str) -> dict[str, Any]:
    """Start one run and poll it to its end; answer the poll's last read."""
    started = _ok(hub.client.post(f"/api/projects/{project_id}/steward/runs", json={}))
    run_id = started["run_id"]
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        detail = _ok(hub.client.get(f"/api/steward/runs/{run_id}"))
        if detail["run"]["state"] in ("completed", "interrupted", "failed"):
            return {"start": started, "detail": detail}
        time.sleep(0.1)
    raise AssertionError(f"run {run_id} did not end")


def record() -> dict[str, Any]:
    with pytest.MonkeyPatch.context() as mp:
        root = Path(tempfile.mkdtemp(prefix="steward-record-"))
        hub = seeds._boot(root, mp, gh_runner=seeds._signed_out_gh)
        try:
            project = _ok(hub.client.post("/api/projects", json={
                "name": "Steward Project", "description": "The steward's recorded run",
                "command_id": "steward-record-room"}))["project"]
            pid = project["id"]
            _ok(hub.client.post(f"/api/projects/{pid}/items", json={
                "item_type": "risk", "title": "Vendor contract lapses", "severity": "high",
                "lifecycle": "open", "due_at": "2026-01-15", "details": {"likelihood": "high", "impact": "high"}, "command_id": "steward-record-risk"}))
            policy = _ok(hub.client.put(f"/api/projects/{pid}/steward/policy", json={
                "eligible_effect_kinds": EFFECTS, "enabled": True}))
            completed = _run(hub, pid)
            # A GitHub watch on the Room (the posture lists it), and a source
            # bound to a watch that is gone: the next run's OBSERVE answers
            # partial coverage, the collector's own `failed` state.
            seeds._insert_watch(hub, "w-gh-record", pid, "gh", "pull_requests",
                                {"repository": "acme/payments"})
            hub.db.automations.create_project_source(
                source_id="psrc_record_gone", project_id=pid, source_ref="watch:w-gone",
                label="Retired watch")
            partial = _run(hub, pid)
            return {
                "projectId": pid,
                "policy": policy,
                "completed": completed,
                "partial": partial,
                "list": _ok(hub.client.get(f"/api/projects/{pid}/steward/runs")),
                "getPolicy": _ok(hub.client.get(f"/api/projects/{pid}/steward/policy")),
                "watches": _ok(hub.client.get(f"/api/projects/{pid}/watches")),
                # The drafted updates (an `update:<id>` receipt opens one).
                "updates": _ok(hub.client.get(f"/api/projects/{pid}/updates")),
            }
        finally:
            from holdspeak.db import reset_database

            reset_database()
            composition.install(composition.bare(label="record"))


def main() -> int:
    fixture = {
        "schema": "steward-recorded@1",
        "recordedBy": "scripts/record_steward_fixture.py",
        **record(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
