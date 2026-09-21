"""HS-202-02 — the import lands on the OPEN record, with no reload.

The gap this fences (the first-use smoke's `import-refresh` leg, red at
both widths before HS-202-02 closed it):

  the import worker announces the desk change the instant the transcript
  lands (`holdspeak/services/meeting_service.py:285`). That is BEFORE the
  owner clicks the row it just changed, so the announcement arrives while
  nothing is open. `HistoryCore` debounced that announcement by 300 ms
  inside an effect that listed `refreshFace` as a dependency; opening a
  record changes `selectedId`, which changes `refreshFace`, which re-ran
  the effect -- and its cleanup `clearTimeout`-ed the pending refresh.
  The ledger was therefore never re-read, the open record kept the
  `importing` snapshot the click had taken, and `Run summary` (gated on
  `summaryIsOff(selected)`, `HistoryCore.tsx:480`) stayed off the record
  until the owner reopened it.

The walk is the stranger's: one real hub on an isolated HOME, one real
browser, one fixture WAV (never the microphone), one Import gesture. The
fixture transcriber is held shut until the importing row is on the glass,
so the announcement always precedes the click -- the exact order that was
red. After the click the fence waits, bounded, for the record to carry
the transcript, the `Run summary` verb and the planned host, and asserts
the browser never navigated while it happened.
"""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from holdspeak.kernel.runtime import _configure
from .test_hs201_summary_face_glass import _chip_label
from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    seed_meeting_engines,
)

pytestmark = pytest.mark.timeout(600, method="thread")

REPO = Path(__file__).resolve().parents[2]
FIXTURE_WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
TOKEN = "hs202-02-import"
TITLE = "Imported first meeting"  # + the width, so the two legs never share a row
WORDS = "The quick brown fox jumps over the lazy dog."
# The record must catch up on the hub's own announcement. Generous enough
# for a loaded machine, far short of "the owner reloaded the page".
CATCH_UP_MS = 6000


class _HeldImportTranscriber:
    """Stands in for Whisper on the import path; never loads a model.

    Held shut until the fence opens it, so the transcript -- and with it
    the completion announcement -- lands at a moment the fence chooses.
    """

    def __init__(self, permit: threading.Event) -> None:
        self.permit = permit

    def transcribe(self, audio, **_admission):  # noqa: ANN001 - product seam
        assert self.permit.wait(60), "the fence never released the import"
        return WORDS


def _wait_for_the_record(page, expression, *, arg, timeout):
    """Wait for the caught-up record, and SAY what was missing if it never came.

    A bare timeout reads the same whether the transcript never landed or
    the verb alone stayed away. The counts printed on failure separate
    those: the red state before this story was `words 1` beside
    `verb 0 route 0 needs 0` -- the transcript plainly on the glass and
    the record still refusing the verb that belongs to it.
    """
    try:
        page.wait_for_function(expression, arg=arg, timeout=timeout)
    except Exception:
        print(
            "MISSING verb",
            page.locator("[data-testid=detail-run-intelligence-btn]").count(),
            "route", page.locator("[data-testid=detail-route]").count(),
            "route-unavailable",
            page.locator("[data-testid=detail-route-unavailable]").count(),
            "transcript", page.get_by_text(WORDS, exact=True).count(),
            "needs-you", page.locator("[data-testid=meeting-needs-you]").count(),
        )
        raise


def test_the_import_reaches_the_open_record_with_no_reload(tmp_path, monkeypatch):
    from holdspeak.db import get_database
    from holdspeak.web.routes import meeting_import as import_route
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv(
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json")
    )
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    permit = threading.Event()
    monkeypatch.setattr(
        import_route, "_transcriber_factory", lambda cfg: _HeldImportTranscriber(permit)
    )
    seed_meeting_engines()

    source = tmp_path / FIXTURE_WAV.name
    source.write_bytes(FIXTURE_WAV.read_bytes())

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in ((1440, 900), (393, 852)):
                page = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(
                    page, "PUT", "/api/setup/onboarding",
                    {"disposition": "completed"}, token=TOKEN,
                )
                page.evaluate(
                    """() => {
                        localStorage.removeItem('hs.desk.workspace.v1');
                        sessionStorage.setItem('hs.desk.staged-surface-open',
                            JSON.stringify({key:'review-meetings'}));
                    }"""
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".meetings-head-verbs").wait_for(timeout=15_000)

                # From here the browser must not navigate again: every
                # move below is the product's own, on one loaded page.
                navigations: list[str] = []
                page.on(
                    "framenavigated",
                    lambda frame: navigations.append(frame.url)
                    if frame is page.main_frame
                    else None,
                )

                # ── the Import gesture ──
                page.locator(".meetings-head-verbs").get_by_role(
                    "button", name="Import", exact=True
                ).click()
                file_input = page.locator(".surface-dropwell input[type=file]")
                file_input.wait_for(timeout=15_000, state="attached")
                file_input.set_input_files(str(source))
                title = f"{TITLE} {width}"
                page.get_by_role("textbox", name="Title", exact=True).fill(title)
                with page.expect_response(
                    lambda response: "/api/meetings/import" in response.url
                    and response.request.method == "POST"
                ) as imported:
                    page.locator(".surface-actions").get_by_role(
                        "button", name="Import", exact=True
                    ).click()
                assert imported.value.ok, imported.value.text()

                # The importing row on the glass, before any transcript.
                row = page.locator("[data-testid^='meeting-row-']").filter(
                    has_text=title
                )
                row.first.wait_for(timeout=20_000)
                meeting_id = (row.first.get_attribute("data-testid") or "").removeprefix(
                    "meeting-row-"
                )
                assert meeting_id, "the importing row carries no meeting id"

                # ── the announcement, then the click (the red order) ──
                permit.set()
                for _ in range(300):
                    saved = db.meetings.get_meeting(meeting_id)
                    if saved is not None and saved.segments:
                        break
                    page.wait_for_timeout(100)
                else:  # pragma: no cover - the import must finish
                    pytest.fail("the import never saved a transcript")
                assert db.meetings.get_meeting(meeting_id).intel_status == "disabled"
                detail = _api(
                    page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN
                )
                planned = detail["planned_route"]
                assert planned["status"] == "ready", planned
                host = planned["legs"][0]["host"]

                row.first.locator(".meetings-stream-row-body").click()
                page.locator(".meetings-detail-head").wait_for(timeout=15_000)

                # ── the fence: the record catches up by itself ──
                _wait_for_the_record(page,
                    """([words, host]) => {
                        const seen = el => {
                          if (!el) return false;
                          const r = el.getBoundingClientRect();
                          const s = getComputedStyle(el);
                          return r.width > 0 && r.height > 0 &&
                            s.visibility === 'visible' && s.display !== 'none';
                        };
                        const verb = document.querySelector(
                          '[data-testid=detail-run-intelligence-btn]');
                        const route = document.querySelector('[data-testid=detail-route]');
                        return document.body.innerText.includes(words) &&
                          seen(verb) && seen(route) &&
                          route.innerText.includes(host);
                    }""",
                    arg=[WORDS, _chip_label(host)],
                    timeout=CATCH_UP_MS,
                )
                assert navigations == [], navigations
                print(
                    f"PASS {width}: the imported record shows its transcript, "
                    f"Run summary and host {host} with no reload "
                    f"(meeting {meeting_id})"
                )
                _assert_clean(page, errors)
                permit.clear()
                page.close()
            browser.close()
    finally:
        server.stop()
