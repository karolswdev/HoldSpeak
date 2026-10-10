"""Owner ruling 2026-10-05, "strong defaults, batteries included": the rest.

1. The hub takes port 8765, or a free port when 8765 is busy.
2. A blank MLX dictation model is "not set up": ``auto`` plans llama.cpp.
3. An engine started AFTER boot is found by the light loopback re-scan.
4. The meetings saved before any engine existed are summarised once one does.

Real producers: a real uvicorn listener, the real plan resolver, the real
default / assignment / Model Library services over a real database with real
HTTP engines on 127.0.0.1, and the real Run-intelligence producer
(``project_route`` + ``db.intel.request_intel_retry``).
"""
from __future__ import annotations

import socket
import threading
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.defaults_conductor import DefaultsConductor
from holdspeak.services.meeting_backlog_service import (
    BACKLOG_REASON,
    MeetingSummaryBacklog,
    mark_if_no_engine,
)
from tests.unit.test_batteries_default import (  # noqa: F401  (engines is a fixture)
    _desk,
    _global,
    _receipts,
    _scan_of,
    engines,
)
from tests.unit.test_hs172_loop_wire import (
    _link_meeting_project,
    _seed_meeting,
    _seed_project,
    assign_meeting_engine,
)


# ── 1. the fixed default port ──────────────────────────────────────────────


def _bare_server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, preferred: int):
    from tests.unit.test_web_server_startup import _server

    server = _server(tmp_path, monkeypatch)
    server._preferred_port = preferred
    return server


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health(url: str) -> int:
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f"{url}/health", timeout=5) as r:
        return r.status


def test_the_live_runtime_asks_for_port_8765(monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_runtime as web_runtime
    from holdspeak.web_server import DEFAULT_WEB_PORT
    from tests.unit.test_web_runtime import _config

    monkeypatch.delenv("HOLDSPEAK_WEB_PORT", raising=False)
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=False))
    seen: dict = {}

    class FakeServer:
        def __init__(self, callbacks=None, **kwargs):
            seen.update(kwargs)

        def start(self) -> str:
            raise RuntimeError("stop here")

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    stop = threading.Event()
    stop.set()
    with pytest.raises(SystemExit):
        web_runtime.run_web_runtime(no_open=True, stop_event=stop, register_signal_handlers=False)
    assert DEFAULT_WEB_PORT == 8765
    assert seen["preferred_port"] == 8765
    assert seen["port"] is None  # HOLDSPEAK_WEB_PORT unset


@pytest.mark.timeout(30)
def test_the_hub_takes_the_preferred_port_when_it_is_free(tmp_path, monkeypatch) -> None:
    port = _free_port()
    server = _bare_server(tmp_path, monkeypatch, port)
    try:
        url = server.start()
        assert server.port == port and url.endswith(f":{port}")
        assert _health(url) == 200
    finally:
        server.stop()


@pytest.mark.timeout(30)
def test_the_hub_takes_a_free_port_when_the_preferred_one_is_busy(tmp_path, monkeypatch) -> None:
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    busy = int(holder.getsockname()[1])
    server = _bare_server(tmp_path, monkeypatch, busy)
    try:
        url = server.start()
        assert server.port != busy and server.port
        assert _health(url) == 200
    finally:
        server.stop()
        holder.close()


def test_doctor_falls_back_to_the_hub_default_port() -> None:
    from holdspeak import doctor
    from holdspeak.web_server import DEFAULT_WEB_PORT

    assert doctor.DEFAULT_URL == f"http://127.0.0.1:{DEFAULT_WEB_PORT}"


def test_doctor_uses_the_local_owner_token_only_for_the_local_hub(monkeypatch) -> None:
    from holdspeak import doctor

    monkeypatch.delenv("HOLDSPEAK_URL", raising=False)
    monkeypatch.delenv("HOLDSPEAK_TOKEN", raising=False)
    monkeypatch.setattr(doctor, "_local_owner_token", lambda: "owner-token")
    monkeypatch.setattr(doctor, "discovered_hub_url", lambda: None)
    seen: list[tuple[str, str]] = []
    for name in ("_check_hub_health", "_check_runtime_status", "_check_runtime_preflight", "_check_websocket",
                 "_check_desk_bootstrap", "_check_auth", "_check_inference"):
        monkeypatch.setattr(doctor, name, lambda url, token, _n=name: seen.append((url, token)) or None)
    monkeypatch.setattr(doctor, "_check_mcp_server", lambda: None)
    monkeypatch.setattr(doctor, "_check_database", lambda: None)
    monkeypatch.setattr(doctor, "check_observer", lambda: None)
    doctor.run_checks()
    assert {token for _url, token in seen} == {"owner-token"}
    assert {url for url, _token in seen} == {"http://127.0.0.1:8765"}
    seen.clear()
    doctor.run_checks("http://192.168.1.9:8765")  # a hub he named: his local token never goes there
    assert {token for _url, token in seen} == {""}


class _Recorder:
    """A real HTTP server on 127.0.0.1 that records what reached it."""

    def __init__(self, redirect_to: str = "") -> None:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        self.seen: list[dict[str, str]] = []
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self) -> None:
                recorder.seen.append({k.lower(): v for k, v in self.headers.items()})
                if redirect_to:
                    self.send_response(302)
                    self.send_header("Location", redirect_to + self.path)
                    self.end_headers()
                    return
                body = b'{"status": "ok"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = _answer
            do_POST = _answer

            def log_message(self, *_args) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def test_doctor_never_carries_the_auto_loaded_token_across_a_redirect(monkeypatch) -> None:
    """Astra's repro: the local hub's /health redirects to another server; the
    owner token doctor loaded by itself must not reach it."""
    from holdspeak import doctor

    other = _Recorder()
    hub = _Recorder(redirect_to=other.url)
    try:
        monkeypatch.delenv("HOLDSPEAK_URL", raising=False)
        monkeypatch.delenv("HOLDSPEAK_TOKEN", raising=False)
        monkeypatch.setattr(doctor, "discovered_hub_url", lambda: hub.url)
        monkeypatch.setattr(doctor, "_local_owner_token", lambda: "owner-secret")
        results = {r.name: r for r in doctor.run_checks()}
    finally:
        hub.close()
        other.close()
    assert any(h.get("authorization") == "Bearer owner-secret" for h in hub.seen)  # the hub got it
    leaked = [h for h in other.seen if "owner-secret" in repr(h)]
    assert leaked == [], leaked
    assert results["hub-health"].status == "FAIL"  # a redirect is not the hub


def test_doctor_loads_the_owner_token_only_for_a_loopback_literal(monkeypatch) -> None:
    from holdspeak import doctor

    monkeypatch.delenv("HOLDSPEAK_URL", raising=False)
    monkeypatch.delenv("HOLDSPEAK_TOKEN", raising=False)
    monkeypatch.setattr(doctor, "_local_owner_token", lambda: "owner-secret")
    seen: list[str] = []
    monkeypatch.setattr(doctor, "_check_hub_health", lambda url, token: seen.append(token) or None)
    for name in ("_check_runtime_status", "_check_runtime_preflight", "_check_websocket",
                 "_check_desk_bootstrap", "_check_auth", "_check_inference"):
        monkeypatch.setattr(doctor, name, lambda url, token: None)
    for name in ("_check_mcp_server", "_check_database", "check_observer"):
        monkeypatch.setattr(doctor, name, lambda: None)
    for discovered, expected in (("http://192.168.1.9:8765", ""), ("http://hub.example:8765", ""),
                                 ("http://localhost:8765", "owner-secret")):
        monkeypatch.setattr(doctor, "discovered_hub_url", lambda d=discovered: d)
        seen.clear()
        doctor.run_checks()
        assert seen == [expected], discovered


@pytest.mark.timeout(30)
def test_doctor_websocket_reads_past_the_hubs_own_frames(tmp_path, monkeypatch) -> None:
    from holdspeak import doctor

    server = _bare_server(tmp_path, monkeypatch, _free_port())
    # The live hub's state has a duration, so it pushes {"type":"duration"}
    # on connect before it answers the ping (seen on a real boot).
    server.get_state = lambda: {"duration": 0}
    try:
        url = server.start()
        result = doctor._check_websocket(url, server.auth_token)
    finally:
        server.stop()
    assert result.status == "PASS", result.detail


# ── 2. a blank MLX model is "not set up" ──────────────────────────────────


@pytest.fixture()
def mlx_installed(monkeypatch: pytest.MonkeyPatch):
    """A Mac with mlx_lm importable, whatever this machine has."""
    import importlib
    import platform
    import types

    real = importlib.import_module
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    monkeypatch.setattr(
        importlib, "import_module",
        lambda name, *a, **k: types.ModuleType("mlx_lm") if name == "mlx_lm" else real(name, *a, **k),
    )


def test_the_default_mlx_model_is_blank() -> None:
    from holdspeak.config import Config

    assert Config().dictation.runtime.mlx_model == ""


def test_auto_plans_llama_cpp_when_no_mlx_model_is_set(mlx_installed) -> None:
    from holdspeak.config import Config
    from holdspeak.speech_session.plan import _pipeline_terms, dictation_local_deployment_identity

    terms = _pipeline_terms(Config())
    identity = dictation_local_deployment_identity(terms)
    assert identity is not None, "a blank MLX model must not leave dictation without an artifact"
    assert identity.engine == "llama_cpp"
    assert identity.model_path.endswith("Qwen3.5-4B-Q4_K_M.gguf")


def test_auto_still_plans_mlx_when_the_owner_names_a_model(mlx_installed) -> None:
    from holdspeak.config import Config
    from holdspeak.speech_session.plan import _pipeline_terms, dictation_local_deployment_identity

    config = Config()
    config.dictation.runtime.mlx_model = "~/Models/mlx/Some-Model-4bit"
    identity = dictation_local_deployment_identity(_pipeline_terms(config))
    assert identity is not None and identity.engine == "mlx"
    assert identity.model == "Some-Model-4bit"


def test_runtime_resolution_agrees_with_the_plan() -> None:
    from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError, resolve_backend

    yes = lambda: True  # noqa: E731
    seams = dict(on_arm64=yes, mlx_importable=yes, llama_cpp_importable=yes)
    assert resolve_backend("auto", **seams, mlx_model_set=False)[0] == "llama_cpp"
    assert resolve_backend("auto", **seams, mlx_model_set=True)[0] == "mlx"
    assert resolve_backend("auto", **seams)[0] == "mlx"  # unknown model: package rule
    with pytest.raises(RuntimeUnavailableError, match="no model set up"):
        resolve_backend("mlx", **seams, mlx_model_set=False)


def test_build_runtime_with_a_blank_mlx_model_builds_llama_cpp() -> None:
    from holdspeak.plugins.dictation.runtime import build_runtime

    built: list[str] = []

    def factory(kind: str):
        def make(**_kwargs):
            built.append(kind)
            return object()
        return make

    yes = lambda: True  # noqa: E731
    build_runtime(
        backend="auto", mlx_model="", on_arm64=yes, mlx_importable=yes, llama_cpp_importable=yes,
        factories={k: factory(k) for k in ("mlx", "llama_cpp", "openai_compatible")},
    )
    assert built == ["llama_cpp"]


# ── 3. an engine started after boot ──────────────────────────────────────


def test_an_engine_started_after_boot_is_found_by_the_rescan(tmp_path: Path, engines) -> None:
    found: list = []
    desk = _desk(tmp_path, scan=lambda: list(found))
    assert desk.defaults.ensure(reason="boot")["status"] == "needs_setup"
    assert _global(desk.db) is None

    conductor = DefaultsConductor(defaults_service=desk.defaults, interval=3600)
    assert conductor.tick()["rescan"]["status"] == "none"  # still nothing running

    ollama = engines(["qwen3:8b"], tags={"qwen3:8b": "8.2B"})  # started after boot
    found.extend(_scan_of((ollama, "Ollama"))())
    result = conductor.tick()["rescan"]
    assert result["status"] == "assigned"
    assert result["assigned"]["label"] == "qwen3:8b on Ollama" and result["assigned"]["lamp"] == "local"
    head = _global(desk.db)
    assert head is not None and int(head["revision"]) == 1
    assert len(_receipts(desk.db)) == 1

    # A default exists: the conductor stops scanning; the engine sees no more calls.
    calls = len(ollama.requests)
    assert conductor.scanning is False
    assert "rescan" not in conductor.tick()
    assert len(ollama.requests) == calls


def test_the_rescan_never_runs_over_a_default_the_owner_made(tmp_path: Path, engines) -> None:
    from tests.unit.test_batteries_default import OWNER
    from tests.unit.test_phase143_inference_assignments import _profile

    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    _profile(desk.db, "owner-lan", boundary="private_network")
    desk.assignments.set_assignment(OWNER, {
        "command_id": "owner-default", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "owner-lan", "profile_revision": 1}],
    })
    assert desk.defaults.rescan()["status"] == "has_default"
    assert llama.requests == []
    assert _receipts(desk.db) == []


# ── 4. the summary backlog: durable per-meeting marks ─────────────────────


def _jobs(db: Database) -> dict[str, str]:
    with db._connection() as conn:
        rows = conn.execute("SELECT meeting_id, status FROM intel_jobs").fetchall()
    return {str(r["meeting_id"]): str(r["status"]) for r in rows}


def _marks(db: Database) -> set[str]:
    with db._connection() as conn:
        return {str(r[0]) for r in conn.execute("SELECT meeting_id FROM meeting_summary_backlog")}


def _set_ended(db: Database, meeting_id: str, when: datetime) -> None:
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET ended_at=? WHERE id=?", (when.isoformat(), meeting_id))


def _backlog(db: Database, *, auto: str = "every", limit: int = 10, route_for=None) -> MeetingSummaryBacklog:
    return MeetingSummaryBacklog(lambda: db, auto_mode=lambda: auto, limit=limit, route_for=route_for)


def _saved_without_engine(db: Database, meeting_id: str, *, ended: datetime | None = None, **kwargs) -> None:
    """A meeting saved at Stop while no engine could summarise it: the real mark."""
    _seed_meeting(db, meeting_id, **kwargs)
    if ended is not None:
        _set_ended(db, meeting_id, ended)
    assert mark_if_no_engine(db, meeting_id) is True


def test_a_meeting_saved_with_no_engine_is_marked_and_queued_once_one_can(tmp_path: Path) -> None:
    db = Database(tmp_path / "backlog.db")
    base = datetime.now() - timedelta(days=3)
    for index in range(3):
        _saved_without_engine(db, f"m{index}", ended=base + timedelta(hours=index))
    _seed_meeting(db, "empty", has_segments=False)
    assert mark_if_no_engine(db, "empty") is False  # no transcript, nothing to summarise
    assert _marks(db) == {"m0", "m1", "m2"}

    backlog = _backlog(db)
    assert backlog.tick()["status"] == "waiting_consent"  # no engine at all: marks wait
    assert _jobs(db) == {} and _marks(db) == {"m0", "m1", "m2"}

    assign_meeting_engine(db)  # the owner assigns an engine
    result = backlog.tick()
    assert result["queued"] == ["m2", "m1", "m0"]  # newest first, oldest last
    assert _jobs(db) == {"m0": "queued", "m1": "queued", "m2": "queued"}
    assert _marks(db) == set()
    with db._connection() as conn:
        reasons = {r[0] for r in conn.execute("SELECT intel_status_detail FROM meetings WHERE id LIKE 'm%'")}
        events = conn.execute(
            "SELECT COUNT(*) FROM service_events WHERE event_type='meeting.auto_intel_enqueued'"
        ).fetchone()[0]
    assert reasons == {BACKLOG_REASON} and events == 3
    assert backlog.tick() == {"status": "idle", "queued": []}


def test_a_restart_never_queues_a_meeting_saved_with_an_engine(tmp_path: Path) -> None:
    """Astra's repro: saved WITH an engine (left transcript-only by the Stop
    decision), then the hub restarts: the backlog must not summarise it."""
    db = Database(tmp_path / "restart.db")
    assign_meeting_engine(db)
    _seed_meeting(db, "with-engine")
    assert mark_if_no_engine(db, "with-engine") is False  # its route was ready at Stop
    for _restart in range(2):
        assert _backlog(db).tick() == {"status": "idle", "queued": []}  # a fresh process each time
    assert _jobs(db) == {} and _marks(db) == set()


def test_an_explicit_skip_clears_the_mark(tmp_path: Path) -> None:
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from tests.unit.test_batteries_default import OWNER

    db = Database(tmp_path / "skip.db")
    _saved_without_engine(db, "skipped")
    _saved_without_engine(db, "kept")
    MeetingIntelService(db).skip_recovery(OWNER, "skipped")
    assert _marks(db) == {"kept"}
    assign_meeting_engine(db)
    assert _backlog(db).tick()["queued"] == ["kept"]
    assert set(_jobs(db)) == {"kept"}


def test_the_backlog_is_bounded_per_tick_and_drains_oldest_last(tmp_path: Path) -> None:
    db = Database(tmp_path / "bounded.db")
    base = datetime.now() - timedelta(days=10)
    for index in range(5):
        _saved_without_engine(db, f"m{index}", ended=base + timedelta(days=index))
    assign_meeting_engine(db)
    backlog = _backlog(db, limit=2)
    assert backlog.tick()["queued"] == ["m4", "m3"]
    assert backlog.tick()["queued"] == ["m2", "m1"]
    assert backlog.tick()["queued"] == ["m0"]
    assert backlog.tick() == {"status": "idle", "queued": []}


def test_the_backlog_follows_intelligence_auto(tmp_path: Path) -> None:
    db = Database(tmp_path / "auto.db")
    _saved_without_engine(db, "linked")
    _saved_without_engine(db, "loose")
    _seed_project(db, "room")
    _link_meeting_project(db, "linked", "room")
    assign_meeting_engine(db)
    assert _backlog(db, auto="off").tick()["queued"] == []
    assert _backlog(db, auto="room_linked").tick()["queued"] == ["linked"]
    assert set(_jobs(db)) == {"linked"} and _marks(db) == {"loose"}  # pending, never dropped


def test_a_route_that_is_not_ready_keeps_the_marks_and_resumes(tmp_path: Path) -> None:
    from holdspeak.services.meeting_route_projection import project_route

    db = Database(tmp_path / "repair.db")
    _saved_without_engine(db, "pending")
    assign_meeting_engine(db)
    broken = {"on": True}

    def route_for(database, meeting_id):
        if broken["on"]:
            return {"status": "unavailable", "reason_code": "route unavailable", "legs": []}
        return project_route(database, invocation_id=f"meeting:{meeting_id}")

    backlog = _backlog(db, route_for=route_for)
    assert backlog.tick()["status"] == "waiting_route"
    assert _marks(db) == {"pending"} and _jobs(db) == {}
    broken["on"] = False  # the route is repaired
    assert backlog.tick()["queued"] == ["pending"]
    assert _marks(db) == set()


def test_a_network_engine_the_owner_did_not_press_for_never_gets_backlog_work(tmp_path: Path) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_batteries_default import OWNER
    from tests.unit.test_phase143_inference_assignments import _profile

    db = Database(tmp_path / "consent.db")
    _saved_without_engine(db, "waiting")
    from holdspeak.inference_capabilities import process_inference_capability_registry

    schema = process_inference_capability_registry().require("meeting.deferred_analysis")
    _profile(db, "lan-engine", boundary="private_network",
             claims=("language", f"result_schema:{schema.output_schema_sha256}"))
    assignments = InferenceAssignmentService(db)
    # Not something the product writes by itself (#855 fences that); here the
    # revision says HoldSpeak made a network default, and the backlog refuses it.
    unpressed = assignments.set_assignment(OWNER, {
        "command_id": "unpressed-lan", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "lan-engine", "profile_revision": 1}],
    }, made_by="holdspeak_default")
    result = _backlog(db).tick()
    assert result["status"] == "waiting_consent"
    assert result["consent"] == {"allowed": False, "lamp": "private_network", "made_by": "holdspeak_default",
                                 "source": "global"}
    assert _jobs(db) == {} and _marks(db) == {"waiting"}

    assignments.set_assignment(OWNER, {  # the owner presses for the same engine
        "command_id": "pressed-lan", "expected_revision": int(unpressed["revision"]), "scope": {"kind": "global"},
        "entries": [{"profile_id": "lan-engine", "profile_revision": 1}],
    })
    assert _backlog(db).tick()["queued"] == ["waiting"]


def test_the_default_for_ai_work_routes_the_backlog_through_the_conductor(tmp_path: Path, engines) -> None:
    """The defaults watcher assigns a loopback default; the same tick queues the
    marked meeting through the queue's own route (meeting-intel-queue@2)."""
    from holdspeak.services.meeting_route_projection import project_route

    found: list = []
    desk = _desk(tmp_path, scan=lambda: list(found))
    _saved_without_engine(desk.db, "before-engine")
    conductor = DefaultsConductor(
        defaults_service=desk.defaults, backlog=_backlog(desk.db), interval=3600,
    )
    first = conductor.tick()
    assert first["rescan"]["status"] == "none" and first["backlog"]["status"] == "waiting_consent"

    ollama = engines(["qwen3:8b"], tags={"qwen3:8b": "8.2B"})
    found.extend(_scan_of((ollama, "Ollama"))())
    second = conductor.tick()
    assert second["rescan"]["status"] == "assigned"
    assert project_route(desk.db, invocation_id="meeting:before-engine")["status"] == "ready"
    assert second["backlog"]["queued"] == ["before-engine"]
    assert _jobs(desk.db) == {"before-engine": "queued"}


# ── 5. PHILO-17: "Summary after every meeting" holds at Import too ───────────


def test_an_import_with_an_engine_queues_its_summary(tmp_path: Path, monkeypatch) -> None:
    from types import SimpleNamespace

    from holdspeak.config import Config
    from holdspeak.meeting_import import import_transcript

    cfg = Config()
    cfg.meeting.intelligence_auto = "every"
    monkeypatch.setattr(Config, "load", lambda: cfg)
    monkeypatch.setattr("holdspeak.intel_queue_conductor.wake_intel_queue_conductor", lambda: True)
    db = Database(tmp_path / "import.db")
    assign_meeting_engine(db)
    path = tmp_path / "weekly sync.vtt"
    path.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Priya>the rollout starts monday\n")
    config = SimpleNamespace(meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True))

    result = import_transcript(path, db=db, config=config)

    assert result.intel_job_enqueued is True
    assert _jobs(db) == {result.state.id: "queued"}
    assert db.meetings.get_meeting(result.state.id).intel_status == "queued"


def test_queue_after_save_follows_the_setting_and_consent(tmp_path: Path) -> None:
    from holdspeak.services.meeting_backlog_service import queue_after_save

    db = Database(tmp_path / "after-save.db")
    _seed_meeting(db, "no-engine")
    assert queue_after_save(db, "no-engine", auto_mode="every") == {"queued": False, "reason": "no_engine"}
    assert _marks(db) == {"no-engine"}  # the backlog runs it once an engine can

    assign_meeting_engine(db)
    _seed_meeting(db, "off")
    assert queue_after_save(db, "off", auto_mode="off")["queued"] is False
    _seed_meeting(db, "loose")
    assert queue_after_save(db, "loose", auto_mode="room_linked")["reason"] == "not_room_linked"
    _seed_meeting(db, "empty", has_segments=False)
    assert queue_after_save(db, "empty", auto_mode="every")["reason"] == "no_transcript"
    _seed_meeting(db, "every")
    assert queue_after_save(db, "every", auto_mode="every") == {"queued": True, "reason": "queued"}
    assert _jobs(db) == {"every": "queued"}
