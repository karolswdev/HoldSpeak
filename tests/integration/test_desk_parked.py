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
    from tests.e2e.chair_rig import _seed

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


# ── Betterment setup ST1: one home each (Rhythm, Wallpaper) ───────────


@pytest.mark.parametrize(("window_id", "app"), [
    ("surface-cadence", "configure-cadence"),
    ("surface-places", "change-places"),
])
def test_the_parked_rhythm_and_places_windows_are_retired_and_a_saved_row_still_closes(
    tmp_path: Path, window_id: str, app: str,
) -> None:
    """Betterment setup ST1: the Rhythm window and Change places are parked;
    Settings ▸ Rhythm and Settings ▸ Wallpaper are their one home. The hub
    refuses a NEW old window by name and lists it as retired (the browser
    then closes a saved row and opens Settings at the section,
    ``web/src/desk/compositor/__tests__/hubWindows.test.ts``); a row saved
    before the slice still closes; Settings itself still opens."""
    from holdspeak.db import Database
    from holdspeak.services.desk_window_service import DeskWindowService
    from holdspeak.services.errors import ValidationError

    svc = DeskWindowService(Database(tmp_path / "w.db"), on_changed=lambda op, ids: None)
    with pytest.raises(ValidationError) as refused:
        svc.open(window_id)
    assert refused.value.code == "window_retired"
    registry = svc.list()["registry"]
    assert registry["static"][window_id] == app
    assert "Settings" in registry["retired"][window_id]
    with svc._db._connection() as conn:  # noqa: SLF001 -- a row saved before the slice
        conn.execute(
            "INSERT INTO desk_windows (id, app, object_ref, depth, minimized, revision) VALUES (?, ?, ?, ?, ?, ?)",
            (window_id, app, None, 1, 0, 1),
        )
    assert [w["id"] for w in svc.list()["windows"]] == [window_id]
    assert svc.close(window_id)["closed"] is True
    assert svc.list()["windows"] == []
    assert svc.open("surface-settings")["app"] == "configure-settings"
