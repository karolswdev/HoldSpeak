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


def _assign_global(db: Database, profile_id: str) -> None:
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"global-{profile_id}", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


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


def test_memory_jobs_inherit_a_loopback_endpoint_default(tmp_path: Path, engines) -> None:
    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    assert desk.defaults.ensure(reason="boot")["status"] == "assigned"
    with desk.db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is not None, capability


@pytest.mark.parametrize("boundary", ["private_network", "cloud", "mesh"])
def test_memory_jobs_do_not_inherit_a_network_or_cloud_default(tmp_path: Path, boundary: str) -> None:
    db = Database(tmp_path / f"{boundary}.db")
    _profile(db, "far-model", boundary=boundary)
    _assign_global(db, "far-model")
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is None, capability
    assert resolve_extractor(_configure(db), OWNER) is None


def test_a_network_background_group_wins_over_a_local_default(tmp_path: Path) -> None:
    db = Database(tmp_path / "group.db")
    _profile(db, "local-model")
    _profile(db, "lan-model", boundary="private_network")
    _assign_global(db, "local-model")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "group-bg", "expected_revision": 0,
        "scope": {"kind": "group", "group_id": "background"},
        "entries": [{"profile_id": "lan-model", "profile_revision": 1}],
    })
    with db._connection() as conn:
        for capability in LOCAL_INHERITING_CAPABILITIES:
            assert _assignment_head(conn, capability) is None, capability


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


def test_state_with_a_network_default_keeps_memory_dark(tmp_path: Path) -> None:
    desk = _desk(tmp_path)
    _profile(desk.db, "lan-model", boundary="private_network")
    _assign_global(desk.db, "lan-model")
    rows = _by_id(desk.defaults.state(OWNER))
    assert rows["chat.turn"]["state"] == "inherited_from_default"
    assert rows["chat.turn"]["lamp"] == "private_network"
    for capability in LOCAL_INHERITING_CAPABILITIES:
        assert (rows[capability]["state"], rows[capability]["reason"]) == ("needs_setup", "default_not_local")


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
