"""Owner ruling 2026-10-05: strong defaults, batteries included.

* A LOCAL engine found on this machine becomes "Default for AI work" by
  itself, once, with a receipt and the LOCAL lamp.
* An assignment the owner made is never changed.
* A LAN or cloud engine is a proposal only.
* Detection never opens a socket to a non-loopback address.
* memory.extract / consolidate / page inherit a LOCAL default, never a
  network or cloud one.
* One read says, per capability, assigned / inherited_from_default /
  proposed / needs_setup.

The engines are real HTTP servers on 127.0.0.1; the assignment, profile and
Model Library services are the real ones over a real database.
"""
from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.inference_capabilities import builtin_capability_definitions
from holdspeak.kernel.runtime import _configure
from holdspeak.memory.engine import LOCAL_INHERITING_CAPABILITIES, _assignment_head
from holdspeak.memory.extract import resolve_extractor
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_default_service import (
    ASSIGNED_OPERATION,
    InferenceDefaultService,
    LOOPBACK_ENGINE_PORTS,
    LoopbackOnlyError,
    parameter_billions,
    rank_key,
    scan_loopback_engines,
)
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_key_service import ProfileKeyService
from tests.unit.test_phase143_inference_assignments import _profile

OWNER = Principal(PrincipalKind.OWNER, "batteries-owner")


# ── fake engines: real HTTP servers on 127.0.0.1 ─────────────────────────


class _Engine:
    def __init__(self, models: list[str], *, tags: dict[str, str] | None = None) -> None:
        self.models = models
        self.tags = tags or {}
        self.requests: list[str] = []
        engine = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                engine.requests.append(self.path)
                if self.path == "/v1/models":
                    body = {"object": "list", "data": [{"id": m} for m in engine.models]}
                elif self.path == "/api/tags" and engine.tags:
                    body = {"models": [
                        {"name": name, "details": {"parameter_size": size}}
                        for name, size in engine.tags.items()
                    ]}
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                raw = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *_args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = int(self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def engines():
    started: list[_Engine] = []

    def start(models: list[str], **kwargs: Any) -> _Engine:
        engine = _Engine(models, **kwargs)
        started.append(engine)
        return engine

    yield start
    for engine in started:
        engine.close()


def _desk(tmp_path: Path, *, scan=None, detect_http_get=None) -> SimpleNamespace:
    db = Database(tmp_path / "desk.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home",
    )
    library = ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition,
        profile_key_service=ProfileKeyService(db, store=ProfileKeyStore(tmp_path / "keys.json")),
    )
    assignments = InferenceAssignmentService(db)
    defaults = InferenceDefaultService(
        db, assignment_service=assignments, model_library_service=library,
        home_provider=lambda: tmp_path / "home", scan=scan or (lambda: []),
        detect_http_get=detect_http_get or (lambda *_a, **_k: (200, b'{"data": []}')),
    )
    return SimpleNamespace(db=db, library=library, assignments=assignments, defaults=defaults)


def _scan_of(*pairs: tuple[_Engine, str]):
    return lambda: scan_loopback_engines(ports=[(engine.port, name) for engine, name in pairs])


def _receipts(db: Database) -> list[Any]:
    with db._connection() as conn:
        return conn.execute(
            """SELECT o.operation_id,o.placement,o.principal_identity,r.outcome,r.result_ref
                 FROM kernel_operations o JOIN kernel_receipts r ON r.operation_id=o.operation_id
                WHERE o.name=?""",
            (ASSIGNED_OPERATION,),
        ).fetchall()


def _global(db: Database) -> Any:
    with db._connection() as conn:
        return conn.execute(
            "SELECT assignment_id,revision,cleared FROM inference_assignment_heads WHERE assignment_key='global'"
        ).fetchone()


# ── ranking ──────────────────────────────────────────────────────────────


def test_parameter_count_is_read_from_size_words_and_model_names() -> None:
    assert parameter_billions("8.0B") == 8.0
    assert parameter_billions(None, "qwen3:8b") == 8.0
    assert parameter_billions("Qwen3.5-27B-Instruct-Q6_K") == 27.0
    assert parameter_billions("mixtral-8x7b-instruct") == 56.0
    assert parameter_billions("137M") == pytest.approx(0.137)
    assert parameter_billions("llama3.2:latest") is None


def test_rank_prefers_known_larger_then_signed_then_engine_order() -> None:
    rows = [
        {"model": "unknown:latest", "params_b": None, "signed": True, "order": 0},
        {"model": "small:4b", "params_b": 4.0, "signed": True, "order": 0},
        {"model": "big:27b", "params_b": 27.0, "signed": False, "order": 3},
        {"model": "big-signed:27b", "params_b": 27.0, "signed": True, "order": 4},
    ]
    assert [r["model"] for r in sorted(rows, key=rank_key)] == [
        "big-signed:27b", "big:27b", "small:4b", "unknown:latest",
    ]


# ── fence 1 + 2: a local engine is assigned once, with a receipt ─────────


def test_a_local_engine_is_assigned_once_with_a_receipt_and_the_local_lamp(tmp_path: Path, engines) -> None:
    ollama = engines(["qwen3:8b", "nomic-embed-text:latest"], tags={"qwen3:8b": "8.2B"})
    llama = engines(["Qwen3.5-27B-Instruct-Q6_K"])
    desk = _desk(tmp_path, scan=_scan_of((ollama, "Ollama"), (llama, "llama.cpp")))

    result = desk.defaults.ensure(reason="boot")

    assert result["status"] == "assigned"
    assigned = result["assigned"]
    # The largest known chat model wins; the embedding model is never a candidate.
    assert assigned["label"] == "Qwen3.5-27B-Instruct-Q6_K on llama.cpp"
    assert assigned["lamp"] == "local"
    head = _global(desk.db)
    assert head is not None and int(head["revision"]) == 1 and int(head["cleared"]) == 0
    projection = desk.assignments.get_assignment(OWNER, {"kind": "global"})
    assert [e["boundary"] for e in projection["entries"]] == ["local"]
    assert projection["entries"][0]["readiness"] == "ready"
    receipts = _receipts(desk.db)
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["placement"] == "local" and receipt["principal_identity"] == "batteries-default"
    assert "Boundary LOCAL" in receipt["outcome"] and "batteries-included default" in receipt["outcome"]
    assert receipt["result_ref"] == f"inference_assignment:{head['assignment_id']}@1"
    # The health probe reached the winner; the 8B engine was only listed.
    assert llama.requests.count("/v1/models") >= 2

    # Second boot: a new service over the same database changes nothing.
    second = InferenceDefaultService(
        desk.db, assignment_service=InferenceAssignmentService(desk.db),
        model_library_service=desk.library, home_provider=lambda: tmp_path / "home",
        scan=_scan_of((ollama, "Ollama"), (llama, "llama.cpp")),
    )
    with desk.db._connection() as conn:
        profiles_before = conn.execute("SELECT COUNT(*) FROM model_profile_revisions").fetchone()[0]
    assert second.ensure(reason="boot")["status"] == "kept"
    assert tuple(_global(desk.db)) == tuple(head)
    assert len(_receipts(desk.db)) == 1
    with desk.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM model_profile_revisions").fetchone()[0] == profiles_before


def test_an_engine_that_fails_its_health_probe_is_skipped_for_the_next(tmp_path: Path, engines) -> None:
    big = engines(["llama-70b-instruct"])
    small = engines(["qwen3:8b"])
    scan = _scan_of((big, "llama.cpp"), (small, "Ollama"))
    found = scan()
    big.close()  # listed at scan time, gone at the readiness probe
    desk = _desk(tmp_path, scan=lambda: found)
    result = desk.defaults.ensure(reason="boot")
    assert result["status"] == "assigned"
    assert result["assigned"]["label"] == "qwen3:8b on Ollama"


# ── fence 3: an owner assignment is never overwritten ────────────────────


def test_an_owner_default_is_never_overwritten(tmp_path: Path, engines) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    _profile(desk.db, "owner-lan", boundary="private_network")
    owner = desk.assignments.set_assignment(OWNER, {
        "command_id": "owner-default", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "owner-lan", "profile_revision": 1}],
    })
    assert desk.defaults.ensure(reason="boot")["status"] == "kept"
    current = desk.assignments.get_assignment(OWNER, {"kind": "global"})
    assert current["id"] == owner["id"] and current["revision"] == 1
    assert [e["profile_id"] for e in current["entries"]] == ["owner-lan"]
    assert _receipts(desk.db) == []
    assert llama.requests == []  # the scan does not even run


def test_a_default_the_owner_cleared_stays_cleared(tmp_path: Path, engines) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    _profile(desk.db, "owner-local")
    desk.assignments.set_assignment(OWNER, {
        "command_id": "owner-default", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "owner-local", "profile_revision": 1}],
    })
    desk.assignments.clear_assignment(OWNER, {
        "command_id": "owner-clear", "expected_revision": 1, "scope": {"kind": "global"},
        "capability_id": "ask.answer",
    })
    assert int(_global(desk.db)["cleared"]) == 1
    assert desk.defaults.ensure(reason="boot")["status"] == "kept"
    assert int(_global(desk.db)["cleared"]) == 1
    assert _receipts(desk.db) == []


# ── fence 4: a LAN / cloud engine is a proposal only ─────────────────────


def test_a_lan_engine_is_a_proposal_and_never_assigned(tmp_path: Path, monkeypatch) -> None:
    wire: list[str] = []

    def fake_wire(url: str, **_kwargs: Any) -> tuple[int, bytes]:
        wire.append(url)
        return 200, json.dumps({"data": [{"id": "qwen3.8-27b"}]}).encode()

    # The readiness probe of define_endpoint is the one wire call: faked.
    monkeypatch.setattr(
        "holdspeak.setup_runtime._default_http_json", fake_wire,
    )
    desk = _desk(tmp_path, detect_http_get=fake_wire)
    desk.library.define_endpoint(OWNER, {
        "request_id": "lan-1", "profile_id": "lan-main", "expected_profile_revision": 0,
        "label": "LAN model", "provider_family": "openai_compatible", "model": "qwen3.8-27b",
        "endpoint": "http://192.168.77.10:8080/v1", "requires_key": False,
    }, None)

    result = desk.defaults.ensure(reason="boot")

    assert result["status"] == "proposed" and result["proposals"] == 1
    assert _global(desk.db) is None
    assert _receipts(desk.db) == []
    proposals = desk.defaults.proposals()
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["lamp"] == "private_network" and proposal["verb"] == "Use it"
    assert (proposal["profile_id"], proposal["profile_revision"]) == ("lan-main", 1)
    # A second pass does not duplicate it.
    desk.defaults.ensure(reason="detect")
    assert len(desk.defaults.proposals()) == 1

    # The owner's press assigns it.
    used = desk.defaults.use_proposal(OWNER, proposal["id"])
    assert used["assignment"]["revision"] == 1
    assert desk.defaults.proposals() == []
    state = desk.defaults.state(OWNER)
    assert state["default"] == {"status": "assigned", "lamp": "private_network",
                                "made_by": "owner", "receipt_id": None}
    # "Use it" is the owner's press: memory follows it onto the LAN.
    with desk.db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is not None, capability


# ── fence 5: detection never touches a non-loopback address ──────────────


@pytest.fixture()
def sockets(monkeypatch):
    """Record every connect at the socket layer; never connect for real."""
    seen: list[Any] = []

    def connect(self, address):  # noqa: ANN001
        seen.append(address)
        raise ConnectionRefusedError(61, "refused by the test")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", lambda self, address: (seen.append(address), 61)[1])
    return seen


def test_the_scan_connects_only_to_loopback_even_with_a_proxy_set(sockets, monkeypatch) -> None:
    # An HTTP proxy in the environment would carry a plain urlopen to the
    # proxy host.  The scan opener ignores proxies.
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HTTP_PROXY", "http://192.0.2.50:3128")
    monkeypatch.setenv("http_proxy", "http://192.0.2.50:3128")

    assert scan_loopback_engines() == []

    assert sockets, "the scan made no connection attempt at all"
    hosts = {address[0] for address in sockets}
    ports = {address[1] for address in sockets}
    assert hosts == {"127.0.0.1"}
    assert ports <= {port for port, _engine in LOOPBACK_ENGINE_PORTS}


def test_a_non_loopback_host_is_refused_before_any_socket(sockets) -> None:
    for host in ("192.0.2.1", "192.168.1.43", "localhost.example", "8.8.8.8"):
        with pytest.raises(LoopbackOnlyError):
            scan_loopback_engines(host=host)
    assert sockets == []


# ── fence 6: memory inherits a LOCAL default, never a network one ────────


def _assign_global(db: Database, profile_id: str) -> dict[str, Any]:
    """The owner's own press: an owner-only set_assignment, no product receipt."""
    return InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"global-{profile_id}", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def mark_made_by_holdspeak(db: Database, assignment: dict[str, Any]) -> None:
    """Mark a revision as the product's own write (its durable ``made_by``)
    for a NON-local default the product never makes: the auto-assign refuses
    one (``test_the_auto_assign_never_writes_a_network_default``).  This forges
    the impossible state so the memory guard is fenced on its own."""
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_assignment_revisions SET made_by='holdspeak_default'"
            " WHERE assignment_id=? AND revision=?",
            (assignment["id"], assignment["revision"]),
        )


def test_memory_jobs_are_in_the_background_group() -> None:
    groups = {c.id: c.group_id for c in builtin_capability_definitions()}
    assert {groups[c] for c in LOCAL_INHERITING_CAPABILITIES} == {"background"}
    assert "memory.embed" not in LOCAL_INHERITING_CAPABILITIES


def test_memory_jobs_inherit_a_local_default(tmp_path: Path) -> None:
    db = Database(tmp_path / "local.db")
    _profile(db, "this-machine-model")  # same_device deployment
    _assign_global(db, "this-machine-model")
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is not None, capability
        assert _assignment_head(conn, "memory.embed") is None
    # The planner resolves the same default: the engine exists.
    assert resolve_extractor(_configure(db), OWNER) is not None


def test_memory_jobs_inherit_an_auto_assigned_local_default(tmp_path: Path, engines) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    assert desk.defaults.ensure(reason="boot")["status"] == "assigned"
    assert len(_receipts(desk.db)) == 1  # made by HoldSpeak, and local
    with desk.db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is not None, capability


@pytest.mark.parametrize("boundary", ["private_network", "cloud", "mesh"])
def test_memory_jobs_inherit_a_network_default_the_owner_set(tmp_path: Path, boundary: str) -> None:
    # Owner ruling 2026-10-05: his LAN server is his default INCLUDING memory.
    db = Database(tmp_path / f"{boundary}.db")
    _profile(db, "far-model", boundary=boundary)
    _assign_global(db, "far-model")
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is not None, capability
    assert resolve_extractor(_configure(db), OWNER) is not None


@pytest.mark.parametrize("boundary", ["private_network", "cloud", "mesh"])
def test_memory_jobs_stay_dark_on_a_network_default_without_the_owners_press(tmp_path: Path, boundary: str) -> None:
    db = Database(tmp_path / f"{boundary}.db")
    _profile(db, "far-model", boundary=boundary)
    mark_made_by_holdspeak(db, _assign_global(db, "far-model"))
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is None, capability
    assert resolve_extractor(_configure(db), OWNER) is None


def test_the_auto_assign_never_writes_a_network_default(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    _profile(desk.db, "lan-model", boundary="private_network")
    candidate = {"id": "profile:lan-model", "source": "profile", "profile_id": "lan-model",
                 "profile_revision": 1, "label": "LAN model", "model": "lan-model", "engine": "x"}
    assert desk.defaults._try_assign(candidate) is None
    assert _global(desk.db) is None and _receipts(desk.db) == []


def test_an_owner_network_background_group_is_inherited_before_the_default(tmp_path: Path) -> None:
    db = Database(tmp_path / "group.db")
    _profile(db, "local-model")
    _profile(db, "lan-model", boundary="private_network")
    _assign_global(db, "local-model")
    group = InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "group-bg", "expected_revision": 0,
        "scope": {"kind": "group", "group_id": "background"},
        "entries": [{"profile_id": "lan-model", "profile_revision": 1}],
    })
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) == f"{group['id']}@1", capability


def test_an_own_network_assignment_still_runs_memory(tmp_path: Path) -> None:
    db = Database(tmp_path / "own.db")
    _profile(db, "lan-model", boundary="private_network")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "own-extract", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "memory.extract"},
        "entries": [{"profile_id": "lan-model", "profile_revision": 1}],
    })
    with db._connection() as conn:
        assert _assignment_head(conn, "memory.extract") is not None


# ── fence 7: the per-capability state read ───────────────────────────────


def _by_id(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in state["capabilities"]}


def test_state_on_a_fresh_desk_says_needs_setup(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    state = desk.defaults.state(OWNER)
    assert state["schema"] == "InferenceDefaultsState@1"
    assert state["default"]["status"] == "needs_setup" and state["proposals"] == []
    rows = _by_id(state)
    assert rows["ask.answer"]["state"] == "needs_setup"
    assert rows["memory.embed"]["reason"] == "embedding_model_needed"


def test_state_after_the_local_default(tmp_path: Path, engines) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    desk.defaults.ensure(reason="boot")
    _profile(desk.db, "own-ask")
    desk.assignments.set_assignment(OWNER, {
        "command_id": "own-ask", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": "own-ask", "profile_revision": 1}],
    })
    state = desk.defaults.state(OWNER)
    assert state["default"]["status"] == "assigned"
    assert state["default"]["made_by"] == "holdspeak" and state["default"]["lamp"] == "local"
    assert state["default"]["receipt_id"]
    rows = _by_id(state)
    assert rows["ask.answer"]["state"] == "assigned"
    assert rows["chat.turn"]["state"] == "inherited_from_default"
    assert (rows["chat.turn"]["inherited_from"], rows["chat.turn"]["lamp"]) == ("global", "local")
    for capability in LOCAL_INHERITING_CAPABILITIES:
        assert rows[capability]["state"] == "inherited_from_default", capability
    assert rows["memory.embed"]["state"] == "needs_setup"


def test_state_with_an_owner_network_default_shows_memory_on_lan(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    _profile(desk.db, "lan-model", boundary="private_network")
    _assign_global(desk.db, "lan-model")
    state = desk.defaults.state(OWNER)
    assert (state["default"]["made_by"], state["default"]["lamp"]) == ("owner", "private_network")
    rows = _by_id(state)
    for capability in ("chat.turn", *LOCAL_INHERITING_CAPABILITIES):
        assert (rows[capability]["state"], rows[capability]["lamp"]) == (
            "inherited_from_default", "private_network"), capability


def test_state_with_a_network_default_without_the_owners_press_keeps_memory_dark(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    _profile(desk.db, "lan-model", boundary="private_network")
    mark_made_by_holdspeak(desk.db, _assign_global(desk.db, "lan-model"))
    rows = _by_id(desk.defaults.state(OWNER))
    assert rows["chat.turn"]["state"] == "inherited_from_default"
    for capability in LOCAL_INHERITING_CAPABILITIES:
        assert (rows[capability]["state"], rows[capability]["reason"]) == (
            "needs_setup", "default_not_local_not_owner"), capability


def test_state_with_a_proposal_says_proposed(tmp_path: Path, monkeypatch) -> None:
    wire = lambda url, **_k: (200, json.dumps({"data": [{"id": "m"}]}).encode())  # noqa: E731
    monkeypatch.setattr("holdspeak.setup_runtime._default_http_json", wire)
    desk = _desk(tmp_path, detect_http_get=wire)
    desk.library.define_endpoint(OWNER, {
        "request_id": "lan-1", "profile_id": "lan-main", "expected_profile_revision": 0,
        "label": "LAN model", "provider_family": "openai_compatible", "model": "m",
        "endpoint": "http://192.168.77.10:8080/v1", "requires_key": False,
    }, None)
    desk.defaults.ensure(reason="boot")
    state = desk.defaults.state(OWNER)
    assert state["default"]["status"] == "proposed"
    assert _by_id(state)["ask.answer"]["state"] == "proposed"


def test_state_route_and_use_it_press(tmp_path: Path, engines) -> None:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    from holdspeak.web.routes.inference_assignments import build_inference_assignments_router

    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    desk.defaults.ensure(reason="boot")
    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_inference_assignments_router(SimpleNamespace(
        inference_assignment_service=desk.assignments, inference_default_service=desk.defaults,
    )))
    client = TestClient(app)
    body = client.get("/api/inference/defaults").json()
    assert body["default"]["made_by"] == "holdspeak"
    assert _by_id(body)["chat.turn"]["state"] == "inherited_from_default"
    missing = client.post("/api/inference/defaults/use-proposal", json={"proposal_id": "nope"})
    assert missing.status_code == 404
    bad = client.post("/api/inference/defaults/use-proposal", json={"proposal_id": "x", "more": 1})
    assert bad.status_code == 400


# ── review round (Astra, 2026-10-05): Article III at every connect ───────


class _Recorder:
    """A plain HTTP server that records every request line it gets (a proxy
    or a redirect target).  It answers 502 so nothing proceeds through it."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            def _any(self) -> None:
                recorder.lines.append(f"{self.command} {self.path}")
                self.send_response(502)
                self.end_headers()

            do_GET = do_POST = do_CONNECT = _any  # noqa: N815

            def log_message(self, *_args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = int(self.server.server_address[1])
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def recorder():
    started: list[_Recorder] = []

    def start() -> _Recorder:
        r = _Recorder()
        started.append(r)
        return r

    yield start
    for r in started:
        r.close()


def _proxy_env(monkeypatch, proxy: _Recorder) -> None:
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    url = f"http://127.0.0.1:{proxy.port}"
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(name, url)


def _define(desk: SimpleNamespace, profile_id: str, endpoint: str, model: str = "qwen3:8b") -> None:
    desk.library.define_endpoint(OWNER, {
        "request_id": f"def-{profile_id}", "profile_id": profile_id, "expected_profile_revision": 0,
        "label": f"{profile_id} model", "provider_family": "openai_compatible", "model": model,
        "endpoint": endpoint, "requires_key": False,
    }, None)


@pytest.fixture()
def resolver(monkeypatch):
    """Override name resolution: ``names`` maps a host name to an address
    (or None = the lookup fails).  Every looked-up name is recorded."""
    real = socket.getaddrinfo
    looked: list[str] = []
    names: dict[str, Any] = {}

    def getaddrinfo(host, *args, **kwargs):  # noqa: ANN001
        if isinstance(host, str) and host in names:
            looked.append(host)
            if names[host] is None:
                raise socket.gaierror(8, "lookup refused by the test")
            return real(names[host], *args, **kwargs)
        if isinstance(host, str):
            looked.append(host)
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    return SimpleNamespace(looked=looked, names=names)


# 1 [P1] a name is never LOCAL; the word "localhost" is never resolved


def test_a_name_that_resolves_to_a_listener_is_never_local(tmp_path: Path, engines, resolver) -> None:
    # localhost.localdomain resolves (here: to the test listener; on a real
    # desk it could be a LAN box).  The lamp must not trust the name.
    lan = engines(["qwen3:8b"])
    resolver.names["localhost.localdomain"] = "127.0.0.1"
    desk = _desk(tmp_path)
    _define(desk, "named", f"http://localhost.localdomain:{lan.port}/v1")
    assert lan.requests, "the owner's endpoint answered its readiness probe"

    result = desk.defaults.ensure(reason="boot")

    assert result["status"] != "assigned" and _global(desk.db) is None
    # The owner can still choose it; its lamp is LAN, and memory follows his press.
    owner = _assign_global(desk.db, "named")
    assert [e["boundary"] for e in owner["entries"]] == ["private_network"]
    state = desk.defaults.state(OWNER)
    assert state["default"]["lamp"] == "private_network" and state["default"]["made_by"] == "owner"


def test_the_word_localhost_is_pinned_and_never_resolved(tmp_path: Path, engines, resolver) -> None:
    from holdspeak.intel.engine import MeetingIntel

    engine = engines(["qwen3:8b"])
    resolver.names["localhost"] = None  # a lookup of the word would fail
    desk = _desk(tmp_path)
    _define(desk, "word", f"http://localhost:{engine.port}/v1")
    observation = desk.defaults._live_ready("word", 1)
    assert observation is True
    intel = MeetingIntel(provider="cloud", cloud_model="qwen3:8b", cloud_base_url=f"http://localhost:{engine.port}/v1")
    intel._ensure_openai_client_loaded()
    assert [m.id for m in intel._openai_client.models.list().data] == ["qwen3:8b"]
    assert "localhost" not in resolver.looked
    with desk.db._connection() as conn:
        from holdspeak.inference_locality import head_lamp  # noqa: F401
    assert desk.assignments.get_assignment  # the lamp of this endpoint is local:
    owner = _assign_global(desk.db, "word")
    assert [e["boundary"] for e in owner["entries"]] == ["local"]


# 2 [P1] the scan and the readiness probe follow no redirect


def test_a_redirect_is_not_an_engine(tmp_path: Path, recorder) -> None:
    from holdspeak.setup_runtime import discover_endpoint_models

    target = recorder()

    class Redirect(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.port}/v1/models")
            self.end_headers()

        def log_message(self, *_args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = int(server.server_address[1])
        assert scan_loopback_engines(ports=[(port, "Ollama")]) == []
        assert discover_endpoint_models(f"http://127.0.0.1:{port}/v1")["ok"] is False
    finally:
        server.shutdown()
        server.server_close()
    assert target.lines == []


# 3 [P1] no proxy for the scan, the readiness probe or the engine's calls


def test_the_scan_bypasses_a_real_proxy(engines, recorder, monkeypatch) -> None:
    engine = engines(["qwen3:8b"])
    proxy = recorder()
    _proxy_env(monkeypatch, proxy)
    found = scan_loopback_engines(ports=[(engine.port, "llama.cpp")])
    assert [f["model"] for f in found] == ["qwen3:8b"]
    assert proxy.lines == [] and engine.requests == ["/v1/models"]


def test_the_readiness_probe_bypasses_a_real_proxy(tmp_path: Path, engines, recorder, monkeypatch) -> None:
    engine = engines(["qwen3:8b"])
    proxy = recorder()
    _proxy_env(monkeypatch, proxy)
    desk = _desk(tmp_path)
    _define(desk, "probe", f"http://127.0.0.1:{engine.port}/v1")
    assert desk.defaults._live_ready("probe", 1) is True
    assert proxy.lines == [] and engine.requests


def test_the_engine_calls_bypass_a_real_proxy(engines, recorder, monkeypatch) -> None:
    from holdspeak.intel.engine import MeetingIntel

    engine = engines(["qwen3:8b"])
    proxy = recorder()
    _proxy_env(monkeypatch, proxy)
    intel = MeetingIntel(provider="cloud", cloud_model="qwen3:8b", cloud_base_url=f"http://127.0.0.1:{engine.port}/v1")
    intel._ensure_openai_client_loaded()
    assert [m.id for m in intel._openai_client.models.list().data] == ["qwen3:8b"]
    assert proxy.lines == [] and engine.requests == ["/v1/models"]


# 4 [P2] who made the default is durable with the revision


def test_a_lost_receipt_never_turns_the_default_into_an_owner_press(tmp_path: Path, engines, monkeypatch) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))

    def broken(*_args: Any, **_kwargs: Any) -> str:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(desk.defaults, "_write_receipt", broken)
    assert desk.defaults.ensure(reason="boot")["status"] == "assigned"
    assert _receipts(desk.db) == []
    head = _global(desk.db)
    with desk.db._connection() as conn:
        made_by = conn.execute(
            "SELECT made_by FROM inference_assignment_revisions WHERE assignment_id=? AND revision=?",
            (head["assignment_id"], head["revision"]),
        ).fetchone()[0]
    assert made_by == "holdspeak_default"
    assert desk.defaults.state(OWNER)["default"]["made_by"] == "holdspeak"


def test_an_owner_press_is_recorded_as_the_owner(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    _profile(desk.db, "mine")
    head = _assign_global(desk.db, "mine")
    with desk.db._connection() as conn:
        assert conn.execute(
            "SELECT made_by FROM inference_assignment_revisions WHERE assignment_id=?", (head["id"],),
        ).fetchone()[0] == "owner"
    with pytest.raises(ValueError):
        desk.assignments.set_assignment(OWNER, {
            "command_id": "bad", "expected_revision": 1, "scope": {"kind": "global"},
            "entries": [{"profile_id": "mine", "profile_revision": 1}],
        }, made_by="someone")


# 5 [P2] the owner's Turn off is final for automatic embedding adoption


def _meaning_desk(tmp_path: Path) -> SimpleNamespace:
    from holdspeak.services.meaning_search_service import MeaningSearchService

    desk = _desk(tmp_path)
    meaning = MeaningSearchService(
        desk.db, assignment_service=desk.assignments, broker_provider=lambda: None,
        home_provider=lambda: tmp_path / "home", wake=lambda: None,
    )
    model_file = tmp_path / "embed.gguf"
    model_file.write_bytes(b"gguf")
    desk.defaults = InferenceDefaultService(
        desk.db, assignment_service=desk.assignments, model_library_service=desk.library,
        meaning_search=meaning, home_provider=lambda: tmp_path / "home", scan=lambda: [],
        detect_http_get=lambda *_a, **_k: (200, b'{"data": []}'),
        find_embed_model=lambda *_a: model_file,
    )
    return SimpleNamespace(**vars(desk), meaning=meaning, model_file=model_file)


def _embed_head(db: Database) -> Any:
    with db._connection() as conn:
        return conn.execute(
            """SELECT h.revision,h.cleared,r.made_by FROM inference_assignment_heads h
                 JOIN inference_assignment_revisions r
                   ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                WHERE h.assignment_key='capability:memory.embed'"""
        ).fetchone()


def test_embedding_is_adopted_when_the_model_is_here_and_never_assigned(tmp_path: Path) -> None:
    desk = _meaning_desk(tmp_path)
    assert desk.defaults._ensure_meaning_search() == "adopted"
    head = _embed_head(desk.db)
    assert (head["revision"], head["cleared"], head["made_by"]) == (1, 0, "holdspeak_default")


def test_a_turn_off_is_final_even_inside_the_race(tmp_path: Path, monkeypatch) -> None:
    desk = _meaning_desk(tmp_path)
    desk.meaning._activate(OWNER, desk.model_file)  # the owner's Turn on (r1)
    desk.meaning.turn_off(OWNER)  # the owner's Turn off (r2, cleared)
    assert tuple(_embed_head(desk.db)) == (2, 1, "owner")
    # The race: the quick read ran before the owner's clear landed.
    monkeypatch.setattr(desk.defaults, "_embed_head_ever_existed", lambda: False)
    assert desk.defaults._ensure_meaning_search() == "kept"
    assert tuple(_embed_head(desk.db)) == (2, 1, "owner")


# 6 [P2] readiness is probed live; HoldSpeak's own dead default is re-picked


def test_a_dead_default_of_holdspeaks_is_repicked_to_a_live_engine(tmp_path: Path, engines) -> None:
    big = engines(["llama-70b-instruct"])
    small = engines(["qwen3:8b"])
    desk = _desk(tmp_path, scan=_scan_of((big, "llama.cpp"), (small, "Ollama")))
    first = desk.defaults.ensure(reason="boot")
    assert first["assigned"]["label"] == "llama-70b-instruct on llama.cpp"

    big.close()  # its readiness observation still says "ready"
    desk.defaults._scan = _scan_of((small, "Ollama"))
    second = desk.defaults.ensure(reason="boot")

    assert second["status"] == "repicked"
    assert second["assigned"]["label"] == "qwen3:8b on Ollama"
    head = _global(desk.db)
    assert int(head["revision"]) == 2
    assert len(_receipts(desk.db)) == 2
    assert desk.defaults.state(OWNER)["default"]["made_by"] == "holdspeak"


def test_a_dead_owner_default_is_never_touched(tmp_path: Path, engines) -> None:
    big = engines(["llama-70b-instruct"])
    small = engines(["qwen3:8b"])
    desk = _desk(tmp_path)
    _define(desk, "owner-big", f"http://127.0.0.1:{big.port}/v1", model="llama-70b-instruct")
    _assign_global(desk.db, "owner-big")
    big.close()
    desk.defaults._scan = _scan_of((small, "Ollama"))
    assert desk.defaults.ensure(reason="boot")["status"] == "kept"
    current = desk.assignments.get_assignment(OWNER, {"kind": "global"})
    assert current["revision"] == 1 and current["entries"][0]["profile_id"] == "owner-big"
    assert _receipts(desk.db) == []


# 7 [P3] the census lives outside pm/roadmap


def test_the_census_fence_reads_the_maintained_copy() -> None:
    from tests.unit import test_phase143_surface_fallback_census as census

    assert census.ARTIFACT.relative_to(census.REPO).as_posix() == "docs/internal/surface-fallback-census.md"


@pytest.mark.parametrize("url", [
    "http://localhost:41234/v1",
    "http://localhost.:41234/v1",
    "http://LOCALHOST.:41234/v1",
    "http://127.0.0.1:41234/v1",
    "http://127.0.0.1.:41234/v1",
    "http://127.0.0.2:41234/v1",
    "http://[::1]:41234/v1",
    "http://localhost.localdomain:41234/v1",
    "http://dev.localhost:41234/v1",
    "http://192.168.1.43:8080/v1",
])
def test_the_lamp_says_local_only_where_the_transport_is_loopback(url: str) -> None:
    """Astra, #855 iteration 2: the egress lamp and the loopback transport
    read ONE rule.  "localhost." normalised to a LOCAL lamp while the
    transport (which pins only the exact word) sent it through the proxy."""
    from holdspeak.intel.providers import EGRESS_LOCAL, egress_boundary
    from holdspeak.loopback_http import is_loopback_url

    assert (egress_boundary(base_url=url) == EGRESS_LOCAL) == is_loopback_url(url), url
