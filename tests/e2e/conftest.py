"""e2e conftest — the 163 stale-bundle law for EVERY rig.

`glass_infra._ensure_build` rebuilds the web bundle when any web source
is newer than the oldest built chunk. 19 of 33 glass rigs imported it;
the other 14 (HS-144, HS-152, HS-153, …) booted their own hub and tested
whatever bundle happened to be on disk — seen 2026-09-05: a rig asserting
against a bundle from before the species sweep. This autouse session
fixture applies the law to every test under tests/e2e/, once per
process (xdist workers serialize under the file lock; the mtime check
makes every later call a no-op).
"""
from __future__ import annotations

import weakref

import pytest

from .glass_infra import _ensure_build


@pytest.fixture(scope="session", autouse=True)
def _web_bundle_is_fresh() -> None:
    _ensure_build()


# ── HS-200-03 follow-through: no hub outlives the database it serves ──
#
# `glass_infra._boot` (51 rigs) and a dozen hand-rolled rigs start a real
# MeetingWebServer and never stop it. A started hub runs
# `MeetingWebServer._kernel_liveness_loop` (holdspeak/web_server.py:1348)
# on its own thread; that loop calls `holdspeak.kernel.runtime._service()`,
# which REBUILDS the process-global kernel broker whenever the database
# singleton has changed underneath it (holdspeak/kernel/runtime.py:198-207).
# So a hub left running by an earlier test rebuilds the broker of the
# CURRENT test — after that test injected its engine factory onto the
# broker IT configured — and the injected engine is silently replaced by
# the real `build_intel_for_revision` one.
#
# Seen on the macOS runner (run 34059711954) and reproduced locally:
# `tests/e2e/test_hs175_arrival_glass.py` then
# `tests/e2e/test_hs141_thought_workbench_glass.py::…[1440]` fails at
# `assert engine.started.wait(5)` with llama.cpp trying to load the rig's
# empty placeholder .gguf. Traced to two `_build` calls on the same
# database object: one from the test's own `_configure`, one from the
# previous module's leaked hub thread. Order- and timing-dependent, which
# is why a slower runner sees it and a fast single-file run does not.
#
# The law enforced here is the narrow one that removes the damage without
# guessing fixture lifetimes: a hub must not outlive the database it was
# booted against. `reset_database()` is a pure test seam (no caller in
# holdspeak/), so every rig that installs a fresh database first stops
# every hub still serving the old one. A module-scoped hub (HS-172's
# `glass`) keeps running across its own tests, because nothing resets the
# database under it. No assertion is weakened; the rigs simply clean up.

_LIVE_HUBS: "weakref.WeakSet[object]" = weakref.WeakSet()


def _stop_live_hubs() -> None:
    for hub in list(_LIVE_HUBS):
        _LIVE_HUBS.discard(hub)
        try:
            hub.stop()
        except Exception:  # a rig may already have stopped it
            pass


@pytest.fixture(scope="session", autouse=True)
def _no_hub_outlives_its_database():
    import holdspeak.db as db_pkg
    import holdspeak.db.core as db_core
    from holdspeak.web_server import MeetingWebServer

    original_start = MeetingWebServer.start
    original_reset = db_core.reset_database

    def _tracked_start(self, *args, **kwargs):
        url = original_start(self, *args, **kwargs)
        _LIVE_HUBS.add(self)
        return url

    def _reset_database(*args, **kwargs):
        _stop_live_hubs()
        return original_reset(*args, **kwargs)

    MeetingWebServer.start = _tracked_start
    db_core.reset_database = _reset_database
    # `holdspeak.db` re-exports the symbol, and that is the name the rigs
    # import; rebind both so either import path is covered.
    patched_pkg = getattr(db_pkg, "reset_database", None) is original_reset
    if patched_pkg:
        db_pkg.reset_database = _reset_database
    try:
        yield
    finally:
        MeetingWebServer.start = original_start
        db_core.reset_database = original_reset
        if patched_pkg:
            db_pkg.reset_database = original_reset
        _stop_live_hubs()
