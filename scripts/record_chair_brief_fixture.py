#!/usr/bin/env python3
"""Record the hub's own Brief answers for the Chair's Brief window tests (the test diet, 2026-10-11).

``web/src/desk/__tests__/chair.app.test.tsx`` replays them through a mocked
``apiFetch``. Every answer comes from the real hub (``MeetingWebServer``
through ``TestClient``) on an isolated HOME and database
(``tests/unit/test_desk_needs_you.py::_boot``), with the seeds of
tests/e2e/test_philo15_05_strong_defaults_glass.py:

* ``scheduled``: the real cadence tick (``CadenceMixin._cadence_tick_body``,
  shipped defaults) at 06:00 today: the Brief generated itself.
* ``partial``: ``MondayBriefService.generate`` for ``SERVICE heartbeat``, a
  principal the needs-you rule cannot read for: two NOT READ rows.

The hub runs in America/Denver (the zone chair.app.test.tsx pins), so the
local 06:00 of the tick is the 06:00 the face prints. Nothing is typed by hand.

    HOME=$(mktemp -d) uv run python scripts/record_chair_brief_fixture.py
"""
from __future__ import annotations

import os
import time

os.environ["TZ"] = "America/Denver"
time.tzset()

import json  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402
from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "chair-brief" / "brief.recorded.json"
GETS = ("/api/desk/needs-you?fresh=1", "/api/door", "/api/inference/assignments", "/api/brief/latest")


def _gets(hub: Any) -> dict[str, Any]:
    out = {}
    for path in GETS:
        response = hub.client.get(path)
        assert response.status_code == 200, (path, response.text[:300])
        out[path] = response.json()
    return out


def _scenario(name: str, make: Any) -> dict[str, Any]:
    with pytest.MonkeyPatch.context() as mp:
        hub = seeds._boot(Path(tempfile.mkdtemp(prefix=f"chair-brief-{name}-")), mp)
        try:
            make()
            return {"gets": _gets(hub)}
        finally:
            from holdspeak.db import reset_database

            reset_database()
            composition.install(composition.bare(label="record"))


def _scheduled() -> None:
    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    class _Runtime(CadenceMixin):
        def __init__(self) -> None:
            self.config = Config()

    runtime = _Runtime()
    assert runtime._cadence_jobs_enabled() and not runtime._cadence_enabled()
    six = datetime.now().astimezone().replace(hour=6, minute=0, second=0, microsecond=0)
    with patch("holdspeak.runtime.cadence.local_now", return_value=six):
        runtime._cadence_tick_body()


def _partial() -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService

    MondayBriefService(get_database()).generate(Principal(PrincipalKind.SERVICE, "heartbeat"))


def main() -> int:
    fixture = {
        "schema": "chair-brief-recorded@1",
        "recordedBy": "scripts/record_chair_brief_fixture.py",
        "scheduled": _scenario("scheduled", _scheduled),
        "partial": _scenario("partial", _partial),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
