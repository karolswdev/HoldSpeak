"""PHILO-17 wayin -- one token URL signs a browser in to its hub, on glass.

The walker's blocker: a desk opened without ``?token=`` (a new tab, a
bookmark, a browser restart) showed only "Meetings: principal_right_required"
and Retry. Through ONE real hub on an isolated HOME and the built bundle:

  W1 a browser opens the token URL; the desk loads.
  W2 the same browser opens ``/`` and ``/welcome`` with no token (a new tab,
     a bookmark): the desk loads, no request is refused, the websocket opens.
  W3 a fresh browser with a wrong token (1440 and 393): the hub refuses it,
     the page forgets it, and the one sign-in sentence shows in place of the
     raw error code.
  W4 a fresh browser with no token at all: the same one sentence.

Shots: docs/internal/philo/phase-17/wayin-shots/ (``.tmp/evidence-shots/`` unless HOLDSPEAK_EVIDENCE_WRITE=1).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the wayin glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "philo17-wayin"
SHOTS = evidence_dir("docs/internal/philo/phase-17/wayin-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
SENTENCE = 'To open the desk, use the address that "holdspeak web" prints on your Mac.'
STORED_JS = "() => localStorage.getItem('hs.web.token')"


def _watch(page: Any) -> dict[str, list[Any]]:
    seen: dict[str, list[Any]] = {"refused": [], "errors": [], "sockets": []}
    page.on("response", lambda r: seen["refused"].append(f"{r.status} {r.url}")
            if r.status == 401 else None)
    page.on("pageerror", lambda e: seen["errors"].append(str(e)[:200]))

    page.on("websocket", lambda ws: seen["sockets"].append(ws))
    return seen


def _body(page: Any) -> str:
    return str(page.evaluate("() => document.body.innerText"))


class TestWayIn:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _signed_out(self, browser: Any, width: int, query: str, name: str) -> dict[str, Any]:
        """A fresh browser (its own storage) opens ``/{query}``; what it shows."""
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        seen = _watch(page)
        page.goto(f"{self.base}/{query}", wait_until="load")
        try:
            page.get_by_text(SENTENCE).first.wait_for(timeout=15_000)
        except Exception:
            pass
        page.wait_for_timeout(600)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))
        out = {
            "sentence": SENTENCE in _body(page),
            "raw_code": "principal_right_required" in _body(page),
            "stored": page.evaluate(STORED_JS),
            "refused": len(seen["refused"]),
            "errors": seen["errors"],
        }
        ctx.close()
        return out

    def test_one_token_url_signs_the_browser_in(self) -> None:
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # ── W1: the token URL ────────────────────────────────────────
                ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                          device_scale_factor=1)
                first = ctx.new_page()
                first.set_default_timeout(T)
                first.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(first)
                if "token=" in first.url:
                    fails["W1 the token leaves the address bar"] = first.url
                if first.evaluate(STORED_JS) != TOKEN:
                    fails["W1 the browser keeps the token"] = first.evaluate(STORED_JS)
                first.close()

                # ── W2: a new tab / bookmark with no token, at 1440 and 393 ──
                for width, path in ((1440, "/"), (393, "/"), (1440, "/welcome")):
                    page = ctx.new_page()
                    page.set_viewport_size({"width": width, "height": SIZES[width]})
                    page.set_default_timeout(T)
                    seen = _watch(page)
                    page.goto(f"{self.base}{path}", wait_until="load")
                    if path == "/":
                        _normal_chair(page)
                    page.wait_for_timeout(1500)
                    _settle(page)
                    tag = f"W2 {path} {width}"
                    page.screenshot(path=str(SHOTS / f"bookmark{path.replace('/', '-') or '-'}-{width}.png"))
                    if seen["refused"]:
                        fails[f"{tag}: no request is refused"] = seen["refused"][:5]
                    if SENTENCE in _body(page) or "principal_right_required" in _body(page):
                        fails[f"{tag}: the desk loads signed in"] = _body(page)[:300]
                    if path == "/" and not any(not ws.is_closed() for ws in seen["sockets"]):
                        fails[f"{tag}: the websocket opens and stays open"] = len(seen["sockets"])
                    if seen["errors"]:
                        fails[f"{tag}: no page error"] = seen["errors"]
                    page.close()
                ctx.close()

                # ── W3 / W4: a wrong token, then no token at all ─────────────
                for width in SIZES:
                    for query, name in ((f"?token=wrong-{TOKEN}", "W3 wrong token"), ("", "W4 no token")):
                        out = self._signed_out(browser, width, query, name.split()[0].lower())
                        tag = f"{name} {width}"
                        if not out["refused"]:
                            fails[f"{tag}: the hub refuses it"] = out
                        if not out["sentence"]:
                            fails[f"{tag}: the one sentence shows"] = out
                        if out["raw_code"]:
                            fails[f"{tag}: no raw error code"] = out
                        if out["stored"]:
                            fails[f"{tag}: the refused token is forgotten"] = out
                        if out["errors"]:
                            fails[f"{tag}: no page error"] = out["errors"]
            finally:
                browser.close()
        assert not fails, fails
