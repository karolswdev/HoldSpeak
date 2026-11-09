# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_routes_missioncontrol.py to restore.

# ruff: noqa


# --- TestReceipts::test_receipts_route_is_get_only: P3/P8: reads FastAPI route.methods ('== {"GET"}') and hasattr on a removed name; no answer is checked
# (was a method of class TestReceipts)
def test_receipts_route_is_get_only(self, tmp_path):
    """The belt addition registers no write path (RFC B1)."""
    from holdspeak.web.routes import missioncontrol as mc_module

    app = FastAPI()
    _authenticate_owner(app)
    app.include_router(
        build_missioncontrol_router(
            WebContext(get_state=lambda: {}),
            runner=_gh_runner(RECEIPTS_DOC),
            map_path=_make_map(tmp_path),
        )
    )
    for route in app.routes:
        path = getattr(route, "path", "")
        if "receipts" in path:
            assert set(route.methods) == {"GET"}
    assert not hasattr(mc_module, "_belt_write")


# --- TestEvidenceInPlace::test_route_is_get_only: P3/P8: reads FastAPI route.methods ('== {"GET"}') and hasattr on a removed name; no answer is checked
# (was a method of class TestEvidenceInPlace)
def test_route_is_get_only(self, tmp_path):
    app = FastAPI()
    _authenticate_owner(app)
    app.include_router(
        build_missioncontrol_router(
            WebContext(get_state=lambda: {}),
            runner=_runner_for({}),
            map_path=_make_map(tmp_path),
        )
    )
    for route in app.routes:
        if "evidence" in getattr(route, "path", ""):
            assert set(route.methods) == {"GET"}


# --- TestRailsJournal::test_journal_is_get_only: P3/P8: reads FastAPI route.methods ('== {"GET"}') and hasattr on a removed name; no answer is checked
# (was a method of class TestRailsJournal)
def test_journal_is_get_only(self, tmp_path):
    app = FastAPI()
    _authenticate_owner(app)
    app.include_router(
        build_missioncontrol_router(
            WebContext(get_state=lambda: {}),
            runner=_runner_for({}),
            map_path=_make_map(tmp_path),
        )
    )
    for route in app.routes:
        if "rails/journal" in getattr(route, "path", ""):
            assert set(route.methods) == {"GET"}
