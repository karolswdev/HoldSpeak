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
import time
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


def test_a_cached_file_with_a_different_hash_is_disclosed_as_a_download(desk) -> None:
    """Review of #817, finding 1: the right size is not the right file.  The
    row may say "on this device" only for a file whose hash is verified."""
    cached = desk.home / ".cache" / "holdspeak-models" / "embed" / PINNED.filename
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"GGUF" + bytes(len(CONTENT) - 4))  # the pinned size, other bytes

    before = desk.service.status(OWNER)
    assert before["model"]["on_device"] is False
    assert before["egress"] == {"destination": "huggingface.co", "what": "model file request"}
    assert desk.source.requests == [] and _egress_receipts(desk.db) == []

    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    # The press did what the row said: one download, one egress receipt.
    assert desk.source.requests == [""]
    receipts = _egress_receipts(desk.db)
    assert [row["outcome"] for row in receipts] == ["succeeded"]
    assert "egress:huggingface.co" in receipts[0]["refs_json"]
    memory_conductor.tick(desk.db, desk.broker)
    assert set(desk.loaded) == {str(model_dir(desk.home) / PINNED.filename)}
    assert desk.service.status(OWNER)["egress"] is None


def test_the_hash_is_checked_once_for_an_unchanged_file(desk, monkeypatch) -> None:
    from holdspeak.memory import local_model

    cached = desk.home / ".cache" / "holdspeak-models" / "embed" / PINNED.filename
    cached.parent.mkdir(parents=True)
    cached.write_bytes(CONTENT)
    hashed: list[str] = []
    real = local_model.hash_file
    monkeypatch.setattr(local_model, "hash_file", lambda path: hashed.append(str(path)) or real(path))
    for _ in range(5):
        assert desk.service.status(OWNER)["model"]["on_device"] is True
    assert hashed == [str(cached)]
    # A changed file is hashed again, and is no longer "on this device".
    cached.write_bytes(b"GGUF" + bytes(len(CONTENT) - 4))
    assert desk.service.status(OWNER)["model"]["on_device"] is False
    assert len(hashed) == 2


def test_a_part_file_that_is_a_link_is_never_written_through(desk) -> None:
    """Review of #817, finding 2: with `.part` a link to another file, the
    download wrote into that file."""
    victim = desk.home / "victim.txt"
    victim.write_bytes(b"the owner's own file")
    folder = model_dir(desk.home)
    folder.mkdir(parents=True)
    (folder / (PINNED.filename + ".part")).symlink_to(victim)

    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    assert victim.read_bytes() == b"the owner's own file"
    status = desk.service.status(OWNER)
    assert status["state"] == "off" and "link" in status["error"]
    # Refused before any request left this device.
    assert desk.source.requests == [] and _egress_receipts(desk.db) == []
    assert not _assigned(desk.db)


def test_a_model_file_that_is_a_link_is_not_adopted_and_not_replaced(desk) -> None:
    elsewhere = desk.home / "elsewhere.gguf"
    elsewhere.write_bytes(CONTENT)  # the pinned bytes, behind a link
    folder = model_dir(desk.home)
    folder.mkdir(parents=True)
    (folder / PINNED.filename).symlink_to(elsewhere)

    before = desk.service.status(OWNER)
    assert before["model"]["on_device"] is False and before["egress"] is not None
    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    assert not _assigned(desk.db) and desk.loaded == []
    assert (folder / PINNED.filename).is_symlink() and elsewhere.read_bytes() == CONTENT
    assert desk.source.requests == [] and "link" in desk.service.status(OWNER)["error"]


def test_a_model_folder_that_is_a_link_is_refused(desk) -> None:
    outside = desk.home / "outside"
    outside.mkdir()
    (outside / PINNED.filename).write_bytes(CONTENT)
    model_dir(desk.home).parent.mkdir(parents=True)
    model_dir(desk.home).symlink_to(outside, target_is_directory=True)

    assert desk.service.status(OWNER)["model"]["on_device"] is False
    desk.service.turn_on(OWNER)
    desk.service.wait(30)

    assert not _assigned(desk.db) and desk.source.requests == []
    assert sorted(path.name for path in outside.iterdir()) == [PINNED.filename]


def test_the_fetch_opens_the_part_file_without_following_a_link(desk, tmp_path) -> None:
    """The link appears AFTER the check (a race): the open itself refuses it."""
    from holdspeak.memory import local_model

    victim = tmp_path / "victim.bin"
    victim.write_bytes(b"keep")
    destination = model_dir(desk.home) / PINNED.filename
    real_check = local_model.check_destination

    def check_then_link(path: Path) -> None:
        real_check(path)
        path.with_name(path.name + ".part").symlink_to(victim)

    import pytest as _pytest
    from unittest import mock

    with mock.patch.object(local_model, "check_destination", check_then_link):
        with _pytest.raises(OSError):
            local_model.fetch(
                PINNED, destination, url=desk.source.url,
                allowed_host=lambda host: host == "127.0.0.1",
            )
    assert victim.read_bytes() == b"keep"


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


def test_a_write_on_the_bus_tells_the_conductor_what_changed(monkeypatch) -> None:
    """Every producer's write ends in one desk_changed send.  That send gives
    the conductor the kind and the id of each change."""
    from holdspeak.runtime.composition import RuntimeServices

    woken: list[list[tuple[str, str]]] = []
    monkeypatch.setattr(memory_conductor, "wake", lambda changes=None: woken.append(list(changes)))
    RuntimeServices(db=None, observer=None).emit_desk_changed("note", "n1", "create")
    assert woken == [[("note", "n1")]]


def _count_source_reads(monkeypatch) -> list[str]:
    """Every source the sweep (full or by ref) reads and hashes."""
    from holdspeak.memory import retain

    reads: list[str] = []
    real = retain._redacted
    monkeypatch.setattr(retain, "_redacted", lambda source: reads.append(source.ref) or real(source))
    return reads


DESK_NOTES = 1500
EDITS = 12


def _big_desk(db: Database) -> None:
    for index in range(DESK_NOTES):
        db.notes.upsert(
            note_id=f"big-{index}", title=f"Site visit {index}",
            body_markdown=f"Visit {index}: the crew checked pump {index % 17}.",
        )


def _run_worker(desk, monkeypatch):
    from holdspeak import intel_queue_conductor
    from holdspeak.kernel import runtime as kernel_runtime
    import holdspeak.db as db_package

    monkeypatch.setattr(intel_queue_conductor, "owns_database", lambda: True)
    monkeypatch.setattr(db_package, "get_database", lambda *a, **k: desk.db)
    monkeypatch.setattr(kernel_runtime, "_service", lambda: desk.broker)
    monkeypatch.setattr(memory_conductor, "WAKE_GAP_SECONDS", 0.05)
    worker = memory_conductor.start_memory_conductor(poll_seconds=120)
    deadline = time.time() + 60
    while not worker.last_report and time.time() < deadline:
        time.sleep(0.05)
    assert worker.last_report, "the first (full) pass did not run"
    return worker


def test_writes_cost_nothing_while_meaning_search_is_off(desk, monkeypatch) -> None:
    """Review of #817, finding 3: 12 edits on a 5,000-note desk ran three
    full sweeps with meaning search OFF.  Now a wake while memory.embed is
    unassigned reads no source at all."""
    from holdspeak.runtime.composition import RuntimeServices

    _big_desk(desk.db)
    worker = _run_worker(desk, monkeypatch)
    try:
        reads = _count_source_reads(monkeypatch)
        bus = RuntimeServices(db=None, observer=None)
        for index in range(EDITS):
            desk.db.notes.upsert(note_id=f"big-{index}", title="Edited", body_markdown=f"Edit {index}.")
            bus.emit_desk_changed("note", f"big-{index}", "update")
            time.sleep(0.1)
        time.sleep(1.0)
        assert reads == []
        assert memory_conductor.tick(desk.db, desk.broker, refs=["note:big-0"]).get("skipped") == 1
    finally:
        memory_conductor.stop_memory_conductor(timeout=10)


def test_n_edits_cost_n_source_reads_when_meaning_search_is_on(desk, monkeypatch) -> None:
    """Work proportional to the number of changes, not to the desk."""
    from holdspeak.runtime.composition import RuntimeServices

    _big_desk(desk.db)
    _profile(desk.db, "embed-model", model=MODEL, claims=("embedding",))
    _assign(desk.db, MEMORY_EMBED_CAPABILITY, ["embed-model"])
    full = _count_source_reads(monkeypatch)
    from holdspeak.memory.retain import sweep

    sweep(desk.db)
    assert len(full) >= DESK_NOTES  # what one full sweep reads
    worker = _run_worker(desk, monkeypatch)
    try:
        del full[:]
        bus = RuntimeServices(db=None, observer=None)
        for index in range(EDITS):
            desk.db.notes.upsert(
                note_id=f"big-{index}", title="Kiln schedule",
                body_markdown=f"The kiln is fired on Tuesday {index}.",
            )
            bus.emit_desk_changed("note", f"big-{index}", "update")
            time.sleep(0.1)
        wanted = {f"note:big-{index}" for index in range(EDITS)}
        deadline = time.time() + 20  # far below the 120 s poll
        while time.time() < deadline:
            with desk.db._connection() as conn:
                found = conn.execute(
                    "SELECT count(DISTINCT source_ref) FROM memory_chunks WHERE text LIKE '%kiln is fired%'"
                ).fetchone()[0]
            if found == EDITS:
                break
            time.sleep(0.05)
        assert found == EDITS
        # Each changed source was read; no other source was.  Twelve edits
        # close together are at most a few passes, each over its own refs.
        assert set(full) == wanted
        assert len(full) <= 2 * EDITS, len(full)
    finally:
        memory_conductor.stop_memory_conductor(timeout=10)


def test_a_change_names_only_the_kinds_memory_holds() -> None:
    from holdspeak.memory.retain import refs_for_change

    assert refs_for_change("note", "n1") == ["note:n1"]
    assert refs_for_change("decision", "d1") == ["decision:d1", "decision_record:d1", "desk_decision:d1"]
    assert refs_for_change("directory", "z1") == []  # the slow full sweep sees it
    assert refs_for_change("note", "") == []


def test_a_deleted_source_named_by_a_wake_leaves_the_index(desk) -> None:
    _profile(desk.db, "embed-model", model=MODEL, claims=("embedding",))
    _assign(desk.db, MEMORY_EMBED_CAPABILITY, ["embed-model"])
    desk.db.notes.upsert(note_id="gone-soon", title="Kiln", body_markdown="The kiln is fired on Tuesday.")
    memory_conductor.tick(desk.db, desk.broker, refs=["note:gone-soon"])
    assert desk.db.memory_index.ledger_for(["note:gone-soon"])["note:gone-soon"]["state"] == "live"
    with desk.db._connection() as conn:
        conn.execute("UPDATE notes SET deleted=1 WHERE id='gone-soon'")
    report = memory_conductor.tick(desk.db, desk.broker, refs=["note:gone-soon"])
    assert report["swept"]["gone"] == 1
    assert desk.db.memory_index.ledger_for(["note:gone-soon"])["note:gone-soon"]["state"] == "gone"
