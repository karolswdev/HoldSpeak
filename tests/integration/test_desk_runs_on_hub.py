"""Runs on, against a real hub: the hub half of the browser walks it replaces.

The test diet (2026-10-11): the browser walk of HS-201-09 checked the hub's
answers through the page. This file asks the same real hub (``_boot``: a
real MeetingWebServer, isolated HOME and DB) the same questions over HTTP,
in the order the Runs on face asks them, with the same local
OpenAI-compatible stub engine. No browser. The face's words for these
answers are fenced in web/src/desk/__tests__/runs-on.app.test.tsx.
"""
from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.engine_stub_rig import _StubHandler
from tests.e2e.glass_infra import _boot

TOKEN = "runs-on-hub"
SUMMARY_CAPABILITY = "meeting.deferred_analysis"
BAD_URL = "http://127.0.0.1:9/v1"  # discard port: always refuses

pytestmark = pytest.mark.timeout(120, method="thread")


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


@pytest.fixture()
def engine():
    """The same local stub the browser walk used when the LAN box was away."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _key_for(url: str, model: str = "") -> str:
    """endpointDraft.ts `endpointProfileId`: ``engine-<host-port slug>-<model slug>``
    (Betterment E3: one engine for each model; no model = the old host-only id)."""
    host = re.sub(r"[^a-z0-9]+", "-", url.split("://", 1)[1].split("/")[0].lower()).strip("-")
    name = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    return (f"engine-{host}-{name}" if name else f"engine-{host}")[:96].rstrip("-")


def _rows(base: str) -> dict[str, dict]:
    return {row["id"]: row for row in _ok(base, "GET", "/api/inference/assignments")["rows"]}


def _summary_task(base: str) -> dict:
    roster = _ok(base, "GET", "/api/inference/assignments")
    return next(t for t in roster["task_overrides"] if t["id"] == SUMMARY_CAPABILITY)


def _summary(base: str) -> dict:
    return _ok(base, "GET", "/api/concierge/detect")["summaryAssignment"]


def test_a_stranger_connects_an_engine_and_the_hub_keeps_his_choice(hub: str, engine: str) -> None:
    """replaces: tests/e2e/test_hs201_09_connect_engine_glass.py::TestConnectAnEngineFromTheFace::test_a_stranger_connects_an_engine_and_the_face_keeps_his_choice (hub half)

    Add engine -> bad address refused -> Check READY with the model -> Add
    (no wire) -> patch Meetings (the exact summary row) -> patch the Default
    -> Undo, Undo (summary back to inheritance) -> patch again over the
    tombstone.
    """
    base = hub
    key = _key_for(engine, _StubHandler.MODEL)

    # Nothing is assigned on this desk yet.
    assert _summary(base)["status"] == "unassigned"

    # A bad address: refused with a plain reason, never the socket's words.
    status, refused = _call(base, "POST", "/api/setup/discover-models", {"base_url": BAD_URL, "check_tools": True})
    assert status == 422 and refused["ok"] is False and refused["models"] == [], refused
    assert refused["detail"], refused
    assert "errno" not in refused["detail"].lower() and "urlopen" not in refused["detail"].lower(), refused

    # The engine's address: READY, and the model it serves is named.
    checked = _ok(base, "POST", "/api/setup/discover-models", {"base_url": engine, "check_tools": True})
    assert checked["ok"] is True and checked["models"] == [_StubHandler.MODEL], checked

    # Add: the Model Library defines it (endpointDraft.ts body); no assignment.
    host_port = engine.split("://", 1)[1].split("/")[0]
    defined = _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {
            "request_id": "runs-on-hub-add", "profile_id": key, "expected_profile_revision": 0,
            "label": host_port, "provider_family": "openai_compatible", "model": _StubHandler.MODEL,
            "endpoint": engine, "requires_key": False, "context_tokens": None,
        },
        "secret": None,
    })
    assert defined["provider"]["profile_id"] == key, defined
    revision = int(defined["provider"]["profile_revision"])
    assert revision >= 1
    detected = _ok(base, "GET", "/api/concierge/detect")
    assert any(e.get("profileId") == key for e in detected["engines"]), detected["engines"]
    wired = [
        row["id"] for row in _rows(base).values()
        if (row.get("assignment") or {}).get("entries")
        and row["inherited_from"] != "global"
        and any(e["profile_id"] == key for e in row["assignment"]["entries"])
    ]
    assert wired == [], f"an Add drew a wire: {wired}"

    # Patch Meetings: the group chain, then the exact summary row the queue reads.
    meetings = _rows(base)["meetings"]
    _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "runs-on-hub-meetings", "expected_revision": meetings["expected_revision"],
        "scope": {"kind": "group", "group_id": "meetings"},
        "entries": [{"profile_id": key, "profile_revision": revision}],
    })
    before = _summary(base)
    chosen = _ok(base, "POST", "/api/concierge/summary-selection", {
        "commandId": "runs-on-hub-summary", "expectedAssignmentRevision": before["assignmentRevision"],
        "profileId": key, "profileRevision": revision,
    })
    assert chosen["result"]["state"] == "READY", chosen
    assigned = _summary(base)
    assert assigned["status"] == "assigned" and assigned["profileId"] == key, assigned
    assert int(assigned["profileRevision"]) >= 1

    # Patch the Default for AI work.
    default = _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "runs-on-hub-default", "expected_revision": _rows(base)["global"]["expected_revision"],
        "scope": {"kind": "global"},
        "entries": [{"profile_id": key, "profile_revision": revision}],
    })
    assert default["scope"] == {"kind": "global"}, default
    assert [e["profile_id"] for e in default["entries"]] == [key], default

    # Undo, Undo: the Default, then Meetings and its summary row (inherited
    # before, so cleared back to inheritance, never re-written).
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-default", "expected_revision": _rows(base)["global"]["expected_revision"],
        "scope": {"kind": "global"}, "capability_id": "ask.answer",
    })
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-meetings", "expected_revision": _rows(base)["meetings"]["expected_revision"],
        "scope": {"kind": "group", "group_id": "meetings"}, "capability_id": SUMMARY_CAPABILITY,
    })
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-summary", "expected_revision": _summary(base)["assignmentRevision"],
        "scope": {"kind": "capability", "capability_id": SUMMARY_CAPABILITY},
        "capability_id": SUMMARY_CAPABILITY,
    })
    assert _summary_task(base)["has_override"] is False

    # Back ON over the tombstone: the cleared row's revision does not refuse it.
    tombstone = _summary(base)["assignmentRevision"]
    assert tombstone >= 1, "the clear left no tombstone revision to present"
    again = _ok(base, "POST", "/api/concierge/summary-selection", {
        "commandId": "runs-on-hub-summary-again", "expectedAssignmentRevision": tombstone,
        "profileId": key, "profileRevision": revision,
    })
    assert again["result"]["state"] == "READY", again
    back_on = _summary(base)
    assert back_on["status"] == "assigned" and back_on["profileId"] == key, back_on


# ── the hub's answers the face replays (PHILO-17 test diet, final lane A) ──
#
# SCAR LAW: the vitest successors in web/src/desk/__tests__/runs-on.app.test.tsx
# ("recorded hub") read these answers as their `fetch` answers. Each run asks
# the real hub again and fails when a stored answer's SHAPE is not the hub's
# (tests/integration/test_desk_agents_wire._same_shape). HOLDSPEAK_WIRE_WRITE=1
# rewrites them, scrubbed of this run's paths and ports.

import os  # noqa: E402
import re  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from http.server import BaseHTTPRequestHandler  # noqa: E402

from tests.integration.test_desk_agents_wire import _same_shape, _scrub, _shape  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TRUTH_DIR = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "runs-on-truth"
#: Every stored answer names the stub engine at this address.
STUB_HOST = "127.0.0.1:8099"
#: The reads Runs on makes when it opens and after each write (useRunsOn).
FACE_READS = ("/api/inference/assignments", "/api/concierge/detect", "/api/memory/meaning-search",
              "/api/setup/local-ai", "/api/concierge/speech")  # speech: RECIPE LINE-6's Phone speech group
TOOLS_MODEL = "stub-qwen"


class _ToolsEngine(BaseHTTPRequestHandler):
    """The PHILO-15 10 stub: /models, /props with tool support, a 1-token chat."""

    def _json(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path.endswith("/models"):
            self._json({"object": "list", "data": [{"id": TOOLS_MODEL, "object": "model"}]})
        elif path.endswith("/props"):
            self._json({"chat_template_caps": {"supports_tools": True}})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._json({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    def log_message(self, *_args: Any) -> None:
        return


@pytest.fixture()
def tools_engine():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ToolsEngine)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture()
def hub_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """(base, tmp_path): a hub whose HOME the recorder can scrub."""
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base, tmp_path
    finally:
        server.stop()


def _stub_scrub(value: Any, engine: str | None) -> Any:
    if not engine:
        return value
    port = engine.split("://", 1)[1].split("/")[0].split(":")[1]
    text = json.dumps(value)
    text = text.replace(f"127.0.0.1:{port}", STUB_HOST).replace(f"127-0-0-1-{port}", "127-0-0-1-8099")
    return json.loads(text)


def _record(scenario: str, name: str, payload: Any, tmp_path: Path, base: str, engine: str | None = None) -> None:
    """Store (or fence) one of the hub's answers under fixtures/runs-on-truth/<scenario>/<name>.json."""
    scrubbed = _stub_scrub(_scrub(payload, tmp_path, base), engine)
    path = TRUTH_DIR / scenario / f"{name}.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "_": f"The hub's own answer, captured by {Path(__file__).relative_to(REPO)}; "
                 "HOLDSPEAK_WIRE_WRITE=1 rewrites it.",
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "wire": scrubbed,
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    diffs = _same_shape(_shape(json.loads(path.read_text())["wire"]), _shape(scrubbed))
    assert not diffs, f"{scenario}/{name}: the stored answer is not the hub's shape: {diffs[:10]}"


def _record_reads(scenario: str, stage: str, base: str, tmp_path: Path, engine: str | None = None) -> dict[str, Any]:
    out = {}
    for path in FACE_READS:
        out[path] = _ok(base, "GET", path)
        _record(scenario, f"{stage}{path.replace('/', '_')}", out[path], tmp_path, base, engine)
    return out


def test_ready_means_ready_and_a_default_engine_is_limited_where_it_serves_part(hub_dir, tools_engine: str) -> None:
    """replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestEngineTruth::test_ready_means_ready_and_every_press_leaves_a_receipt (hub half)

    Check -> the server's tool answer; Add -> defined, no wire; patch the
    Default -> the hub's default is set; Agents is LIMITED (never READY) and
    no proposed row is READY while blocked; speech never routes to a preset.
    The face half replays these answers (runs-on.app.test.tsx, recorded hub).
    """
    base, tmp_path = hub_dir
    engine = tools_engine
    key = _key_for(engine, TOOLS_MODEL)
    _ok(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _record_reads("engine-truth", "0-open", base, tmp_path, engine)

    checked = _ok(base, "POST", "/api/setup/discover-models", {"base_url": engine, "check_tools": True})
    assert checked["ok"] is True and checked["models"] == [TOOLS_MODEL] and checked["tools"] == "yes", checked
    _record("engine-truth", "check", checked, tmp_path, base, engine)

    host_port = engine.split("://", 1)[1].split("/")[0]
    defined = _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {
            "request_id": "engine-truth-add", "profile_id": key, "expected_profile_revision": 0,
            "label": host_port, "provider_family": "openai_compatible", "model": TOOLS_MODEL,
            "endpoint": engine, "requires_key": False, "context_tokens": None,
        },
        "secret": None,
    })
    _record("engine-truth", "define", defined, tmp_path, base, engine)
    revision = int(defined["provider"]["profile_revision"])
    added = _record_reads("engine-truth", "1-added", base, tmp_path, engine)
    assert any(e.get("profileId") == key for e in added["/api/concierge/detect"]["engines"])

    patched = _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "engine-truth-default", "expected_revision": _rows(base)["global"]["expected_revision"],
        "scope": {"kind": "global"}, "entries": [{"profile_id": key, "profile_revision": revision}],
    })
    assert patched["scope"] == {"kind": "global"}, patched
    _record("engine-truth", "set-default", patched, tmp_path, base, engine)
    after = _record_reads("engine-truth", "2-patched", base, tmp_path, engine)

    assert _ok(base, "GET", "/api/settings/hub")["models"]["defaultSet"] is True
    engine_row = next(e for e in after["/api/concierge/detect"]["engines"] if e.get("profileId") == key)
    fits = engine_row["fits"]
    assert fits["agents_tools"]["state"] == "LIMITED", fits
    assert fits["thoughts_notes"]["state"] == "READY", fits
    rows = _ok(base, "POST", "/api/concierge/propose")["rows"]
    assert not [r for r in rows if r["state"] == "READY" and r.get("blocked")], rows
    speech = next(r for r in rows if r["group"] == "speech_recognition")
    assert not str(speech.get("engineId") or "").startswith("preset:"), speech


def test_a_record_less_engine_is_on_the_board_with_no_revision_and_the_hub_refuses_a_write_for_it(
    hub_dir, tools_engine: str,
) -> None:
    """replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestTwoFailures::test_every_failed_group_is_named_with_its_token (hub half)

    A hand-made endpoint record from before the Model Library answers, and
    has no model record: detect names it with no profile revision (the face
    refuses the drop on that, features/runson/model.ts accepts), and a write
    for it is refused by the authority, so nothing is written.
    """
    from holdspeak.db import get_database

    base, tmp_path = hub_dir
    _ok(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    get_database().profiles.upsert(
        profile_id="old-box", name="Old box", kind="openAICompatible", base_url=tools_engine, model=TOOLS_MODEL,
    )
    reads = _record_reads("no-record", "0-open", base, tmp_path, tools_engine)
    old = next(e for e in reads["/api/concierge/detect"]["engines"] if e.get("profileId") == "old-box")
    assert not old.get("profileRevision"), old

    before = _rows(base)
    status, refused = _call(base, "POST", "/api/inference/assignments/set", {
        "command_id": "no-record-write", "expected_revision": before["thoughts_notes"]["expected_revision"],
        "scope": {"kind": "group", "group_id": "thoughts_notes"},
        "entries": [{"profile_id": "old-box", "profile_revision": 0}],
    })
    assert status >= 400, (status, refused)
    after = _rows(base)
    assert after["thoughts_notes"]["assignment"] == before["thoughts_notes"]["assignment"], after["thoughts_notes"]


def test_an_anthropic_profile_is_a_service_on_the_hub(hub_dir) -> None:
    """replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_the_runs_on_anthropic_plate_reads_not_supported_yet (hub half)

    Betterment E4 (DECISIONS #9): Anthropic runs through its OpenAI-compatible
    endpoint. The glass's two legacy cloud profiles through the real detect:
    with no key held, both read NOT_SET (a key to add), never NOT_SUPPORTED.
    """
    from holdspeak.db import get_database

    base, tmp_path = hub_dir
    _ok(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    db = get_database()
    db.profiles.upsert(profile_id="cloud-anthropic", name="Claude", kind="openAICompatible",
                       base_url="https://api.anthropic.com/v1", model="claude-sonnet", requires_key=True)
    db.profiles.upsert(profile_id="cloud-openrouter", name="OpenRouter Qwen", kind="openAICompatible",
                       base_url="https://openrouter.ai/api/v1", model="qwen/qwen3", requires_key=True)
    reads = _record_reads("anthropic", "0-open", base, tmp_path)
    claude = next(e for e in reads["/api/concierge/detect"]["engines"] if e.get("profileId") == "cloud-anthropic")
    assert claude["state"] == "NOT_SET", claude


def test_an_engine_whose_server_stops_reads_not_answering_by_the_name_he_gave_it(hub_dir) -> None:
    """W1-TRUTH (atlas 2026-10-27): "It says Ready; the server is off." "Two
    names for one engine."

    He adds an engine named Studio engine and makes it the default; its
    server stops; Check all (detect) reads it UNREACHABLE, by his name, with
    the model id as its own field. The face half replays these answers
    (runs-on.app.test.tsx "an engine whose server stopped").
    """
    base, tmp_path = hub_dir
    _ok(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ToolsEngine)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    engine = f"http://127.0.0.1:{server.server_address[1]}/v1"
    key = _key_for(engine, TOOLS_MODEL)
    try:
        defined = _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
            "draft": {
                "request_id": "engine-down-add", "profile_id": key, "expected_profile_revision": 0,
                "label": "Studio engine", "provider_family": "openai_compatible", "model": TOOLS_MODEL,
                "endpoint": engine, "requires_key": False, "context_tokens": None,
            },
            "secret": None,
        })
        revision = int(defined["provider"]["profile_revision"])
        _ok(base, "POST", "/api/inference/assignments/set", {
            "command_id": "engine-down-default", "expected_revision": _rows(base)["global"]["expected_revision"],
            "scope": {"kind": "global"}, "entries": [{"profile_id": key, "profile_revision": revision}],
        })
        up = next(e for e in _ok(base, "GET", "/api/concierge/detect")["engines"] if e.get("profileId") == key)
        assert up["state"] == "READY", up
    finally:
        server.shutdown()
        server.server_close()

    reads = _record_reads("engine-down", "0-down", base, tmp_path, engine)
    down = next(e for e in reads["/api/concierge/detect"]["engines"] if e.get("profileId") == key)
    assert down["state"] == "UNREACHABLE", down
    assert down["name"] == "Studio engine", down
    assert down["modelId"] == TOOLS_MODEL, down
    editor = _ok(base, "POST", "/api/inference/assignments/editor", {"scope": {"kind": "global"}, "capability_id": "ask.answer"})
    _record("engine-down", "editor-default", editor, tmp_path, base, engine)
