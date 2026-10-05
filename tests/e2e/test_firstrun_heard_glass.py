"""First run "C1 · Heard first" (owner ratified 2026-10-05) on the real hub.

A cold isolated HOME opens on the first-run face. The "Set up local AI"
API is PR #856's (`/api/setup/local-ai`); this PR merges after it, so the
rig answers that one route with a scripted fake of its contract. Every
other read and write is the real hub: the owner's name through
`PUT /api/settings`, the first sentence through the real dictation socket
(Chromium's fake device plays a WAV; the hub's transcriber is a fixture),
and Keep as note through `POST /api/notes`.

The flow, at 1440 and 393: before -> running (First words lights when the
speech model lands, while the chat model still downloads) -> stopped ->
ready -> name typed -> listening -> writing -> heard (his words at the
display step) -> Keep as note creates the note and the Desk opens.

Shots go to $FIRSTRUN_SHOTS when it is set (the owner's comparison page),
else to the test's tmp folder.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import REPO, SPEECH_CAPABILITY, _boot, _ensure_build, assign_engine, engine_profile

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(240, method="thread")]

TOKEN = "firstrun-c1"
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
WORDS = "Send the cutover plan to Priya before Friday."
HF = "https://huggingface.co"
MB = 1_000_000


class FakeLocalAi:
    """PR #856's GET/POST /api/setup/local-ai, scripted by the test."""

    FILES = [
        ("whisper", "whisper-base-mlx", 142 * MB),
        ("embed", "nomic-embed-text v1.5", 146 * MB),
        ("starter", "Qwen3.5 4B", 2_741 * MB),
    ]

    def __init__(self) -> None:
        self.state = "not_started"
        self.on_device = {key: False for key, _, _ in self.FILES}
        self.bytes_done = 0
        self.error = ""
        self.posts: list[str] = []
        self.post_ready = False

    def body(self) -> dict[str, Any]:
        files = [
            {"key": key, "label": label, "filename": f"{key}.bin", "url": f"{HF}/x/{key}.bin",
             "size_bytes": size, "sha256": "0" * 64, "on_device": self.on_device[key]}
            for key, label, size in self.FILES
        ]
        missing = [row for row in files if not row["on_device"]]
        total = sum(size for _, _, size in self.FILES) if self.state in {"downloading", "failed"} else sum(
            row["size_bytes"] for row in missing)
        return {
            "state": self.state,
            "runtime": {"ready": True},
            "files": files,
            "bytes_total": total,
            "bytes_done": self.bytes_done if self.state == "downloading" else 0,
            "percent": 0,
            "egress": ({"destination": "huggingface.co", "what": "model file request", "files": len(missing),
                        "bytes": sum(row["size_bytes"] for row in missing)}
                       if missing and self.state != "downloading" else None),
            "local_engine": {"ready": self.state == "ready"},
            "meaning_search": "on" if self.state == "ready" else "off",
            "error": self.error,
            "error_code": "network" if self.error else "",
        }

    def run(self, *, whisper: bool, bytes_done: int) -> None:
        self.state = "downloading"
        self.error = ""
        self.on_device["whisper"] = whisper
        self.on_device["embed"] = whisper
        self.bytes_done = bytes_done

    def handle(self, route: Any) -> None:
        request = route.request
        if request.method == "POST":
            self.posts.append(request.url)
            if request.url.endswith("/cancel"):
                self.state = "not_started"
            elif self.post_ready:
                self.state, self.error = "ready", ""
                self.on_device = {key: True for key in self.on_device}
            else:
                self.run(whisper=False, bytes_done=40 * MB)
        route.fulfill(status=200 if request.method == "GET" else 202,
                      content_type="application/json", body=json.dumps(self.body()))


def _no_cut(page: Any, selector: str) -> list[str]:
    """Every matching label whose text is cut (scrollWidth > clientWidth)."""
    return page.eval_on_selector_all(
        selector, "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)")


def _display_count(page: Any) -> int:
    """Elements on the face drawn at the display step (26 px, weight 650)."""
    return page.eval_on_selector_all(
        "[data-testid='firstrun'] *",
        """els => els.filter(e => {
            const s = getComputedStyle(e);
            const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
            return own && s.fontSize === '26px' && s.fontWeight === '650';
        }).length""")


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_first_run_heard_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
    _ensure_build()
    import holdspeak.web_server as web_server

    gate = threading.Event()
    heard: list[int] = []
    original = web_server.WebRuntimeCallbacks

    def transcribe(audio: Any, **_: Any) -> str:
        import numpy as np

        assert np.asarray(audio).size, "the hub got no audio"
        heard.append(1)
        assert gate.wait(30), "the rig never released the transcript"
        return WORDS

    monkeypatch.setattr(web_server, "WebRuntimeCallbacks",
                        lambda **kwargs: original(**kwargs, on_transcribe=transcribe))
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    fake = FakeLocalAi()
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(10_000)
            page.route("**/api/setup/local-ai**", fake.handle)

            def shot(name: str) -> None:
                page.wait_for_timeout(350)
                path = out / f"C1-{name}-{width}.png"
                page.screenshot(path=str(path), full_page=width < 720)
                print("SHOT", path)

            page.goto(f"{base}/?token={TOKEN}")
            face = page.get_by_test_id("firstrun")
            face.wait_for(timeout=30_000)
            local_ai = page.get_by_test_id("firstrun-local-ai")
            words = page.get_by_test_id("firstrun-first-words")

            # ── before: one press, its size, the host on the row that leaves ──
            press = local_ai.get_by_role("button", name="Set up local AI · 3.0 GB", exact=True)
            expect(press).to_be_visible()
            expect(local_ai.locator(".gadget-chip-egress")).to_have_text("HUGGINGFACE.CO")
            expect(words.get_by_role("button", name="Dictate one sentence")).to_be_disabled()
            expect(words.get_by_text("WAITS FOR SPEECH")).to_be_visible()
            assert _display_count(page) == 1
            shot("before")

            # ── You: the name and the aliases, stored ──
            you = page.get_by_test_id("firstrun-you")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"):
                you.get_by_role("textbox", name="Your name", exact=True).fill("Karol Sane")
            alias = you.get_by_role("textbox", name="Also called", exact=True)
            alias.fill("Karol")
            alias.press("Enter")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"
                                      and "KS" in (r.request.post_data or "")):
                alias.fill("KS, me")
            expect(you.get_by_role("status", name="SET", exact=True)).to_be_visible()
            from holdspeak.config import Config

            owner = Config.load().owner
            assert owner.name == "Karol Sane" and owner.aliases == ["Karol", "KS", "me"], owner

            # ── running: speech not here yet -> First words stays shut ──
            press.click()
            expect(local_ai.get_by_role("group", name="Local AI download")).to_be_visible()
            expect(words.get_by_role("button", name="Dictate one sentence")).to_be_disabled()
            assert fake.posts and not fake.posts[0].endswith("/cancel")

            # ── the speech model lands while the chat model downloads ──
            fake.run(whisper=True, bytes_done=288 * MB + 1_080 * MB)
            page.wait_for_timeout(1000)
            fake.run(whisper=True, bytes_done=288 * MB + 1_126 * MB)
            page.wait_for_timeout(1000)
            dictate = words.get_by_role("button", name="◖ Dictate one sentence")
            expect(dictate).to_be_enabled()
            expect(words).to_have_attribute("data-lit", "true")
            expect(words.get_by_text("SPEECH READY")).to_be_visible()
            chat = local_ai.locator("[role='listitem'][data-status='running']")
            expect(chat).to_contain_text("Chat")
            expect(chat).to_contain_text("/ 2.7 GB")
            # The species fix: the running label is whole at every width.
            assert _no_cut(page, "[data-testid='firstrun-local-ai'] [role='listitem'] > span:nth-child(2)") == []
            expect(local_ai.get_by_role("button", name="Stop", exact=True)).to_be_visible()
            shot("running")

            # ── stopped: the plain reason and one verb ──
            fake.state, fake.error = "failed", "The download stopped. Try again to continue."
            expect(local_ai.get_by_text("CAN'T DOWNLOAD")).to_be_visible()
            expect(local_ai.get_by_text(fake.error)).to_be_visible()
            shot("failed")

            # ── Try again -> ready ──
            fake.post_ready = True
            local_ai.get_by_role("button", name="Try again", exact=True).click()
            expect(local_ai.get_by_text("3 MODELS · 3.0 GB · FROM HUGGINGFACE.CO")).to_be_visible()
            expect(local_ai.locator(".gadget-chip-egress")).to_have_count(0)

            # ── listening -> writing -> heard ──
            if width < 720:
                dictate.scroll_into_view_if_needed()
            dictate.click()
            stop = words.get_by_role("button", name="Stop listening", exact=True)
            expect(stop).to_be_visible()
            expect(words.get_by_text("LISTENING")).to_be_visible()
            page.wait_for_timeout(1500)
            shot("done-1")
            stop.click()
            expect(words.get_by_text("WRITING")).to_be_visible()
            shot("done-2")
            gate.set()
            quote = words.get_by_test_id("heard-quote")
            expect(quote.locator("blockquote")).to_have_text(f"“{WORDS}”")
            expect(quote).to_contain_text("8 WORDS")
            assert heard == [1]
            # One display element: his words. The heading stepped down.
            assert _display_count(page) == 1
            assert quote.locator("blockquote").evaluate("e => getComputedStyle(e).fontSize") == "26px"
            expect(page.get_by_role("heading", name="Heard")).to_be_visible()
            expect(words.get_by_role("button", name="Again", exact=True)).to_be_visible()
            if width < 720:
                # 393: his words come first, on screen without a scroll.
                page.evaluate("window.scrollTo(0, 0)")
                box = quote.locator("blockquote").bounding_box()
                assert box and box["y"] + box["height"] <= height, box
                tops = [page.get_by_test_id(t).bounding_box()["y"]
                        for t in ("firstrun-first-words", "firstrun-local-ai", "firstrun-you")]
                assert tops[0] < tops[1] and tops[0] < tops[2], tops
            shot("done-3")

            # ── Keep as note: a real note, then the Desk ──
            with page.expect_response(lambda r: r.url.endswith("/api/notes") and r.request.method == "POST") as made:
                words.get_by_role("button", name="Keep as note", exact=True).click()
            assert made.value.ok, made.value.text()
            note = made.value.json()["note"]
            assert note["body_markdown"] == WORDS and note["title"] == "First dictation"
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            page.locator(".chair:not(.chair-first-value)").wait_for()
            browser.close()
    finally:
        gate.set()
        server.stop()
