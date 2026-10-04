"""Meaning search row in Models (THE SET): glass at 1440 and 393.

The hub and the Meaning search service are the real ones.  The Models face
gets its engine list from the Concierge rig (as the other Concierge glass
tests do).  States on glass:

* OFF, the model is not on this device (the press downloads: egress chip)
* DOWNLOADING n% (the source is a slow file server on this device)
* INDEXING n of m, ON, and OFF again (the real GGUF, adopted; needs
  ``HOLDSPEAK_MEMORY_EMBED_MODEL`` and ``llama-cpp-python``)

The shots go to ``.tmp/meaning-search-shots/`` for the owner's review
(UX-CANON A.13).
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _normal_chair, _rendered_text_faults, _settle
from .test_hs170_concierge_glass import _monkeypatch_concierge, _open_concierge, _window

REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / ".tmp" / "meaning-search-shots"
SHOTS.mkdir(parents=True, exist_ok=True)
TOKEN = "glass-test"
WIDTHS = ((1440, 900), (393, 852))

pytestmark = [pytest.mark.timeout(300)]


def _shot(page: Any, name: str, width: int) -> Path:
    """The whole Models window and the row alone."""
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    row = page.get_by_test_id("concierge-meaning-search")
    row.scroll_into_view_if_needed()
    _settle(page)
    _window(page).screenshot(path=str(path))
    row.screenshot(path=str(SHOTS / f"{name}-{width}-row.png"))
    page.set_viewport_size(old)
    assert path.stat().st_size > 2_000
    return path


def _open(page: Any, url: str) -> Any:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _normal_chair(page)
    _open_concierge(page)
    page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
    row = page.get_by_test_id("concierge-meaning-search")
    row.wait_for(timeout=10_000)
    return row


def _state(page: Any, state: str, timeout: float = 60_000) -> None:
    page.locator(f'[data-testid="meaning-search-state"][data-state="{state}"]').wait_for(timeout=timeout)


def _assert_species(page: Any, row: Any) -> None:
    """Every verb is the library Button; the row has no raw button and no dialog."""
    assert row.locator("button:not(.btn):not(.surface-ledger-line):not(.gadget-chip-egress)").count() == 0
    assert page.locator("[role='dialog']").count() == 0
    # Every drawn leaf of the row is inside the window (nothing is cut at 393).
    # (The species' line-2 box itself is wider than the window on every SET row.)
    outside = row.evaluate(
        """el => { const w = el.closest('.desk-surface-window').getBoundingClientRect();
                  return [...el.querySelectorAll('*')].filter(n => {
                    const r = n.getBoundingClientRect();
                    return n.children.length === 0 && r.width > 0 && (r.left < w.left - 1 || r.right > w.right + 1); })
                    .map(n => n.className + ' ' + Math.round(n.getBoundingClientRect().right) + '>' + Math.round(w.right)); }"""
    )
    assert outside == [], outside


ROW = '[data-testid="concierge-meaning-search"]'


def _assert_whole_on_glass(page: Any, where: str) -> None:
    """The on-glass text reader: no text of the row is cut, nothing overlaps."""
    faults = _rendered_text_faults(page, ROW, on_glass=True)
    assert faults["scopes"] == 1, f"{where}: {faults}"
    assert not faults["clipped"] and not faults["overlaps"] and not faults["ellipsis"], f"{where}: {faults}"


def _stand_in_service(monkeypatch: Any, source: Any, pinned_bytes: bytes) -> None:
    """The real service, with a source on this device in place of Hugging Face."""
    from holdspeak.memory.local_model import EMBED_MODEL, PinnedModel
    from holdspeak.services import meaning_search_service as module

    monkeypatch.delenv("HOLDSPEAK_MEMORY_EMBED_MODEL", raising=False)
    stand_in = PinnedModel(**{
        **EMBED_MODEL.__dict__, "sha256": hashlib.sha256(pinned_bytes).hexdigest(), "size": len(pinned_bytes),
    })
    real_init = module.MeaningSearchService.__init__

    def init(self, db, **kwargs):
        real_init(self, db, **{
            **kwargs, "model": stand_in, "source_url": source.url,
            "allowed_host": lambda host: host == "127.0.0.1",
        })

    monkeypatch.setattr(module.MeaningSearchService, "__init__", init)


class _SlowSource:
    def __init__(self, content: bytes, filename: str, pause: float = 0.7) -> None:
        source = self
        self.content = content
        self.pause = pause

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Length", str(len(source.content)))
                self.end_headers()
                step = 1024 * 1024
                try:
                    for start in range(0, len(source.content), step):
                        self.wfile.write(source.content[start:start + step])
                        self.wfile.flush()
                        time.sleep(source.pause)
                except OSError:
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/{filename}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.mark.parametrize("width,height", WIDTHS)
def test_off_and_downloading(tmp_path, monkeypatch, width, height):
    from holdspeak.memory.local_model import EMBED_MODEL

    content = b"GGUF" + bytes(12 * 1024 * 1024)
    source = _SlowSource(content, EMBED_MODEL.filename)
    # The real model name on the face; the bytes (12 MB) come from this device.
    _stand_in_service(monkeypatch, source, content)
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            row = _open(page, url)

            # OFF: the press will download, and the row says where from.
            _state(page, "off")
            assert row.get_by_test_id("meaning-search-verb").inner_text().strip() == "Turn on"
            text = row.inner_text()
            assert "Meaning search" in text and "OFF" in text
            assert "HUGGINGFACE.CO" in text and "DOWNLOAD" in text
            _shot(page, "1-off-download", width)
            _assert_species(page, row)
            _assert_whole_on_glass(page, f"off {width}")

            # The press: DOWNLOADING n%.
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "downloading")
            page.wait_for_function(
                """() => /DOWNLOADING [1-9]\\d?%/.test(
                    document.querySelector('[data-testid="meaning-search-state"]').textContent)""",
                timeout=20_000,
            )
            assert row.get_by_test_id("meaning-search-verb").inner_text().strip() == "Turn off"
            _shot(page, "2-downloading", width)
            _assert_species(page, row)
            _assert_whole_on_glass(page, f"downloading {width}")

            # Turn off stops the download.
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "off", timeout=20_000)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        source.close()


@pytest.mark.slow
@pytest.mark.requires_llama_cpp
@pytest.mark.parametrize("width,height", WIDTHS)
def test_indexing_on_and_off_with_the_real_model(tmp_path, monkeypatch, width, height):
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    if not model_path or not Path(model_path).is_file():
        pytest.skip("set HOLDSPEAK_MEMORY_EMBED_MODEL to nomic-embed-text-v1.5.Q8_0.gguf")
    pytest.importorskip("llama_cpp")
    from holdspeak import runtime_lock

    _monkeypatch_concierge(monkeypatch)
    # The hub that owns the database runs the memory conductor.
    runtime_lock.claim_database(tmp_path / "holdspeak.db", label="meaning-search-glass")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database

    db = get_database()
    for index in range(700):
        db.notes.upsert(
            note_id=f"seed-{index}", title=f"Site visit {index}",
            body_markdown=f"Visit {index}: the crew checked pump {index % 17} and logged valve {index % 29}.",
        )
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            row = _open(page, url)

            # OFF with the file on this device: the press sends nothing out.
            _state(page, "off")
            text = row.inner_text()
            assert "THIS DEVICE" in text and "HUGGINGFACE.CO" not in text and "DOWNLOAD" not in text
            _shot(page, "5-off-on-device", width)

            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "indexing", timeout=30_000)
            page.wait_for_function(
                """() => /INDEXING [1-9]\\d* OF \\d+/.test(
                    document.querySelector('[data-testid="meaning-search-state"]').textContent)""",
                timeout=60_000,
            )
            _shot(page, "3-indexing", width)
            _assert_species(page, row)

            _state(page, "on", timeout=180_000)
            assert row.get_by_test_id("meaning-search-verb").inner_text().strip() == "Turn off"
            assert "THIS DEVICE" in row.inner_text()
            _shot(page, "4-on", width)
            _assert_species(page, row)

            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "off", timeout=20_000)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        runtime_lock.release_database()


@pytest.mark.parametrize("width,height", WIDTHS)
def test_a_refused_press_is_named_with_a_way_forward(tmp_path, monkeypatch, width, height):
    """Review of #820, P2-1: the real hub answers 401 (missing right: owner)
    and the row stayed OFF with no reason.  The request below reaches the real
    hub with a token the hub does not know; the 401 is the hub's own."""
    from holdspeak.memory.local_model import EMBED_MODEL

    content = b"GGUF" + bytes(12 * 1024 * 1024)
    source = _SlowSource(content, EMBED_MODEL.filename)
    _stand_in_service(monkeypatch, source, content)
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    answers: list[int] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: answers.append(r.status) if r.url.endswith("/turn-on") else None)
            row = _open(page, url)
            _state(page, "off")

            def not_the_owner(route: Any) -> None:
                route.continue_(headers={**route.request.headers, "x-holdspeak-token": "not-the-owner"})

            page.route("**/api/memory/meaning-search/turn-on", not_the_owner)
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "failed", timeout=20_000)
            assert answers == [401], answers  # the hub's own refusal
            text = row.inner_text()
            assert "NOT PERMITTED" in text
            assert "Only the owner can do this. Open this desk as the owner. Then press Try again." in text
            assert row.get_by_test_id("meaning-search-verb").inner_text().strip() == "Try again"
            assert row.get_by_test_id("meaning-search-error").get_attribute("role") == "alert"
            _shot(page, "6-refused", width)
            _assert_species(page, row)
            _assert_whole_on_glass(page, f"refused {width}")

            # The way forward works: the same press, as the owner.
            page.unroute("**/api/memory/meaning-search/turn-on")
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "downloading", timeout=20_000)
            assert answers == [401, 200]
            assert row.get_by_test_id("meaning-search-error").count() == 0
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "off", timeout=20_000)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        source.close()


@pytest.mark.parametrize("width,height", WIDTHS)
def test_a_wrong_file_is_named_and_the_whole_reason_is_on_the_glass(tmp_path, monkeypatch, width, height):
    """Review of #820, P2-2: a real hash mismatch gave an alert whose first
    sentence was cut at 1440.  The mismatch here is real: the source serves
    bytes that do not have the pinned hash."""
    from holdspeak.memory.local_model import EMBED_MODEL

    pinned = b"GGUF" + bytes(range(256)) * 1200
    source = _SlowSource(b"GGUF" + bytes(len(pinned) - 4), EMBED_MODEL.filename, pause=0.0)
    _stand_in_service(monkeypatch, source, pinned)
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            row = _open(page, url)
            _state(page, "off")
            row.get_by_test_id("meaning-search-verb").click()
            _state(page, "failed", timeout=30_000)
            text = row.inner_text()
            assert "WRONG FILE" in text
            assert "The file was not correct. Press Try again to download it again." in text
            assert row.get_by_test_id("meaning-search-verb").inner_text().strip() == "Try again"
            _shot(page, "7-wrong-file", width)
            _assert_species(page, row)
            _assert_whole_on_glass(page, f"wrong file {width}")
            # Every other state of the row is whole on the glass too.
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        source.close()
