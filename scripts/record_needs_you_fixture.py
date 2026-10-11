#!/usr/bin/env python3
"""Record the hub's own answers for the Needs-you face tests (the test diet, 2026-10-11).

The face tests in ``web/src/desk/__tests__/needsYou.app.test.tsx`` and
``needsChair.app.test.tsx`` replay these answers through a mocked ``apiFetch``.
Every answer here comes from the real hub (``MeetingWebServer`` through
``TestClient``) on an isolated HOME and database, seeded with the browser
tests' own seeds (``tests/unit/test_desk_needs_you.py``). Nothing is typed by
hand, so no field the face reads can be invented (the SCAR LAW).

Run it again when a producer's answer shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_needs_you_fixture.py

It writes ``web/src/desk/__tests__/fixtures/needsYou.recorded.json``.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "needsYou.recorded.json"

# The reads the Chair and the Settings window make (found by replaying the
# face with an empty table and listing every path it asked for).
COMMON_GETS = ("/api/desk/needs-you?fresh=1", "/api/door", "/api/inference/assignments")
SETTINGS_GETS = (
    "/api/settings",
    "/api/settings/hub",
    "/api/authority/policy",
    "/api/connections",
)


def _get(hub: Any, path: str) -> Any:
    response = hub.client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _post(hub: Any, path: str, body: dict[str, Any] | None = None) -> Any:
    response = hub.client.post(path, json=body) if body is not None else hub.client.post(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _gets(hub: Any, paths: tuple[str, ...]) -> dict[str, Any]:
    return {path: _get(hub, path) for path in paths}


def _boot(name: str, mp: pytest.MonkeyPatch, **kwargs: Any) -> Any:
    root = Path(tempfile.mkdtemp(prefix=f"needs-you-{name}-"))
    return seeds._boot(root, mp, **kwargs)


def _close() -> None:
    from holdspeak.db import reset_database

    reset_database()
    composition.install(composition.bare(label="record"))


def cold() -> dict[str, Any]:
    """A fresh HOME: no engine assigned, nothing seeded."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("cold", mp)
        try:
            return {"gets": _gets(hub, COMMON_GETS)}
        finally:
            _close()


def unfiled() -> dict[str, Any]:
    """PHILO-15 08: an unfiled meeting's action and decision proposals, one hub boot.

    Confirm the action, then Defer the decision; every answer is read after each press."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("unfiled", mp)
        try:
            ids = seeds._seed_unfiled(hub)
            before = _gets(hub, COMMON_GETS)
            decision = next(
                row["proposalId"] for row in before["/api/desk/needs-you?fresh=1"]["items"]
                if row.get("proposalKind") == "decision"
            )
            confirm_path = f"/api/proposals/{ids['proposal_id']}/confirm"
            confirmed = _post(hub, confirm_path)
            after_confirm = _gets(hub, COMMON_GETS)
            defer_path = f"/api/proposals/{decision}/defer"
            deferred = _post(hub, defer_path, {})
            after_defer = _gets(hub, COMMON_GETS)
            return {
                "action": seeds.ACTION,
                "decision": seeds.DECISION,
                "steps": [
                    {"name": "before", "gets": before},
                    {"name": "confirm", "post": confirm_path, "answer": confirmed, "gets": after_confirm},
                    {"name": "defer", "post": defer_path, "answer": deferred, "gets": after_defer},
                ],
            }
        finally:
            _close()


def arrival() -> dict[str, Any]:
    """HS-172: a Room's ran meeting with an action and a decision proposal, one hub boot.

    The read before Confirm, Confirm on the action, the read after."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("arrival", mp)
        try:
            seeds._seed_hs172(hub)
            before = _gets(hub, COMMON_GETS)
            action = next(
                row for row in before["/api/desk/needs-you?fresh=1"]["items"]
                if row.get("proposalKind") == "action"
            )
            confirm_path = f"/api/proposals/{action['proposalId']}/confirm"
            confirmed = _post(hub, confirm_path)
            return {
                "action": action["title"],
                "steps": [
                    {"name": "before", "gets": before},
                    {"name": "confirm", "post": confirm_path, "answer": confirmed,
                     "gets": _gets(hub, COMMON_GETS)},
                ],
            }
        finally:
            _close()


def grouped() -> dict[str, Any]:
    """PHILO-17: 30 signed-out GitHub sources (the producer's baseline errors), plus Settings' reads."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("grouped", mp, gh_runner=seeds._signed_out_gh)
        try:
            rooms = {}
            for key, name in (("a", "Payments ledger"), ("b", "Staff hiring")):
                created = _post(hub, "/api/projects", {
                    "name": name, "description": "PHILO-17 grouped sources", "command_id": f"p17-room-{key}"})
                rooms[key] = created["project"]["id"]
            for n in range(30):
                room = rooms["a"] if n % 2 == 0 else rooms["b"]
                seeds._insert_watch(hub, f"w-gh-{n}", room, "gh", "pull_requests",
                                    {"repository": f"acme/repo-{n:02d}"})
                assert hub.client.post(f"/api/watches/w-gh-{n}/baseline", json={}).status_code >= 400
            seeds._insert_watch(hub, "w-gh-paused", rooms["b"], "gh", "pull_requests",
                                {"repository": "acme/paused"},
                                last_success_at=seeds._utc_naive(-timedelta(minutes=5)))
            _post(hub, "/api/watches/w-gh-paused/pause", {})
            return {"gets": _gets(hub, COMMON_GETS + SETTINGS_GETS)}
        finally:
            _close()


def main() -> int:
    fixture = {
        "schema": "needs-you-recorded@1",
        "recordedBy": "scripts/record_needs_you_fixture.py",
        "cold": cold(),
        "unfiled": unfiled(),
        "arrival": arrival(),
        "grouped": grouped(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
