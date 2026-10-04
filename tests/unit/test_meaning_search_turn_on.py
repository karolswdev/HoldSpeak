"""Meaning search: the one step that turns it on (MEMORY-DESIGN.md §4).

The router, the assignment service, the profile service, the runner, the
kernel (egress operation + receipt) and the conductor are the real ones.  The
download talks to a real HTTP server on this device that serves a small
stand-in file; the pinned hash is that file's hash.  Two physical leaves are
replaced: the installed ``llama-cpp-python`` (this test extra does not carry
it) and the model the adapter loads (vectors from the benchmark fixture).
"""
from __future__ import annotations

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.memory.engine import EmbeddingAdapter, MEMORY_EMBED_CAPABILITY
from holdspeak.memory.local_model import PinnedModel, model_dir
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import meaning_search_service as service_module
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meaning_search_service import MeaningSearchService, PROFILE_ID
from holdspeak.services.model_profile_service import ModelProfileService

from tests.memory_bench.corpus import build_corpus
from tests.unit.test_memory_engine import MODEL, FixtureModel
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

CONTENT = b"GGUF" + bytes(range(256)) * 1200  # 307,204 bytes
SHA = hashlib.sha256(CONTENT).hexdigest()
PINNED = PinnedModel(
    name=MODEL, label="nomic-embed-text v1.5", repository="nomic-ai/nomic-embed-text-v1.5-GGUF",
    revision="r1", filename="nomic-embed-text-v1.5.Q8_0.gguf", sha256=SHA, size=len(CONTENT),
    license="Apache-2.0", architecture="nomic-bert", context_ceiling=2048,
)


class _Source:
    """A file server on this device.  It records every request it gets."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        self.requests: list[str] = []  # the Range header of each request ("" = none)
        self.cut_after: int | None = None  # close the first answer after N bytes
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def do_GET(self) -> None:
                header = self.headers.get("Range", "")
                source.requests.append(header)
                body, start = source.content, 0
                if header.startswith("bytes="):
                    start = int(header[6:].split("-")[0])
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
                else:
                    self.send_response(200)
                rest = body[start:]
                self.send_header("Content-Length", str(len(rest)))
                self.end_headers()
                if source.cut_after is not None and len(source.requests) == 1:
                    rest = rest[: source.cut_after]
                self.wfile.write(rest)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/{PINNED.filename}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def desk(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "meaning.db")
    refs = build_corpus(db)
    broker = _configure(db)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("HOLDSPEAK_MEMORY_EMBED_MODEL", raising=False)
    # Leaf 1: the installed local runtime.
    monkeypatch.setattr(service_module.importlib.metadata, "version", lambda name: "0.3.35")
    monkeypatch.setattr(ModelProfileService, "_local_runtime_readiness", staticmethod(lambda runtime_id: ("ready", "ready")))
    # Leaf 2: the model the adapter loads.
    model = FixtureModel()
    loaded: list[str] = []

    def fake_load(model_path: Path):
        loaded.append(str(model_path))
        return model, threading.Lock()

    monkeypatch.setattr(EmbeddingAdapter, "_local_model", staticmethod(fake_load))
    source = _Source(CONTENT)
    woken: list[int] = []
    service = MeaningSearchService(
        db,
        assignment_service=InferenceAssignmentService(db),
        broker_provider=lambda: broker,
        model=PINNED,
        home_provider=lambda: home,
        source_url=source.url,
        allowed_host=lambda host: host == "127.0.0.1",
        wake=lambda: woken.append(1),
    )
    yield SimpleNamespace(
        db=db, refs=refs, broker=broker, home=home, source=source, service=service,
        loaded=loaded, woken=woken,
    )
    service.wait(10)
    source.close()


def _egress_receipts(db: Database) -> list[dict]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT o.principal_identity,o.state,j.refs_json,r.outcome FROM kernel_journal j "
            "JOIN kernel_operations o ON o.operation_id=j.operation_id "
            "JOIN kernel_receipts r ON r.operation_id=j.operation_id "
            "WHERE j.event_type='operation.admitted' AND o.name='external.egress' "
            "ORDER BY j.hub_sequence"
        ).fetchall()
    return [dict(row) for row in rows]


def _assigned(db: Database) -> bool:
    with db._connection() as conn:
        return conn.execute(
            "SELECT 1 FROM inference_assignment_heads WHERE assignment_key=? AND cleared=0",
            (f"capability:{MEMORY_EMBED_CAPABILITY}",),
        ).fetchone() is not None


def test_nothing_downloads_without_the_press(desk) -> None:
    for _ in range(3):
        status = desk.service.status(OWNER)
        memory_conductor.tick(desk.db, desk.broker)
    assert status["state"] == "off" and status["model"]["on_device"] is False
    # The row says what the press will send out.
    assert status["egress"] == {"destination": "huggingface.co", "what": "model file request"}
    assert desk.source.requests == []
    assert _egress_receipts(desk.db) == []
    assert not _assigned(desk.db)


def test_only_the_owner_can_turn_it_on(desk) -> None:
    with pytest.raises(ServiceError) as refused:
        desk.service.turn_on(Principal(PrincipalKind.AGENT, "an-agent"))
    assert refused.value.code == "meaning_search_owner_required"
    assert desk.source.requests == [] and not _assigned(desk.db)


def test_the_press_downloads_checks_the_hash_and_writes_the_egress_receipt(desk) -> None:
    first = desk.service.turn_on(OWNER)
    assert first["state"] in {"downloading", "indexing", "on"}
    desk.service.wait(30)

    # One request, the complete file, the pinned hash.
    assert desk.source.requests == [""]
    target = model_dir(desk.home) / PINNED.filename
    assert hashlib.sha256(target.read_bytes()).hexdigest() == SHA
    assert not target.with_name(target.name + ".part").exists()
    # The download was one external.egress operation with a receipt, for the
    # owner who pressed, to the model's public source.
    receipts = _egress_receipts(desk.db)
    assert len(receipts) == 1
    assert receipts[0]["outcome"] == "succeeded"
    assert receipts[0]["principal_identity"] == OWNER.identity
    assert "egress:huggingface.co" in receipts[0]["refs_json"]
    assert "data-class:model_file_request" in receipts[0]["refs_json"]

    # The profile carries the embedding claim, and memory.embed is assigned.
    profile = ModelProfileService(desk.db).get_profile(OWNER, PROFILE_ID)
    assert "embedding" in str(profile)
    assert _assigned(desk.db) and desk.woken
    status = desk.service.status(OWNER)
    assert status["state"] == "indexing" and status["indexed"] == 0

    # The conductor embeds through the assigned engine; the row reads ON.
    report = memory_conductor.tick(desk.db, desk.broker)
    assert report["error"] == "" and report["engine"] == f"{MODEL}@256"
    assert set(desk.loaded) == {str(target)}
    status = desk.service.status(OWNER)
    assert status["state"] == "on" and status["indexed"] == status["total"] > 0
    assert status["egress"] is None
    assert desk.db.memory.search("where is the company retreat").fusion is not None


def test_a_file_with_a_different_hash_is_refused(desk) -> None:
    desk.source.content = b"GGUF" + bytes(len(CONTENT) - 4)  # the same size, other bytes
    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    status = desk.service.status(OWNER)
    assert status["state"] == "off"
    assert status["error"] == "The downloaded file is not the correct file. Press Turn on to download it again."
    target = model_dir(desk.home) / PINNED.filename
    assert not target.exists()
    assert target.with_name(target.name + ".invalid").exists()
    assert not _assigned(desk.db)
    with desk.db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_profile_revisions WHERE profile_id LIKE 'meaning-search%'").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM inference_model_artifacts WHERE source_kind='pinned_local_file'").fetchone()[0] == 0
    # The egress happened, so its receipt is there.
    assert len(_egress_receipts(desk.db)) == 1


def test_a_stopped_download_continues_from_the_partial_file(desk) -> None:
    desk.source.cut_after = 100_000
    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    status = desk.service.status(OWNER)
    assert status["state"] == "off"
    assert status["error"] == "The download stopped. Press Turn on to continue."
    part = model_dir(desk.home) / (PINNED.filename + ".part")
    assert part.stat().st_size == 100_000 and not _assigned(desk.db)

    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    # The second request asked only for the rest.
    assert desk.source.requests == ["", "bytes=100000-"]
    target = model_dir(desk.home) / PINNED.filename
    assert hashlib.sha256(target.read_bytes()).hexdigest() == SHA
    assert _assigned(desk.db) and desk.service.status(OWNER)["error"] == ""
    assert [row["outcome"] for row in _egress_receipts(desk.db)] == ["indeterminate", "succeeded"]


def test_a_file_on_this_device_is_adopted_with_no_download(desk) -> None:
    cached = desk.home / ".cache" / "holdspeak-models" / "embed" / PINNED.filename
    cached.parent.mkdir(parents=True)
    cached.write_bytes(CONTENT)
    before = desk.service.status(OWNER)
    assert before["model"]["on_device"] is True and before["egress"] is None

    status = desk.service.turn_on(OWNER)

    assert status["state"] == "indexing"
    assert desk.source.requests == [] and _egress_receipts(desk.db) == []
    memory_conductor.tick(desk.db, desk.broker)
    assert set(desk.loaded) == {str(cached)}  # used in place, not copied
    assert desk.service.status(OWNER)["state"] == "on"


def test_a_file_on_this_device_with_a_different_hash_is_not_adopted(desk) -> None:
    cached = desk.home / ".cache" / "holdspeak-models" / "embed" / PINNED.filename
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"GGUF" + bytes(len(CONTENT) - 4))

    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    # It was not used: the hub downloaded the pinned file to its own place.
    assert desk.source.requests == [""]
    memory_conductor.tick(desk.db, desk.broker)
    assert set(desk.loaded) == {str(model_dir(desk.home) / PINNED.filename)}


def test_turn_off_clears_the_assignment_and_keyword_search_continues(desk) -> None:
    (model_dir(desk.home)).mkdir(parents=True)
    (model_dir(desk.home) / PINNED.filename).write_bytes(CONTENT)
    desk.service.turn_on(OWNER)
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.search("where is the company retreat").fusion is not None

    status = desk.service.turn_off(OWNER)

    assert status["state"] == "off" and not _assigned(desk.db)
    paraphrase = desk.db.memory.search("where is the company retreat")
    assert paraphrase.fusion is None and paraphrase.hits == []
    assert desk.db.memory.search("offsite").hits  # the keyword search is whole

    # On again: the same profile and file, no download.
    assert desk.service.turn_on(OWNER)["state"] in {"indexing", "on"}
    assert _assigned(desk.db) and desk.source.requests == []
    with desk.db._connection() as conn:
        assert [row[0] for row in conn.execute(
            "SELECT profile_id||'@'||revision FROM model_profile_revisions WHERE profile_id LIKE 'meaning-search%'"
        )] == [PROFILE_ID + "@1"]


def test_only_an_embedding_profile_can_serve_memory_embed(desk) -> None:
    _profile(desk.db, "chat-model")
    with pytest.raises(ServiceError) as refused:
        _assign(desk.db, MEMORY_EMBED_CAPABILITY, ["chat-model"])
    assert "capability_class_unsupported" in str(refused.value.context) + str(refused.value.detail) + refused.value.code
    assert not _assigned(desk.db)


def test_the_embedding_model_is_not_offered_for_a_chat_capability(desk) -> None:
    (model_dir(desk.home)).mkdir(parents=True)
    (model_dir(desk.home) / PINNED.filename).write_bytes(CONTENT)
    desk.service.turn_on(OWNER)
    with pytest.raises(ServiceError) as refused:
        _assign(desk.db, "ask.answer", [PROFILE_ID])
    assert "embedding_model_only" in str(refused.value.context) + str(refused.value.detail) + refused.value.code


def test_a_write_on_the_bus_wakes_the_conductor(monkeypatch) -> None:
    """Every producer's write ends in one desk_changed send.  That send wakes
    the conductor, so a new item is in the index in seconds."""
    from holdspeak.runtime.composition import RuntimeServices

    woken: list[int] = []
    monkeypatch.setattr(memory_conductor, "wake", lambda: woken.append(1))
    RuntimeServices(db=None, observer=None).emit_desk_changed("note", "n1", "create")
    assert woken == [1]


def test_a_woken_conductor_indexes_a_new_note_in_seconds(desk, monkeypatch) -> None:
    from holdspeak import intel_queue_conductor
    from holdspeak.kernel import runtime as kernel_runtime
    from holdspeak.runtime.composition import RuntimeServices
    import holdspeak.db as db_package

    monkeypatch.setattr(intel_queue_conductor, "owns_database", lambda: True)
    monkeypatch.setattr(db_package, "get_database", lambda *a, **k: desk.db)
    monkeypatch.setattr(kernel_runtime, "_service", lambda: desk.broker)
    monkeypatch.setattr(memory_conductor, "WAKE_GAP_SECONDS", 0.05)
    worker = memory_conductor.start_memory_conductor(poll_seconds=120)
    try:
        import time

        deadline = time.time() + 20
        while not worker.last_report and time.time() < deadline:
            time.sleep(0.05)
        assert worker.last_report, "the first tick did not run"
        desk.db.notes.upsert(note_id="kiln", title="Kiln schedule", body_markdown="The kiln is fired on the first Tuesday.")
        # The producer's announcement (the real seam every write uses).
        RuntimeServices(db=None, observer=None).emit_desk_changed("note", "any", "create")
        deadline = time.time() + 10  # far below the 120 s poll
        while time.time() < deadline and "note:kiln" not in desk.db.memory_index.ledger(["note"]):
            time.sleep(0.05)
        assert "note:kiln" in desk.db.memory_index.ledger(["note"])
        with desk.db._connection() as conn:
            assert conn.execute(
                "SELECT count(*) FROM memory_chunks WHERE text LIKE '%kiln is fired%'"
            ).fetchone()[0] == 1
    finally:
        memory_conductor.stop_memory_conductor(timeout=10)
