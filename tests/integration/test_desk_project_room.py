"""The Project Room on the hub: the T1 successors of the Room's browser walks.

The test diet (PHILO-17, 2026-10-11). Each test below asserts, against the
hub's REAL routers (the full ``MeetingWebServer`` app through a
``TestClient``, no uvicorn, no browser), the hub facts a Room browser walk
asserted. The words the face draws stay with the face's vitest file; what
the hub says, stores and sends is here.

The rig: an isolated HOME, the hub's own database file in ``tmp_path``, the
same isolation switches the glass rig sets (``tests/e2e/glass_infra._boot``),
and no real network. A model is a fake OpenAI-compatible HTTP server on
127.0.0.1; GitHub is a fake at the ``gh`` boundary; nothing reaches the LAN.
"""
from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest

pytestmark = [pytest.mark.timeout(240)]

TOKEN = "desk-project-room"
PURPOSE = "Architecture review, cut-over sequencing"


# ── the rig: one hub, in process, on an isolated HOME ────────────────


@dataclass
class Hub:
    server: Any
    client: Any
    tmp_path: Path

    @property
    def db(self) -> Any:
        from holdspeak.db import get_database

        return get_database()

    @property
    def home(self) -> Path:
        return self.tmp_path / "home"

    def ok(self, method: str, path: str, body: Any = None) -> dict[str, Any]:
        resp = self.client.request(method, path, json=body)
        assert resp.status_code < 400, f"{method} {path} -> {resp.status_code}: {resp.text}"
        return resp.json()

    def kernel_ops(self) -> list[tuple[str, str]]:
        conn = sqlite3.connect(str(self.tmp_path / "holdspeak.db"))
        try:
            rows = conn.execute(
                "SELECT name, state FROM kernel_operations WHERE name LIKE 'inference%' ORDER BY created_at"
            ).fetchall()
        finally:
            conn.close()
        return [(str(r[0]), str(r[1])) for r in rows]


def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The glass rig's isolation (tests/e2e/glass_infra.py `_boot`), no browser."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    keyfile = home / "people.key"
    if not keyfile.exists():
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
    for name, value in {
        "HOME": str(home),
        "HOLDSPEAK_MACOS_CALENDAR": "0",
        "HOLDSPEAK_AGENT_STATE": "off",
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOLDSPEAK_TEST_NO_REAL_CLI": "1",
        "GH_CONFIG_DIR": str(home / ".config" / "gh"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "HOLDSPEAK_DESKTOP_NOTIFY": "0",
        "HOLDSPEAK_CHANNEL_KEYSTORE_FILE": str(home / "channel-keys.json"),
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(keyfile),
        "CLAUDE_CONFIG_DIR": str(home / ".claude"),
        "CODEX_HOME": str(home / ".codex"),
        "PI_CODING_AGENT_DIR": str(home / ".pi" / "agent"),
        "HOLDSPEAK_ACTIVE_TARGET": "off",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    monkeypatch.setattr(db_core, "_db", None, raising=False)
    monkeypatch.setattr(db_core, "_observer", None, raising=False)
    return home


@contextlib.contextmanager
def _hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, gh_runner: Any = None, lifespan: bool = False,
    acli_runner: Any = None,
) -> Iterator[Hub]:
    """The hub's whole app. ``lifespan`` runs its startup (the PR poll, the
    intel drainer) for the legs that need the hub's own timers."""
    from starlette.testclient import TestClient

    from holdspeak.db import reset_database
    from holdspeak.runtime import composition
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    _isolate(tmp_path, monkeypatch)
    kwargs: dict[str, Any] = {"gh_runner": gh_runner} if gh_runner is not None else {}
    if acli_runner is not None:
        kwargs["acli_runner"] = acli_runner
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
        **kwargs,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    try:
        if lifespan:
            with client:
                yield Hub(server, client, tmp_path)
        else:
            yield Hub(server, client, tmp_path)
    finally:
        client.close()
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── the preparation brief (HS-200-11): seeds, the fake model, the route ──
#
# Copied from tests/e2e/test_hs200_preparation_brief_glass.py (plain Python):
# the four Watches with their recorded facts, the current + superseded
# decision, and the fake OpenAI-compatible server.


def _seed_watch(
    db: Any, project_id: str, connector: str, query_kind: str, query: dict[str, Any], *,
    snapshot: dict[str, Any] | None = None, last_success_at: str | None = None,
    next_evaluation_at: str | None = None, last_error: str | None = None,
) -> str:
    watch_id = f"w_{connector}_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    with db._connection() as conn:
        db.automations.create_watch_in_transaction(
            conn, watch_id=watch_id, connector_id=connector, query_kind=query_kind,
            name=f"{connector} {query_kind}", query_json=json.dumps(query, sort_keys=True),
            enabled=True, schema_version="WatchSpec@1", project_id=project_id, intent="Track",
            subject_kind=query_kind, trigger_kind="poll", trigger_json="{}", mode="yolo",
            state="active", revision=1, baseline_state="", test_state="",
            created_at=now_iso, updated_at=now_iso,
        )
        conn.execute(
            """UPDATE connector_watches
               SET snapshot_json = ?, last_success_at = ?, next_evaluation_at = ?, last_error = ?
               WHERE id = ?""",
            (json.dumps(snapshot) if snapshot is not None else None,
             last_success_at, next_evaluation_at, last_error, watch_id),
        )
    return watch_id


def _seed_brief_room(hub: Hub, command_id: str) -> str:
    """The HS-200-11 Room: GitHub read, Jira stale, Confluence credential
    failed, the meeting Watch read; one current and one superseded decision."""
    from holdspeak.services.watch_service import ensure_meeting_watch

    project_id = hub.ok("POST", "/api/projects", {
        "name": "Q4 platform", "description": "Seeded for the HS-200-11 proof.", "command_id": command_id,
    })["project"]["id"]
    db = hub.db
    meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    current, old = f"decrec_cur_{uuid.uuid4().hex[:8]}", f"decrec_old_{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, title, started_at, ended_at, created_at) VALUES (?, ?, ?, ?, ?)",
                     (meeting_id, "Cut-over sync", now_iso, now_iso, now_iso))
        conn.execute("INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
                     (meeting_id, project_id))
        for rid, text, lifecycle in (
            (current, "Cut-over runs on the read replica first", "active"),
            (old, "Cut-over runs under a full freeze", "superseded"),
        ):
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, lifecycle, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, ?, 'meeting', ?, ?, ?)""", (rid, text, lifecycle, meeting_id, now_iso, now_iso))
            conn.execute(
                """INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""", (f"src_{rid}", rid, meeting_id, now_iso))
        conn.execute(
            """INSERT INTO decision_record_revisions (id, record_id, field_name, old_value, new_value, created_at)
               VALUES (?, ?, 'successor_id', NULL, ?, ?)""", (f"rev_{old}", old, current, now_iso))

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    fresh = (now - timedelta(minutes=2)).isoformat(timespec="seconds")
    ahead = (now + timedelta(hours=1)).isoformat(timespec="seconds")
    _seed_watch(db, project_id, "gh", "pull_requests", {"repository": "karolswdev/HoldSpeak"},
                snapshot={"entities": {"pr_1": {"state": "open", "title": "Cut-over runbook"},
                                       "pr_2": {"state": "open", "title": "Replica failover"}}},
                last_success_at=fresh, next_evaluation_at=ahead)
    _seed_watch(db, project_id, "jira", "issues",
                {"projects": ["KAN"], "connection_ref": "acme.atlassian.net|me@acme.com"},
                snapshot={"entities": {}},
                last_success_at=(now - timedelta(hours=20)).isoformat(timespec="seconds"),
                next_evaluation_at=(now - timedelta(hours=19)).isoformat(timespec="seconds"))
    _seed_watch(db, project_id, "confluence", "pages", {"connection_ref": "acme.atlassian.net|me@acme.com"},
                last_success_at=(now - timedelta(hours=1)).isoformat(timespec="seconds"),
                last_error="Confluence rejected the token (401)")
    meeting_watch = ensure_meeting_watch(db, project_id)
    assert meeting_watch and meeting_watch.get("id"), meeting_watch
    with db._connection() as conn:
        conn.execute(
            """UPDATE connector_watches SET last_success_at = ?, snapshot_json = ?,
               next_evaluation_at = ?, last_error = NULL WHERE id = ?""",
            (fresh, json.dumps({"entities": {}}), ahead, meeting_watch["id"]),
        )
    return project_id


class FakeLLM:
    """An OpenAI-compatible server on 127.0.0.1: answers every POST with a
    chat completion carrying ``reply`` (a callable gets the request body)."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.reply: Any = "{}"
        self.delay_s = 0.0
        self.status = 200
        self.answered = threading.Event()  # a POST's answer was written (or its caller had gone)
        probe = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:
                pass

            def _send(self, body: dict[str, Any], status: int = 200) -> None:
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:
                probe.requests.append({"method": "GET", "path": self.path})
                self._send({"data": [{"id": "qwen3-35b", "object": "model"}], "object": "list"})

            def do_POST(self) -> None:
                n = int(self.headers.get("content-length") or 0)
                body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
                probe.requests.append({"method": "POST", "path": self.path, "body": body})
                if probe.delay_s:
                    time.sleep(probe.delay_s)
                try:
                    if probe.status != 200:
                        self._send({"error": {"message": "server exploded"}}, probe.status)
                        return
                    text = probe.reply(body) if callable(probe.reply) else str(probe.reply)
                    self._send({
                        "id": "cmpl-1", "object": "chat.completion", "model": "qwen3-35b",
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                     "finish_reason": "stop"}],
                        "content": text,
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    })
                finally:
                    probe.answered.set()

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"

    @property
    def posts(self) -> list[dict[str, Any]]:
        return [r for r in self.requests if r["method"] == "POST"]

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def llm() -> Iterator[FakeLLM]:
    server = FakeLLM()
    try:
        yield server
    finally:
        server.stop()


def _define_route(home: Path, endpoint: str, profile_id: str, *, requires_key: bool = False) -> None:
    """A real endpoint profile through the product's model-library and
    assignment services, assigned to the brief capability."""
    from holdspeak.config import Config
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.preparation_brief_service import PREPARATION_BRIEF_CAPABILITY

    owner = Principal(PrincipalKind.OWNER, "desk-project-room")
    db = get_database()
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: home)
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=home / "models", home_provider=lambda: home,
    )
    ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).define_endpoint(
        owner,
        {
            "request_id": f"room-endpoint-{profile_id}", "profile_id": profile_id,
            "expected_profile_revision": 0, "label": f"Probe {profile_id}",
            "provider_family": "openai_compatible" if requires_key else "private_endpoint",
            "model": "qwen3-35b", "endpoint": endpoint, "requires_key": requires_key,
        },
        {"value": "sk-room-key"} if requires_key else None,
    )
    assignments = InferenceAssignmentService(db)
    for scope_name, scope in (("global", {"kind": "global"}),
                              ("capability", {"kind": "capability", "capability_id": PREPARATION_BRIEF_CAPABILITY})):
        assignments.set_assignment(owner, {
            "command_id": f"room-{scope_name}-{profile_id}", "expected_revision": 0,
            "scope": scope, "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })


def _board_reply(body: str) -> str:
    """The board's claim mix, cited to the REAL refs the prompt carried."""
    prompt = json.loads(body).get("messages", [{}])[-1].get("content", "") if body.startswith("{") else body
    refs = re.findall(r"(decision_record:[A-Za-z0-9_]+|source:[A-Za-z0-9_]+)", prompt)
    current = next((r for r in refs if "decrec_cur_" in r), "")
    old = next((r for r in refs if "decrec_old_" in r), "")
    gh = next((r for r in refs if r.startswith("source:w_gh_")), "")
    return json.dumps({
        "priorities": [
            {"text": "Cut-over runs on the read replica first", "cited_refs": [current]},
            {"text": "Cut-over runs under a full freeze", "cited_refs": [old]},
            {"text": "Two open pull requests wait on the runbook", "cited_refs": [gh]},
            {"text": "Rehearse the rollback on the replica", "cited_refs": [gh]},
            {"text": "Extra priority four", "cited_refs": [gh]},
            {"text": "Extra priority five", "cited_refs": [gh]},
        ],
        "questions": [
            {"text": "Priya expects the cut-over at 95% by 2026-12-31", "cited_refs": [gh]},
            {"text": "Sprint velocity improved over the trailing average", "cited_refs": []},
        ],
        "obligations": [],
    })




def _claims(brief: dict[str, Any]) -> list[dict[str, Any]]:
    return list(json.loads(brief.get("claims_json") or "[]"))


def _refused(resp: Any) -> dict[str, Any]:
    """A refused preparation: 409 with the route state AND the purpose."""
    assert resp.status_code == 409, f"{resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("purpose") == PURPOSE, body
    return body


def test_a_brief_is_drafted_over_the_wire_kept_and_reread_with_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """A real dispatch to the fake model: the claims on three axes with typed
    unknowns, the superseded decision kept out of the document, what the
    bound left out, the two unread sources; Keep flips the same row once;
    re-read by id the brief carries its frozen manifest.

    replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read
    """
    llm.reply = _board_reply
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_brief_room(hub, "room-brief-kept")
        _define_route(hub.home, llm.endpoint, "probe-llm")
        route = hub.ok("GET", f"/api/projects/{project_id}/briefs/route")["route"]
        assert (route["state"], route["model"], route["host"]) == ("ready", "QWEN3 35B", "127.0.0.1"), route
        before = hub.ok("GET", f"/api/projects/{project_id}/briefs/manifest")["manifest"]
        assert before["coverage"] == {"expected": 4, "available": 2, "complete": False}, before["coverage"]
        assert llm.posts == [], "the route probe and the manifest send nothing"

        brief = hub.ok("POST", f"/api/projects/{project_id}/briefs/prepare",
                       {"purpose": PURPOSE, "attempt_id": "att_kept"})["brief"]
        assert len(llm.posts) == 1, llm.requests
        assert "read replica" in llm.posts[0]["body"], "the decision travelled in the prompt"
        assert hub.kernel_ops()[-1] == ("inference.invoke", "succeeded"), hub.kernel_ops()
        assert brief["lifecycle"] == "draft" and brief["manifest_revision"] == 1, brief
        assert (brief["generator_model"], brief["generator_host"]) == ("QWEN3 35B", "127.0.0.1"), brief

        # The document is the bounded outline; the superseded decision and
        # the priorities over the bound are not lines of it.
        doc = brief["body_md"]
        assert "Sprint velocity improved" in doc, doc
        assert "full freeze" not in doc and "Extra priority" not in doc, doc

        claims = _claims(brief)
        listed = [c for c in claims if c["section"] != "superseded"]
        superseded = [c for c in claims if c["section"] == "superseded"]
        assert [c["kind"] for c in listed] == ["decision"] + ["inference"] * 4, listed
        assert [c["support"] for c in listed] == ["supported"] + ["source_linked"] * 3 + ["unknown"], listed
        assert [c["acceptance"] for c in listed] == ["accepted"] + ["unreviewed"] * 4, listed
        unknowns = {(u["type"], u["value"]) for c in listed for u in c.get("unknowns", [])}
        assert {("deadline", "2026-12-31"), ("number", "95%")} <= unknowns, unknowns
        assert not [u for u in unknowns if u[0] == "name"], "no known person on this desk: no NAME unknown"
        assert [c["refs"] for c in listed if c["support"] == "unknown"] == [[]], "NO SOURCE is a claim with no ref"
        assert len(superseded) == 1 and "full freeze" in superseded[0]["text"], superseded

        manifest = brief["manifest"]
        assert len(manifest["not_included"]) == 2, manifest["not_included"]
        assert sorted(o["state"] for o in manifest["omitted"]) == ["failed", "stale"], manifest["omitted"]
        assert sorted(s["state"] for s in manifest["sources"] if s["state"] == "available") == ["available"] * 2

        # Keep: the same row flips; a second Keep writes nothing.
        kept = hub.ok("POST", f"/api/briefs/{brief['id']}/keep")["brief"]
        assert (kept["id"], kept["lifecycle"]) == (brief["id"], "kept"), kept
        listed_kept = hub.ok("GET", f"/api/projects/{project_id}/briefs?lifecycle=kept")["briefs"]
        hub.ok("POST", f"/api/briefs/{brief['id']}/keep")
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs?lifecycle=kept")["briefs"] == listed_kept
        assert hub.client.post(f"/api/briefs/{brief['id']}/discard").status_code == 409, "a kept brief is not discarded"

        # Re-read by id: the frozen manifest, verified.
        again = hub.ok("GET", f"/api/briefs/{brief['id']}")["brief"]
        assert (again["lifecycle"], again["integrity"], again["project_id"]) == ("kept", "verified", project_id)
        frozen = again["manifest"]
        assert frozen["coverage"] == {"expected": 4, "available": 2, "complete": False}
        assert sorted(d["lifecycle"] for d in frozen["decisions"]) == ["current", "superseded"]
        assert next(d for d in frozen["decisions"] if d["lifecycle"] == "superseded")["successor_ref"]
        assert frozen["calendar"] == {"present": False}
        assert again["generator_host"] == "127.0.0.1"


def test_an_unreachable_model_refuses_keeps_the_purpose_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A closed port: READY before the run (the probe sends nothing); the run
    is refused ENDPOINT UNREACHABLE with the purpose back, the receipt says a
    request left (a kernel operation exists), and no brief row is written.

    replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_unavailable_model_refuses_and_keeps_the_purpose
    """
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_brief_room(hub, "room-brief-closed")
        _define_route(hub.home, "http://127.0.0.1:1/v1", "closed-port")
        route = hub.ok("GET", f"/api/projects/{project_id}/briefs/route")["route"]
        assert (route["state"], route["host"], route["model"], route["boundary"]) == (
            "ready", "127.0.0.1", "QWEN3 35B", "private_network"), route

        body = _refused(hub.client.post(f"/api/projects/{project_id}/briefs/prepare",
                                        json={"purpose": PURPOSE, "attempt_id": "att_closed"}))
        refused = body["route"]
        assert (refused["state"], refused["token"]) == ("unreachable", "ENDPOINT UNREACHABLE"), refused
        assert refused["invoke"]["sent"] is True and refused["invoke"]["operation_id"], refused["invoke"]
        assert refused["invoke"]["host"] == "127.0.0.1", refused["invoke"]
        assert refused["invoke"]["outcome"] != "succeeded", refused["invoke"]
        assert (refused["model"], refused["repair"]) == ("QWEN3 35B", "Set up model"), refused
        ops = hub.kernel_ops()
        assert ops and ops[-1][0] == "inference.invoke", ops
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs")["briefs"] == []
        # A failed run clears no known gap: the coverage is what it was.
        manifest = hub.ok("GET", f"/api/projects/{project_id}/briefs/manifest")["manifest"]
        assert manifest["coverage"] == {"expected": 4, "available": 2, "complete": False}


def test_a_sent_and_answered_request_is_sent_never_nothing_sent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """P0: the model answers prose. The kernel operation SUCCEEDED, so the
    refusal's receipt says the request was sent and answered (the face's
    `SENT · 127.0.0.1 · NOTHING USABLE RECEIVED`), never NOTHING SENT; an HTTP
    500 from the target is still sent, not answered.

    replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_a_sent_and_answered_request_is_never_reported_as_nothing_sent
    """
    llm.reply = "Sure! Here is a brief in prose: decide the cut-over window today."
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_brief_room(hub, "room-brief-prose")
        _define_route(hub.home, llm.endpoint, "probe-llm")
        refused = _refused(hub.client.post(f"/api/projects/{project_id}/briefs/prepare",
                                           json={"purpose": PURPOSE, "attempt_id": "att_prose"}))["route"]
        assert len(llm.posts) == 1, llm.requests
        assert hub.kernel_ops()[-1] == ("inference.invoke", "succeeded"), hub.kernel_ops()
        assert (refused["state"], refused["token"]) == ("unusable_output", "OUTPUT UNUSABLE"), refused
        assert refused["invoke"]["sent"] is True, refused["invoke"]
        assert refused["invoke"]["outcome"] == "succeeded", refused["invoke"]
        assert refused["invoke"]["host"] == "127.0.0.1", refused["invoke"]
        assert refused["invoke"]["operation_id"], refused["invoke"]
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs")["briefs"] == []

        llm.status = 500
        refused = _refused(hub.client.post(f"/api/projects/{project_id}/briefs/prepare",
                                           json={"purpose": PURPOSE, "attempt_id": "att_500"}))["route"]
        assert refused["invoke"]["sent"] is True and refused["invoke"]["host"] == "127.0.0.1", refused["invoke"]
        assert refused["invoke"]["outcome"] != "succeeded", refused["invoke"]
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs")["briefs"] == []


def test_a_hosted_endpoint_without_its_key_is_key_not_set_before_a_byte_leaves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real hosted endpoint; the owner removes its key from the slot the
    runner reads: the route reads KEY NOT SET, Prepare is refused 409, no
    kernel operation exists and nothing is written.

    replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_a_hosted_endpoint_without_its_key_is_key_not_set
    """
    from holdspeak.profile_key_store import _default_profile_key_store

    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_brief_room(hub, "room-brief-key")
        _define_route(hub.home, "https://api.example.test/v1", "hosted-llm", requires_key=True)
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs/route")["route"]["state"] == "ready"
        with hub.db._connection() as conn:
            slot = conn.execute(
                "SELECT secret_slot FROM deployment_revisions WHERE secret_slot != '' ORDER BY rowid DESC LIMIT 1"
            ).fetchone()[0]
        _default_profile_key_store().delete(slot)
        route = hub.ok("GET", f"/api/projects/{project_id}/briefs/route")["route"]
        assert (route["state"], route["token"]) == ("key_missing", "KEY NOT SET"), route
        assert (route["host"], route["model"], route["repair"]) == ("api.example.test", "QWEN3 35B", "Set up model")

        refused = _refused(hub.client.post(f"/api/projects/{project_id}/briefs/prepare",
                                           json={"purpose": PURPOSE}))["route"]
        assert refused["state"] == "key_missing" and refused["invoke"]["sent"] is False, refused
        assert hub.kernel_ops() == [], "no request may leave without the key"
        assert hub.ok("GET", f"/api/projects/{project_id}/briefs")["briefs"] == []


def test_stop_cancels_the_run_and_leaves_no_orphan_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """The model takes 3 s; Stop lands at 0.5 s. The run comes back STOPPED with
    a receipt that the request had left, and no draft is written, also after
    the slow answer arrives (fast diet 2026-10-12: was 8 s and 1 s, waited out
    by a fixed sleep; now the test waits for the answer itself).

    replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_stop_leaves_no_orphan_draft
    """
    llm.reply = _board_reply
    llm.delay_s = 3.0
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_brief_room(hub, "room-brief-stop")
        _define_route(hub.home, llm.endpoint, "probe-llm")
        answer: dict[str, Any] = {}

        def prepare() -> None:
            answer["resp"] = hub.client.post(f"/api/projects/{project_id}/briefs/prepare",
                                             json={"purpose": PURPOSE, "attempt_id": "att_stop"})

        run = threading.Thread(target=prepare)
        run.start()
        deadline = time.monotonic() + 10
        while not llm.posts and time.monotonic() < deadline:
            time.sleep(0.05)
        assert llm.posts, "the request never left"
        time.sleep(0.5)
        stopped = hub.ok("POST", f"/api/projects/{project_id}/briefs/stop", {"attempt_id": "att_stop"})
        assert stopped["stopped"] is True and stopped["attempt_id"] == "att_stop", stopped
        run.join(30)
        assert not run.is_alive(), "the prepare never returned"
        refused = _refused(answer["resp"])["route"]
        assert refused["state"] == "stopped", refused
        assert refused["invoke"]["sent"] is True, "the face says the request had left"
        assert llm.answered.wait(10), "the slow answer never left the model"
        time.sleep(0.5)  # the slow answer lands after the stop
        listed = hub.ok("GET", f"/api/projects/{project_id}/briefs")["briefs"]
        assert listed == [], [(b["id"], b["lifecycle"]) for b in listed]


# ── deliveries: an UNKNOWN file send is never a delivery (PHILO-10-01) ──


def _long_folder(root: Path) -> Path:
    """A folder the OS accepts whose path leaves no room for the send's file name."""
    import os

    limit = os.pathconf("/", "PC_PATH_MAX")
    folder = root.resolve()
    while len(str(folder)) < limit - 25:
        folder = folder / ("a" * min(100, limit - 25 - len(str(folder)) - 1 or 1))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _file_send(hub: Hub, document_ref: str, name: str, folder: Path) -> Any:
    dest = hub.ok("POST", "/api/channels/destinations",
                  {"name": name, "channel": "file", "folder": str(folder)})["destination"]["id"]
    send_id = hub.ok("POST", "/api/channels/sends",
                     {"document_ref": document_ref, "destination_id": dest})["send"]["id"]
    return hub.client.post("/api/channels/send", json={"send_id": send_id})


def test_a_file_send_the_os_refuses_by_name_length_settles_unknown_not_delivered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two saved folder destinations; one folder leaves no room for the file's
    name, so the OS refuses the create with ENAMETOOLONG (off the pinned
    FAILED list). That send settles UNKNOWN with no proof, and the update's
    delivery history carries it as `unknown`, never as a delivery.

    replaces: tests/e2e/test_philo10_01_unknown_send_face.py::TestUnknownSendFace::test_an_unknown_send_is_never_shown_as_delivered (the hub half; the chips are the face's)
    """
    with _hub(tmp_path, monkeypatch) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Payments ledger cutover"})["project"]["id"]
        uid = hub.ok("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})["update"]["id"]
        hub.ok("PUT", f"/api/updates/{uid}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})
        hub.ok("POST", f"/api/updates/{uid}/publish", {})
        (tmp_path / "out").mkdir()
        ok = _file_send(hub, f"project_update:{uid}", "Team folder", tmp_path / "out")
        bad = _file_send(hub, f"project_update:{uid}", "Long path folder", _long_folder(tmp_path / "deep"))

        assert ok.status_code == 200 and ok.json()["send"]["state"] == "sent", ok.text
        assert Path(ok.json()["send"]["proof"]["path"]).is_file(), ok.json()["send"]
        unknown = bad.json()["send"]
        assert unknown["state"] == "unknown", bad.text
        assert not unknown.get("proof_json") and not unknown.get("proof"), unknown
        updates = hub.ok("GET", f"/api/projects/{pid}/updates")["updates"]
        history = next(u for u in updates if u["id"] == uid)["deliveries"]
        assert [(d["delivered_to"], d["outcome"]) for d in history] == [
            ("Team folder", "sent"), ("Long path folder", "unknown")], history


def test_manual_model_draft_refuses_then_deliberate_retry_and_steward_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The owner's press is strict; steward service calls keep the fallback."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime import composition
    from holdspeak.services.project_update_service import (
        ProjectUpdateService, _ModelDraftFailed,
    )

    with _hub(tmp_path, monkeypatch) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Strict draft"})["project"]["id"]

        def fail_model(self: Any, *args: Any, **kwargs: Any) -> Any:
            raise _ModelDraftFailed("fixture model failure")

        monkeypatch.setattr(ProjectUpdateService, "_draft_with_model", fail_model)
        refused = hub.client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "model", "command_id": "manual-strict-model"},
        )
        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "project_update_model_failed"

        retried = hub.client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic", "command_id": "manual-deterministic-retry"},
        )
        assert retried.status_code == 200, retried.text
        assert retried.json()["update"]["generator"] == "deterministic"

        fallback = composition.current().project_update_service.draft_update(
            Principal(PrincipalKind.OWNER, TOKEN), pid, generator="model",
        )
        assert fallback["generator"] == "deterministic"
        assert fallback["fallback_reason"] == "model_unavailable"


def test_a_slow_model_draft_never_freezes_the_hub_and_a_bad_answer_says_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """P0 (betterment/projects): Draft update runs off the event loop. While a
    slow engine thinks, /health answers at once; the engine's prose (not the
    update JSON) comes back 409 not_usable with the reason in plain words,
    and the failed command keeps that reason."""
    llm.reply = "Here is your update. Progress is good this week."
    llm.delay_s = 4.0
    # lifespan: ONE event loop serves every request, as on the real hub.
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Slow engine"})["project"]["id"]
        _define_route(hub.home, llm.endpoint, "slow-llm")

        answer: dict[str, Any] = {}

        def press() -> None:
            resp = hub.client.post(
                f"/api/projects/{pid}/updates/draft",
                json={"generator": "model", "command_id": "p0-slow-draft"},
            )
            answer["status"], answer["body"] = resp.status_code, resp.json()

        drafting = threading.Thread(target=press)
        drafting.start()
        deadline = time.monotonic() + 10
        while not llm.posts and time.monotonic() < deadline:
            time.sleep(0.05)
        assert llm.posts, "the draft reached the engine"

        started = time.monotonic()
        health = hub.client.get("/health")
        took = time.monotonic() - started
        assert health.status_code == 200, health.text
        assert took < 1.0, f"/health took {took:.2f} s while the draft ran"
        assert drafting.is_alive(), "the draft was still running when /health answered"

        drafting.join(timeout=30)
        assert answer["status"] == 409, answer
        body = answer["body"]
        assert (body["code"], body["reason"]) == ("project_update_model_failed", "not_usable"), body
        assert body["detail"] == "it did not return JSON", body
        command = hub.db.projects.get_project_command("p0-slow-draft")
        assert command and (command["status"], command["error_code"]) == ("failed", "not_usable"), command
        assert hub.ok("GET", f"/api/projects/{pid}/updates")["updates"] == [], "nothing is saved"


# ── Betterment P1: Write update, the records draft first, the engine after ──

ENGINE_UPDATE = json.dumps({"sections": [
    {"key": "progress", "sentences": [{"text": "The ledger cutover is on track for Thursday.", "cited_refs": []}]},
    {"key": "risks_blockers", "sentences": [{"text": "Card tokenization waits on the HSM key ceremony.", "cited_refs": []}]},
]})


def _poll_job(hub: Hub, job_id: str, *, until: tuple[str, ...], timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        job = hub.ok("GET", f"/api/update-jobs/{job_id}")["job"]
        if job["state"] in until or time.monotonic() > deadline:
            return job
        time.sleep(0.1)


def test_write_update_saves_the_records_draft_then_the_engine_improves_it_in_the_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """Betterment P1: the press saves the records draft at once; the engine
    pass runs as a job the face polls, off the request loop; its draft becomes
    the next revision only on apply; Undo is the records draft again."""
    llm.reply = ENGINE_UPDATE
    llm.delay_s = 3.0
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Write update"})["project"]["id"]
        _define_route(hub.home, llm.endpoint, "p1-llm")

        started = time.monotonic()
        records = hub.ok("POST", f"/api/projects/{pid}/updates/draft",
                         {"generator": "deterministic", "command_id": "p1-records"})["update"]
        assert time.monotonic() - started < 1.0
        assert records["generator"] == "deterministic"

        job = hub.ok("POST", f"/api/updates/{records['id']}/engine-pass")["job"]
        assert (job["state"], job["base_update_id"]) == ("running", records["id"]), job
        deadline = time.monotonic() + 10
        while not llm.posts and time.monotonic() < deadline:
            time.sleep(0.05)
        assert llm.posts, "the pass reached the engine"
        t0 = time.monotonic()
        assert hub.client.get("/health").status_code == 200
        assert time.monotonic() - t0 < 1.0, "the hub answers while the engine works"
        assert hub.ok("GET", f"/api/update-jobs/{job['id']}")["job"]["state"] == "running"
        # Nothing is saved until the face applies it.
        assert [u["id"] for u in hub.ok("GET", f"/api/projects/{pid}/updates")["updates"]] == [records["id"]]

        done = _poll_job(hub, job["id"], until=("succeeded", "failed"))
        assert done["state"] == "succeeded", done
        assert "The ledger cutover is on track for Thursday." in done["body_md"]
        assert done["generator_model"]  # the engine that wrote it, for "Written by"

        applied = hub.ok("POST", f"/api/update-jobs/{job['id']}/apply", {})["update"]
        assert applied["generator"].startswith("model:") and applied["draft_revision"] == 2
        assert "The ledger cutover is on track for Thursday." in applied["body_md"]
        # The coverage is still the record of what was read, not the engine's prose.
        assert "## Source Coverage" in applied["body_md"]
        assert hub.ok("GET", f"/api/update-jobs/{job['id']}")["job"]["state"] == "applied"

        undo = hub.ok("POST", f"/api/projects/{pid}/updates/draft",
                      {"generator": "deterministic", "command_id": "p1-undo"})["update"]
        assert (undo["generator"], undo["draft_revision"]) == ("deterministic", 3)


@pytest.mark.parametrize("owner_edits", [False, True])
@pytest.mark.parametrize("tool_writes", [False, True])
def test_project_write_runs_its_existing_workbench_and_keeps_one_delivered_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner_edits: bool, tool_writes: bool,
) -> None:
    """P7/P8: the Room's manual Write uses the one project automation.

    The local engine leaf replays the repository's existing Workbench fixture
    response.  The route, assignment resolver, Workbench runner, artifact
    mint, project delivery, and update job are real; the fixture is only the
    provider answer and makes no model quality or live-provider claim.
    """
    from tests.e2e.glass_infra import assign_engine, engine_profile

    fixture = json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "automations" / "engine_replies.json").read_text()
    )["weekly_update"]
    calls: list[dict[str, Any]] = []
    import threading
    entered = threading.Event()
    released = threading.Event()

    class RecordedFixtureEngine:
        active_provider = "fixture"
        active_model = "recorded-workbench-fixture"
        last_usage: dict[str, int] = {}

        def run_prompt(self, *, system_prompt: str, user_prompt: str, temperature: Any = None,
                       max_tokens: Any = None, **_kwargs: Any) -> str:
            calls.append({"system": system_prompt, "user": user_prompt,
                          "temperature": temperature, "max_tokens": max_tokens})
            self.last_usage = {"total_tokens": 40}
            if owner_edits:
                entered.set()
                assert released.wait(timeout=10), "owner-edit probe did not release the engine"
            if tool_writes:
                from holdspeak.services import run_trace
                from holdspeak.services.engine_tool_loop import call_tool
                item_id = run_trace.current_item()
                assert item_id, "the Workbench did not bind its item trace"
                reply = json.loads(call_tool(
                    "fixture-update-run", run_trace.item_trace(item_id),
                    "project.update_draft", {"update_id": records["id"],
                        "body_md": fixture, "source_refs": [f"project:{project_id}"]},
                    1, allow_project_update=True, project_id=project_id,
                ))
                assert "error" not in reply, reply
                written_ids.append(reply["update"]["id"])
            return fixture

    written_ids: list[str] = []
    engine = RecordedFixtureEngine()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **_kwargs: engine,
    )

    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        # Use the real local profile/deployment and assignment helpers.  The
        # test leaf is the only provider boundary replaced.
        engine_profile(automation=True)
        assign_engine("workbench.item", 11)
        assign_engine("project.update_draft", 12)
        from holdspeak.kernel.runtime import _service

        # The profile and assignment stay real.  This is the existing
        # Workbench fixture seam for a local recorded leaf; WorkbenchService,
        # WorkbenchRunner, delivery, and the route dispatcher remain live.
        broker = _service()
        monkeypatch.setattr(broker.inference_runner, "_engine_factory",
                            lambda _revision, **_kwargs: engine)

        project_id = hub.ok("POST", "/api/projects", {
            "name": "Ledger cutover", "command_id": "p7-real-write",
        })["project"]["id"]
        from holdspeak.meeting_session import MeetingState, TranscriptSegment

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        linked_meeting = MeetingState(
            id="m-ledger-sync", started_at=now - timedelta(minutes=30),
            ended_at=now - timedelta(minutes=10), title="Ledger project sync",
            segments=[TranscriptSegment(
                text="The ordinary project sync confirms the ledger cutover is ready.",
                speaker="Mira", start_time=1.0, end_time=4.0,
            )], intel_status="completed",
        )
        private_one_on_one = MeetingState(
            id="m-mira-private-1on1", started_at=now - timedelta(minutes=20),
            ended_at=now - timedelta(minutes=5), title="1:1 with Mira",
            segments=[TranscriptSegment(
                text="PRIVATE_ONE_ON_ONE_TEXT: Mira's promotion concern stays private.",
                speaker="Mira", start_time=1.0, end_time=4.0,
            )], intel_status="completed",
        )
        hub.db.meetings.save_meeting(linked_meeting)
        hub.db.meetings.save_meeting(private_one_on_one)
        hub.ok("POST", f"/api/projects/{project_id}/meetings/{linked_meeting.id}")
        hub.ok("POST", f"/api/projects/{project_id}/meetings/{private_one_on_one.id}")
        records = hub.ok(
            "POST", f"/api/projects/{project_id}/updates/draft",
            {"generator": "deterministic", "command_id": "p7-records"},
        )["update"]
        automations = [
            wb for wb in hub.db.workbenches.list()
            if wb.output_target == f"project_updates:{project_id}"
        ]
        assert len(automations) == 1, automations
        automation = automations[0]
        assert automation.id == f"project-update-{project_id}"

        # This is the exact Room API payload: the existing automation ID is
        # carried into the manual Write engine pass.
        job = hub.ok(
            "POST", f"/api/updates/{records['id']}/engine-pass",
            {"automation_id": automation.id},
        )["job"]
        if owner_edits:
            assert entered.wait(timeout=10), "the real automation did not reach its engine"
            try:
                hub.ok("PUT", f"/api/updates/{records['id']}", {"body_md": "My own Friday words."})
            finally:
                released.set()
        done = _poll_job(hub, job["id"], until=("succeeded", "failed"), timeout=45)
        if owner_edits:
            refused = hub.client.post(f"/api/update-jobs/{job['id']}/apply", json={})
            assert refused.status_code == 409 and refused.json()["code"] == "draft_changed", refused.text
            assert hub.ok("GET", f"/api/updates/{records['id']}")["update"]["body_md"] == "My own Friday words."
        diagnostic_items = hub.db.workbench_items.list_for_workbench(automation.id)
        diagnostic_runs = hub.db.workbench_runs.list_for_workbench(automation.id)
        assert done["state"] == "succeeded", (
            f"job={done!r}; calls={calls!r}; item={diagnostic_items[0].to_dict() if diagnostic_items else None!r}; "
            f"run={diagnostic_runs[0].to_dict() if diagnostic_runs else None!r}"
        )
        assert len(calls) == 1, calls
        assert "The ordinary project sync confirms" in calls[0]["user"]
        assert "PRIVATE_ONE_ON_ONE_TEXT" not in calls[0]["user"]
        assert private_one_on_one.id not in calls[0]["user"]

        # The Workbench produced exactly one terminal run, one occurrence and
        # one minted artifact before the project delivery was applied.
        runs = hub.db.workbench_runs.list_for_workbench(automation.id)
        assert len(runs) == 1 and runs[0].status == "completed", runs
        items = hub.db.workbench_items.list_for_workbench(automation.id)
        assert len(items) == 1 and items[0].status == "done", items
        assert items[0].result_artifact_id
        artifact = hub.db.plugins.get_artifact(items[0].result_artifact_id)
        assert artifact is not None, items[0]
        assert json.loads(items[0].grounding_json) == {"refs": [f"project:{project_id}"]}

        delivered = hub.db.project_updates.list_updates(project_id)[0]
        assert delivered["id"] != records["id"]
        assert delivered["body_md"].rstrip() == fixture
        assert delivered["generator"].startswith("agent:")
        if tool_writes:
            assert written_ids == [delivered["id"]], written_ids
        manifest = json.loads(delivered["source_manifest_json"])
        assert manifest["agent_sources"] == [f"project:{project_id}"]
        assert private_one_on_one.id not in json.dumps(manifest)
        with hub.db._connection() as conn:
            result_json = conn.execute(
                "SELECT result_json FROM project_update_jobs WHERE id=?", (job["id"],)
            ).fetchone()["result_json"]
        result = json.loads(result_json)
        assert result["automation_id"] == automation.id
        assert result["automation_run_id"] == runs[0].id
        print("P7P8_REAL_ROUTE_PROOF", json.dumps({
            "automation_id": automation.id,
            "run_id": runs[0].id,
            "artifact_id": items[0].result_artifact_id,
            "job_id": job["id"],
            "update_id": delivered["id"],
            "source_refs": manifest["agent_sources"],
            "grounding_refs": json.loads(items[0].grounding_json)["refs"],
        }, sort_keys=True))

        applied = hub.ok("POST", f"/api/update-jobs/{job['id']}/apply", {"force": True} if owner_edits else {})["update"]
        assert applied["id"] == delivered["id"]
        assert len(hub.db.project_updates.list_updates(project_id)) == 2
        assert len([
            update for update in hub.db.project_updates.list_updates(project_id)
            if str(update["generator"]).startswith("agent:")
        ]) == 1

        # Friday changes the same Workbench record's When/With state.  The
        # newest Open payload is the delivered row, with no second automation.
        friday = hub.ok("PUT", f"/api/workbenches/{automation.id}", {
            "schedule": "0 15 * * 5", "schedule_enabled": True,
        })["workbench"]
        assert friday["id"] == automation.id
        assert friday["schedule"] == "0 15 * * 5" and friday["schedule_enabled"] is True
        room = hub.ok("GET", f"/api/projects/{project_id}/room")
        assert room["updates"]["automation"]["id"] == automation.id
        assert room["updates"]["automation"]["schedule"] == "0 15 * * 5"
        newest = hub.ok("GET", f"/api/projects/{project_id}/updates")["updates"][0]
        assert newest["id"] == delivered["id"] and newest["body_md"].rstrip() == fixture
        assert len([
            wb for wb in hub.db.workbenches.list()
            if wb.output_target == f"project_updates:{project_id}"
        ]) == 1


def test_project_update_run_credential_scopes_native_mcp_reads_and_draft_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real run credential exposes the update writer and the filtered reads."""
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.principals import agent_credentials
    from holdspeak.services.conductor_launch import RUN_IDENTITY_PREFIX
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        project_id = hub.ok("POST", "/api/projects", {"name": "Scoped update"})["project"]["id"]
        other_project = hub.ok("POST", "/api/projects", {"name": "Other project"})["project"]["id"]
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ordinary = MeetingState(
            id="m-scoped-ordinary", started_at=now - timedelta(minutes=20),
            ended_at=now - timedelta(minutes=10), title="Scoped project sync",
            segments=[TranscriptSegment(
                text="ORDINARY_PROJECT_TEXT: the cutover is ready.", speaker="Mira",
                start_time=1.0, end_time=4.0,
            )], intel_status="completed",
        )
        private = MeetingState(
            id="m-scoped-private", started_at=now - timedelta(minutes=18),
            ended_at=now - timedelta(minutes=8), title="1:1 with Mira",
            segments=[TranscriptSegment(
                text="PRIVATE_ONE_ON_ONE_TEXT: keep this private.", speaker="Mira",
                start_time=1.0, end_time=4.0,
            )], intel_status="completed",
        )
        hub.db.meetings.save_meeting(ordinary)
        hub.db.meetings.save_meeting(private)
        unlinked = MeetingState(
            id="m-scoped-unlinked", started_at=now - timedelta(minutes=16),
            ended_at=now - timedelta(minutes=6), title="Private catch-up",
            segments=[TranscriptSegment(
                text="UNLINKED_PRIVATE_TEXT: outside this project.", speaker="Noor",
                start_time=1.0, end_time=4.0,
            )], intel_status="completed",
        )
        hub.db.meetings.save_meeting(unlinked)
        hub.ok("POST", f"/api/projects/{project_id}/meetings/{ordinary.id}")
        hub.ok("POST", f"/api/projects/{project_id}/meetings/{private.id}")
        private_action_id = "a-scoped-private-filed"
        with hub.db._connection() as conn:
            conn.execute(
                """INSERT INTO action_items
                   (id, meeting_id, task, owner, status, review_state, created_at)
                   VALUES (?, ?, ?, ?, 'open', 'accepted', ?)""",
                (private_action_id, private.id, "PRIVATE_1TO1_OWED_ACTION", "Karol", now.isoformat()),
            )
        # An owner-filed action is an explicit project source. P2 keeps this
        # owed item while still withholding the 1:1 meeting itself.
        hub.db.project_relationships.upsert(
            project_id=project_id, resource_ref=f"action:{private_action_id}",
            relationship="source", source="manual",
        )
        records = hub.ok(
            "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"},
        )["update"]
        assert "PRIVATE_1TO1_OWED_ACTION" in records["body_md"]
        other_records = hub.ok(
            "POST", f"/api/projects/{other_project}/updates/draft", {"generator": "deterministic"},
        )["update"]

        run_id = "scoped-native-mcp-proof"
        credential = agent_credentials.issue(
            f"{RUN_IDENTITY_PREFIX}{run_id}",
            palette=resolve_palette(CONDUCTOR), palette_name=CONDUCTOR,
            launch_id=run_id, project_id=project_id,
        )

        def mcp(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
            response = hub.client.post(
                "/api/mcp", headers={"X-HoldSpeak-Token": credential.token},
                json={"jsonrpc": "2.0", "id": method, "method": method, "params": params or {}},
            )
            assert response.status_code == 200, response.text
            return response.json()

        def tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            return mcp("tools/call", {"name": name, "arguments": arguments})

        try:
            listed = mcp("tools/list")
            names = {row["name"] for row in listed["result"]["tools"]}
            assert "project.update_draft" in names
            assert not any(name.startswith("people.") for name in names)
            resources = mcp("resources/list")["result"]
            assert resources == {"resources": [], "resourceTemplates": []}
            raw_private = mcp("resources/read", {"uri": f"holdspeak://meetings/{private.id}"})
            assert raw_private["error"]["data"]["code"] == "MCP-005"
            assert "PRIVATE_ONE_ON_ONE_TEXT" not in json.dumps(raw_private)

            meetings = json.loads(tool("meeting.list", {})["result"]["content"][0]["text"])
            listed_ids = {row["id"] for row in meetings["meetings"]}
            assert ordinary.id in listed_ids and private.id not in listed_ids
            assert unlinked.id not in listed_ids
            assert tool("meeting.get", {"meeting_id": unlinked.id})["result"]["isError"]
            assert "ORDINARY_PROJECT_TEXT" not in json.dumps(meetings)
            private_reply = tool("meeting.get", {"meeting_id": private.id})
            assert private_reply["result"]["isError"]
            private_error = json.loads(private_reply["result"]["content"][0]["text"])
            assert "outside project update sources" in private_error["error"]
            ordinary_reply = tool("meeting.get", {"meeting_id": ordinary.id})
            assert "ORDINARY_PROJECT_TEXT" in ordinary_reply["result"]["content"][0]["text"]
            # The HTTP loop has no durable CLI credential, but it must use
            # the same restricted tools and keep positive project reads.
            from holdspeak.services.engine_tool_loop import call_tool
            http_ordinary = call_tool(
                "scoped-http-proof", "scoped-http-proof", "meeting.get",
                {"meeting_id": ordinary.id}, 1, allow_project_update=True,
                project_id=project_id,
            )
            assert "ORDINARY_PROJECT_TEXT" in http_ordinary
            http_unlinked = call_tool(
                "scoped-http-proof", "scoped-http-proof", "meeting.get",
                {"meeting_id": unlinked.id}, 3, allow_project_update=True,
                project_id=project_id,
            )
            assert "UNLINKED_PRIVATE_TEXT" not in http_unlinked
            assert "error" in json.loads(http_unlinked)
            http_people = call_tool(
                "scoped-http-proof", "scoped-http-proof", "people.relationship.list",
                {}, 2, allow_project_update=True, project_id=project_id,
            )
            assert "error" in json.loads(http_people), http_people

            saved = tool("project.update_draft", {
                "update_id": records["id"], "body_md": "Agent scoped words.",
                "source_refs": [
                    f"meeting:{ordinary.id}", f"meeting:{private.id}",
                    f"action_item:{private_action_id}",
                ],
            })
            assert not saved["result"]["isError"], saved
            saved_update = json.loads(saved["result"]["content"][0]["text"])["update"]
            assert saved_update["id"] != records["id"]
            assert hub.db.project_updates.get_update(records["id"])["body_md"] == records["body_md"]
            assert saved_update["body_md"].rstrip() == "Agent scoped words."
            manifest = json.loads(saved_update["source_manifest_json"])
            edited = tool("project.update_draft", {
                "update_id": saved_update["id"], "body_md": "Agent revised words.",
            })
            edited_update = json.loads(edited["result"]["content"][0]["text"])["update"]
            assert edited_update["id"] == saved_update["id"]
            assert f"action_item:{private_action_id}" in manifest["agent_sources"]
            assert f"meeting:{private.id}" not in manifest["agent_sources"]
            refused = tool("project.update_draft", {
                "update_id": other_records["id"], "body_md": "Wrong project words.",
            })
            assert refused["result"]["isError"]
            assert "outside the project update scope" in refused["result"]["content"][0]["text"]
        finally:
            agent_credentials.revoke(credential.principal.identity, "proof_done")


def test_the_engine_never_overwrites_his_words_and_a_failure_keeps_the_records_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    llm.reply = ENGINE_UPDATE
    with _hub(tmp_path, monkeypatch) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "His words"})["project"]["id"]
        _define_route(hub.home, llm.endpoint, "p1-words")
        records = hub.ok("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})["update"]
        job = hub.ok("POST", f"/api/updates/{records['id']}/engine-pass")["job"]
        hub.ok("PUT", f"/api/updates/{records['id']}", {"body_md": "My own words for Friday."})
        assert _poll_job(hub, job["id"], until=("succeeded", "failed"))["state"] == "succeeded"

        refused = hub.client.post(f"/api/update-jobs/{job['id']}/apply", json={})
        assert refused.status_code == 409 and refused.json()["code"] == "draft_changed", refused.text
        assert hub.ok("GET", f"/api/updates/{records['id']}")["update"]["body_md"] == "My own words for Friday."
        used = hub.ok("POST", f"/api/update-jobs/{job['id']}/apply", {"force": True})["update"]
        assert "The ledger cutover is on track for Thursday." in used["body_md"]

        # A failed pass: one reason in words; the records draft stays the draft.
        llm.reply = "Here is your update. Progress is good."
        records = hub.ok("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})["update"]
        job = hub.ok("POST", f"/api/updates/{records['id']}/engine-pass")["job"]
        failed = _poll_job(hub, job["id"], until=("succeeded", "failed"))
        assert (failed["state"], failed["reason"], failed["detail"]) == (
            "failed", "not_usable", "it did not return JSON"), failed
        drafts = hub.ok("GET", f"/api/projects/{pid}/updates?lifecycle=draft")["updates"]
        assert [d["id"] for d in drafts] == [records["id"]]
        assert hub.client.post(f"/api/update-jobs/{job['id']}/apply", json={}).status_code == 409

        # Stop: the late answer is dropped.
        llm.reply, llm.delay_s = ENGINE_UPDATE, 1.5
        job = hub.ok("POST", f"/api/updates/{records['id']}/engine-pass")["job"]
        stopped = hub.ok("POST", f"/api/update-jobs/{job['id']}/stop")["job"]
        assert (stopped["state"], stopped["reason"]) == ("stopped", "stopped")
        time.sleep(2.5)
        assert hub.ok("GET", f"/api/update-jobs/{job['id']}")["job"]["state"] == "stopped"
        assert hub.client.post(f"/api/update-jobs/{job['id']}/apply", json={"force": True}).status_code == 409


def test_a_hub_restart_ends_a_running_engine_pass_with_a_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Betterment P1: the pass's thread dies with the old process. On start
    the hub marks a job left running as failed, so the face shows Try again."""
    with _hub(tmp_path, monkeypatch) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Restart"})["project"]["id"]
        records = hub.ok("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})["update"]
        with hub.db._connection() as conn:  # a pass the old process left running
            conn.execute(
                "INSERT INTO project_update_jobs (id, project_id, base_update_id, state) VALUES (?, ?, ?, 'running')",
                ("pujob_left_running", pid, records["id"]),
            )
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        job = hub.ok("GET", "/api/update-jobs/pujob_left_running")["job"]
        assert (job["state"], job["reason"], job["detail"]) == (
            "failed", "did_not_answer", "the hub restarted"), job


# ── the merge receipt (PHILO-15 lane 17): the hub's own poll ─────────

MERGE_PROJECT = "proj-philo1517abcd"
MERGE_ACTION = "action_philo15_17"
MERGE_TASK = "Add a contributing file to the rehearsal repository with the three rules"
PR_TITLE = "Add CONTRIBUTING.md with the three pull request rules"
PR_URL = "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1"
MERGED_ROW = f"Merged: {PR_TITLE} (PR #1) {PR_URL}"


class FakeGitHub:
    """GitHub at the ``gh pr view`` boundary (the receipts' ``view_pr``):
    PR #1, open until the test merges it."""

    def __init__(self) -> None:
        self.state = "open"
        self.merged_at = ""
        self.views = 0

    def view_pr(self, source_id: str, url: str):
        self.views += 1
        merged = self.state == "merged"
        return {
            "url": PR_URL, "number": 1, "title": PR_TITLE, "state": self.state,
            "merged_at": self.merged_at if merged else "", "merged_sha": "f" * 40 if merged else "",
            "head_sha": "e" * 40, "review_decision": "", "ci": "none", "checks": [],
        }, "live"

    def merge(self) -> None:
        self.merged_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state = "merged"


def _seed_merge_launch(db: Any, launches: Path) -> None:
    """The Project, its action item, and the agent's launch with PR #1 open
    (cleanup already final, so the merge only closes the item)."""
    now = datetime.now(timezone.utc)
    with db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (MERGE_PROJECT, "Payments ledger cutover"))
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m-1517', ?, 'Payments ledger sync')",
                     ((now - timedelta(hours=1)).isoformat(),))
        conn.execute("INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m-1517', ?, 0.9)",
                     (MERGE_PROJECT,))
        conn.execute("INSERT INTO action_items (id, meeting_id, task, owner, status) VALUES (?, 'm-1517', ?, 'Me', 'open')",
                     (MERGE_ACTION, MERGE_TASK))
        conn.commit()
    launches.parent.mkdir(parents=True, exist_ok=True)
    launches.write_text(json.dumps({"launches_schema": 1, "launches": [{
        "launch_id": "launch-1517", "state": "registered", "attempt_id": "att-1517",
        "worktree_id": "wt-1517", "source_id": "src-1517", "launched_at": (now - timedelta(minutes=40)).isoformat(),
        "origin_ref": {"kind": "action", "id": MERGE_ACTION}, "profile_id": "codex-default",
        "follow_through": {
            "pr_state": "pr_open",
            "pr": {"url": PR_URL, "number": 1, "title": PR_TITLE, "state": "open"},
            "cleanup": {"session": "killed", "worktree": "worktree_kept_not_ours", "mcp": "released",
                        "gate": "not_armed"},
        },
    }]}), encoding="utf-8")


def test_the_hubs_poll_closes_the_item_on_merge_and_the_sent_update_carries_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PR #1 is open on the launch. GitHub merges it; nobody presses anything;
    the hub's own poll (1 s here) reads it, the flight reads merged by the
    PR's own title and the item is closed. The drafted update carries the
    Merged row; a line the model marked [UNVERIFIED] never reaches the sent
    file, which carries the Merged row.

    replaces: tests/e2e/test_philo15_17_merge_receipt_glass.py::TestMergeReachesTheUpdate::test_the_receipt_and_the_sent_update (the hub half; the receipt's words and Open PR are the face's)
    """
    from types import SimpleNamespace

    from holdspeak.delivery import factory_launch, follow_through
    from holdspeak.delivery.attempts import WorkAttemptService
    from holdspeak.delivery.factory_launch import LaunchLedger

    launches = tmp_path / "home" / ".holdspeak" / "agent_launches.json"
    github = FakeGitHub()
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
    monkeypatch.setattr(follow_through, "POLL_SECONDS", 0.3)  # fast diet: was 1 s
    monkeypatch.setattr(follow_through, "default_follow_through", lambda db: follow_through.FollowThroughObserver(
        db, ledger=LaunchLedger(launches), registry=SimpleNamespace(get=lambda _id: None), receipts=github,
        attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: "yolo",
    ))
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        _seed_merge_launch(hub.db, launches)

        def flight() -> dict[str, Any]:
            flights = hub.ok("GET", "/api/coders/sessions?include_ended=false")["flights"]
            assert len(flights) == 1, flights
            return flights[0]

        assert (flight()["state"], flight()["pr"]["title"]) == ("pr_open", PR_TITLE)
        github.merge()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and flight().get("close") != "closed":
            time.sleep(0.2)
        landed = flight()
        assert landed["state"] == "merged" and landed["close"] == "closed", landed
        assert landed["pr"] == {"number": 1, "url": PR_URL, "state": "merged", "title": PR_TITLE}, landed["pr"]
        with hub.db._connection() as conn:
            status = conn.execute("SELECT status FROM action_items WHERE id = ?", (MERGE_ACTION,)).fetchone()[0]
        assert status == "done", status

        drafted = hub.ok("POST", f"/api/projects/{MERGE_PROJECT}/updates/draft", {"generator": "deterministic"})["update"]
        assert MERGED_ROW in drafted["body_md"], drafted["body_md"]
        marked = drafted["body_md"].replace("## Dependencies\n\nNo dependencies tracked.",
                                            "## Dependencies\n\n- **[UNVERIFIED]** No dependencies tracked.", 1)
        assert "[UNVERIFIED]" in marked, drafted["body_md"]
        hub.ok("PUT", f"/api/updates/{drafted['id']}", {"body_md": marked})
        hub.ok("POST", f"/api/updates/{drafted['id']}/publish", {})
        folder = tmp_path / "sent"
        folder.mkdir()
        sent = _file_send(hub, f"project_update:{drafted['id']}", "Sent folder", folder)
        assert sent.status_code == 200 and sent.json()["send"]["state"] == "sent", sent.text
        [written] = list(folder.glob("*.md"))
        text = written.read_text(encoding="utf-8")
        assert MERGED_ROW in text, text
        assert text.startswith("# Payments ledger cutover · Update · "), text
        assert "UNVERIFIED" not in text and "No dependencies tracked." not in text, text
        assert text.rstrip().endswith("1 claim not checked, kept on the desk."), text
        assert "meeting_summary_unavailable" not in text


def test_the_merge_poll_tells_the_open_room_once_the_pr_merges_and_not_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mounted Room re-reads on a ``desk_changed`` frame whose changes are
    not windows only (web/src/desk/useDeskChangedRefresh.ts; the consumer half
    is roomInFlight.f2.test.tsx "the merge lands while the Room stays open").
    The hub's own PR poll (HeartbeatService.poll_open_prs) runs every 0.3 s:
    while PR #1 is open it sends no frame; once GitHub merges it, the poll
    sends ONE ``desk_changed`` frame. Frames are captured at the hub's
    WebSocket fan-out (``WebSocketManager.broadcast``), as every client gets them.

    replaces: tests/e2e/test_philo15_17_merge_receipt_glass.py::TestMergeReachesTheUpdate::test_the_receipt_and_the_sent_update (the no-press arrival)
    """
    from types import SimpleNamespace

    from holdspeak.delivery import factory_launch, follow_through
    from holdspeak.delivery.attempts import WorkAttemptService
    from holdspeak.delivery.factory_launch import LaunchLedger

    launches = tmp_path / "home" / ".holdspeak" / "agent_launches.json"
    github = FakeGitHub()
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
    monkeypatch.setattr(follow_through, "POLL_SECONDS", 0.3)  # fast diet: was 1 s
    monkeypatch.setattr(follow_through, "default_follow_through", lambda db: follow_through.FollowThroughObserver(
        db, ledger=LaunchLedger(launches), registry=SimpleNamespace(get=lambda _id: None), receipts=github,
        attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: "yolo",
    ))
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        frames: list[dict[str, Any]] = []
        fan_out = hub.server._ws.broadcast

        async def capture(message: Any) -> None:
            frames.append(message.to_dict())
            await fan_out(message)

        monkeypatch.setattr(hub.server._ws, "broadcast", capture)
        _seed_merge_launch(hub.db, launches)

        # The hub's other startup beats (the scheduled-recording reconcile, a
        # workbench tick) can land in this window on a busy worker; they are
        # not the PR poll's word and are left out (seen 2026-10-11 whenever
        # another hub test ran first in the same process).
        other_beats = {("scheduled_recording", "reconcile"), ("workbench", "tick")}

        def desk_changed() -> list[dict[str, Any]]:
            return [f for f in frames if f.get("type") == "desk_changed"
                    and not all((c.get("kind"), c.get("op")) in other_beats
                                for c in (f.get("data") or {}).get("changes") or [{}])]

        # PR #1 open: the poll reads it (one gh pr view a poll) and says nothing.
        frames.clear()
        views = github.views
        assert _wait(lambda: github.views >= views + 3, timeout=10), "the hub's poll never read the open PR"
        assert desk_changed() == [], desk_changed()

        github.merge()
        assert _wait(lambda: bool(desk_changed()), timeout=10), frames
        time.sleep(1.0)  # three more polls: the closed flight is not announced again
        [frame] = desk_changed()
        data = frame["data"]
        changes = data["changes"]
        # Not windows only, so the Room re-reads (isWindowsOnlyFrame is false).
        assert changes and all(c["kind"] != "windows" for c in changes), data
        assert data["origin"] == "hub", data
        # Completion names the actual changed row inside the poll's announce
        # scope. That suppresses its generic heartbeat fallback; one frame
        # still tells the open Room to re-read the merged flight.
        assert changes == [{"kind": "action_item", "id": "action_philo15_17", "op": "done"}], changes
        assert next(f for f in hub.ok("GET", "/api/coders/sessions?include_ended=false")["flights"])["close"] == "closed"


# ── the second morning (PHILO-15 lane 21) ───────────────────────────

MORNING_PROJECT = "prj-hygiene"
MORNING_REPO = "karolswdev/holdspeak-dayone-rehearsal-1558"


def _naive_utc(delta: timedelta) -> str:
    return (datetime.now(timezone.utc).replace(tzinfo=None) - delta).isoformat(timespec="seconds")


def _the_second_morning(db: Any) -> datetime:
    """Quiet hours that hold now (began 8 h ago); a GitHub Watch checked 10 h
    ago (fresh when quiet hours began), a meeting Watch checked 20 h ago
    (late before them); the real Heartbeat sweep runs and is held. Returns
    the quiet end."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.heartbeat_service import HeartbeatService

    db.projects.create_project(project_id=MORNING_PROJECT, name="Rehearsal repo hygiene")
    due = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")
    with db._connection() as conn:
        for wid, connector, kind, query, checked in (
            ("w-gh", "gh", "pull_requests", {"repository": MORNING_REPO}, timedelta(hours=10)),
            ("w-mtg", "meeting", "meetings", {"project_id": MORNING_PROJECT}, timedelta(hours=20)),
        ):
            conn.execute(
                "INSERT INTO connector_watches "
                "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, state, "
                " last_success_at, next_evaluation_at, project_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, '[]', 1, 'active', ?, ?, ?, datetime('now'), datetime('now'))",
                (wid, connector, kind, f"{connector} watch", json.dumps(query), _naive_utc(checked), due,
                 MORNING_PROJECT),
            )
    hour = datetime.now().astimezone().hour
    hb = HeartbeatService(db)
    hb.update_settings({"quiet_hours": {"start": (hour - 8) % 24, "end": (hour + 2) % 24}})
    receipt = hb.run_sweep(Principal(PrincipalKind.OWNER, "heartbeat-conductor"))
    assert receipt["held"] is True and receipt["quiet_hold"]["sources"] == 2, receipt
    return datetime.fromisoformat(receipt["quiet_hold"]["until"])


def test_quiet_hours_hold_github_uncounted_the_stale_meeting_counts_and_retry_rechecks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At seven: the GitHub source reads QUIET UNTIL <end> and is not counted;
    the meeting source reads STALE and is counted; Retry re-checks THAT source
    through the hub's single-Watch route and the count drops by one; the Room
    reads the quiet end, never a next check in the past.

    replaces: tests/e2e/test_philo15_21_morning_truth_glass.py::TestTheSecondMorning::test_needs_you_and_the_room_at_seven (the hub half; the rows' words and the receipt line are the face's)
    """
    from holdspeak.services.needs_you_membership import unread_sources

    with _hub(tmp_path, monkeypatch) as hub:
        quiet_end = _the_second_morning(hub.db)
        quiet = f"QUIET UNTIL {quiet_end.astimezone():%H:%M}"

        def rows() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
            wire = hub.ok("GET", "/api/desk/needs-you?fresh=1")
            by_id = {r.get("source_id"): r for r in wire["coverage"]}
            return wire, by_id

        before, by_id = rows()
        gh, mtg = by_id["watch:w-gh"], by_id["watch:w-mtg"]
        assert gh["state"] == "quiet" and gh["repair"]["token"] == quiet, gh
        assert gh["label"] == f"GitHub · {MORNING_REPO}", gh
        assert mtg["state"] == "stale" and mtg["label"] == "Meetings", mtg
        assert mtg["watch_ids"] == ["w-mtg"], mtg
        counted = {r.get("source_id") for r in unread_sources(before["coverage"])}
        assert "watch:w-mtg" in counted and "watch:w-gh" not in counted, counted

        retried = hub.client.post("/api/watches/w-mtg/evaluate")
        assert retried.status_code == 200, retried.text
        after, by_id = rows()
        assert by_id["watch:w-mtg"]["state"] == "available", by_id["watch:w-mtg"]
        assert by_id["watch:w-gh"]["state"] == "quiet", "the retry re-checks THAT source only"
        assert after["count"] == before["count"] - 1, (before["count"], after["count"])

        sources = hub.ok("GET", f"/api/projects/{MORNING_PROJECT}/room")["sources"]
        assert sources["quietUntil"], sources
        assert datetime.fromisoformat(sources["quietUntil"]) == quiet_end, sources
        assert datetime.fromisoformat(sources["nextCheckAt"]) > datetime.now(timezone.utc), sources


MODEL_BODY = "## Progress\n\n- The ledger moved to staging.\n- Carol is to add a CODEOWNERS file by Friday.\n"
MODEL_CLAIMS = [
    {"span_id": "s_progress_0", "text": "The ledger moved to staging.", "refs": ["item:hygiene"],
     "section": "progress", "kind": "inference", "support": "source_linked", "acceptance": "unreviewed"},
    {"span_id": "s_progress_1", "text": "Carol is to add a CODEOWNERS file by Friday.", "refs": ["item:hygiene"],
     "section": "progress", "kind": "inference", "support": "source_linked", "acceptance": "unreviewed"},
]


def test_accept_and_reject_in_the_editor_and_the_sent_text_keeps_the_accepted_claim_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The model's two inferences arrive unreviewed. The owner accepts one and
    rejects the other through the editor's route; the update is sendable and
    the channel preview carries the accepted claim only.

    replaces: tests/e2e/test_philo15_21_morning_truth_glass.py::TestTheOwnerReviewsEachClaim::test_accept_and_reject_in_the_editor (the hub half; OMITTED and REVIEWED are the face's words)
    """
    from holdspeak.services import project_update_service as pus

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        return MODEL_BODY, json.dumps(MODEL_CLAIMS), "model:ia_1", "192.168.1.43:8080", "qwen3.8-27b"

    monkeypatch.setattr(pus.ProjectUpdateService, "_draft_with_model", model)
    with _hub(tmp_path, monkeypatch) as hub:
        pid = hub.ok("POST", "/api/projects", {"name": "Rehearsal repo hygiene"})["project"]["id"]
        update = hub.ok("POST", f"/api/projects/{pid}/updates/draft", {"generator": "model"})["update"]
        uid = update["id"]
        assert [c["acceptance"] for c in json.loads(update["claims_json"])] == ["unreviewed", "unreviewed"]
        hub.ok("POST", f"/api/updates/{uid}/claims/s_progress_0/review", {"acceptance": "accepted"})
        rejected = hub.ok("POST", f"/api/updates/{uid}/claims/s_progress_1/review", {"acceptance": "rejected"})
        states = {c["span_id"]: c["acceptance"] for c in json.loads(rejected["update"]["claims_json"])}
        assert states == {"s_progress_0": "accepted", "s_progress_1": "rejected"}, states

        hub.ok("POST", f"/api/updates/{uid}/publish", {})
        folder = tmp_path / "sent"
        folder.mkdir()
        dest = hub.ok("POST", "/api/channels/destinations",
                      {"name": "Team folder", "channel": "file", "folder": str(folder)})["destination"]["id"]
        preview = hub.ok("POST", "/api/channels/preview",
                         {"document_ref": f"project_update:{uid}", "destination_id": dest})
        text = json.dumps(preview["preview"])
        assert "The ledger moved to staging." in text and "CODEOWNERS" not in text, text


# ── sources in the Room (PHILO-17 U10, U30) ──────────────────────────


def _gh_signed_in(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
    """gh signed in as acme with one repository; every list read is empty."""
    args = list(argv)
    if args[:3] == ["gh", "auth", "status"]:
        return subprocess.CompletedProcess(
            argv, 0, stdout="", stderr="github.com\n  Logged in to github.com account acme (keyring)\n")
    if args[:3] == ["gh", "repo", "list"]:
        return subprocess.CompletedProcess(
            argv, 0, stdout='[{"name":"app","owner":{"login":"acme"},"visibility":"PUBLIC"}]', stderr="")
    return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")


def _gh_not_signed_in(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
    if list(argv[:3]) == ["gh", "auth", "status"]:
        return subprocess.CompletedProcess(
            argv, 1, stdout="", stderr="You are not logged into any GitHub hosts. To log in, run: gh auth login\n")
    return subprocess.CompletedProcess(argv, 1, stdout="", stderr="not logged in")


GITHUB_SOURCE = {"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}


def test_project_door_preview_and_create_links_found_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real Door route checks pasted providers and files selected Found rows."""
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    owner = Principal(PrincipalKind.OWNER, "test")
    with _hub(tmp_path, monkeypatch, gh_runner=_gh_signed_in) as hub:
        db = hub.db
        started = datetime.now().replace(microsecond=0) - timedelta(hours=2)
        db.meetings.save_meeting(MeetingState(
            id="m-door-found",
            started_at=started,
            ended_at=started + timedelta(minutes=30),
            title="Payments migration review",
            segments=[TranscriptSegment(
                text="Payments migration is ready for the next cutover.",
                speaker="Mira Okafor",
                start_time=1.0,
                end_time=4.0,
            )],
            intel=IntelSnapshot(timestamp=1.0, topics=["payments"], summary="Cutover review."),
            intel_status="completed",
        ))
        note = PrimitiveService(db).create_note(
            owner, title="Payments migration risks", body_markdown="Review payments cutover risk.",
        )

        preview = hub.ok("POST", "/api/projects/door/preview", {
            "outcome": "Payments migration",
            "pasted": "github.com/acme/app https://wiki.example.com/spaces/PAYM",
        })
        assert [(row["provider"], row["state"]) for row in preview["sources"]] == [
            ("github", "checked"),
            ("confluence", "not_checked"),
        ], preview
        found_ids = {item["id"] for item in preview["found"]}
        assert {"m-door-found", note["id"]} <= found_ids, preview["found"]
        assert preview["people"] == ["Mira Okafor"], preview["people"]

        created = hub.ok("POST", "/api/projects/door", {
            "outcome": "Payments migration",
            "sources": [GITHUB_SOURCE],
            "found": {"meeting_ids": ["m-door-found"], "note_ids": [note["id"]]},
        })
        assert created["found_links"] == [
            {"kind": "meeting", "id": "m-door-found", "state": "linked", "error": None},
            {"kind": "note", "id": note["id"], "state": "linked", "error": None},
        ]
        project_id = created["projectId"]
        resources = hub.ok("GET", f"/api/projects/{project_id}/resources")["resources"]
        refs = {item["resource_ref"] for item in resources}
        assert "note:" + note["id"] in refs, refs
        assert any(item["resource_ref"] == "meeting:m-door-found" for item in resources), refs


def test_project_door_partial_found_link_reports_error_and_retries_durably(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A one-time leaf failure stays visible; Retry uses the existing Project.

    The hub, route, Door service, Project service and database are real.  The
    only seam is one note-link leaf failing once, so the meeting proves that a
    successful link is not retried or duplicated while the note is retried and
    read back from durable Project resources.
    """
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services import project_door_service as door_module
    from holdspeak.services.primitive_service import PrimitiveService

    owner = Principal(PrincipalKind.OWNER, "test")
    with _hub(tmp_path, monkeypatch, gh_runner=_gh_signed_in) as hub:
        db = hub.db
        started = datetime.now().replace(microsecond=0) - timedelta(hours=2)
        db.meetings.save_meeting(MeetingState(
            id="m-door-retry",
            started_at=started,
            ended_at=started + timedelta(minutes=30),
            title="Payments migration review",
            segments=[TranscriptSegment(
                text="Payments migration is ready for the next cutover.",
                speaker="Mira Okafor",
                start_time=1.0,
                end_time=4.0,
            )],
            intel=IntelSnapshot(timestamp=1.0, topics=["payments"], summary="Cutover review."),
            intel_status="completed",
        ))
        note = PrimitiveService(db).create_note(
            owner, title="Payments migration risks", body_markdown="Review payments cutover risk.",
        )
        door = __import__("holdspeak.runtime.composition", fromlist=["current"]).current().project_door_service
        project_service = door._project_service
        real_add_resource = project_service.add_resource
        failed_once = False

        def fail_note_once(principal: Any, project_id: str, resource_ref: str, *args: Any, **kwargs: Any) -> Any:
            nonlocal failed_once
            if resource_ref == f"note:{note['id']}" and not failed_once:
                failed_once = True
                raise door_module.ServiceError("note_store_unavailable", "Notes store is read-only")
            return real_add_resource(principal, project_id, resource_ref, *args, **kwargs)

        monkeypatch.setattr(project_service, "add_resource", fail_note_once)

        created = hub.ok("POST", "/api/projects/door", {
            "outcome": "Payments migration",
            "found": {"meeting_ids": ["m-door-retry"], "note_ids": [note["id"]]},
        })
        project_id = created["projectId"]
        assert created["found_links"] == [
            {"kind": "meeting", "id": "m-door-retry", "state": "linked", "error": None},
            {"kind": "note", "id": note["id"], "state": "failed", "error": "Notes store is read-only"},
        ]
        before = hub.ok("GET", f"/api/projects/{project_id}/resources")["resources"]
        before_refs = [row["resource_ref"] for row in before]
        assert before_refs.count("meeting:m-door-retry") == 1, before
        assert f"note:{note['id']}" not in before_refs, before

        retried = hub.ok("POST", "/api/projects/door", {
            "project_id": project_id,
            "sources": [],
            "found": {"meeting_ids": [], "note_ids": [note["id"]]},
        })
        assert retried["found_links"] == [
            {"kind": "note", "id": note["id"], "state": "linked", "error": None},
        ]
        after = hub.ok("GET", f"/api/projects/{project_id}/resources")["resources"]
        after_refs = [row["resource_ref"] for row in after]
        assert after_refs.count("meeting:m-door-retry") == 1, after
        assert after_refs.count(f"note:{note['id']}") == 1, after
        assert failed_once is True


def test_project_room_offers_unfiled_meeting_that_mentions_project_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Room producer offers a real transcript match until Add files it."""
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    with _hub(tmp_path, monkeypatch) as hub:
        project_id = hub.ok("POST", "/api/projects", {
            "name": "Payments migration", "command_id": "room-match-project",
        })["project"]["id"]
        started = datetime.now().replace(microsecond=0) - timedelta(hours=1)
        hub.db.meetings.save_meeting(MeetingState(
            id="m-room-match",
            started_at=started,
            ended_at=started + timedelta(minutes=20),
            title="Migration sync",
            segments=[TranscriptSegment(
                text="Payments migration needs a final owner before cutover.",
                speaker="Mira Okafor",
                start_time=1.0,
                end_time=4.0,
            )],
            intel_status="completed",
        ))

        before = hub.ok("GET", f"/api/projects/{project_id}/room")
        matches = [row for row in before["needsYou"]["items"] if row.get("kind") == "meeting_match"]
        assert len(matches) == 1, before["needsYou"]
        assert matches[0]["meeting_id"] == "m-room-match"
        assert matches[0]["title"] == "mentions payments"
        hub.ok("POST", f"/api/projects/{project_id}/meetings/m-room-match")

        after = hub.ok("GET", f"/api/projects/{project_id}/room")
        assert not [row for row in after["needsYou"]["items"] if row.get("kind") == "meeting_match"]


def test_a_repository_added_in_the_room_stays_and_the_same_one_again_is_already_watched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bare project from the Door; the Room's Add source posts the Door's
    rows with the project's id; the repository is the project's source on the
    next read (a reload) with its Watches armed; the same repository again is
    refused Already watched and nothing doubles.

    replaces: tests/e2e/test_philo17_sources_glass.py::test_add_a_repository_and_it_stays_after_reload (the hub half; the picker and the well are the face's)
    """
    with _hub(tmp_path, monkeypatch, gh_runner=_gh_signed_in) as hub:
        pid = hub.ok("POST", "/api/projects/door", {"outcome": "Ledger cutover"})["projectId"]
        hub.ok("POST", "/api/connections/github/recheck", {})
        hub.ok("POST", "/api/projects/door", {"project_id": pid, "sources": [GITHUB_SOURCE]})

        def watch_ids() -> list[str]:
            items = hub.ok("GET", f"/api/projects/{pid}/room")["sources"]["items"]
            return sorted(i for item in items if item.get("scope") == "acme/app" for i in item.get("watchIds", []))

        before = watch_ids()
        assert before, "the added repository arms its watches"
        again = hub.client.post("/api/projects/door", json={"project_id": pid, "sources": [GITHUB_SOURCE]})
        assert again.status_code == 409, again.text
        assert again.json()["message"] == "Already watched", again.text
        assert watch_ids() == before


def test_park_from_files_parks_the_meeting_and_restore_brings_it_back_to_the_room(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A project with one filed meeting. Park (the existing Meeting delete
    route) takes it off the project and lists it as parked; Restore brings it
    back, still filed in the project.

    replaces: tests/e2e/test_philo17_sources_glass.py::test_park_from_files_leaves_its_receipt_and_restore_in_the_room (the hub half; `PARKED · Vendor call` and the Restore verb are the face's)
    """
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    with _hub(tmp_path, monkeypatch, gh_runner=_gh_not_signed_in) as hub:
        db = hub.db
        start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
        db.projects.create_project(project_id="p-lone", name="Vendor review", description="One meeting.",
                                   keywords=["vendor"])
        db.meetings.save_meeting(MeetingState(
            id="m-lone", started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor call",
            segments=[TranscriptSegment(text="We pick the vendor.", speaker="Me", start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["vendor"], summary="Pick it.", action_items=[]),
            intel_status="completed"))
        db.projects.associate_meeting_project(meeting_id="m-lone", project_id="p-lone", source="manual",
                                              confidence=1.0)

        def room_meetings() -> list[str]:
            """The Room's meetings: its count and the latest one."""
            section = hub.ok("GET", "/api/projects/p-lone/room")["meetings"]
            latest = section.get("latest") or {}
            ids = [str(latest.get("id"))] if latest else []
            assert section["count"] == len(ids), section
            return ids

        def listed(path: str) -> list[str]:
            return [str(m.get("id")) for m in hub.ok("GET", path)["meetings"]]

        assert room_meetings() == ["m-lone"]
        assert hub.client.delete("/api/meetings/m-lone").status_code == 200
        assert "m-lone" not in room_meetings()
        assert "m-lone" not in listed("/api/meetings")
        assert "m-lone" in listed("/api/meetings?parked=true")

        restored = hub.ok("POST", "/api/meetings/m-lone/restore")
        assert restored["meeting"]["id"] == "m-lone", restored
        assert room_meetings() == ["m-lone"]
        assert "m-lone" in listed("/api/meetings")


def test_an_older_project_registers_its_watched_repository_registered_not_cloned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A project that watches acme/app with no registration (made by the API):
    the Room's Register posts the repository; it is registered, not cloned.

    replaces: tests/e2e/test_philo17_sources_glass.py::test_an_older_project_registers_its_repository_in_the_room (the hub half; the Register verb leaving is the face's)
    """
    with _hub(tmp_path, monkeypatch, gh_runner=_gh_signed_in) as hub:
        pid = hub.ok("POST", "/api/projects/door", {"outcome": "Ledger cutover", "sources": [GITHUB_SOURCE]})["projectId"]
        before = hub.ok("GET", f"/api/projects/{pid}/repository")
        assert (before["registered"], before["watched"]) == (False, ["acme/app"]), before
        hub.ok("POST", f"/api/projects/{pid}/repository", {"repository": "acme/app"})
        after = hub.ok("GET", f"/api/projects/{pid}/repository")
        assert (after["repository"], after["registered"], after["cloned"]) == ("acme/app", True, False), after


# ── two working days (HS-200-16): the Project carries the work ───────
#
# The seeds and the two controlled adapters are copied from
# tests/e2e/test_phase200_daily_loop.py (plain Python): the GitHub + Jira
# Watches, the scripted meeting engine, the brief's reply, and the labelled
# HISTORICAL FIXTURE that seeds the day-1 decision and commitment.

LOOP_PROJECT = "Q4 Platform"
LOOP_PURPOSE = "Architecture review, cut-over sequencing"
DECISION_TEXT = "Rollback runbook is rehearsed on the read replica first"
DECISION_WHY = "The replica absorbs the first cut-over without touching writes"
COMMITMENT_TEXT = "Draft the rollback runbook"
OWNER_HINT = "Marek"
PERSON_NAME = "Marek Kubiak"
DEC_PLUGIN = "decision_capture"
ACT_PLUGIN = "action_owner_enforcer"
TRANSCRIPT_SRT = """1
00:00:00,000 --> 00:02:00,000
Karol: Let's start with the cut-over sequencing for the payments platform.

2
00:18:00,000 --> 00:21:00,000
Priya: Rollback runbook is rehearsed on the read replica first.

3
00:31:00,000 --> 00:33:00,000
Marek: I'll draft the rollback runbook before the freeze.
"""
DECISIONS_JSON = json.dumps({
    "decisions": [{"decision": DECISION_TEXT, "rationale": DECISION_WHY, "source_timestamp": 1100.0}],
    "open_questions": [],
})
ACTIONS_JSON = json.dumps({"action_items": [{"task": COMMITMENT_TEXT, "owner": OWNER_HINT, "due": None}]})


def _root_db() -> Any:
    """The database of the process's ONE composition root (the handle every route writes through)."""
    from holdspeak.runtime import composition

    return composition.current().db


def _scripted_engine() -> Any:
    from holdspeak.intel import IntelResult
    from tests.unit.test_meeting_deferred_admission import FakeIntel

    class ScriptedIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.plugin_calls: list[str] = []
            self.result = IntelResult(
                topics=[], action_items=[],
                summary="The cut-over plan has one recorded decision and one open commitment.",
                raw_response="{}",
            )

        def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
            system = str(messages[0].get("content") or "") if messages else ""
            plugin = DEC_PLUGIN if "decisions and open questions" in system else ACT_PLUGIN
            self.plugin_calls.append(plugin)
            return DECISIONS_JSON if plugin == DEC_PLUGIN else ACTIONS_JSON

    return ScriptedIntel()


def _wire_provider(monkeypatch: pytest.MonkeyPatch, engine: Any) -> None:
    """Only the provider seam is replaced; queue, executor, plugin host, bridge and routes are the product's."""
    from tests.unit.test_meeting_deferred_admission import _Route, _assign_deferred_queue_routes

    _assign_deferred_queue_routes(_root_db())
    monkeypatch.setattr("holdspeak.services.meeting_backlog_service._configured_auto_mode", lambda: "off")
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript",
                        lambda **kwargs: _Route((DEC_PLUGIN, ACT_PLUGIN)))


def _loop_brief_reply(body: str) -> str:
    prompt = json.loads(body).get("messages", [{}])[-1].get("content", "") if body.startswith("{") else body
    refs = re.findall(r"(decision_record:[A-Za-z0-9_:\-]+|source:[A-Za-z0-9_\-]+)", prompt)
    gh = next((r for r in refs if r.startswith("source:w_gh")), next(iter(refs), ""))
    decision = next((r for r in refs if r.startswith("decision_record:")), "")
    priorities = [{"text": "Two open pull requests wait on the runbook", "cited_refs": [gh] if gh else []}]
    if decision:
        priorities.insert(0, {"text": DECISION_TEXT, "cited_refs": [decision]})
    return json.dumps({
        "priorities": priorities,
        "questions": [{"text": "Sprint velocity improved over the trailing average", "cited_refs": []}],
        "obligations": [],
    })


def _seed_loop_sources(project_id: str) -> None:
    """One readable GitHub Watch and one Jira Watch that cannot check."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = (
        ("w_gh_loop", "gh", "pull_requests", {"repository": "karolswdev/HoldSpeak"},
         [{"number": 612, "title": "Cut-over runbook", "state": "OPEN",
           "url": "https://github.com/karolswdev/HoldSpeak/pull/612", "reviewRequests": ["karolswdev"],
           "checks": "passing", "updatedAt": (now - timedelta(days=2)).isoformat()},
          {"number": 613, "title": "Replica failover", "state": "OPEN",
           "url": "https://github.com/karolswdev/HoldSpeak/pull/613", "reviewRequests": ["karolswdev"],
           "checks": "passing", "updatedAt": (now - timedelta(days=1)).isoformat()}],
         (now - timedelta(minutes=4)).isoformat(timespec="seconds"), None),
        ("w_jira_loop", "jira", "issues", {"jql": "project = KAN AND due < now()"}, [],
         (now - timedelta(minutes=31)).isoformat(timespec="seconds"),
         "JQL parse error: The value 'KAN' does not exist for the field 'project'."),
    )
    db = _root_db()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', 'karolswdev', 'connected', datetime('now'), datetime('now'), datetime('now'))",
        )
        for wid, connector, kind, query, snapshot, success_at, error in rows:
            conn.execute(
                "INSERT INTO connector_watches "
                "(id, connector_id, query_kind, name, query_json, snapshot_json, "
                " enabled, last_success_at, last_error, project_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, datetime('now'), datetime('now'))",
                (wid, connector, kind, f"{connector} {kind}", json.dumps(query, sort_keys=True),
                 json.dumps(snapshot), success_at, error, project_id),
            )


def _seed_historical_proposal_fixture(meeting_id: str, engine: Any) -> list[Any]:
    """HISTORICAL FIXTURE, not summary output: the two real extractor plugins
    on the imported transcript, their outputs recorded, the real bridge."""
    from holdspeak.plugins.builtin.action_owner_enforcer import ActionOwnerEnforcerPlugin
    from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin
    from holdspeak.plugins.intelligence import PLUGIN_DISPATCH_KEY
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.plugin_dispatch_rig import admitted_dispatch, unbind

    db = _root_db()
    meeting = db.meetings.get_meeting(meeting_id)
    assert meeting is not None
    segments = list(meeting.segments)
    context = {
        "transcript": "\n".join(str(s.text) for s in segments),
        "transcript_segments": [{"text": s.text, "speaker": s.speaker, "start_time": s.start_time,
                                 "end_time": s.end_time} for s in segments],
        "project_name": LOOP_PROJECT,
        "active_intents": [],
    }

    def _run(plugin: Any) -> dict[str, Any]:
        dispatch, bound_engine, dispatch_context = admitted_dispatch(engine=engine)
        try:
            return plugin.run({**context, PLUGIN_DISPATCH_KEY: dispatch})
        finally:
            unbind(bound_engine, dispatch_context)

    for plugin, kind in ((DecisionCapturePlugin(), "decisions"), (ActionOwnerEnforcerPlugin(), "action_items")):
        output = _run(plugin)
        assert output.get(kind), output
        db.plugins.record_artifact(
            artifact_id=f"historical-{meeting_id}-{kind}", meeting_id=meeting_id, artifact_type=kind,
            title=f"HISTORICAL FIXTURE {kind} output", structured_json=output,
            confidence=float(output.get("confidence_hint") or 0.0), status="draft",
            plugin_id=plugin.id, plugin_version=plugin.version,
        )
    created = ProposalBridgeService(db).bridge_meeting_artifacts(meeting_id)
    assert len(created) == 2, created
    return created


def _wait(predicate: Any, *, timeout: float = 90.0, step: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return bool(predicate())


@pytest.mark.timeout(600)
def test_a_project_carries_work_across_two_working_days(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """Day 1 on hub #1: a brief is prepared over the wire and kept; a
    transcript is imported with a day-1 start, linked and summarised; its
    plugins run on the disclosed route (Capture C4) and propose one decision
    and one commitment, both confirmed; the commitment is attention. The hub stops; hub #2 opens the SAME database file. Day 2:
    recall returns the decision first with its rationale, dated day 1, and the
    commitment still owed; the person carries it; explicit acts complete it;
    the person no longer owes it; day 2's manifest carries the decision and
    the commitment, each as its own kind.

    Not moved (face only): the proposal caption's drawn date, the singular
    `1 DAY` on the Room text, the TARGET chip, the Review wing's
    `SUMMARY · RAN · NONE`, and the CARRIED FORWARD emblems and DUE token as
    drawn. The hub facts under each are asserted here.

    replaces: tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days
    """
    from holdspeak import intel_queue_conductor as conductor
    from holdspeak.runtime_identity import database_identity
    from holdspeak.runtime_lock import claim_database, current_lock, release_database

    day1 = (datetime.now() - timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    llm.reply = _loop_brief_reply
    engine = _scripted_engine()
    db_path = tmp_path / "holdspeak.db"
    state: dict[str, Any] = {}

    # ══ DAY 1: hub #1, the owner claim held so the intel drainer runs ══
    assert current_lock() is None, "this process already owns a database"
    assert claim_database(db_path).held
    try:
        with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
            assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"
            project_id = hub.ok("POST", "/api/projects", {
                "name": LOOP_PROJECT, "description": "The HS-200-16 two-day loop.",
                "command_id": f"hs200-16-{uuid.uuid4().hex[:8]}",
            })["project"]["id"]
            state["project_id"] = project_id
            _seed_loop_sources(project_id)
            _define_route(hub.home, llm.endpoint, "loop-llm")
            hub.ok("POST", "/api/people/setup", {})
            person = hub.ok("POST", "/api/people/relationships", {"display_name": PERSON_NAME})["relationship"]["id"]
            hub.ok("POST", f"/api/people/relationships/{person}/owner-aliases", {"alias": OWNER_HINT.lower()})
            hub.ok("POST", f"/api/people/relationships/{person}/projects/{project_id}", {})

            # S1: the brief, prepared over the wire and kept.
            assert hub.ok("GET", f"/api/projects/{project_id}/briefs/route")["route"]["state"] == "ready"
            manifest = hub.ok("GET", f"/api/projects/{project_id}/briefs/manifest")["manifest"]
            assert manifest["coverage"] == {"expected": 2, "available": 1, "complete": False}, manifest["coverage"]
            brief = hub.ok("POST", f"/api/projects/{project_id}/briefs/prepare",
                           {"purpose": LOOP_PURPOSE, "attempt_id": "att_day1"})["brief"]
            assert len(llm.posts) == 1, llm.requests
            hub.ok("POST", f"/api/briefs/{brief['id']}/keep")
            kept = hub.ok("GET", f"/api/projects/{project_id}/briefs?lifecycle=kept")["briefs"]
            assert [b["id"] for b in kept] == [brief["id"]] and kept[0]["lifecycle"] == "kept", kept

            # S2: the meeting, imported with a day-1 start, linked, summarised.
            _wire_provider(monkeypatch, engine)
            imported = hub.client.post(
                "/api/meetings/import",
                files={"file": ("architecture-review.srt", TRANSCRIPT_SRT.encode(), "text/plain")},
                data={"title": "Architecture review", "started_at_ms": str(int(day1.timestamp() * 1000))},
            )
            assert imported.status_code == 202, imported.text
            meeting_id = str(imported.json()["meeting_id"])
            assert _wait(lambda: len(hub.ok("GET", f"/api/meetings/{meeting_id}").get("segments") or []) == 3,
                         timeout=30), "the import never produced three segments"
            hub.ok("POST", f"/api/projects/{project_id}/meetings/{meeting_id}")
            planned = hub.ok("GET", f"/api/meetings/{meeting_id}")["planned_route"]
            assert planned["status"] == "ready" and planned["selection_hash"], planned
            run = hub.ok("POST", f"/api/meetings/{meeting_id}/intelligence/run",
                         {"expected_selection_hash": planned["selection_hash"]})
            assert run["state"] == "queued" and run["drainer"] == "running", run

            def review() -> dict[str, Any]:
                return hub.ok("GET", f"/api/meetings/{meeting_id}/outcome-review")

            assert _wait(lambda: (review().get("job") or {}).get("status") == "succeeded", timeout=120.0), (
                review(), engine.plugin_calls)
            first = review()
            assert first["coverage"]["turns"] == 3 and first["coverage"]["read"] == 3, first["coverage"]
            # Capture C4: the job's plugins run on its disclosed route, and the
            # two real extractors' output is the day-1 decision and commitment.
            assert sorted(engine.plugin_calls) == [ACT_PLUGIN, DEC_PLUGIN], engine.plugin_calls
            detail = hub.ok("GET", f"/api/meetings/{meeting_id}")
            assert detail["intel"]["summary"] == engine.result.summary, detail["intel"]
            started_at = detail.get("started_at") or (detail.get("meeting") or {}).get("started_at")
            assert str(started_at)[:10] == day1.date().isoformat(), started_at

            proposals = review()["proposals"]
            assert sorted(p["kind"] for p in proposals) == ["action", "decision"], proposals

            # The Room dates a pending proposal by its MEETING, not by the row's write.
            room = hub.ok("GET", f"/api/projects/{project_id}/room")
            pending = [r for r in (room["needsYou"].get("items") or []) if r.get("meeting_started_at")]
            assert pending, room["needsYou"]
            assert all(str(r["meeting_started_at"])[:10] == day1.date().isoformat() for r in pending), pending
            words = json.dumps(room)
            assert "1 DAYS" not in words and "1 HOURS" not in words, "one day is a day"

            # S3: confirm one decision and one commitment.
            for proposal in proposals:
                hub.ok("POST", f"/api/proposals/{proposal['id']}/confirm", {})
            confirmed = [p for p in review()["proposals"] if p["state"] == "confirmed"]
            assert len(confirmed) == 2, confirmed
            decision = next(p for p in confirmed if p["kind"] == "decision")
            commitment = next(p for p in confirmed if p["kind"] == "action")
            assert decision["decision_record_id"] and commitment["commitment_id"], confirmed
            state["decision_record_id"] = decision["decision_record_id"]

            # S4: the commitment is a real attention row; coverage is partial.
            wire = hub.ok("GET", "/api/desk/needs-you?fresh=1")
            rows = [i for i in wire["items"] if i["source"] == "commitment" and i["title"] == COMMITMENT_TEXT]
            assert len(rows) == 1, [i["title"] for i in wire["items"]]
            assert wire["complete"] is False, wire["coverage"]
        day1_db = database_identity(db_path)
    finally:
        conductor.stop_intel_queue_conductor()
        release_database()

    # ══ THE DAY BOUNDARY: hub #2 on the SAME database file ══
    assert claim_database(db_path).held
    try:
        with _hub(tmp_path, monkeypatch) as hub:
            assert database_identity(db_path) == day1_db, "hub #2 opened another file"
            project_id = state["project_id"]

            # S5: recall returns yesterday's decision first, dated day 1, and the owed commitment.
            recall = hub.ok("GET", "/api/memory/recall?query=rollback+runbook&filter=all")
            current = [c for c in recall["current"] if c["text"] == DECISION_TEXT]
            assert current and current[0]["state"] == "current", recall["current"]
            card = current[0]
            assert card["rationale"] == DECISION_WHY, card
            assert card["dec_token"] == f"DEC {day1:%m-%d}", card
            assert card["source"]["token"].startswith(f"MTG {day1:%m-%d}"), card["source"]
            owed = [r for r in recall["owed"] if r["text"] == COMMITMENT_TEXT]
            assert len(owed) == 1, recall["owed"]
            action_item_id = owed[0]["action_item_id"]
            hub.ok("POST", f"/api/decision-records/{card['id']}/carry", {"project_id": project_id})
            again = hub.ok("GET", "/api/memory/recall?query=rollback+runbook&filter=all")
            assert next(c for c in again["current"] if c["id"] == card["id"])["carried"] is True

            # S6: the person carries yesterday's commitment.
            def person_commitments() -> list[str]:
                people = hub.ok("GET", f"/api/projects/{project_id}/people")["people"]
                marek = [p for p in people if p.get("display_name") == PERSON_NAME]
                assert marek, people
                return [str(c.get("text") or c.get("title") or "") for c in marek[0].get("commitments") or []]

            assert person_commitments() == [COMMITMENT_TEXT]

            # S7: completion by explicit acts (name / date, then done).
            due_day = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            for _ in range(4):
                row = next(r for r in hub.ok("GET", "/api/memory/recall?query=rollback+runbook&filter=all")["owed"]
                           if r["action_item_id"] == action_item_id)
                if row["next_action"] == "mark_done":
                    break
                verb, payload = (("delegate", {"to": PERSON_NAME}) if row["next_action"] == "name_owner"
                                 else ("due", {"due_at": due_day}))
                hub.ok("POST", "/api/follow-through/complete",
                       {"card_id": action_item_id, "verb": verb, "payload": payload})
            else:
                raise AssertionError("the owed row never reached mark_done")
            hub.ok("POST", "/api/follow-through/complete", {"card_id": action_item_id, "verb": "done", "payload": {}})
            board = hub.ok("GET", "/api/follow-through/board")
            after = [c for lane in board.values() if isinstance(lane, list) for c in lane
                     if c.get("id") == action_item_id]
            assert not after or after[0]["status"] in ("completed", "done"), after
            assert person_commitments() == [], "the completed commitment is no longer owed"
            owed_now = hub.ok("GET", "/api/memory/recall?query=rollback+runbook&filter=all")["owed"]
            assert not [r for r in owed_now if r["action_item_id"] == action_item_id], owed_now
            # S8: day 2's manifest carries both, each as its own kind, the due a DAY.
            carried = hub.ok("GET", f"/api/projects/{project_id}/briefs/manifest")["manifest"]
            dec_rows = [d for d in carried["decisions"] if d["text"] == DECISION_TEXT]
            cmt_rows = [c for c in carried["commitments"] if c["text"] == COMMITMENT_TEXT]
            assert [d["kind"] for d in dec_rows] == ["decision"], carried["decisions"]
            assert [c["kind"] for c in cmt_rows] == ["action"], carried["commitments"]
            assert str(cmt_rows[0]["due_at"])[:10] == due_day, cmt_rows
            assert not [d for d in carried["decisions"] if d["text"] == COMMITMENT_TEXT], \
                "an action is never carried as a decision"

    finally:
        release_database()


# ── the unattended steward (HS-164-06): two conductor ticks, two runs ──
#
# The seeds and the gh fixture runner are copied verbatim from
# tests/e2e/test_hs164_unattended_glass.py (parked by the test diet), so the
# recorder (scripts/record_room_wires.py) and this test drive the same desk.

HS164_GH_AUTH_CONNECTED = {"stdout": json.dumps({"username": "testuser"}), "returncode": 0}
HS164_GH_REPO_LIST = json.dumps([{"name": "HoldSpeak", "owner": {"login": "testuser"}, "visibility": "public"}])
HS164_GH_PR_VALIDATE_OK = json.dumps([{"number": 1}])
HS164_GH_PR_SNAPSHOT_BASELINE = json.dumps([
    {"number": 100, "title": "feat: add payment gateway", "url": "https://github.com/testuser/HoldSpeak/pull/100",
     "state": "OPEN", "isDraft": False, "reviewRequests": [{"login": "reviewer1"}], "reviewDecision": "",
     "statusCheckRollup": [{"conclusion": "SUCCESS"}], "headRefOid": "aaaa1111aaaa",
     "updatedAt": "2026-08-30T10:00:00Z"},
    {"number": 101, "title": "fix: correct ledger rounding", "url": "https://github.com/testuser/HoldSpeak/pull/101",
     "state": "OPEN", "isDraft": False, "reviewRequests": [], "reviewDecision": "APPROVED",
     "statusCheckRollup": [{"conclusion": "SUCCESS"}], "headRefOid": "bbbb2222bbbb",
     "updatedAt": "2026-08-30T11:00:00Z"},
])
# Changed snapshot: PR 100 checks failed, PR 101 merged.
HS164_GH_PR_SNAPSHOT_TICK1 = json.dumps([
    {"number": 100, "title": "feat: add payment gateway", "url": "https://github.com/testuser/HoldSpeak/pull/100",
     "state": "OPEN", "isDraft": False, "reviewRequests": [{"login": "reviewer1"}], "reviewDecision": "",
     "statusCheckRollup": [{"conclusion": "FAILURE"}], "headRefOid": "cccc3333cccc",
     "updatedAt": "2026-08-31T10:00:00Z"},
    {"number": 101, "title": "fix: correct ledger rounding", "url": "https://github.com/testuser/HoldSpeak/pull/101",
     "state": "MERGED", "isDraft": False, "reviewRequests": [], "reviewDecision": "APPROVED",
     "statusCheckRollup": [{"conclusion": "SUCCESS"}], "headRefOid": "bbbb2222bbbb",
     "updatedAt": "2026-08-31T11:00:00Z"},
])
# Second change: PR 100 checks now pass again, new PR 102.
HS164_GH_PR_SNAPSHOT_TICK2 = json.dumps([
    {"number": 100, "title": "feat: add payment gateway", "url": "https://github.com/testuser/HoldSpeak/pull/100",
     "state": "OPEN", "isDraft": False, "reviewRequests": [], "reviewDecision": "APPROVED",
     "statusCheckRollup": [{"conclusion": "SUCCESS"}], "headRefOid": "dddd4444dddd",
     "updatedAt": "2026-09-01T10:00:00Z"},
    {"number": 102, "title": "chore: update dependencies", "url": "https://github.com/testuser/HoldSpeak/pull/102",
     "state": "OPEN", "isDraft": False, "reviewRequests": [{"login": "reviewer2"}], "reviewDecision": "",
     "statusCheckRollup": [{"conclusion": "SUCCESS"}], "headRefOid": "eeee5555eeee",
     "updatedAt": "2026-09-01T11:00:00Z"},
])


def hs164_fixture_runner(fixture_path: Path) -> Any:
    """Canned response runner (re-reads the file on every call)."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        with open(fixture_path) as f:
            fixture = json.load(f)
        if "auth status" in cmd_str:
            entry = fixture.get("auth_status", {})
        elif "repo list" in cmd_str:
            entry = fixture.get("repo_list", {})
        elif ("pr list" in cmd_str and "-R" in cmd_str
              and "--limit" in cmd_str and "1" in cmd_str):
            entry = fixture.get("pr_validate", {})
        elif "pr list" in cmd_str:
            entry = fixture.get("pr_list", {})
        else:
            entry = {"returncode": 1, "stderr": f"no fixture match: {cmd_str}"}
        return subprocess.CompletedProcess(
            args=cmd, returncode=entry.get("returncode", 0),
            stdout=entry.get("stdout", ""), stderr=entry.get("stderr", ""),
        )
    return runner


def hs164_write_fixture(path: Path, pr_list: dict[str, Any]) -> None:
    path.write_text(json.dumps({
        "auth_status": HS164_GH_AUTH_CONNECTED,
        "repo_list": {"stdout": HS164_GH_REPO_LIST, "returncode": 0},
        "pr_validate": {"stdout": HS164_GH_PR_VALIDATE_OK, "returncode": 0},
        "pr_list": pr_list,
    }, indent=2))


def hs164_seed_room(hub: Hub) -> str:
    """The project, its three items (one overdue high-severity risk) and the
    steward policy with unattended ON (the glass's own wire calls)."""
    pid = hub.ok("POST", "/api/projects", {
        "name": "Unattended Glass Project", "description": "Seeded for HS-164-06 unattended glass.",
        "command_id": "hs164-glass-create-proj"})["project"]["id"]
    base = f"/api/projects/{pid}/items"
    past_due = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    hub.ok("POST", base, {
        "item_type": "risk", "title": "PCI compliance deadline at risk", "lifecycle": "open", "severity": "high",
        "due_at": past_due, "summary": "Compliance docs overdue; 30-day deadline approaching",
        "details": {"likelihood": "high", "impact": "critical", "mitigation": "Escalate to compliance team this week"}})
    hub.ok("POST", base, {"item_type": "workstream", "title": "Q4 Payments Platform Integration",
                          "lifecycle": "active", "summary": "Integrate payment gateway with event sourcing"})
    hub.ok("POST", base, {"item_type": "dependency", "title": "Infrastructure team load test environment",
                          "lifecycle": "at_risk", "summary": "Black Friday load test env provisioning stalled",
                          "details": {"direction": "upstream", "counterpart_ref": "team:infrastructure"}})
    hub.ok("PUT", f"/api/projects/{pid}/steward/policy", {
        "eligible_effect_kinds": ["refresh_sources", "create_proposals", "apply_proposal_effects", "draft_update",
                                  "create_door_item"],
        "max_retries": 3, "max_actions_per_run": 10, "cooldown_seconds": 0, "enabled": True,
        "unattended_enabled": True})
    return pid


def hs164_seed_graduated_watch(db: Any, project_id: str, watch_id: str = "cw_glass_unattended_001") -> str:
    """A graduated watch (state active, due now, baseline established) bound
    to the project, with a rule that runs the steward on any PR change, and
    its baseline snapshot."""
    from holdspeak.services.reaction_service import normalize_snapshot

    now_iso = datetime.now().isoformat()
    past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches (
                id, name, connector_id, query_kind, query_json, project_id, state, revision, enabled,
                evaluation_cadence_minutes, next_evaluation_at, baseline_state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (watch_id, "PR review queue (glass)", "gh", "pull_requests",
             json.dumps({"repository": "testuser/HoldSpeak", "state": "open"}), project_id, "active", 1, 1, 1,
             past_iso, "established", now_iso, now_iso),
        )
        conn.execute(
            """INSERT INTO project_sources (id, project_id, source_ref, label, semantic_role, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"psrc_{watch_id}", project_id, f"watch:{watch_id}", "PR review queue (glass)", "watch", now_iso,
             now_iso),
        )
        condition = {"schema": "WatchCondition@1", "operator": "any", "clauses": [
            {"field": "state", "comparison": "changed"}, {"field": "head_sha", "comparison": "changed"},
            {"field": "checks", "comparison": "changed"}, {"field": "review_decision", "comparison": "changed"},
            {"field": "review_requested", "comparison": "changed"}]}
        conn.execute(
            """INSERT INTO watch_rules (id, watch_id, ordinal, condition_schema, condition_json, action_schema,
                                        action_json, enabled, revision)
               VALUES (?, ?, 0, 'WatchCondition@1', ?, 'WatchAction@1', ?, 1, 0)""",
            (f"wrule_{watch_id}", watch_id, json.dumps(condition),
             json.dumps([{"schema": "WatchAction@1", "kind": "project.steward.run_once"}])),
        )
    snapshot = normalize_snapshot("gh", json.loads(HS164_GH_PR_SNAPSHOT_BASELINE))
    with db._connection() as conn:
        conn.execute("UPDATE connector_watches SET snapshot_json=? WHERE id=?",
                     (json.dumps(snapshot, sort_keys=True, separators=(",", ":")), watch_id))
    return watch_id


def hs164_due_now(db: Any, watch_id: str) -> None:
    past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
    with db._connection() as conn:
        conn.execute("UPDATE connector_watches SET next_evaluation_at=? WHERE id=?", (past_iso, watch_id))


@contextlib.contextmanager
def hs164_conductor(hub: Hub) -> Iterator[Any]:
    """The hub's own composed scheduler services (the instances its startup
    hands the conductor, ``web_server.py`` set_scheduler_services), ticked by
    this test alone: no lifespan, so no background conductor."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime import composition

    root = composition.installed()
    watch_service, steward_service = root.watch_service, root.project_steward_service
    assert watch_service is not None and steward_service is not None, "the hub composed no scheduler services"
    owner = Principal(PrincipalKind.OWNER, "local-steward-conductor")
    yield lambda: (watch_service.evaluate_due(owner), steward_service.run_due(owner))


def hs164_door_texts(hub: Hub) -> list[str]:
    board = hub.ok("GET", "/api/door").get("board", {})
    return [it.get("text", "") for bucket in ("now", "waiting", "unassigned", "overdue")
            for it in board.get(bucket, [])]


def test_two_conductor_ticks_make_two_completed_unattended_runs_with_no_duplicate_door_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate A on the hub: a watched repository changes twice; each conductor
    tick evaluates the watch and starts a run; both runs complete with their
    steps, both carry the conductor's identity, and the Door holds no item
    twice.

    replaces: tests/e2e/test_hs164_unattended_glass.py::test_gate_a_two_unattended_runs (the hub half; the
    Scheduled chips and the run detail are steward.app.test.tsx's)
    """
    fixture = tmp_path / "gh_fixture.json"
    hs164_write_fixture(fixture, {"stdout": HS164_GH_PR_SNAPSHOT_BASELINE, "returncode": 0})
    with _hub(tmp_path, monkeypatch, gh_runner=hs164_fixture_runner(fixture)) as hub, \
            hs164_conductor(hub) as tick:
        pid = hs164_seed_room(hub)
        watch_id = hs164_seed_graduated_watch(hub.db, pid)
        started: list[str] = []
        for snapshot in (HS164_GH_PR_SNAPSHOT_TICK1, HS164_GH_PR_SNAPSHOT_TICK2):
            hs164_write_fixture(fixture, {"stdout": snapshot, "returncode": 0})
            hs164_due_now(hub.db, watch_id)
            evaluated, ran = tick()
            assert any(o.get("outcome") in ("evaluated", "probe_half_open") for o in evaluated), evaluated
            assert any(o.get("outcome") == "run_started" for o in ran), ran
            started.append(next(o["run_id"] for o in ran if o.get("outcome") == "run_started"))
        assert len(set(started)) == 2, started
        runs = hub.ok("GET", f"/api/projects/{pid}/steward/runs")["runs"]
        completed = [r for r in runs if r.get("state") == "completed"]
        assert len(completed) >= 2, runs
        assert {r.get("requested_by") for r in runs} == {"principal:local-steward-conductor"}, runs
        for run_id in started:
            assert hub.ok("GET", f"/api/steward/runs/{run_id}").get("steps"), run_id
        texts = hs164_door_texts(hub)
        assert len(texts) == len(set(texts)), texts


# ── Betterment P3: the Now wing (where it stands in ten seconds) ──────
#
# The RECON seed (docs/internal/betterment/projects/RECON.md): a payments
# platform sync that names the HSM blocker, an architecture review with a
# decision to confirm, a 1:1 with Mira, the "open risks" note filed as a
# source, one confirmed decision, and owed items for Theo, Jun, Mira and him.

P3_WIRE = (Path(__file__).resolve().parents[2] / "web" / "src" / "features" / "project-room"
           / "__tests__" / "room-wires" / "nowP3.json")


def _p3_meeting(db: Any, project_id: str, meeting_id: str, title: str, summary: str,
                started: datetime, speakers: tuple[str, ...], actions: list[dict[str, Any]]) -> None:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=started, title=title,
        segments=[TranscriptSegment(text=f"line {i}", speaker=s, start_time=float(i), end_time=float(i) + 1)
                  for i, s in enumerate(speakers)],
        intel=IntelSnapshot(timestamp=1.0, summary=summary, action_items=actions),
    ))
    db.projects.associate_meeting_project(meeting_id=meeting_id, project_id=project_id,
                                          source="test", confidence=1.0)


def _seed_payments_week(hub: Hub) -> str:
    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService

    owner = Principal(PrincipalKind.OWNER, "p3-now-test")
    project_id = hub.ok("POST", "/api/projects", {
        "name": "Payments migration", "command_id": f"p3-{uuid.uuid4().hex[:8]}",
    })["project"]["id"]
    db = hub.db
    day = (datetime.now() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    in_days = lambda n: (datetime.now() + timedelta(days=n)).date().isoformat()  # noqa: E731
    _p3_meeting(
        db, project_id, "p3-sync", "Payments platform sync",
        "The staging dry run passed. Card tokenization is blocked on the HSM key ceremony. "
        "Jun will get a date from Security.",
        day, ("Me", "Theo", "Jun", "Mira"),
        [
            {"id": "p3-theo-1", "task": "Review the rollback runbook", "owner": "Theo",
             "due": in_days(2), "status": "pending", "review_state": "accepted"},
            {"id": "p3-theo-2", "task": "Estimate the Kafka cost", "owner": "Theo",
             "due": in_days(1), "status": "pending", "review_state": "accepted"},
            {"id": "p3-jun-1", "task": "Get a date for the HSM ceremony", "owner": "Jun",
             "due": in_days(3), "status": "pending", "review_state": "accepted"},
            {"id": "p3-jun-2", "task": "Write the ledger ADR", "owner": "Jun",
             "due": in_days(5), "status": "pending", "review_state": "accepted"},
            {"id": "p3-mira-1", "task": "Review PLAT-212", "owner": "Mira",
             "due": in_days(0), "status": "pending", "review_state": "accepted"},
            {"id": "p3-me-1", "task": "Put Mira on the guild agenda (Nov)", "owner": "Me",
             "status": "pending", "review_state": "accepted"},
        ],
    )
    _p3_meeting(
        db, project_id, "p3-arch", "Architecture review",
        "We keep the old ledger read-only for 30 days after cutover. Kafka looks right for ledger events.",
        day + timedelta(hours=3), ("Me", "Theo", "Jun"), [],
    )
    _p3_meeting(
        db, project_id, "p3-one-on-one", "1:1 with Mira",
        "Mira reported a heavy cutover load and a risk of burnout.",
        day + timedelta(hours=5), ("Me", "Mira"), [],
    )
    db.proposals.create_proposal(
        meeting_id="p3-arch", project_id=project_id, kind="decision",
        text="Kafka for ledger events", source_plugin="p3-test",
    )
    db.plugins.record_artifact(
        artifact_id="p3-arch-decisions", meeting_id="p3-arch", artifact_type="decisions",
        title="Architecture review decisions",
        structured_json={"decisions": [{"decision": "Keep the old ledger read-only for 30 days",
                                        "rationale": "rollback"}]},
        plugin_id="p3-test",
    )
    with db._connection() as conn:
        backfill_decisions(conn)
    DecisionRecordService(db).create_from_meeting(owner, db.decisions.list(meeting_id="p3-arch")[0].id)
    db.notes.upsert(note_id="p3-risks", title="Payments migration: open risks", body_markdown=(
        "# Open risks\n- Rollback runbook is still a draft\n- Bus factor 1 on the ledger schema\n"))
    from holdspeak.services.project_service import ProjectService

    ProjectService(db).add_resource(owner, project_id, "note:p3-risks")
    return project_id


def test_the_now_wing_says_where_it_stands_from_this_weeks_meetings_and_notes(tmp_path, monkeypatch):
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = _seed_payments_week(hub)
        room = hub.ok("GET", f"/api/projects/{project_id}/room")

        # The head: at risk, and why, in words from the sync (not "On track").
        health = room["health"]
        assert health["state"] == "ok"
        assert health["assessment"] == "at_risk"
        assert health["project_state"] == "at_risk"
        assert health["state_reason"] == "Card tokenization is blocked on the HSM key ceremony"
        assert health["state_ref"] == "meeting:p3-sync"

        # Needs you: his own owed item and the decision to confirm; the
        # others' owed items are theirs (Waiting on), never his.
        rows = room["needsYou"]["items"]
        mine = [r["title"] for r in rows if r.get("direction") == "mine"]
        assert "Put Mira on the guild agenda (Nov)" in mine
        assert any(r.get("proposal_id") and r["title"] == "Kafka for ledger events" for r in rows)
        theirs: dict[str, int] = {}
        for r in rows:
            if r.get("direction") == "theirs":
                theirs[r["owner"]] = theirs.get(r["owner"], 0) + 1
        assert theirs == {"Theo": 2, "Jun": 2, "Mira": 1}

        # This week: the confirmed decision and the runbook risk, each with
        # its source; the 1:1's words never reach it.
        now = room["now"]
        assert now["state"] == "ok"
        assert [d["text"] for d in now["decided"]] == ["Keep the old ledger read-only for 30 days"]
        assert now["decided"][0]["ref"].startswith("decision_record:")
        assert now["decided"][0]["source_ref"] == "meeting:p3-arch"
        risks = {r["text"]: r for r in now["risks"]}
        assert risks["Rollback runbook is still a draft"]["ref"] == "note:p3-risks"
        assert risks["Card tokenization is blocked on the HSM key ceremony."]["token"].startswith("MTG ")
        assert not any("burnout" in text for text in risks)
        assert now["meetings_this_week"] in (0, 3)  # the seed sits on yesterday: Monday splits it
        assert now["last_update_at"] is None

        if __import__("os").environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
            P3_WIRE.write_text(json.dumps({
                "_recorded": "tests/integration/test_desk_project_room.py::"
                             "test_the_now_wing_says_where_it_stands_from_this_weeks_meetings_and_notes "
                             "(HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit a field a test reads)",
                "room": room,
                "proposals": hub.ok("GET", f"/api/projects/{project_id}/proposals"),
            }, indent=1, sort_keys=True) + "\n")


def test_a_quiet_project_is_on_track_with_no_reason(tmp_path, monkeypatch):
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = hub.ok("POST", "/api/projects", {"name": "Quiet", "command_id": "p3-quiet"})["project"]["id"]
        room = hub.ok("GET", f"/api/projects/{project_id}/room")
        assert (room["health"]["project_state"], room["health"]["state_reason"]) == ("on_track", None)
        assert room["health"]["assessment"] == "on_track"
        assert room["now"]["risks"] == [] and room["now"]["decided"] == []


def test_waiting_on_action_preserves_its_real_destination_for_nudge(tmp_path, monkeypatch):
    """The active Now producer carries an explicit action destination through
    Waiting on; a missing destination stays absent for the UI gate."""
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = hub.ok("POST", "/api/projects", {
            "name": "Payments migration", "command_id": f"p6-{uuid.uuid4().hex[:8]}",
        })["project"]["id"]
        db = hub.db
        started = datetime.now() - timedelta(days=2)
        _p3_meeting(
            db, project_id, "p6-sync", "Payments migration review",
            "Ania owns the migration review.", started, ("Me", "Ania"),
            [{"id": "p6-action", "task": "Review migration PR", "owner": "Ania",
              "due": (datetime.now() + timedelta(days=1)).date().isoformat(),
              "status": "pending", "review_state": "accepted"}],
        )
        with db._connection() as conn:
            conn.execute(
                "UPDATE action_items SET source_ref=? WHERE id=?",
                ("https://github.com/org/repo/pull/612", "p6-action"),
            )
        room = hub.ok("GET", f"/api/projects/{project_id}/room")
        row = next(item for item in room["needsYou"]["items"] if item.get("action_item_id") == "p6-action")
        assert row["direction"] == "theirs", row
        assert row["url"] == "https://github.com/org/repo/pull/612", row


def test_waiting_on_nudge_matches_saved_targets_and_uses_the_document_send_boundary(tmp_path, monkeypatch):
    """Jira, Slack, and email Nudges come from real action rows and exact
    active destinations.  A preview and prepare are safe; only the isolated
    file destination is pressed to prove the existing Send boundary renders
    the stored project nudge document."""
    from holdspeak.db.channels import ChannelDestinationsRepository
    from holdspeak.services.channel_contract import render_document

    with _hub(tmp_path, monkeypatch) as hub:
        project_id = hub.ok("POST", "/api/projects", {
            "name": "Payments migration", "command_id": f"p6-generic-{uuid.uuid4().hex[:8]}",
        })["project"]["id"]
        db = hub.db
        _p3_meeting(
            db, project_id, "p6-generic-sync", "Payments migration review",
            "Ania owns the migration review.",
            datetime.now() - timedelta(days=2), ("Me", "Ania"),
            [
                {"id": "p6-jira", "task": "Review the Jira migration item", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-slack", "task": "Review the Slack migration thread", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-slack-thread", "task": "Review the Slack migration reply", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-email", "task": "Review the email migration request", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-jira-mismatch", "task": "Review the mismatched Jira item", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-slack-mismatch", "task": "Review the mismatched Slack thread", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-email-mismatch", "task": "Review the mismatched email request", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
                {"id": "p6-missing", "task": "Review the item with no saved destination", "owner": "Ania",
                 "status": "pending", "review_state": "accepted"},
            ],
        )
        refs = {
            "p6-jira": "https://acme.atlassian.net/browse/PAY-123",
            "p6-slack": "slack:#payments-review",
            "p6-slack-thread": "slack:#payments-review?thread_ts=171",
            "p6-email": "mailto:reviewer@example.com",
            "p6-jira-mismatch": "https://other.atlassian.net/browse/PAY-123",
            "p6-slack-mismatch": "slack:#other-review",
            "p6-email-mismatch": "mailto:someone-else@example.com",
            "p6-missing": "https://unconfigured.atlassian.net/browse/PAY-999",
        }
        with db._connection() as conn:
            for action_id, source_ref in refs.items():
                conn.execute("UPDATE action_items SET source_ref=? WHERE id=?", (source_ref, action_id))
            saved = (
                ("p6-dest-jira", "Jira Payments", "jira", {"site": "acme.atlassian.net", "email": "owner@example.com"}, {"key": "PAY-123"}),
                ("p6-dest-slack", "Slack Payments", "slack", {"key_ref": "slack-test"}, {"channel_label": "#payments-review"}),
                ("p6-dest-slack-thread", "Slack Payments thread", "slack", {"key_ref": "slack-test"}, {"channel_label": "#payments-review", "thread_ts": "171"}),
                ("p6-dest-email", "Email Payments", "email", {"provider": "sendgrid", "from_email": "owner@example.com", "from_name": "Owner", "key_ref": "sendgrid-test"}, {"to": ["reviewer@example.com"], "cc": []}),
                ("p6-dest-jira-wrong-site", "Jira Wrong Site", "jira", {"site": "other.atlassian.net", "email": "owner@example.com"}, {"key": "PAY-999"}),
                ("p6-dest-slack-wrong", "Slack Wrong", "slack", {"key_ref": "slack-test-2"}, {"channel_label": "#payments-archive"}),
                ("p6-dest-email-wrong", "Email Wrong", "email", {"provider": "sendgrid", "from_email": "owner@example.com", "from_name": "Owner", "key_ref": "sendgrid-test-2"}, {"to": ["other@example.com"], "cc": []}),
            )
            for destination_id, name, channel, account, target in saved:
                ChannelDestinationsRepository.insert_in_transaction(
                    conn, destination_id=destination_id, name=name, channel=channel,
                    account=account, target=target, synced=False,
                )

        room = hub.ok("GET", f"/api/projects/{project_id}/room")
        by_action = {row.get("action_item_id"): row for row in room["needsYou"]["items"]}
        assert by_action["p6-jira"]["nudge"]["destination_id"] == "p6-dest-jira", by_action["p6-jira"]
        assert by_action["p6-jira"]["nudge"]["channel"] == "jira", by_action["p6-jira"]
        assert by_action["p6-slack"]["nudge"]["destination_id"] == "p6-dest-slack", by_action["p6-slack"]
        assert by_action["p6-slack-thread"]["nudge"]["destination_id"] == "p6-dest-slack-thread", by_action["p6-slack-thread"]
        assert by_action["p6-email"]["nudge"]["destination_id"] == "p6-dest-email", by_action["p6-email"]
        for action_id in ("p6-jira-mismatch", "p6-slack-mismatch", "p6-email-mismatch", "p6-missing"):
            assert "nudge" not in by_action[action_id], by_action[action_id]

        nudge_ref = by_action["p6-jira"]["nudge"]["document_ref"]
        document = render_document(db, nudge_ref)
        assert document.ref == nudge_ref
        assert "Please review: Review the Jira migration item" in document.body_md
        assert "caller" not in document.body_md.lower()
        assert "NUDGE" == document.label

        # Preview and prepare use the real channel service, but no real Jira,
        # Slack, or email destination is sent in this proof.
        for action_id, destination_id in (
            ("p6-jira", "p6-dest-jira"),
            ("p6-slack", "p6-dest-slack"),
            ("p6-slack-thread", "p6-dest-slack-thread"),
            ("p6-email", "p6-dest-email"),
        ):
            preview = hub.client.post("/api/channels/preview", json={
                "document_ref": by_action[action_id]["nudge"]["document_ref"],
                "destination_id": destination_id,
            })
            assert preview.status_code == 200, preview.text
        assert hub.ok("GET", "/api/channels/sends")["sends"] == []

        folder = tmp_path / "nudge-sent"
        folder.mkdir()
        file_dest = hub.ok("POST", "/api/channels/destinations", {
            "name": "Nudge proof folder", "channel": "file", "folder": str(folder),
        })["destination"]["id"]
        prepared = hub.ok("POST", "/api/channels/sends", {
            "document_ref": nudge_ref, "destination_id": file_dest,
        })["send"]
        assert prepared["state"] == "prepared", prepared
        assert prepared["dispatch_started_at"] is None and prepared["send_operation_id"] is None, prepared
        assert not list(folder.iterdir())
        sent = hub.client.post("/api/channels/send", json={"send_id": prepared["id"]})
        assert sent.status_code == 200 and sent.json()["send"]["state"] == "sent", sent.text
        files = list(folder.glob("*.md"))
        assert len(files) == 1
        assert "Please review: Review the Jira migration item" in files[0].read_text(encoding="utf-8")


def test_project_update_line_records_the_real_manual_and_friday_wire(tmp_path, monkeypatch):
    """P7's consumer fixture is the actual shared Room/Workbench response."""
    import os
    with _hub(tmp_path, monkeypatch) as hub:
        project_id = hub.ok("POST", "/api/projects", {"name": "Friday update wire"})["project"]["id"]
        draft = hub.ok("POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"})["update"]
        manual = hub.ok("GET", f"/api/projects/{project_id}/room")
        automation_id = manual["updates"]["automation"]["id"]
        assert not manual["updates"]["automation"]["schedule_enabled"]
        refused = hub.client.put(f"/api/workbenches/{automation_id}", json={
            "schedule": "0 15 * * 5", "schedule_enabled": True,
        })
        assert refused.status_code == 400
        from tests.e2e.glass_infra import ENGINE_PROFILE, engine_profile, assign_engine
        engine_profile(automation=True)
        assign_engine("workbench.item", 11)
        assign_engine("project.update_draft", 12)
        friday = hub.ok("PUT", f"/api/workbenches/{automation_id}", {
            "schedule": "0 15 * * 5", "schedule_enabled": True,
        })
        scheduled = hub.ok("GET", f"/api/projects/{project_id}/room")
        assert scheduled["updates"]["automation"]["schedule_enabled"]
        assert scheduled["updates"]["automation"]["id"] == automation_id
        assert hub.db.workbenches.get(automation_id).schedule == "0 15 * * 5"
        assert manual["updates"]["automation"]["engine_label"] == "Engine not set"
        assert scheduled["updates"]["automation"]["profile_id"] == ENGINE_PROFILE
        assert scheduled["updates"]["automation"]["engine_label"] != "Engine not set"
        if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
            path = Path(__file__).resolve().parents[2] / "web/src/features/project-room/__tests__/room-wires/updateAutomationP7.json"
            path.write_text(json.dumps({"manual": manual, "scheduled": scheduled,
                "draft": draft, "friday": friday, "refusal": refused.json()}, indent=2) + "\n")
