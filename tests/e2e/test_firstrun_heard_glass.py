"""First run "C1 · Heard first" (owner ratified 2026-10-05) on the real hub.

A cold isolated HOME opens on the first-run face. Every read and write is
the real hub, "Set up local AI" included: the merged #856 service
(`LocalAISetupService`, GET/POST /api/setup/local-ai) runs whole. Only its
leaves are replaced, the way #856's own fences replace them
(tests/unit/test_local_ai_setup.py): the pinned files are small blobs
served by a file server on this device (the real pins name 3 GB on
huggingface.co), and the runtime-readiness probe says ready (the blob is
not a loadable model). The download, the per-file `on_device` reads, the
one egress receipt, the stop and the resume are the service's own.

The owner's name goes through `PUT /api/settings`, the first sentence
through the real dictation socket (Chromium's fake device plays a WAV; the
hub's transcriber is a fixture), and Keep as note through `POST /api/notes`.

The flow, at 1440 and 393: before -> running (First words lights when the
Whisper files land, while the chat model still downloads) -> stopped
(the connection drops) -> Try again resumes -> ready -> listening ->
writing -> heard (his words at the display step) -> Keep as note creates
the note and the Desk opens.

Shots go to $FIRSTRUN_SHOTS when it is set (the owner's comparison page),
else to the test's tmp folder.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from .glass_infra import REPO, SPEECH_CAPABILITY, _boot, _ensure_build, assign_engine, engine_profile

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(240, method="thread")]

TOKEN = "firstrun-c1"
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
WORDS = "Send the cutover plan to Priya before Friday."
MB = 1_000_000
WHISPER_REPO = "mlx-community/whisper-base-mlx"
STARTER_PATH = "/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf"


def _blob(tag: bytes, size: int, magic: bytes = b"") -> bytes:
    return (magic + tag * (size // len(tag) + 1))[:size]


@functools.cache
def _pins() -> SimpleNamespace:
    """Small pinned blobs (#856's fence shape), sized so the face reads true."""
    from holdspeak.memory.local_model import PinnedModel
    from holdspeak.services.local_ai_setup_service import STARTER_PRESET_ID

    def pin(repository: str, filename: str, content: bytes, magic: bytes, label: str) -> PinnedModel:
        return PinnedModel(
            name=filename, label=label, repository=repository, revision="r1", filename=filename,
            sha256=hashlib.sha256(content).hexdigest(), size=len(content), license="MIT",
            architecture="test", context_ceiling=2048, magic=magic,
        )

    config, weights = b'{"model_type": "whisper"}', _blob(b"whisper-weights-", 14 * MB)
    embed, starter = _blob(b"embed-", 15 * MB, b"GGUF"), _blob(b"starter-", 120 * MB, b"GGUF")
    whisper = (pin(WHISPER_REPO, "config.json", config, b"", "whisper-base-mlx"),
               pin(WHISPER_REPO, "weights.npz", weights, b"", "whisper-base-mlx"))
    embed_pin = pin("nomic-ai/nomic-embed-text-v1.5-GGUF", "nomic-embed-text-v1.5.Q8_0.gguf", embed, b"GGUF",
                    "nomic-embed-text v1.5")
    starter_sha = "sha256:" + hashlib.sha256(starter).hexdigest()
    manifest = {"files": [{"path": "Qwen3.5-4B-Q4_K_M.gguf", "sha256": starter_sha, "size": len(starter)}]}
    manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    catalog = {"catalog_revision": 9, "entries": [{
        "id": STARTER_PRESET_ID, "label": "Qwen3.5 4B",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {"repository": "unsloth/Qwen3.5-4B-GGUF", "revision": "r1",
                   "filename": "Qwen3.5-4B-Q4_K_M.gguf", "file_sha256": starter_sha,
                   "manifest_sha256": manifest_sha, "download_bytes": len(starter),
                   "installed_bytes": len(starter), "peak_free_bytes": len(starter) * 2,
                   "license": "Apache-2.0"},
    }]}
    files = {f"/{WHISPER_REPO}/config.json": config, f"/{WHISPER_REPO}/weights.npz": weights,
             f"/{embed_pin.repository}/{embed_pin.filename}": embed, STARTER_PATH: starter}
    return SimpleNamespace(whisper=whisper, embed=embed_pin, catalog=catalog, files=files)


class Source:
    """The model host, on this device. The chat model's first answer sends
    half its bytes, then holds until the rig releases it; `drop` ends that
    answer short (the connection drops). A resume (Range) answers whole."""

    def __init__(self) -> None:
        self.files = _pins().files
        self.hold = threading.Event()
        self.drop = False
        self.requests: list[tuple[str, str]] = []
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                header = self.headers.get("Range", "")
                source.requests.append((self.path, header))
                body = source.files.get(self.path)
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                start = int(header[6:].split("-")[0]) if header.startswith("bytes=") else 0
                if start:
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
                else:
                    self.send_response(200)
                rest = body[start:]
                self.send_header("Content-Length", str(len(rest)))
                self.end_headers()
                if self.path == STARTER_PATH and not start:
                    half = len(rest) // 2
                    self.wfile.write(rest[:half])
                    self.wfile.flush()
                    source.hold.wait(60)
                    if source.drop:
                        return  # short answer: the client reads a broken download
                    rest = rest[half:]
                self.wfile.write(rest)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def url_for(self, model: Any) -> str:
        return f"{self.base}/{model.repository}/{model.filename}"

    def close(self) -> None:
        self.hold.set()
        self.server.shutdown()
        self.server.server_close()


def _real_local_ai(monkeypatch: pytest.MonkeyPatch, source: Source) -> None:
    """The hub builds the REAL #856 service; only its leaves point here."""
    from holdspeak.services import local_ai_setup_service as module
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.meaning_search_service import MeaningSearchService
    from holdspeak.services.model_profile_service import ModelProfileService

    pins = _pins()
    allowed = lambda host: host == "127.0.0.1"  # noqa: E731
    monkeypatch.setattr(ModelProfileService, "_local_runtime_readiness",
                        staticmethod(lambda runtime_id: ("ready", "ready")))
    monkeypatch.setattr("holdspeak.whisper_models._PINNED", {("mlx", "base"): pins.whisper})
    real = module.LocalAISetupService

    def build(db: Any, *, meaning_search: Any, broker_provider: Any = None, **_: Any) -> Any:
        meaning = MeaningSearchService(
            db, assignment_service=InferenceAssignmentService(db), broker_provider=broker_provider,
            model=pins.embed, source_url=source.url_for(pins.embed), allowed_host=allowed,
            wake=lambda: None,
        )
        return real(
            db, meaning_search=meaning, broker_provider=broker_provider,
            config_provider=lambda: SimpleNamespace(model=SimpleNamespace(name="base", backend="mlx")),
            catalog_provider=lambda: pins.catalog, url_for=source.url_for, allowed_host=allowed,
        )

    monkeypatch.setattr(module, "LocalAISetupService", build)


def _seed_lan_proposal(monkeypatch: pytest.MonkeyPatch) -> str:
    """One ready LAN engine, stored as a proposal by #855's own producer
    (`InferenceDefaultService._record_proposals`); detection is the leaf."""
    from holdspeak.db import get_database
    from holdspeak.services import concierge_service
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_default_service import InferenceDefaultService

    from .glass_infra import ENGINE_PROFILE

    engine = {
        "id": f"lan:{ENGINE_PROFILE}", "kind": concierge_service.KIND_LAN, "name": "qwen3.8-27b",
        "host": "192.168.1.43", "state": concierge_service.STATE_READY,
        "baseUrl": "http://192.168.1.43:8080/v1", "profileId": ENGINE_PROFILE, "profileRevision": 1,
    }
    monkeypatch.setattr(concierge_service, "detect", lambda **_: {"engines": [engine]})
    db = get_database()
    service = InferenceDefaultService(db, assignment_service=InferenceAssignmentService(db))
    assert service._record_proposals() == 1
    return engine["id"]


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
    source = Source()
    _real_local_ai(monkeypatch, source)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    proposal_id = _seed_lan_proposal(monkeypatch)
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
            press = local_ai.get_by_role("button", name="Set up local AI · 149 MB", exact=True)
            expect(press).to_be_visible()
            expect(local_ai.locator(".gadget-chip-egress")).to_have_text("HUGGINGFACE.CO")
            expect(words.get_by_role("button", name="Dictate one sentence")).to_be_disabled()
            expect(words.get_by_text("WAITS FOR SPEECH")).to_be_visible()
            assert _display_count(page) == 1
            # FOUND: the stored LAN proposal, its egress chip on its row.
            found = page.get_by_test_id("firstrun-found")
            expect(found).to_contain_text("qwen3.8-27b")
            expect(found).to_contain_text("LAN SERVER")
            expect(found.locator(".gadget-chip-egress")).to_have_text("192.168.1.43 · LAN")
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

            # ── running: the Whisper files land first; the chat model holds half-way ──
            words_shut = words.get_by_role("button", name="Dictate one sentence", exact=True)
            expect(words_shut).to_be_disabled()
            press.click()
            expect(local_ai.get_by_role("group", name="Local AI download")).to_be_visible()
            dictate = words.get_by_role("button", name="◖ Dictate one sentence")
            expect(dictate).to_be_enabled(timeout=20_000)
            expect(words).to_have_attribute("data-lit", "true")
            expect(words.get_by_role("status", name="SPEECH READY")).to_be_visible()
            chat = local_ai.locator("[role='listitem'][data-status='running']")
            expect(chat).to_contain_text("Chat")
            expect(chat).to_contain_text("/ 120 MB")
            done = local_ai.locator("[role='listitem'][data-status='done']")
            expect(done).to_have_count(2)
            # The Whisper files are on this device before the chat model is.
            pins = _pins()
            assert [p for p, _ in source.requests][:3] == [
                f"/{WHISPER_REPO}/config.json", f"/{WHISPER_REPO}/weights.npz",
                f"/{pins.embed.repository}/{pins.embed.filename}"], source.requests
            # The species fix: the running label is whole at every width.
            assert _no_cut(page, "[data-testid='firstrun-local-ai'] [role='listitem'] > span:nth-child(2)") == []
            expect(local_ai.get_by_role("button", name="Stop", exact=True)).to_be_visible()
            shot("running")

            # ── stopped: the connection drops; the plain reason and one verb ──
            source.drop = True
            source.hold.set()
            expect(local_ai.get_by_role("status", name="CAN'T DOWNLOAD")).to_be_visible(timeout=20_000)
            expect(local_ai.get_by_text("The download stopped. Try again to continue.")).to_be_visible()
            # Speech stays: First words is still open.
            expect(dictate).to_be_enabled()
            shot("failed")

            # ── Try again resumes the part file -> ready ──
            source.drop = False
            local_ai.get_by_role("button", name="Try again", exact=True).click()
            expect(local_ai.get_by_text("3 MODELS · 149 MB · FROM HUGGINGFACE.CO")).to_be_visible(timeout=30_000)
            assert any(p == STARTER_PATH and r.startswith("bytes=") for p, r in source.requests), source.requests
            expect(local_ai.locator(".gadget-chip-egress")).to_have_count(0)

            # ── Use it: the owner's press makes the LAN engine the default ──
            with page.expect_response(lambda r: r.url.endswith("/api/inference/defaults/use-proposal")) as used:
                found.get_by_role("button", name="Use qwen3.8-27b", exact=True).click()
            assert used.value.ok, used.value.text()
            assert used.value.request.post_data_json == {"proposal_id": proposal_id}
            expect(found.get_by_role("status", name="IN USE · DEFAULT")).to_be_visible()
            from holdspeak.db import get_database

            with get_database()._connection() as conn:
                row = conn.execute(
                    "SELECT state FROM inference_default_proposals WHERE engine_id=?", (proposal_id,)).fetchone()
            assert row["state"] == "used"

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
        source.close()
