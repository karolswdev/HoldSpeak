"""The Parked drawer, against a real hub: the hub half of the PHILO-15 04
browser walk (the test diet, PHILO-17 final lane A, 2026-10-11).

A real hub (``tests/e2e/glass_infra._boot``, isolated HOME) with the canvas
week of the browser walk; a meeting and a Project are parked through the real
DELETE routes; the drawer's read, the Project's Restore and the read after it
are asserted and recorded. The face half,
``web/src/desk/__tests__/parked.app.test.tsx``, renders the real ParkedDrawer
on those answers. Each run fences the stored answers' SHAPE against the hub's;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites ``fixtures/parked-wire/``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.glass_infra import _boot
from tests.integration.test_desk_firstrun import _ok
from tests.integration.test_desk_firstrun import _Recorder as _FirstRunRecorder

TOKEN = "firstrun-hub"  # the shared _ok helper speaks with this token

pytestmark = pytest.mark.timeout(120, method="thread")


class _Recorder(_FirstRunRecorder):
    def __init__(self, tmp_path: Path, base: str) -> None:
        super().__init__("unused", tmp_path, base)
        self.dir = self.dir.parent / "parked-wire"


def test_park_a_meeting_and_a_project_see_both_restore_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_philo15_04_small_gaps_glass.py::TestParkedDrawer::test_park_a_meeting_and_a_project_see_both_restore_one (hub half)"""
    from tests.e2e.test_philo13_11_chair_glass import _seed

    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        _seed(tmp_path / "home")
        rec = _Recorder(tmp_path, base)
        _ok(base, "DELETE", "/api/meetings/m-arch")
        _ok(base, "DELETE", "/api/projects/p-hiring")

        before = rec.keep("parked-before", _ok(base, "GET", "/api/desk/parked"))
        assert sorted((i["kind"], i["id"], i["name"]) for i in before["items"]) == [
            ("meeting", "m-arch", "Architecture review: tracing"),
            ("project", "p-hiring", "Staff hiring loop"),
        ], before
        assert not before.get("not_read"), before

        rec.keep("restore-project", _ok(base, "POST", "/api/projects/p-hiring/restore"))
        after = rec.keep("parked-after", _ok(base, "GET", "/api/desk/parked"))
        assert [(i["kind"], i["id"]) for i in after["items"]] == [("meeting", "m-arch")], after
        assert any(p["id"] == "p-hiring" for p in _ok(base, "GET", "/api/projects")["projects"])
    finally:
        server.stop()
