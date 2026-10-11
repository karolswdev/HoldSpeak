"""PHILO-17 autoflow: the owner's real day one, summary after every meeting.

Astra's condition on #1079: one browser case where nothing is driven by hand
after the Import press.

  - the default setting ("after every meeting", never patched here);
  - an engine the owner chose (the product's assignment service, an owner
    press; the provider is a rig double, so there is no egress);
  - the Import gesture in the browser;
  - the REAL intel conductor the hub lifespan starts (no explicit drain);
  - the meeting record is OPEN before the run finishes, and the summary and
    the receipt that names the host appear in it with no reload.

At 1440 and at 393.
"""
from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any

import pytest

from holdspeak.kernel.runtime import _configure
from tests._evidence import evidence_dir
from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
    clear_hub_windows,
    seed_meeting_engines,
)
from .test_hs201_summary_face_glass import FIXTURE_WAV, _chip_label, _FixtureImportTranscriber, _wait_record_host

pytestmark = [pytest.mark.timeout(600, method="thread"), pytest.mark.chair_windows_open]

TOKEN = "philo17-autoflow"
SIZES = ((1440, 900), (393, 852))
SHOTS = evidence_dir("pm/evidence/philo17-autoflow")


class _HeldIntel(FakeIntel):
    """The provider double. It holds its answer until the record is open,
    so the summary can only reach the face by the face's own refresh."""

    def __init__(self) -> None:
        super().__init__()
        self.gate = threading.Event()
        self.timed_out = False

    def analyze(self, transcript: str, *, stream: bool = False, memory_context: str = "") -> Any:
        self.entered.set()
        if not self.gate.wait(60):
            # Astra r1: a gate that times out FAILS the case; it never
            # answers by itself (the test asserts `timed_out` is False).
            self.timed_out = True
            raise RuntimeError("the provider gate was never released")
        return super().analyze(transcript, stream=stream, memory_context=memory_context)


def test_summary_after_every_meeting_reaches_the_open_record_by_itself(tmp_path: Path, monkeypatch):
    from playwright.sync_api import sync_playwright

    from holdspeak import intel_queue_conductor as conductor
    from holdspeak.db import get_database
    from holdspeak.runtime_lock import claim_database, current_lock, release_database
    from holdspeak.web.routes import meeting_import as import_route

    _ensure_build()
    # The drainer is scheduled work and runs only in the database owner
    # (HS-200-42), as the hub command claims it at boot.
    assert current_lock() is None, "this process already owns a database"
    lock = claim_database(tmp_path / "holdspeak.db")
    assert lock.held
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    engine = _HeldIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
    monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(()))
    monkeypatch.setattr(import_route, "_transcriber_factory", lambda cfg: _FixtureImportTranscriber())
    seed_meeting_engines()  # the owner's own press, a local engine
    assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in SIZES:
                engine.gate.clear()
                engine.entered.clear()
                page = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                navigations: list[str] = []
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                clear_hub_windows(page, TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                # The owner's own door: the Dock's Meetings (a gesture, so the
                # window comes to the front over the Chair's windows).
                page.locator(".desk-dock").get_by_role("button", name="Meetings", exact=True).click()
                page.locator(".meetings-head-verbs").wait_for(timeout=15_000)
                page.on(
                    "framenavigated",
                    lambda frame: navigations.append(frame.url) if frame is page.main_frame else None,
                )

                # ── the Import gesture ──
                title = f"Day one standup {width}"
                page.locator(".meetings-head-verbs").get_by_role("button", name="Import", exact=True).click()
                file_input = page.locator(".surface-dropwell input[type=file]")
                file_input.wait_for(timeout=15_000, state="attached")
                file_input.set_input_files(str(FIXTURE_WAV))
                page.get_by_role("textbox", name="Title", exact=True).fill(title)
                with page.expect_response(
                    lambda r: "/api/meetings/import" in r.url and r.request.method == "POST"
                ) as imported:
                    page.locator(".surface-actions").get_by_role("button", name="Import", exact=True).click()
                assert imported.value.ok, imported.value.text()
                meeting_id = imported.value.json()["meeting_id"]

                # The setting queued the summary on the disclosed route, and the
                # REAL drainer took it: the provider double is now holding.
                assert engine.entered.wait(60), "the running conductor never ran the queued summary"
                job = db.intel.get_latest_intel_job(meeting_id)
                assert job is not None and job.planned_route, job
                planned = job.planned_route
                host = planned["legs"][0]["host"]

                # ── open the record while the run is still going ──
                row = page.get_by_test_id(f"meeting-row-{meeting_id}")
                row.wait_for(timeout=20_000)
                with page.expect_response(
                    lambda r: r.request.method == "GET"
                    and r.url.split("?")[0].endswith(f"/api/meetings/{meeting_id}")
                ) as opened:
                    row.locator(".meetings-stream-row-body").click()
                # Astra r1: the record's OWN detail read answered with no
                # summary, and the face draws the pending state from it.
                pending = opened.value.json()
                assert not ((pending.get("intel") or {}).get("summary")), pending.get("intel")
                head = page.locator(".meetings-detail-head")
                head.wait_for(timeout=15_000)
                page.wait_for_function(
                    "() => /RUNNING|QUEUED/.test(document.querySelector('.meetings-detail-head')?.textContent || '')",
                    timeout=15_000,
                )
                # PHILO-17 ("A meeting opens in one window"): the record is the
                # meeting's own window.
                record = f"[id='pullout:meeting:{meeting_id}']"
                surface = page.locator(record)
                assert surface.get_by_test_id("meeting-summary-text").count() == 0
                # The list reads the same state as the record (the coordinator's
                # catch: the row said IMPORTING while the record said RUNNING).
                page.wait_for_function(
                    """(id) => /RUNNING|QUEUED|NOT DRAINING/.test(document.querySelector(
                        `[data-testid=meeting-row-${id}] [data-testid=state-token]`)?.textContent || '')""",
                    arg=meeting_id, timeout=15_000,
                )
                assert db.meetings.get_meeting(meeting_id).intel is None  # not yet
                SHOTS.mkdir(parents=True, exist_ok=True)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"record-pending-{width}.png"))

                # ── let the run finish; the open record catches up by itself ──
                engine.gate.set()
                summary_text = surface.get_by_test_id("meeting-summary-text")
                summary_text.wait_for(timeout=60_000)
                assert (summary_text.text_content() or "").strip() == engine.result.summary
                _wait_record_host(page, _chip_label(host), scope=record)
                receipt = db.intel.get_run_receipt(meeting_id)
                assert receipt["outcome"] == "succeeded", receipt
                assert receipt["selection_hash"] == planned["selection_hash"], receipt
                assert receipt["attempts"][0]["host"] == host, receipt
                assert navigations == [], navigations  # no reload, no navigation
                assert not engine.timed_out
                # The completion transition, from the pending state drawn above.
                assert not re.search(r"RUNNING|QUEUED", head.text_content() or "")
                _settle(page)
                page.screenshot(path=str(SHOTS / f"record-completed-{width}.png"))
                print(f"PASS {width}: summary and host {host} in the open record by the running conductor")
                _assert_clean(page, errors)
                page.close()
            browser.close()
    finally:
        engine.gate.set()
        hub_thread = server._thread
        server.stop()
        if hub_thread is not None:
            hub_thread.join(120)
        conductor.stop_intel_queue_conductor()
        release_database()
