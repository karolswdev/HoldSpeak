#!/usr/bin/env python3
"""Record the hub's own answers for the Rhythm face tests (the test diet, 2026-10-11).

``web/src/pages/cores/__tests__/rhythm.app.test.tsx`` replays these answers
through a stubbed ``fetch``. Every answer comes from the real hub
(``MeetingWebServer`` through ``TestClient``) on an isolated HOME and
database (``tests/unit/test_desk_needs_you.py::_boot``), seeded with the
browser tests' own seeds (tests/e2e/test_hs171_rhythm_glass.py and
tests/e2e/test_hs174_rhythm_runs_on_glass.py). Nothing is typed by hand (the
SCAR LAW). Each scenario is one hub boot: the reads before a press, the
press and the hub's answer, the reads after.

Run it again when an answer shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_chair_rhythm_fixture.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "pages" / "cores" / "__tests__" / "fixtures" / "rhythm-wire" / "rhythm.recorded.json"

# Every read CadenceCore makes (CadenceCore.tsx useResource calls).
GETS = (
    "/api/settings/heartbeat",
    "/api/brief/latest",
    "/api/door",
    "/api/projects",
    "/api/cadence/status",
    "/api/cadence/loops",
    "/api/cadence/history?limit=20",
)
REMOTE = "192.168.1.43"


def _call(hub: Any, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    response = hub.client.request(method, path, json=body)
    assert response.status_code == 200, (method, path, response.status_code, response.text[:300])
    return response.json()


def _gets(hub: Any) -> dict[str, Any]:
    return {path: _call(hub, "GET", path) for path in GETS}


def _seed_remote_pipeline_event(caller: str = REMOTE) -> None:
    """tests/e2e/test_hs174_rhythm_runs_on_glass.py::_seed_remote_pipeline_event, verbatim."""
    from holdspeak.db import get_database

    db = get_database()
    now = time.time()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method,
                principal_kind, principal_identity, args_summary,
                result_summary, error, error_code, duration_ms,
                correlation_id, is_async, origin, caller, caller_identity)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()), now, "HeartbeatService", "run_sweep",
                "agent", "sweep-runner", "{}",
                '{"watches":4,"rooms":2,"held":false}',
                None, None, 42.0,
                str(uuid.uuid4()), 0, "remote", caller, "sweep-runner",
            ),
        )


def _scenario(name: str, presses: list[tuple[str, str, dict[str, Any] | None]], *,
              seed: Any = None) -> dict[str, Any]:
    """One hub boot: the reads, then each press with its answer and the reads after it."""
    with pytest.MonkeyPatch.context() as mp:
        root = Path(tempfile.mkdtemp(prefix=f"rhythm-{name}-"))
        hub = seeds._boot(root, mp)
        try:
            extra = seed(hub) if seed else None
            steps: list[dict[str, Any]] = [{"name": "before", "gets": _gets(hub)}]
            for method, path, body in presses:
                body = json.loads(json.dumps(body).replace("{project}", str(extra))) if body else body
                answer = _call(hub, method, path, body)
                steps.append({"name": f"{method} {path}", "method": method, "path": path, "body": body,
                              "answer": answer, "gets": _gets(hub)})
            return {"steps": steps, **({"project": extra} if extra else {})}
        finally:
            from holdspeak.db import reset_database

            reset_database()
            composition.install(composition.bare(label="record"))


def _project(hub: Any) -> str:
    created = _call(hub, "POST", "/api/projects", {"name": "Q4 Platform"})
    return created["project"]["id"]


def _remote(hub: Any) -> None:
    _seed_remote_pipeline_event()


def main() -> int:
    fixture = {
        "schema": "rhythm-recorded@1",
        "recordedBy": "scripts/record_chair_rhythm_fixture.py",
        # HS-171-02: the cold face; the sweep interval changed to 30; Run now.
        "change": _scenario("change", [("PUT", "/api/settings/heartbeat", {"sweep_every_minutes": 30})]),
        "runNow": _scenario("run-now", [("POST", "/api/settings/heartbeat/run-now", {})]),
        # A Project's mute token, pressed off (muted) and on again.
        "mute": _scenario("mute", [
            ("PUT", "/api/settings/heartbeat", {"muted_projects": ["{project}"]}),
            ("PUT", "/api/settings/heartbeat", {"muted_projects": []}),
        ], seed=_project),
        # Betterment daily D8: the FINISHED WORK token pressed off (no quiet
        # notice for a new automation result).
        "finished": _scenario("finished", [("PUT", "/api/settings/heartbeat", {"notify_finished": False})]),
        # Quiet hours 09:00-11:00 (the face reads them against the viewer's clock).
        "quiet": _scenario("quiet", [("PUT", "/api/settings/heartbeat", {"quiet_hours": {"start": 9, "end": 11}})]),
        # HS-174-08: a remote run seen, then Runs on set to that host.
        "runsOn": _scenario("runs-on", [("PUT", "/api/settings/heartbeat", {"runs_on": REMOTE})], seed=_remote),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
