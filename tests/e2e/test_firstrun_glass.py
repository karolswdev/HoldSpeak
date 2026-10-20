"""Current Setup browser proof at 1440 and 393.

The real Setup inventory and use producers drive found items, People,
Ready and Open my desk. Native calendar, CLI and model leaves use isolated
fixtures. Fake browser media drives the actual dictation socket and two
notes kept across a reload; late permission grants must stop after exit.
Retired multi-card walks are retained under tests/e2e/_parked/.
"""
from __future__ import annotations

import os
import re
import ssl
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import SPEECH_CAPABILITY, _api, _boot, _ensure_build, assign_engine, engine_profile


def _expand_first_use_setup(page: Any) -> None:
    """Existing media/account flows explicitly enter the optional setup wells."""
    page.locator(".firstrun-chat, .firstrun-optional").evaluate_all("els => els.forEach(el => { el.open = true; })")


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_setup_face_uses_everything_adds_people_and_leaves_for_the_desk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    """ST3-ST5: the real Setup producers drive the two-size owner walk."""
    _ensure_build()
    source = Source()
    source.hold.set()
    _real_local_ai(monkeypatch, source)
    server, base = _boot(tmp_path, monkeypatch, token="setup-st3-st5")
    try:
        # Seed one real calendar projection. PeopleService.suggestions reads
        # this stored title and attendee list; the face never receives a
        # screen-shaped fixture.
        from holdspeak.db import get_database
        from holdspeak.db.calendar_events import CalendarEvent

        start = datetime.now(timezone.utc) + timedelta(days=1)
        get_database().calendar_events.replace_projection(
            "setup-glass",
            [CalendarEvent(
                id="setup-1-1", uid="setup-series", title="1:1 with Mira",
                starts_at=start.isoformat().replace("+00:00", "Z"),
                ends_at=(start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None, meeting_url=None, last_seen_at=time.time(),
                subscription_revision="setup-glass", source_id="work", source_label="Work",
                attendees=("mira.okafor@example.com", "karol@example.com"),
            )],
            seen_at=time.time(), source_id="work", source_label="Work",
        )
        from holdspeak.config import Config

        config = Config.load()
        config.owner.name = "Karol"
        config.owner.aliases = []
        config.save()

        with sync_playwright() as pw:
            from tests._evidence import evidence_dir

            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(20_000)
            page.goto(f"{base}/?token=setup-st3-st5", wait_until="load")
            face = page.get_by_test_id("setup-face")
            face.wait_for(timeout=30_000)
            shots = evidence_dir("setup-st3-st5")

            expect(face.get_by_test_id("setup-found")).to_contain_text("Speech")
            expect(face).to_contain_text("huggingface.co")
            expect(face).not_to_contain_text("3 GB")
            people = face.get_by_test_id("setup-people")
            expect(people).to_contain_text("Mira Okafor")
            found_wire = _api(page, "GET", "/api/setup/found", token="setup-st3-st5")
            mira = next(item for item in found_wire["suggestions"] if item["name"] == "Mira Okafor")
            assert mira["series"]["label"] == "1:1 with Mira"
            page.screenshot(path=str(shots / f"setup-found-{width}.png"), full_page=width < 720)

            people.get_by_role("textbox", name="Your people", exact=True).fill(
                "Mira Okafor, Theo Lindqvist, Jun Park"
            )
            with page.expect_response(
                lambda response: response.url.endswith("/api/setup/people") and response.request.method == "POST"
            ) as added:
                people.get_by_role("button", name="Add", exact=True).click()
            assert added.value.ok, added.value.text()
            expect(people).to_contain_text("Mira Okafor, Theo Lindqvist, Jun Park")
            relationships = _api(page, "GET", "/api/people/relationships", token="setup-st3-st5")["relationships"]
            assert {row["display_name"] for row in relationships} >= {
                "Mira Okafor", "Theo Lindqvist", "Jun Park",
            }

            with page.expect_response(
                lambda response: response.url.endswith("/api/setup/use") and response.request.method == "POST"
            ) as used:
                page.get_by_role("button", name="Use everything found", exact=True).click()
            assert used.value.ok, used.value.text()
            expect(face.get_by_text("Works", exact=True).first).to_be_visible(timeout=30_000)
            expect(face).to_contain_text("Ready, Karol.")
            expect(face.get_by_role("button", name="Say one sentence", exact=True)).to_be_visible()
            expect(face.get_by_role("button", name="Open my desk", exact=True)).to_be_visible()
            page.screenshot(path=str(shots / f"setup-ready-{width}.png"), full_page=width < 720)

            # The current Setup face keeps the microphone door visible while
            # the browser refuses capture.  The owner can name the failure,
            # check the microphone, or press Again; no listening state loses
            # its Stop control.
            page.evaluate(_TOGGLE_MIC)
            page.evaluate("window.__denyMic = true")
            face.get_by_role("button", name="Say one sentence", exact=True).click()
            failure = face.get_by_test_id("setup-take-failure")
            expect(failure).to_contain_text("NO DEVICE FOUND", timeout=15_000)
            expect(failure.get_by_role("button", name="Check the microphone", exact=True)).to_be_visible()
            expect(failure.get_by_role("button", name="Again", exact=True)).to_be_visible()
            page.screenshot(path=str(shots / f"setup-mic-failed-{width}.png"), full_page=width < 720)
            page.evaluate("window.__denyMic = false")

            # The working inventory is a closed fold. Open my desk is the
            # always-available egress and retains the stored people and setup.
            works_summary = face.locator("details").filter(has_text="Works").locator("summary")
            expect(works_summary).to_be_visible()
            works_summary.click()
            expect(face).to_contain_text("Speech")
            face.get_by_role("button", name="Open my desk", exact=True).click()
            expect(page.get_by_test_id("today-day")).to_be_visible(timeout=20_000)

            # Setup is also the later menu window. Its working rows remain in
            # the fold, and the finale's desk verb opens Today.
            page.locator(".desk-mark").click()
            _row(page, "Setup").click()
            later = page.get_by_test_id("setup-face")
            later.wait_for(timeout=15_000)
            expect(later.locator("details").filter(has_text="Works").locator("summary")).to_be_visible()
            later.get_by_role("button", name="Open my desk", exact=True).click()
            expect(page.get_by_test_id("today-day")).to_be_visible(timeout=20_000)
            browser.close()
    finally:
        server.stop()
        source.close()

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402
import functools
import hashlib
import json
from types import SimpleNamespace
from .glass_infra import REPO

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

EMAIL = "karol@acme.com"
SITE = "acme.atlassian.net"


def _ics(name: str, events: list[tuple[str, str, datetime]]) -> bytes:
    stamp = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//glass//EN", f"X-WR-CALNAME:{name}"]
    for uid, title, start in events:
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp(start)}", f"DTSTART:{stamp(start)}",
                  f"DTEND:{stamp(start + timedelta(minutes=30))}", f"SUMMARY:{title}", "END:VEVENT"]
    return ("\r\n".join(lines + ["END:VCALENDAR", ""])).encode()


class FakeEventKit:
    """The four EventKit calls the hub makes. The prompt is counted, never shown."""

    def __init__(self, ics: bytes) -> None:
        self.state = "not_determined"
        self.prompts = 0
        self.ics = ics
        self.delay = 2.0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import holdspeak.macos_calendar as macos

        monkeypatch.setattr(macos, "access_state", lambda: self.state)
        monkeypatch.setattr(macos, "request_access", self.request_access)
        monkeypatch.setattr(macos, "list_calendars", self.list_calendars)
        monkeypatch.setattr(macos, "read_calendar_ics", self.read_calendar_ics)

    def read_calendar_ics(self, source: str, **_: Any) -> bytes:
        # Astra #876 P2: today's calendar reads slowly; tomorrow's link is
        # already on the Door. Ready must wait for this read.
        time.sleep(self.delay)
        return self.ics

    def request_access(self, timeout: float = 120.0) -> str:
        self.prompts += 1
        self.state = "full_access"
        return self.state

    def list_calendars(self) -> list[dict[str, Any]]:
        if self.state != "full_access":
            return []
        return [{"id": "CAL-WORK-1", "title": "Work", "account": EMAIL, "kind": "caldav"}]


class IcsServer:
    """HTTPS on 127.0.0.1: /team.ics is a calendar; anything else is 404."""

    def __init__(self, tmp: Path, ics: bytes) -> None:
        cert, key = tmp / "ics-cert.pem", tmp / "ics-key.pem"
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-keyout", str(key),
             "-out", str(cert), "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"],
            check=True, capture_output=True,
        )
        self.cert = cert
        self.requests: list[str] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                server.requests.append(self.path)
                if self.path != "/team.ics":
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/calendar")
                self.send_header("Content-Length", str(len(ics)))
                self.end_headers()
                self.wfile.write(ics)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cert), str(key))
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"https://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class Runner:
    """The canned gh / acli answers (the shape test_philo9_b1 uses)."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout="Logged in to github.com account karolswdev (keyring)\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "switch"]:
            return subprocess.CompletedProcess(argv, 0, stdout="switched\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout=f"✓ Authenticated\n  Site: {SITE}\n  Email: {EMAIL}\n", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected")


def _sign_ins(home: Path, monkeypatch: pytest.MonkeyPatch, tmp: Path) -> None:
    """gh and acli sign-ins as files under the isolated HOME; stubs on PATH."""
    monkeypatch.delenv("GH_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    gh = home / ".config" / "gh"
    gh.mkdir(parents=True, exist_ok=True)
    (gh / "hosts.yml").write_text(
        "github.com:\n    users:\n        karolswdev:\n    git_protocol: https\n    user: karolswdev\n",
        encoding="utf-8")
    acli = home / ".config" / "acli"
    acli.mkdir(parents=True, exist_ok=True)
    profile = (f"current_profile: cloud-1:acct-1\nprofiles:\n  - site: {SITE}\n    email: {EMAIL}\n"
               "    cloud_id: cloud-1\n    account_id: acct-1\n    display_name: Karol Sane\n    auth_type: oauth\n")
    for product in ("jira", "confluence"):
        (acli / f"{product}_config.yaml").write_text(profile, encoding="utf-8")
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    for tool in ("gh", "acli"):
        stub = bin_dir / tool
        stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")




def test_a_reload_after_keep_never_replaces_the_kept_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Astra #876 P1, her sequence through the real note producer: dictate A,
    Keep as note, reload, dictate B, Keep as note -> two notes, A and B."""
    _ensure_build()
    import holdspeak.web_server as web_server

    sentences = iter([WORDS, "Book the room for the Atlas review."])
    original = web_server.WebRuntimeCallbacks
    monkeypatch.setattr(web_server, "WebRuntimeCallbacks",
                        lambda **kwargs: original(**kwargs, on_transcribe=lambda audio, **_: next(sentences)))
    source = Source()
    source.hold.set()
    _real_local_ai(monkeypatch, source)
    monkeypatch.delenv("GH_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    # Setup's current face opens the first sentence only after the owner
    # name and speech are ready.  Seed the name in this isolated hub just as
    # the shared ready rig does; never read or write the owner's HOME.
    from holdspeak.config import Config

    config = Config.load()
    config.owner.name = "Karol"
    config.save()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.set_default_timeout(15_000)

            def keep_one(text: str) -> None:
                face = _setup_face_ready(page, base)
                dictate = face.get_by_role("button", name="Say one sentence", exact=True)
                expect(dictate).to_be_enabled(timeout=30_000)
                dictate.click()
                page.wait_for_timeout(1000)
                face.get_by_role("button", name="Stop listening", exact=True).click()
                expect(face.get_by_test_id("heard-quote").locator("blockquote")).to_have_text(f"“{text}”")
                with page.expect_response(lambda r: r.url.endswith("/api/notes") and r.request.method == "POST") as made:
                    face.get_by_role("button", name="Keep as note", exact=True).click()
                assert made.value.ok, made.value.text()

            keep_one(WORDS)
            page.reload()
            keep_one("Book the room for the Atlas review.")
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            bodies = sorted(n["body_markdown"] for n in notes if "dictation" in (n.get("tags") or []))
            assert bodies == sorted([WORDS, "Book the room for the Atlas review."]), notes
            browser.close()
    finally:
        server.stop()
        source.close()


# ══ lane e2e-high-1 ════════════════════════════════════════

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


_GATED_MIC = """(() => {
  const media = navigator.mediaDevices;
  const original = media.getUserMedia.bind(media);
  let release;
  window.__gate = new Promise((resolve) => { release = resolve; });
  window.__grant = () => release();
  window.__streams = [];
  media.getUserMedia = async (constraints) => {
    await window.__gate;               // the permission prompt, pending
    const stream = await original(constraints);
    window.__streams.push(stream);
    return stream;
  };
})()"""

_LIVE_TRACKS = """() => (window.__streams || []).flatMap((s) => s.getTracks())
    .filter((t) => t.readyState === 'live').length"""

def _ready_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str, Source]:
    _ensure_build()
    source = Source()
    source.hold.set()  # no stop half-way: every model downloads whole
    _real_local_ai(monkeypatch, source)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    # The current Setup face gates the sentence control on the owner's name;
    # seed that existing setting so this rig reaches the real dictation door.
    from holdspeak.config import Config

    config = Config.load()
    config.owner.name = "Karol"
    config.save()
    return server, base, source

def _setup_face_ready(page: Any, base: str) -> Any:
    page.goto(f"{base}/?token={TOKEN}")
    face = page.get_by_test_id("setup-face")
    face.wait_for(timeout=30_000)
    use_everything = face.get_by_role("button", name="Use everything found", exact=True)
    if use_everything.count():
        use_everything.click()
    expect(face.get_by_role("button", name="Say one sentence", exact=True)).to_be_visible(timeout=60_000)
    return face

@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_a_grant_after_open_my_desk_leaves_no_live_mic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    """Pending permission -> Open my desk -> grant -> zero live tracks."""
    server, base, source = _ready_hub(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_default_timeout(10_000)
            page.add_init_script(_GATED_MIC)
            face = _setup_face_ready(page, base)
            dictate = face.get_by_role("button", name="Say one sentence", exact=True)
            dictate.click()
            page.wait_for_timeout(300)  # the acquisition is pending
            assert page.evaluate(_LIVE_TRACKS) == 0
            face.get_by_role("button", name="Open my desk", exact=True).click()
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            page.evaluate("window.__grant()")
            page.wait_for_function("() => window.__streams.length > 0")
            page.wait_for_timeout(500)
            assert page.evaluate(_LIVE_TRACKS) == 0, "a live microphone outlived the card"
            browser.close()
    finally:
        server.stop()
        source.close()


# ── PHILO-17 firstrun F4 and F5: the recovery doors open their windows ON
#    GLASS over first run (a real fake-device microphone; which window is on
#    top at a point). Moved from test_philo17_firstrun_glass.py (push 2 of
#    the test diet, lane e2e-low-2); its F1-F3 are vitest:
#    surface/__tests__/materialDoors.test.tsx, pages/cores/__tests__/setupCoreInfo.test.tsx,
#    firstrun/__tests__/OneScreen.test.tsx. ──

from .glass_infra import _settle, clear_hub_windows  # noqa: E402


def _row(page: Any, label: str) -> Any:
    """The menu row whose label is `label` (its name also carries a keycap)."""
    return page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(f"^{re.escape(label)}$"))).last


def _desk(page: Any, base: str, query: str = "") -> None:
    if not page.url.startswith(base):
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    clear_hub_windows(page, TOKEN)
    page.goto(f"{base}/?token={TOKEN}{query}", wait_until="load")
    page.locator(".chair:not(.chair-first-value)").wait_for(timeout=30_000)
    _settle(page)


# ── F4 (Astra r1 on #1085): First words' two recovery doors open a window ON
#    GLASS, on a fresh first run and on one opened again from Setup. ──

_TOGGLE_MIC = """(() => {
  const media = navigator.mediaDevices;
  const real = media.getUserMedia.bind(media);
  media.getUserMedia = async (c) => {
    if (window.__denyMic) throw new DOMException("Requested device not found", "NotFoundError");
    return real(c);
  };
})()"""

# The window is painted, and the topmost element at its centre is inside it
# (not under the first-run face).
_ON_TOP = """(el) => {
  const r = el.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return false;
  const x = Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2));
  const y = Math.min(innerHeight - 1, Math.max(0, r.top + Math.min(r.height / 2, 40)));
  const top = document.elementFromPoint(x, y);
  return !!top && el.contains(top);
}"""


def _on_glass(page: Any, selector: str) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=15_000)
    except Exception:  # noqa: BLE001
        return False
    page.wait_for_timeout(400)
    return bool(loc.evaluate(_ON_TOP))




# ── F5 (Astra r2 on #1085): Runs on open BEFORE Get ready waits off glass;
#    pressing "Runs on" (the configure-runs-on alias) brings it back; leaving
#    first run keeps every window, on glass and in the hub's rows. ──
