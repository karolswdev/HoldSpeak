"""HS-141-04 glass walk through the real browser, API, kernel, and projection.

The provider is deliberately deterministic *only* at the runner engine factory:
the browser still creates the note, starts refinement, stops it, reconciles the
real kernel receipt, and writes the owner answer through the ordinary routes.
It is not a fake HTTP response or a pre-seeded review row.
"""
from __future__ import annotations

import threading
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/story-04"
TOKEN = "hs14104-deterministic-glass"


class _GatedQuestionEngine:
    """A cancellable, in-process provider simulation at the real runner seam."""
    active_provider = "deterministic-in-process"

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        self.entered.set()
        assert self.release.wait(10), "test provider was never released"
        return ('{"kind":"question","question":"Who owns the first customer call?",'
                '"reason":"It identifies the next move."}')


def _shot(page, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ASSETS / name), full_page=False)


def _assert_clean(page, errors: list[str]) -> None:
    assert not errors, f"browser errors: {errors}"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,name", [(1440, "1440"), (393, "393")])
def test_hs14104_real_kernel_refinement_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, name: str) -> None:
    """First value -> Develop -> Stop -> question -> Answer, twice on glass."""
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"; home.mkdir()
    db_path = tmp_path / "holdspeak.db"
    model = tmp_path / "deterministic-this-machine.gguf"; model.touch()
    # The browser executable is tooling, not owner state. Keep it outside the
    # isolated HOME so Playwright does not try to install a second browser.
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: str(model))
    reset_database()
    database = db_core.get_database()
    engine = _GatedQuestionEngine()
    broker = _configure(database)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}), auth_token=TOKEN)
    url = server.start()
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            page.locator("textarea").first.fill("Mina should launch the customer call this week.")
            page.get_by_role("button", name="Keep as Note").click()
            page.get_by_role("button", name="Continue later").click()
            page.get_by_role("button", name="Develop this thought").wait_for(timeout=10000)
            page.get_by_role("button", name="Develop this thought").click()
            # Adoption focuses the editable working Note. Close it through the
            # ordinary owner control before asking for a refinement.
            page.get_by_role("button", name="Cancel").click()
            page.get_by_role("button", name="Keep refining").wait_for(timeout=10000)
            _shot(page, f"hs-141-04-ready-{name}.png")

            # First real physical attempt is stopped while the provider is held.
            page.get_by_role("button", name="Keep refining").click()
            assert engine.entered.wait(5)
            if width == 1440:
                assert not page.get_by_role("button", name="More").is_visible()
                assert page.get_by_role("button", name="Finish instead").is_visible()
            else:
                assert page.get_by_role("button", name="More").is_visible()
                assert not page.get_by_role("button", name="Finish instead").is_visible()
                page.get_by_role("button", name="More").click()
                assert page.get_by_label("More thought actions").get_by_role("button", name="Finish instead").is_visible()
                page.get_by_role("button", name="Close more").click()
            page.get_by_role("button", name="Stop").click()
            # The runner may wait for its synchronous provider to unwind before
            # the cancel route replies; release only after the owner pressed
            # Stop, so this remains a late-result suppression proof.
            engine.release.set()
            page.get_by_text("Stopped. Your working note is unchanged.").wait_for(timeout=8000)
            page.wait_for_timeout(1100)
            assert page.get_by_label("Refinement question").count() == 0

            # A distinct second attempt reaches the normal receipt/reconcile path.
            engine.release = threading.Event(); engine.entered = threading.Event()
            page.get_by_role("button", name="Keep refining").click()
            assert engine.entered.wait(5)
            _shot(page, f"hs-141-04-live-stop-{name}.png")
            engine.release.set()
            page.get_by_text("Who owns the first customer call?").wait_for(timeout=10000)
            _shot(page, f"hs-141-04-question-{name}.png")
            if width == 1440:
                assert not page.get_by_role("button", name="More").is_visible()
                assert page.get_by_role("button", name="Edit working note").is_visible()
                assert page.get_by_role("button", name="Reject").is_visible()
            else:
                assert page.get_by_role("button", name="More").is_visible()
                assert not page.get_by_role("button", name="Edit working note").is_visible()
                assert not page.get_by_role("button", name="Reject").is_visible()
                page.get_by_role("button", name="More").click()
                menu = page.get_by_label("More thought actions")
                assert menu.get_by_role("button", name="Copy").is_visible()
                assert menu.get_by_role("button", name="Edit working note").is_visible()
                assert menu.get_by_role("button", name="Reject").is_visible()
                page.get_by_role("button", name="Close more").click()
            page.get_by_label("Answer").fill("Mina owns it.")
            page.get_by_role("button", name="Answer").click()
            page.get_by_text("Answer added to your working note.").wait_for(timeout=8000)
            assert "Question: Who owns the first customer call?" in page.locator("body").inner_text()
            assert "Answer: Mina owns it." in page.locator("body").inner_text()
            assert engine.calls == 2, "Answer must not auto-chain a model call"
            _shot(page, f"hs-141-04-answer-{name}.png")

            # Third attempt proves late provider output is suppressed after Stop.
            engine.release = threading.Event(); engine.entered = threading.Event()
            page.get_by_role("button", name="Keep refining").click()
            assert engine.entered.wait(5)
            page.get_by_role("button", name="Stop").click()
            engine.release.set()
            page.get_by_text("Stopped. Your working note is unchanged.").wait_for(timeout=8000)
            page.wait_for_timeout(1100)
            # The accepted owner Clarification deliberately retains the words;
            # only a new review card would prove a late provider result leaked.
            assert page.get_by_label("Refinement question").count() == 0
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop(); reset_database()
