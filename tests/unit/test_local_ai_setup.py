"""Strong defaults, batteries included (owner ruling 2026-10-05).

Fences for "Set up local AI" and the honest defaults:

* the runtime is checked before any request leaves (Set up local AI and the
  Meaning search press),
* ONE egress receipt names every downloaded file,
* a hash mismatch fails and keeps nothing,
* a second call downloads nothing; a stopped download continues,
* the boot does not download Whisper; a Whisper model on disk still warms,
* ``holdspeak doctor`` finds the running hub's real port,
* meetings are summarised by default; defaults name files the product provides.

The kernel, the database, the assignment and profile services are the real
ones.  The network is a real HTTP server on this device.  Two physical
leaves are replaced: the installed llama-cpp-python revision and the
runtime-readiness probe (the test extra does not carry a model to load).
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.memory.local_model import PinnedModel, model_dir
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import local_ai_setup_service as local_ai_module
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.local_ai_setup_service import (
    STARTER_PRESET_ID,
    STARTER_PROFILE_ID,
    LocalAISetupService,
    file_ref,
    starter_model_path,
)
from holdspeak.services.meaning_search_service import MeaningSearchService
from holdspeak.services.model_profile_service import ModelProfileService

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


def _blob(tag: bytes, size: int, magic: bytes = b"") -> bytes:
    body = magic + (tag * (size // len(tag) + 1))
    return body[:size]


def _pin(repository: str, filename: str, content: bytes, *, magic: bytes) -> PinnedModel:
    return PinnedModel(
        name=filename, label=filename, repository=repository, revision="r1", filename=filename,
        sha256=hashlib.sha256(content).hexdigest(), size=len(content), license="MIT",
        architecture="test", context_ceiling=2048, magic=magic,
    )


WHISPER_CONFIG = b'{"model_type": "whisper"}'
WHISPER_WEIGHTS = _blob(b"whisper-weights-", 40_000)
EMBED = _blob(b"embed-", 30_000, b"GGUF")
STARTER = _blob(b"starter-", 50_000, b"GGUF")

def _mlx_here(backend: str) -> str:
    return "mlx" if backend in ("auto", "mlx") else backend


WHISPER_FILES = (
    _pin("mlx-community/whisper-base-mlx", "config.json", WHISPER_CONFIG, magic=b""),
    _pin("mlx-community/whisper-base-mlx", "weights.npz", WHISPER_WEIGHTS, magic=b""),
)
EMBED_PIN = _pin("nomic-ai/nomic-embed-text-v1.5-GGUF", "nomic-embed-text-v1.5.Q8_0.gguf", EMBED, magic=b"GGUF")
STARTER_SHA = "sha256:" + hashlib.sha256(STARTER).hexdigest()


def _catalog() -> dict:
    manifest = {"files": [{"path": "Qwen3.5-4B-Q4_K_M.gguf", "sha256": STARTER_SHA, "size": len(STARTER)}]}
    manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "catalog_revision": 9,
        "entries": [{
            "id": STARTER_PRESET_ID,
            "label": "Quick local Qwen",
            "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
            "source": {
                "repository": "unsloth/Qwen3.5-4B-GGUF",
                "revision": "r1",
                "filename": "Qwen3.5-4B-Q4_K_M.gguf",
                "file_sha256": STARTER_SHA,
                "manifest_sha256": manifest_sha,
                "download_bytes": len(STARTER),
                "installed_bytes": len(STARTER),
                "peak_free_bytes": len(STARTER) * 2,
                "license": "Apache-2.0",
            },
        }],
    }


class _Source:
    """A file server on this device.  It records every request it gets."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = dict(files)
        self.requests: list[tuple[str, str]] = []  # (path, Range header)
        self.cut: tuple[str, int] | None = None  # (path, N): cut that answer after N bytes once
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def do_GET(self) -> None:
                header = self.headers.get("Range", "")
                source.requests.append((self.path, header))
                body = source.files.get(self.path)
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                start = 0
                if header.startswith("bytes="):
                    start = int(header[6:].split("-")[0])
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
                else:
                    self.send_response(200)
                rest = body[start:]
                if source.cut is not None and source.cut[0] == self.path:
                    rest, source.cut = rest[: source.cut[1]], None
                self.send_header("Content-Length", str(len(rest)))
                self.end_headers()
                self.wfile.write(rest)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def url_for(self, model: PinnedModel) -> str:
        return f"{self.base}/{model.repository}/{model.filename}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def desk(tmp_path: Path, monkeypatch):
    for name in ("HF_HUB_CACHE", "HF_HOME", "HOLDSPEAK_MEMORY_EMBED_MODEL"):
        monkeypatch.delenv(name, raising=False)
    db = Database(tmp_path / "local-ai.db")
    broker = _configure(db)
    home = tmp_path / "home"
    home.mkdir()
    # Leaf 1: the installed runtime (meaning search reads the package version).
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.3.35")
    # Leaf 2: the runtime-readiness probe.
    monkeypatch.setattr(
        ModelProfileService, "_local_runtime_readiness", staticmethod(lambda runtime_id: ("ready", "ready"))
    )
    monkeypatch.setattr("holdspeak.whisper_models._PINNED", {("mlx", "base"): WHISPER_FILES})
    # PHILO-17 speech: readiness asks if the speech library can run here; the
    # rig's library is MLX on every host (the Linux CI has none).
    monkeypatch.setattr("holdspeak.transcribe._resolve_backend", _mlx_here)
    files = {f"/{m.repository}/{m.filename}": c for m, c in zip(WHISPER_FILES, (WHISPER_CONFIG, WHISPER_WEIGHTS))}
    files[f"/{EMBED_PIN.repository}/{EMBED_PIN.filename}"] = EMBED
    files["/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf"] = STARTER
    source = _Source(files)
    allowed = lambda host: host == "127.0.0.1"  # noqa: E731
    meaning = MeaningSearchService(
        db, assignment_service=InferenceAssignmentService(db), broker_provider=lambda: broker,
        model=EMBED_PIN, home_provider=lambda: home, source_url=source.url_for(EMBED_PIN),
        allowed_host=allowed, wake=lambda: None,
    )
    whisper = {"name": "base"}

    def build() -> LocalAISetupService:
        # The runtime check is the real shared one: package metadata (Leaf 1)
        # and a real ``import llama_cpp`` (installed in the base install).
        return LocalAISetupService(
            db, meaning_search=meaning, broker_provider=lambda: broker, home_provider=lambda: home,
            config_provider=lambda: SimpleNamespace(model=SimpleNamespace(name=whisper["name"], backend="mlx")),
            catalog_provider=_catalog, url_for=source.url_for, allowed_host=allowed,
        )

    service = build()
    yield SimpleNamespace(db=db, broker=broker, home=home, source=source, meaning=meaning,
                          service=service, whisper=whisper, build=build)
    service.wait(10)
    meaning.wait(10)
    source.close()


def _egress(db: Database) -> list[dict]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT o.operation_id,j.refs_json,r.outcome FROM kernel_journal j "
            "JOIN kernel_operations o ON o.operation_id=j.operation_id "
            "JOIN kernel_receipts r ON r.operation_id=j.operation_id "
            "WHERE j.event_type='operation.admitted' AND o.name='external.egress' "
            "ORDER BY j.hub_sequence"
        ).fetchall()
    return [{**dict(row), "refs": json.loads(row["refs_json"])} for row in rows]


def _assigned(db: Database, key: str) -> bool:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT cleared FROM inference_assignment_heads WHERE assignment_key=?", (key,)
        ).fetchone()
    return row is not None and not row["cleared"]


def _starter_path(desk) -> Path:
    return starter_model_path(desk.home, _catalog()["entries"][0])


# ── B: Set up local AI ────────────────────────────────────────────────


def _no_llama_import(monkeypatch) -> None:
    def broken() -> None:
        raise ImportError("libllama.dylib could not be loaded")

    monkeypatch.setattr("holdspeak.services.inference_setup_service._import_llama_cpp", broken)


def test_runtime_is_checked_before_any_download(desk, monkeypatch) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    with pytest.raises(ServiceError) as caught:
        desk.service.start(OWNER)
    assert caught.value.code == "local_ai_runtime_unavailable"
    assert desk.source.requests == []
    assert _egress(desk.db) == []
    assert not _starter_path(desk).parent.exists()
    assert desk.service.status(OWNER)["state"] == "needs_runtime"


def test_runtime_too_old_downloads_nothing(desk, monkeypatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.3.16")
    with pytest.raises(ServiceError):
        desk.service.start(OWNER)
    assert desk.source.requests == []


def test_metadata_without_an_importable_runtime_downloads_nothing(desk, monkeypatch) -> None:
    _no_llama_import(monkeypatch)
    with pytest.raises(ServiceError) as caught:
        desk.service.start(OWNER)
    assert caught.value.code == "local_ai_runtime_unavailable"
    assert desk.source.requests == []
    assert _egress(desk.db) == []


@pytest.mark.parametrize("breakage", ["too_old", "not_importable"])
def test_meaning_search_uses_the_same_runtime_rule(desk, monkeypatch, breakage) -> None:
    if breakage == "too_old":
        monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.3.16")
    else:
        _no_llama_import(monkeypatch)
    status = desk.meaning.turn_on(OWNER)
    desk.meaning.wait(10)
    assert status["error_code"] == "runtime"
    assert desk.source.requests == []
    assert _egress(desk.db) == []


def test_meaning_search_press_checks_the_runtime_before_the_download(desk, monkeypatch) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    status = desk.meaning.turn_on(OWNER)
    desk.meaning.wait(10)
    assert status["error_code"] == "runtime"
    assert desk.source.requests == []
    assert _egress(desk.db) == []
    assert not (model_dir(desk.home) / EMBED_PIN.filename).exists()


def test_one_call_downloads_every_file_with_one_receipt(desk) -> None:
    before = desk.service.status(OWNER)
    assert before["state"] == "not_started"
    assert before["egress"] == {
        "destination": "huggingface.co", "what": "model file request", "files": 4,
        "bytes": len(WHISPER_CONFIG) + len(WHISPER_WEIGHTS) + len(EMBED) + len(STARTER),
    }
    desk.service.start(OWNER)
    desk.service.wait(30)

    receipts = _egress(desk.db)
    assert len(receipts) == 1, receipts
    assert receipts[0]["outcome"] == "succeeded"
    for model in (*WHISPER_FILES, EMBED_PIN, local_ai_module.starter_model(_catalog()["entries"][0])):
        assert file_ref(model) in receipts[0]["refs"]
    assert len(desk.source.requests) == 4

    status = desk.service.status(OWNER)
    assert status["state"] == "ready", status
    assert all(row["on_device"] for row in status["files"])
    assert status["egress"] is None
    engine = status["local_engine"]
    assert engine["ready"] is True and engine["profile_id"] == STARTER_PROFILE_ID
    assert status["meaning_search"] in {"on", "indexing"}
    assert _starter_path(desk).read_bytes() == STARTER
    # Meaning search is on; "Default for AI work" is NOT assigned here.
    assert _assigned(desk.db, "capability:memory.embed")
    assert not _assigned(desk.db, "global")


def test_hash_mismatch_fails_and_keeps_nothing(desk) -> None:
    desk.source.files["/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf"] = _blob(b"wrong-", len(STARTER), b"GGUF")
    desk.service.start(OWNER)
    desk.service.wait(30)

    status = desk.service.status(OWNER)
    assert status["state"] == "failed"
    assert status["error_code"] == "integrity"
    folder = _starter_path(desk).parent
    assert sorted(path.name for path in folder.iterdir()) == []
    assert status["local_engine"]["ready"] is False
    with desk.db._connection() as conn:
        starter_artifact = local_ai_module.starter_artifact_id(_catalog()["entries"][0])
        assert conn.execute(
            "SELECT count(*) FROM inference_model_artifacts WHERE artifact_id=?", (starter_artifact,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT count(*) FROM model_profile_revisions WHERE profile_id=?", (STARTER_PROFILE_ID,)
        ).fetchone()[0] == 0
    assert not _assigned(desk.db, "capability:memory.embed")


def test_second_call_downloads_nothing(desk) -> None:
    desk.service.start(OWNER)
    desk.service.wait(30)
    assert desk.service.status(OWNER)["state"] == "ready"
    desk.source.requests.clear()

    again = desk.build()  # a new process: no memory of the first call
    status = again.start(OWNER)
    again.wait(10)
    assert desk.source.requests == []
    assert len(_egress(desk.db)) == 1
    assert status["state"] == "ready"


def _assign(db: Database, scope: dict, profile_id: str, revision: int) -> dict:
    return InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"assign-{scope.get('capability_id', scope['kind'])}",
        "expected_revision": 0,
        "scope": scope,
        "entries": [{"profile_id": profile_id, "profile_revision": revision}],
    })


def test_the_starter_passes_the_editor_for_meeting_analysis_and_the_default(desk) -> None:
    desk.service.start(OWNER)
    desk.service.wait(30)
    engine = desk.service.status(OWNER)["local_engine"]
    assert engine["ready"] is True
    # The real assignment editor (compatibility: modality, structured output
    # result schema, context, boundary).
    _assign(desk.db, {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
            engine["profile_id"], engine["profile_revision"])
    _assign(desk.db, {"kind": "capability", "capability_id": "meeting.live_analysis"},
            engine["profile_id"], engine["profile_revision"])
    _assign(desk.db, {"kind": "global"}, engine["profile_id"], engine["profile_revision"])
    resolved = InferenceAssignmentService(desk.db).resolve_effective(OWNER, capability_id="meeting.deferred_analysis")
    assert resolved["status"] == "assigned", resolved


def test_the_local_engine_enforces_the_meeting_schema() -> None:
    from holdspeak.intel.engine import MeetingIntel
    from holdspeak.intel.parsing import INTEL_JSON_SCHEMA, intel_response_format

    seen: list[dict] = []

    class Llm:
        def create_chat_completion(self, **kwargs):
            seen.append(kwargs)
            return {"choices": [{"message": {"content": "{}"}}]}

    intel = MeetingIntel(provider="local", model_path="/nowhere.gguf")
    intel._ensure_model_loaded = lambda: None
    intel._active_provider = "local"
    intel._llm = Llm()
    intel._chat_completion_text([{"role": "user", "content": "x"}], temperature=0.0, max_tokens=8,
                                response_format=intel_response_format())
    # llama-cpp-python builds its grammar only from this shape.
    assert seen[0]["response_format"] == {"type": "json_object", "schema": INTEL_JSON_SCHEMA}


def test_a_corrupt_whisper_cache_is_not_ready_and_is_downloaded_again(desk) -> None:
    from holdspeak.whisper_models import local_whisper_dir

    root = desk.home / ".cache/huggingface/hub/models--mlx-community--whisper-base-mlx"
    snapshot = root / "snapshots/r0"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}")
    (snapshot / "weights.npz").write_bytes(b"truncated")
    status = desk.service.status(OWNER)
    assert [row["on_device"] for row in status["files"] if row["key"] == "whisper"] == [False, False]
    assert local_whisper_dir("mlx-community/whisper-base-mlx", home=desk.home) is None

    desk.service.start(OWNER)
    desk.service.wait(30)
    after = desk.service.status(OWNER)
    assert after["state"] == "ready", after
    receipt = _egress(desk.db)[0]
    for model in WHISPER_FILES:
        assert file_ref(model) in receipt["refs"]
    assert local_whisper_dir("mlx-community/whisper-base-mlx", home=desk.home) != snapshot


def test_an_unpinned_whisper_choice_is_never_ready(desk) -> None:
    desk.whisper["name"] = "small"  # mlx, no pinned files, not on this device
    desk.service.start(OWNER)
    desk.service.wait(30)
    status = desk.service.status(OWNER)
    assert status["speech"] == {
        "model": "small", "backend": "mlx", "state": "not_covered", "ready": False, "bytes": 0,
    }
    assert status["state"] == "incomplete"
    assert status["error_code"] == "speech_not_covered"


def test_a_stopped_download_continues_its_part_file(desk) -> None:
    desk.source.cut = ("/mlx-community/whisper-base-mlx/weights.npz", 10_000)  # stops early
    desk.service.start(OWNER)
    desk.service.wait(30)
    assert desk.service.status(OWNER)["error_code"] == "network"

    desk.service.start(OWNER)
    desk.service.wait(30)
    assert desk.service.status(OWNER)["state"] == "ready"
    ranges = [header for _path, header in desk.source.requests if header]
    assert ranges == ["bytes=10000-"]


# ── C: the boot does not download Whisper ─────────────────────────────


class _Host:
    def __init__(self, name: str = "base", backend: str = "mlx") -> None:
        self.config = SimpleNamespace(model=SimpleNamespace(name=name, backend=backend, warm_on_start=True))
        self.state_lock = threading.Lock()
        self.transcription_lock = threading.Lock()
        self._transcriber_init_lock = threading.Lock()
        self.runtime_status: dict = {}
        self.transcriber = None

    def _set_runtime_activity(self, *args, **kwargs) -> None:
        pass


def _warm(host) -> None:
    from holdspeak.runtime.transcriber_state import TranscriberStateMixin

    for name in ("_whisper_model_on_disk", "_warm_transcriber_in_background", "_set_transcription_status",
                 "_transcription_warm_on_start_enabled", "_ensure_transcriber_loaded",
                 "_loaded_transcriber_reusable"):
        setattr(host, name, getattr(TranscriberStateMixin, name).__get__(host))
    host._warm_transcriber_in_background()
    until = time.monotonic() + 5
    while host.runtime_status.get("transcription_status") == "warming" and time.monotonic() < until:
        time.sleep(0.01)


@pytest.fixture()
def boot(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in ("HF_HUB_CACHE", "HF_HOME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("holdspeak.whisper_models._PINNED", {("mlx", "base"): WHISPER_FILES})
    # PHILO-17 speech: readiness asks if the speech library can run here; the
    # rig's library is MLX on every host (the Linux CI has none).
    monkeypatch.setattr("holdspeak.transcribe._resolve_backend", _mlx_here)
    connects: list = []
    real_connect = socket.socket.connect

    def record(self, address):  # the fetch layer: every outbound socket
        connects.append(address)
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", record)
    admissions: list[int] = []

    def admission():
        admissions.append(1)
        raise RuntimeError("test stops the warm at admission")

    monkeypatch.setattr("holdspeak.speech_session.preload_service_admission", admission)
    return SimpleNamespace(home=home, connects=connects, admissions=admissions)


def test_boot_without_whisper_on_disk_makes_no_network_call(boot) -> None:
    host = _Host()
    _warm(host)
    assert host.runtime_status["transcription_status"] == "not_loaded"
    assert boot.admissions == []  # the model-loading path was never entered
    assert boot.connects == []


def _hub_cache_copy(home: Path) -> Path:
    root = home / ".cache" / "huggingface" / "hub" / "models--mlx-community--whisper-base-mlx"
    snapshot = root / "snapshots" / "abc123"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_bytes(WHISPER_CONFIG)
    (snapshot / "weights.npz").write_bytes(WHISPER_WEIGHTS)
    (root / "refs").mkdir()
    (root / "refs" / "main").write_text("abc123")
    return snapshot


def test_boot_with_whisper_on_disk_warms_it(boot) -> None:
    snapshot = _hub_cache_copy(boot.home)
    host = _Host()
    _warm(host)
    assert boot.admissions == [1]  # the warm went on to load the model
    assert boot.connects == []
    # The physical load reads the folder on this device, not the hub.
    from holdspeak.transcribe import _local_source

    assert _local_source("mlx-community/whisper-base-mlx") == str(snapshot)


def _mlx_whisper_available() -> bool:
    import importlib.util
    import platform
    import sys

    return (sys.platform == "darwin" and platform.machine() == "arm64"
            and importlib.util.find_spec("mlx_whisper") is not None)


@pytest.mark.skipif(not _mlx_whisper_available(), reason="mlx-whisper runs on macOS arm64 only")
def test_the_physical_mlx_load_never_reaches_the_hub(boot, monkeypatch) -> None:
    """Astra's repro: the model is cached only under the SECOND candidate.

    The real mlx-whisper loader runs.  The hub fetch (``snapshot_download``)
    and every socket are intercepted; the loader gets only the local folder.
    """
    import importlib as _importlib

    load_models = _importlib.import_module("mlx_whisper.load_models")
    mlx_transcribe = _importlib.import_module("mlx_whisper.transcribe")  # the module, not the function

    from holdspeak.transcribe import TranscriberError, _MlxTranscriber

    root = boot.home / ".cache/huggingface/hub/models--mlx-community--whisper-base"
    snapshot = root / "snapshots/c1"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text('{"model_type": "whisper"}')
    (snapshot / "weights.npz").write_bytes(b"not loadable weights")
    fetched: list = []

    def no_hub(*args, **kwargs):
        fetched.append((args, kwargs))
        raise RuntimeError("the test forbids the network")

    monkeypatch.setattr(load_models, "snapshot_download", no_hub)
    real_load = mlx_transcribe.load_model
    loaded: list[str] = []

    def spy(path, **kwargs):
        loaded.append(str(path))
        return real_load(path, **kwargs)

    monkeypatch.setattr(mlx_transcribe, "load_model", spy)
    monkeypatch.setattr(mlx_transcribe.ModelHolder, "model", None)
    monkeypatch.setattr(mlx_transcribe.ModelHolder, "model_path", None)

    transcriber = _MlxTranscriber(model_name="base")
    with pytest.raises(TranscriberError):  # the stand-in weights do not load
        transcriber._load_candidate_sequence(
            candidates=("mlx-community/whisper-base-mlx", "mlx-community/whisper-base"),
            strategies=("model-holder",),
        )
    assert fetched == []
    assert boot.connects == []
    assert loaded == [str(snapshot)]  # only the local folder reached the loader


def test_faster_whisper_loads_only_a_local_folder(boot, monkeypatch) -> None:
    import sys
    from types import ModuleType

    from holdspeak.transcribe import TranscriberError, _FasterWhisperTranscriber

    constructed: list[str] = []
    module = ModuleType("faster_whisper")

    class WhisperModel:
        def __init__(self, model, *, device, compute_type) -> None:
            constructed.append(str(model))

    module.WhisperModel = WhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", module)
    with pytest.raises(TranscriberError):
        _FasterWhisperTranscriber(model_name="base")
    assert constructed == []  # nothing that could fetch was built

    snapshot = boot.home / ".cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots/c1"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}")
    (snapshot / "model.bin").write_bytes(b"model")
    (snapshot / "vocabulary.txt").write_text("a")
    with pytest.raises(TranscriberError):  # no tokenizer.json: the loader would fetch one
        _FasterWhisperTranscriber(model_name="base")
    assert constructed == []
    (snapshot / "tokenizer.json").write_text("{}")
    _FasterWhisperTranscriber(model_name="base")
    assert constructed == [str(snapshot)]
    assert boot.connects == []


def test_the_pinned_whisper_folder_is_found_first(boot, monkeypatch) -> None:
    from holdspeak.whisper_models import local_whisper_dir, pinned_whisper_dir

    _hub_cache_copy(boot.home)
    folder = pinned_whisper_dir("mlx-community/whisper-base-mlx", boot.home)
    folder.mkdir(parents=True)
    (folder / "config.json").write_bytes(WHISPER_CONFIG)
    (folder / "weights.npz").write_bytes(WHISPER_WEIGHTS)
    assert local_whisper_dir("mlx-community/whisper-base-mlx") == folder
    (folder / "weights.npz").write_bytes(b"x" * len(WHISPER_WEIGHTS))  # not the pinned bytes
    assert local_whisper_dir("mlx-community/whisper-base-mlx") != folder


# ── D: doctor and the defaults ────────────────────────────────────────


def test_doctor_finds_the_running_hub(tmp_path: Path, monkeypatch) -> None:
    from holdspeak import doctor
    from holdspeak.runtime_lock import owner_lock_path

    class Health(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

        def do_GET(self) -> None:
            body = b'{"status": "ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        db_path = tmp_path / "holdspeak.db"
        port = server.server_address[1]
        owner_lock_path(db_path).write_text(json.dumps({"pid": os.getpid(), "host": "127.0.0.1", "port": port}))
        monkeypatch.setattr("holdspeak.mcp.server._default_db_path", lambda: db_path)
        monkeypatch.delenv("HOLDSPEAK_URL", raising=False)
        assert doctor.resolve_hub_url() == f"http://127.0.0.1:{port}"
        result = doctor._check_hub_health(doctor.resolve_hub_url(), "")
        assert result.status == "PASS", result
        assert doctor.resolve_hub_url("http://127.0.0.1:1") == "http://127.0.0.1:1"
    finally:
        server.shutdown()
        server.server_close()


def test_meetings_are_summarised_by_default(tmp_path: Path) -> None:
    import unittest.mock as mock

    from holdspeak.config import Config
    from holdspeak.runtime.routing_glue import RoutingGlueMixin
    from tests.unit.test_hs172_loop_wire import _seed_meeting, assign_meeting_engine

    db = Database(tmp_path / "auto-intel.db")
    _seed_meeting(db, "mtg-default-every")  # no Room link: a fresh desk
    assign_meeting_engine(db)
    assert Config().meeting.intelligence_auto == "every"
    with mock.patch("holdspeak.config.Config.load", return_value=Config()):
        with mock.patch("holdspeak.db.get_database", return_value=db):
            result = RoutingGlueMixin._maybe_auto_enqueue_intel(mock.MagicMock(), "mtg-default-every", None)
    assert result["enqueued"] is True, result


def test_no_engine_means_no_job_never_a_permanent_failure(tmp_path: Path) -> None:
    import unittest.mock as mock

    from holdspeak.config import Config
    from holdspeak.runtime.routing_glue import RoutingGlueMixin
    from tests.unit.test_hs172_loop_wire import _seed_meeting, assign_meeting_engine

    db = Database(tmp_path / "no-engine.db")
    _seed_meeting(db, "mtg-no-engine")

    def run() -> dict:
        with mock.patch("holdspeak.config.Config.load", return_value=Config()):
            with mock.patch("holdspeak.db.get_database", return_value=db):
                return RoutingGlueMixin._maybe_auto_enqueue_intel(mock.MagicMock(), "mtg-no-engine", None)

    first = run()
    assert first == {"enqueued": False, "reason": "no_engine"}
    assert db.intel.get_intel_job("mtg-no-engine") is None
    # When an engine appears, the same meeting is still free to run.
    assign_meeting_engine(db)
    assert run()["enqueued"] is True


def test_defaults_name_files_the_product_provides() -> None:
    from holdspeak.config import Config
    from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH
    from holdspeak.services.local_ai_setup_service import starter_preset

    provided = str(starter_model_path(Path("~"), starter_preset()))
    config = Config()
    assert DEFAULT_INTEL_MODEL_PATH == provided
    assert config.meeting.intel_realtime_model == provided
    assert config.dictation.runtime.llama_cpp_model_path == provided


def test_missing_default_model_reads_not_set_up(monkeypatch) -> None:
    from holdspeak import inference_targets
    from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH

    monkeypatch.setattr(inference_targets, "local_model_file_present", lambda path: False)
    target = inference_targets.this_machine_target_from_model_path(DEFAULT_INTEL_MODEL_PATH)
    assert target.readiness_reason == inference_targets.NOT_SET_UP_REASON
    own = inference_targets.this_machine_target_from_model_path("~/Models/mine.gguf")
    assert own.readiness_reason == "model file not found: ~/Models/mine.gguf"


def test_never_loaded_whisper_profile_is_not_broken(monkeypatch) -> None:
    from holdspeak.services.model_library_service import ModelLibraryApplicationService as Library

    item = {
        "profile_id": "speech-migrated-x", "label": "Whisper mlx base", "provider_family": "local",
        "runtime_family": "mlx", "revision": 1, "current_binding": {"binding_id": "b"},
        "latest_readiness": {"state": "unavailable", "reason_code": "artifact_unobserved"},
    }
    library = Library.__new__(Library)
    monkeypatch.setattr(Library, "_local_speech_on_disk", staticmethod(lambda item: False))
    row = library._profile_row(item)
    assert (row["status"], row["selected_action"]) == ("needs_setup", "Add model")
    assert row["repair"] == {"code": "not_set_up", "label": "NOT SET UP"}
    monkeypatch.setattr(Library, "_local_speech_on_disk", staticmethod(lambda item: True))
    row = library._profile_row(item)
    assert (row["status"], row["selected_action"], row["repair"]) == ("configured", "Checking", None)


# ── faster-whisper: no tokenizer on disk, no load (Astra iteration 2) ──

_DENYING_PROXY_RUN = r'''
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

seen = []

class Deny(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_CONNECT(self):
        seen.append(self.path)
        self.send_error(403, "the test denies the network")

    do_GET = do_CONNECT

proxy = ThreadingHTTPServer(("127.0.0.1", 0), Deny)
threading.Thread(target=proxy.serve_forever, daemon=True).start()
# The Rust tokenizer downloader ignores Python sockets but obeys the proxy.
for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy"):
    os.environ[key] = f"http://127.0.0.1:{proxy.server_port}"
for key in ("NO_PROXY", "no_proxy", "HF_HOME", "HF_HUB_CACHE", "HF_HUB_OFFLINE"):
    os.environ.pop(key, None)
os.environ["HF_HUB_ETAG_TIMEOUT"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "1"
from holdspeak.transcribe import _FasterWhisperTranscriber
outcome = "loaded"
try:
    _FasterWhisperTranscriber(model_name=sys.argv[1])
except Exception as exc:
    outcome = type(exc).__name__ + ": " + str(exc)
proxy.shutdown()
print(json.dumps({"connects": seen, "outcome": outcome}))
'''


def _real_faster_whisper_files() -> dict[str, Path] | None:
    """A real faster-whisper model on the owner's account (read only).

    The real ctranslate2 constructor needs a real ``model.bin``; the test
    never downloads one, so it skips where none exists (for example CI).
    """
    import importlib.util
    import pwd

    if importlib.util.find_spec("faster_whisper") is None:
        return None
    hub = Path(pwd.getpwuid(os.getuid()).pw_dir) / ".cache/huggingface/hub"
    for snapshot in sorted(hub.glob("models--Systran--faster-whisper-*/snapshots/*")):
        files = {name: snapshot / name for name in ("config.json", "model.bin", "vocabulary.txt")}
        if all(path.exists() for path in files.values()):
            return {name: path.resolve() for name, path in files.items()}
    return None


@pytest.mark.parametrize("selected", ["cached", "explicit_folder"])
def test_a_faster_whisper_folder_without_its_tokenizer_never_reaches_the_hub(tmp_path: Path, selected) -> None:
    import subprocess
    import sys

    real = _real_faster_whisper_files()
    if real is None:
        pytest.skip("no real faster-whisper model on this account")
    home = tmp_path / "home"
    folder = home / ".cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/c1"
    folder.mkdir(parents=True)
    for name, source in real.items():  # every file but tokenizer.json
        (folder / name).symlink_to(source)
    name = "small" if selected == "cached" else str(folder)
    env = {key: value for key, value in os.environ.items()}
    env["HOME"] = str(home)
    out = subprocess.run(
        [sys.executable, "-c", _DENYING_PROXY_RUN, name],
        capture_output=True, text=True, env=env, timeout=120,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["connects"] == [], result
    assert "not on this device" in result["outcome"], result
