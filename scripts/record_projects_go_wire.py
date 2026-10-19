#!/usr/bin/env python3
"""Record the hub's own answers for the Projects window (Betterment P4).

The face test (``web/src/pages/cores/__tests__/projects.app.test.tsx``, the Projects
window) replays these answers through a mocked ``apiFetch``. The answers
come from the real hub (``MeetingWebServer`` through ``TestClient``, the rig
of ``tests/integration/test_desk_project_room.py``) on an isolated HOME and
database. Nothing is typed by hand (the SCAR LAW).

Seed: "Payments migration" with a target date, a milestone that is late
and a records draft of its update; "Vendor review" with nothing in it.

    HOME=$(mktemp -d) uv run python scripts/record_projects_go_wire.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import record_room_wires as rec  # noqa: E402

OUT = REPO / "web" / "src" / "pages" / "cores" / "__tests__" / "fixtures" / "projects" / "recorded.json"


def projects_go(hub: Any, _mp: Any) -> dict[str, Any]:
    payments = rec._project(hub, "Payments migration", "p4-projects-payments")
    vendor = rec._project(hub, "Vendor review", "p4-projects-vendor")
    target = (date.today() + timedelta(days=5)).isoformat()
    hub.ok("PATCH", f"/api/projects/{payments}", {"target_at": target, "command_id": "p4-target"})
    hub.ok("POST", f"/api/projects/{payments}/items", {
        "item_type": "milestone", "title": "Staging dry run",
        "due_at": (date.today() - timedelta(days=2)).isoformat(), "command_id": "p4-late-item"})
    hub.ok("POST", f"/api/projects/{payments}/updates/draft",
           {"generator": "deterministic", "command_id": "p4-records-draft"})
    gets: dict[str, Any] = {"/api/projects": rec._answer(hub.client.get("/api/projects"))}
    for pid in (payments, vendor):
        path = f"/api/projects/{pid}/room"
        gets[path] = rec._answer(hub.client.get(path))
    return {"payments": payments, "vendor": vendor, "today": date.today().isoformat(), "gets": gets}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema": "projects-go-recorded@1", "recordedBy": "scripts/record_projects_go_wire.py",
            **rec._run("projects-go", projects_go)}
    OUT.write_text(json.dumps(data, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
