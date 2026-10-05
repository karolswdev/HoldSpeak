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


# ── 4. the summary backlog ────────────────────────────────────────────────


def _jobs(db: Database) -> dict[str, str]:
    with db._connection() as conn:
        rows = conn.execute("SELECT meeting_id, status FROM intel_jobs").fetchall()
    return {str(r["meeting_id"]): str(r["status"]) for r in rows}


def _set_ended(db: Database, meeting_id: str, when: datetime) -> None:
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET ended_at=? WHERE id=?", (when.isoformat(), meeting_id))


def _backlog(db: Database, *, auto: str = "every", limit: int = 10, now=None) -> MeetingSummaryBacklog:
    return MeetingSummaryBacklog(
        lambda: db, auto_mode=lambda: auto, limit=limit,
        clock=(lambda: now) if now else datetime.now,
    )


def test_meetings_saved_before_an_engine_are_queued_once_it_has_one(tmp_path: Path) -> None:
    db = Database(tmp_path / "backlog.db")
    base = datetime.now() - timedelta(days=3)
    for index in range(3):
        _seed_meeting(db, f"m{index}")
        _set_ended(db, f"m{index}", base + timedelta(hours=index))
    _seed_meeting(db, "empty", has_segments=False)
    backlog = _backlog(db)

    assert backlog.tick() == {"status": "no_engine"}  # no engine: nothing queued
    assert _jobs(db) == {}

    assign_meeting_engine(db)  # the engine arrives
    result = backlog.tick()
    assert result["status"] == "queued"
    assert result["queued"] == ["m2", "m1", "m0"]  # newest first, oldest last
    assert _jobs(db) == {"m0": "queued", "m1": "queued", "m2": "queued"}
    with db._connection() as conn:
        reasons = {r[0] for r in conn.execute("SELECT intel_status_detail FROM meetings WHERE id LIKE 'm%'")}
        events = conn.execute(
            "SELECT COUNT(*) FROM service_events WHERE event_type='meeting.auto_intel_enqueued'"
        ).fetchone()[0]
    assert reasons == {BACKLOG_REASON}
    assert events == 3

    # Idempotent: the next ticks queue nothing more.
    assert backlog.tick() == {"status": "idle"}
    assert _backlog(db).tick()["queued"] == []  # a fresh hub process: still nothing


def test_the_backlog_is_bounded_per_tick_and_drains_oldest_last(tmp_path: Path) -> None:
    db = Database(tmp_path / "bounded.db")
    base = datetime.now() - timedelta(days=10)
    for index in range(5):
        _seed_meeting(db, f"m{index}")
        _set_ended(db, f"m{index}", base + timedelta(days=index))
    assign_meeting_engine(db)
    backlog = _backlog(db, limit=2)
    assert backlog.tick()["queued"] == ["m4", "m3"]
    assert backlog.tick()["queued"] == ["m2", "m1"]
    assert backlog.tick()["queued"] == ["m0"]
    assert backlog.tick() == {"status": "idle"}


def test_a_meeting_saved_after_the_engine_arrived_is_not_backlog(tmp_path: Path) -> None:
    db = Database(tmp_path / "after.db")
    gained = datetime.now() - timedelta(hours=1)
    _seed_meeting(db, "before")
    _set_ended(db, "before", gained - timedelta(hours=1))
    _seed_meeting(db, "after")
    _set_ended(db, "after", gained + timedelta(minutes=5))
    assign_meeting_engine(db)
    assert _backlog(db, now=gained).tick()["queued"] == ["before"]


def test_the_backlog_follows_intelligence_auto(tmp_path: Path) -> None:
    db = Database(tmp_path / "auto.db")
    _seed_meeting(db, "linked")
    _seed_meeting(db, "loose")
    _seed_project(db, "room")
    _link_meeting_project(db, "linked", "room")
    assign_meeting_engine(db)
    assert _backlog(db, auto="off").tick()["queued"] == []
    assert _backlog(db, auto="room_linked").tick()["queued"] == ["linked"]
    assert set(_jobs(db)) == {"linked"}


def test_a_failed_or_summarised_meeting_is_never_requeued(tmp_path: Path) -> None:
    db = Database(tmp_path / "done.db")
    _seed_meeting(db, "ready")
    _seed_meeting(db, "fresh")
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET intel_status='ready' WHERE id='ready'")
    assign_meeting_engine(db)
    assert _backlog(db).tick()["queued"] == ["fresh"]
