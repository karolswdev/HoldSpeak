"""Route in footer (owner pick 2026-10-05, canvas section 4, option C).

Through the real hub on an isolated HOME, at 1440x900 and 393x852, with
fixture engines behind the real route chain (admission, the fallback
controller, the receipt): each turn wears only its LAMP, read from its
receipt; the footer names the FULL route of the LAST turn (host chip,
model, receipt) and the model once.

  * Ask on a LAN engine: the HUB> turn wears LAN; the footer names
    ``192.168.1.43 · LAN`` and ``LAST TURN · qwen3.8-27b · RECEIPT ··xxxx``.
  * A chat with a LAN, a LOCAL and a CLOUD turn: three lamps; the footer
    moves to the CLOUD host when the third turn lands.
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the route glass needs Playwright")

TOKEN = "route-in-footer"
SIZES = {1440: 900, 393: 852}
SHOTS = Path(os.environ.get("ROUTE_FOOTER_SHOTS", "")) if os.environ.get("ROUTE_FOOTER_SHOTS") else None

ROUTES = {
    "glass-lan": {"model": "qwen3.8-27b", "boundary": "private_network", "endpoint": "http://192.168.1.43:8080/v1"},
    "glass-local": {"model": "Qwen3.5 4B", "boundary": "same_device", "endpoint": ""},
    "glass-cloud": {"model": "gpt-5-mini", "boundary": "external_service", "endpoint": "https://api.openai.com/v1"},
}
ANSWERS = {
    "qwen3.8-27b": "Two risks are open: rollback ownership is disputed, and the load test ran at 60% of peak only.",
    "Qwen3.5 4B": "Rollback owner unclear. Load test at 60% of peak.",
    "gpt-5-mini": "On 17 October we move Atlas to a new cluster. Expect 10 minutes of read-only time from 06:00 UTC.",
}
ASK_ANSWER = "The cutover is on 17 October, after the freeze."


class _Engine:
    """A fixture engine: answers by the deployment it was built for."""

    def __init__(self, model: str) -> None:
        self.active_provider = "fixture"
        self.active_model = model
        self._text = ANSWERS.get(model, ASK_ANSWER)

    def run_prompt_stream(self, *, messages: Any = None, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        for word in self._text.split(" "):
            yield Delta(kind="text", text=word + " ")
        yield Delta(kind="usage", meta={"prompt_tokens": 20, "completion_tokens": 20})
        yield Delta(kind="done")

    def run_prompt_messages(self, *, messages: Any = None, **_kw: Any) -> str:
        return self._text

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "", **_kw: Any) -> Any:
        return ASK_ANSWER


def _seed_routes() -> None:
    from holdspeak.db import get_database
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    from holdspeak.deployment_revisions import DeploymentRevision

    db = get_database()
    original = DeploymentRevision.__dict__["from_artifact"]
    for pid, route in ROUTES.items():
        # The fixture deployment names its endpoint in its content identity;
        # the engine factory below never opens it.
        def with_endpoint(cls, *, _endpoint=route["endpoint"], **kw):
            return original.__func__(cls, **{**kw, "endpoint": _endpoint})

        DeploymentRevision.from_artifact = classmethod(with_endpoint)
        try:
            _profile(db, pid, model=route["model"], boundary=route["boundary"],
                     claims=("language", _result_claim("chat.turn"), _result_claim("ask.answer"),
                             _result_claim("thought.interview"), _result_claim("speech.intent_classify")))
        finally:
            DeploymentRevision.from_artifact = original
    # The routed Ask (the migration marker the product writes on first run).
    from types import SimpleNamespace

    from holdspeak.kernel.runtime import _service
    from holdspeak.principals import Principal, PrincipalKind

    _service().inference_adoption_service.migrate_legacy_config(
        Principal(PrincipalKind.OWNER, "route-glass"),
        SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="glass-lan"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan")),
        ),
    )


def _assign(capability: str, profile_id: str, n: int) -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    db = get_database()
    with db._connection() as conn:
        row = conn.execute(
            "SELECT revision FROM inference_assignment_heads WHERE assignment_key=?",
            (f"capability:{capability}",),
        ).fetchone()
    InferenceAssignmentService(db).set_assignment(Principal(PrincipalKind.OWNER, "route-glass"), {
        "command_id": f"route-glass-{capability}-{n}",
        "expected_revision": int(row["revision"]) if row is not None else 0,
        "scope": {"kind": "capability", "capability_id": capability},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def _wait_turns(page: Any, tid: str, n: int) -> list[dict]:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        msgs = _api(page, "GET", f"/api/threads/{tid}", token=TOKEN).get("messages", [])
        done = [m for m in msgs if m["role"] == "assistant" and not m["streaming"]]
        if len(done) >= n:
            return done
        time.sleep(0.2)
    raise AssertionError(f"turn {n} did not finish")


class TestRouteInFooter:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        from holdspeak.kernel.runtime import _service

        _service().inference_runner._engine_factory = lambda rev, **_kw: _Engine(str(rev.model))
        _seed_routes()
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _shot(page: Any, loc: Any, name: str, width: int) -> None:
        if SHOTS is None:
            return
        SHOTS.mkdir(parents=True, exist_ok=True)
        _settle(page)
        page.screenshot(path=str(SHOTS / f"built-{name}-{width}.png"))
        loc.screenshot(path=str(SHOTS / f"built-{name}-{width}-face.png"))

    @pytest.mark.parametrize("width", list(SIZES))
    def test_ask_on_lan_lamp_on_the_turn_route_in_the_footer(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        _assign("ask.answer", "glass-lan", 1)
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("Ask")
                self._press(page, page.locator("[id='desk-palette-option-go.ask']"), width)
                ask = page.locator(".desk-ask")
                ask.locator("textarea").first.fill("What did we decide about the cutover date?")
                self._press(page, ask.get_by_role("button", name="ASK", exact=True), width)
                hub = ask.locator(".surface-traffic-turn", has_text="HUB>")
                hub.get_by_text("17 October").first.wait_for()
                assert hub.locator(".gadget-lamp").inner_text().strip() == "LAN"
                chip = ask.locator(".surface-footer-egress .gadget-chip-egress")
                assert chip.inner_text().strip().upper() == "192.168.1.43 · LAN"
                line = ask.locator(".surface-footer-receipt").inner_text().strip().upper()
                assert line.startswith("LAST TURN · QWEN3.8-27B · RECEIPT ··"), line
                # The model is named once on the whole face (CONTROL: twice).
                assert ask.inner_text().upper().count("QWEN3.8-27B") == 1
                self._shot(page, ask, "ask", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_chat_with_lan_local_cloud_turns(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                tid = _api(page, "POST", "/api/threads", {"title": "Cutover risks"}, token=TOKEN)["id"]
                for n, (pid, text) in enumerate([
                    ("glass-lan", "List the open risks for the Atlas cutover."),
                    ("glass-local", "Make it shorter."),
                ], start=1):
                    _assign("chat.turn", pid, n)
                    _api(page, "POST", f"/api/threads/{tid}/turns", {"text": text}, token=TOKEN)
                    _wait_turns(page, tid, n)
                page.goto(f"{self.base}/?token={TOKEN}&open=thread:{tid}", wait_until="load")
                window = page.locator(".desk-window", has=page.locator(".thread-pullout-body")).first
                window.locator(".thread-route-footer").wait_for()
                chip = window.locator(".thread-route-footer .gadget-chip-egress")
                assert chip.inner_text().strip().upper() == "THIS DEVICE"

                # The third turn lands while the window is open: the footer moves.
                _assign("chat.turn", "glass-cloud", 3)
                _api(page, "POST", f"/api/threads/{tid}/turns", {"text": "Write the customer notice."}, token=TOKEN)
                _wait_turns(page, tid, 3)
                page.wait_for_function(
                    "() => (document.querySelector('.thread-route-footer .gadget-chip-egress')?.textContent || '')"
                    ".toLowerCase() === 'api.openai.com'"
                )
                lamps = [t.strip() for t in window.locator(".thread-row-assistant .thread-row-head .gadget-lamp").all_inner_texts()]
                assert lamps == ["LAN", "LOCAL", "CLOUD"], lamps
                line = window.locator(".thread-route-footer .surface-footer-receipt").inner_text().strip().upper()
                assert line.startswith("LAST TURN · GPT-5-MINI · RECEIPT ··"), line
                text = window.inner_text().upper()
                assert text.count("GPT-5-MINI") == 1
                assert "QWEN3.8-27B" not in text
                window.locator(".thread-pullout-body").evaluate("b => { b.scrollTop = b.scrollHeight; }")
                self._shot(page, window, "chat", width)
                assert not errors, errors
            finally:
                browser.close()
