"""Drive one corpus episode through the REAL product path (HS-200-08).

Three collectors, one per corpus category:

``interview``
    The Interview thread: the real hub, the real ``ThreadService`` turn loop,
    the real Interview reducer.  Prior owner turns are replayed as actual
    turns, then the episode's prompt.

``meeting``
    The real meeting plugin chain (``run_meeting_plugin_chain``) over a saved
    ``MeetingState``, with the real builtin plugins (``decision_capture``,
    ``action_owner_enforcer``) and an admitted dispatch handle.

``update``
    The real ``ProjectUpdateService.draft_update``: the episode's sources
    become the project's evidence inventory, and the drafted claims come back
    with their C2 axes.

The model is the ONLY substituted part, and only in ``--engine canned``: the
product's own endpoint profile is pointed at a local OpenAI-compatible stub
that answers with recorded text, so the provider client, the egress guard, the
route preflight, admission, the adapters, the parsers and the persistence are
the product's own on both paths.

Isolation: the caller (``scripts/phase200_eval.py``) patches ``Path.home`` and
``os.path.expanduser`` to a temporary directory before this module builds
anything.  Every episode gets its own database.

What this module does NOT establish, stated once so no report implies it:

- The meeting collector mints its dispatch handle through the test-side
  admission rig, not the intel queue's scheduler; queue behaviour is out of
  scope here and is covered by the meeting suites.
- A canned run proves the plumbing, never the model.  Only a run against a
  real route is evidence about a model.
- The update leg models an unavailable source by leaving it out of the seeded
  evidence inventory: it measures what the drafter does with what it can read.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Mapping
from unittest.mock import patch

from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "phase200-eval")

#: The profile id the evaluation route is defined as.  It is deliberately NOT
#: the model id.  It used to be: ``_resolve_for_capability`` matched
#: ``deployment_revisions.model`` against the assigned PROFILE id, so only a
#: profile named after its model resolved at all, and every other one fell
#: back to the deterministic drafter with a log line.  HS-200-08 resolves the
#: deployment through the route plan the Ask path uses, so the harness now
#: runs the shape a real desk has (profile id != model id) and a model run is
#: a model run; the report records the generator each episode came back with.
EVAL_PROFILE_ID = "phase200-eval-route"

#: Kept as the legacy alias for the id above.
EVAL_PROFILE_PREFIX = EVAL_PROFILE_ID

#: Capabilities that resolve by their own assignment key, not the global one.
CAPABILITY_ASSIGNMENTS: tuple[str, ...] = ("project.update_draft",)

NOW_ISO = "2026-06-15T10:00:00"


class EngineUnavailable(RuntimeError):
    """The selected engine cannot serve this category."""


# ── The canned provider leaf ──────────────────────────────────────────


class CannedSource:
    """The recorded outputs, shared by every canned leaf in one run."""

    def __init__(self, canned: Mapping[str, Any]) -> None:
        self.canned = dict(canned or {})
        self.episode_id = ""
        self.calls: list[dict[str, Any]] = []

    def _entries(self) -> list[Mapping[str, Any]]:
        episodes = self.canned.get("episodes") or {}
        entry = episodes.get(self.episode_id)
        if isinstance(entry, str):
            return [{"match": "", "text": entry}]
        if isinstance(entry, list):
            return list(entry)
        return []

    def select(self, prompt: str) -> str:
        """The first entry whose ``match`` appears in the prompt, else the default."""
        lowered = prompt.lower()
        for entry in self._entries():
            match = str(entry.get("match", "")).lower()
            if not match or match in lowered:
                text = str(entry.get("text", ""))
                break
        else:
            text = str(self.canned.get("default", ""))
        self.calls.append({"episode": self.episode_id, "chars": len(prompt), "output": text})
        return text


class CannedModelServer:
    """A local OpenAI-compatible endpoint that answers with recorded text.

    ``--engine canned`` points the product's own endpoint profile at this
    server, so the provider client, the egress guard, the route preflight, the
    adapters and the parsers are all the product's own.  Only the model is a
    stand-in -- which is exactly what "substituted model adapter" means.

    It speaks the two calls the product makes: ``GET /v1/models`` (readiness)
    and ``POST /v1/chat/completions``, streaming or not.
    """

    def __init__(self, source: CannedSource, *, model: str = "canned") -> None:
        self._source = source
        self._model = model
        self._server: Any = None
        self._thread: Any = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}/v1"

    def start(self) -> "CannedModelServer":
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        source = self._source
        model = self._model

        class _Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: Any) -> None:  # silence the access log
                return

            def _json(self, payload: Mapping[str, Any], status: int = 200) -> None:
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802 - the stdlib's spelling
                if self.path.rstrip("/").endswith("/models"):
                    self._json({"object": "list", "data": [{"id": model, "object": "model"}]})
                    return
                self._json({"error": "not found"}, status=404)

            def do_POST(self) -> None:  # noqa: N802 - the stdlib's spelling
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    request = json.loads(raw.decode() or "{}")
                except json.JSONDecodeError:
                    request = {}
                text = source.select(json.dumps(request.get("messages", []), default=str))
                if request.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    chunk = {
                        "id": "canned", "object": "chat.completion.chunk", "model": model,
                        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
                    }
                    done = {
                        "id": "canned", "object": "chat.completion.chunk", "model": model,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    for frame in (chunk, done):
                        self.wfile.write(f"data: {json.dumps(frame)}\n\n".encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                    return
                self._json({
                    "id": "canned",
                    "object": "chat.completion",
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                })

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)


# ── Hub ───────────────────────────────────────────────────────────────


@dataclass
class EvaluationHub:
    """One isolated evaluation session over one selected route."""

    home: Path
    engine: str
    endpoint: str
    model: str
    canned: CannedSource | None = None
    route: dict[str, Any] = field(default_factory=dict)

    @property
    def profile_id(self) -> str:
        """The route profile's id -- never the model id (see EVAL_PROFILE_ID)."""
        return EVAL_PROFILE_ID

    # -- route -------------------------------------------------------

    def route_facts(self) -> dict[str, Any]:
        return dict(self.route)

    def _seed_route(self, db: Any) -> None:
        """Define the endpoint profile and assign it globally, as the product does."""
        from holdspeak.config import Config
        from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
        from holdspeak.services.model_library_service import ModelLibraryApplicationService

        setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: self.home)
        acquisition = InferenceAcquisitionApplicationService(
            db, setup_service=setup, model_root=self.home / "models", home_provider=lambda: self.home
        )
        ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).define_endpoint(
            OWNER,
            {
                "request_id": "phase200-eval-model",
                "profile_id": self.profile_id,
                "expected_profile_revision": 0,
                "label": "Phase 200 evaluation route",
                "provider_family": "private_endpoint",
                "model": self.model or "canned",
                "endpoint": self.endpoint or "http://127.0.0.1:1/v1",
                "requires_key": False,
            },
        )
        assignments = InferenceAssignmentService(db)
        assignments.set_assignment(
            OWNER,
            {
                "command_id": "phase200-eval-assignment",
                "expected_revision": 0,
                "scope": {"kind": "global"},
                "entries": [{"profile_id": self.profile_id, "profile_revision": 1}],
            },
        )
        # The update drafter resolves `capability:project.update_draft` by that
        # exact key (project_update_service._resolve_for_capability); a global
        # assignment does not create it, and without it the model drafter falls
        # back to the deterministic one and the run measures nothing.
        for capability_id in CAPABILITY_ASSIGNMENTS:
            assignments.set_assignment(
                OWNER,
                {
                    "command_id": f"phase200-eval-{capability_id}",
                    "expected_revision": 0,
                    "scope": {"kind": "capability", "capability_id": capability_id},
                    "entries": [{"profile_id": self.profile_id, "profile_revision": 1}],
                },
            )

    def probe_route(self) -> dict[str, Any]:
        """Ask the product where this route actually goes, before spending 33 episodes."""
        from holdspeak.db import get_database, reset_database
        from holdspeak.kernel import runtime
        from holdspeak.services import route_probe

        reset_database()
        db = get_database(self.home / "route.db")
        self._seed_route(db)
        broker = runtime._configure(db)
        try:
            preview = route_probe.preview_route(broker)
            facts: dict[str, Any] = {
                "engine": self.engine,
                "model": self.model or "canned",
                "endpoint": self.endpoint,
                "capability": preview.get("capabilityId", ""),
                "legs": preview.get("legs", []),
                "off_machine": preview.get("offMachine"),
            }
            probe = route_probe.task_probe(
                broker, OWNER, db=db, allow_off_machine=True, nonce="phase200-eval"
            )
            facts.update({
                "state": probe.get("state"),
                "plan_id": probe.get("routePlanId", ""),
                "boundary": probe.get("boundary", ""),
                "host": probe.get("host", ""),
                "probe_model": probe.get("model", ""),
                "probe_engine": probe.get("engine", ""),
                "probe_latency_ms": probe.get("latencyMs"),
                "reason_code": probe.get("reasonCode", ""),
            })
        except Exception as exc:
            facts = {
                "engine": self.engine,
                "model": self.model or "canned",
                "endpoint": self.endpoint,
                "probe_error": f"{type(exc).__name__}: {exc}",
            }
        finally:
            runtime._dispose(broker)
            reset_database()
        self.route = facts
        return facts

    # -- the supplementary judge (never gating) ----------------------

    def judge_outputs(
        self, episodes: list[Mapping[str, Any]], outputs: Mapping[str, Mapping[str, Any]]
    ) -> dict[str, Any]:
        """Ask the same route to score each answer. One column, never a verdict.

        §C12 and the phase's evidence levels: a model judge may assist triage
        and cannot supply acceptance evidence.  Nothing in the report reads
        this to decide a pass, and a critical failure stays a failure whatever
        a judge said.
        """
        from holdspeak.db import get_database, reset_database
        from holdspeak.kernel import runtime
        from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

        reset_database()
        db = get_database(self.home / "judge.db")
        self._seed_route(db)
        broker = runtime._configure(db)
        adoption = broker.inference_adoption_service
        scores: dict[str, Any] = {}
        try:
            for episode in episodes:
                key = str(episode["id"])
                output = outputs.get(key) or {}
                invocation_id = "phase200judge" + hashlib.sha256(key.encode()).hexdigest()[:20]
                payload = {
                    "schema_version": 2,
                    "system_prompt": (
                        "You score an assistant answer for usefulness only. Reply with one "
                        "digit from 1 to 5 and nothing else. 5 means a reviewer could act on "
                        "it unchanged; 1 means it is useless."
                    ),
                    "user_prompt": (
                        f"TASK: {episode['title']}\n\nMATERIAL:\n"
                        f"{json.dumps(episode['material'], default=str)[:4000]}\n\n"
                        f"ANSWER:\n{str(output.get('text') or '')[:4000]}"
                    ),
                    "lens": "Judge",
                    "context_ids": [],
                    "context_titles": [],
                    "grounding": None,
                    "source_text": "",
                    "temperature": None,
                    "max_tokens": 8,
                }
                try:
                    admitted = adoption.admit(
                        OWNER,
                        command_id=f"admit-{invocation_id}",
                        capability_id="ask.answer",
                        operation_id=invocation_id,
                        payload=payload,
                        invocation_id=invocation_id,
                        reserved_output_tokens=8,
                    )
                    routed = adoption.execute(
                        OWNER,
                        execution_id=str(admitted["execution"]["id"]),
                        adapter=CanonicalPromptAdapter(),
                    )
                    result = routed.get("result") if isinstance(routed.get("result"), Mapping) else {}
                    raw = str((result or {}).get("output") or "").strip()
                    digits = re.findall(r"[1-5]", raw)
                    scores[key] = {"raw": raw[:40], "score": int(digits[0]) if digits else None}
                except Exception as exc:
                    scores[key] = {"raw": "", "score": None, "error": f"{type(exc).__name__}: {exc}"}
        finally:
            runtime._dispose(broker)
            reset_database()
        return {
            "enabled": True,
            "note": "supplementary only; never gating",
            "capability": "ask.answer",
            "scores": scores,
        }

    # -- dispatch ----------------------------------------------------

    def run_episode(self, episode: Mapping[str, Any]) -> dict[str, Any]:
        if self.canned is not None:
            self.canned.episode_id = str(episode["id"])
        category = episode["category"]
        if category == "interview":
            return self.run_interview(episode)
        if category == "meeting":
            return self.run_meeting(episode)
        if category == "update":
            return self.run_update(episode)
        raise EngineUnavailable(f"no collector for category {category!r}")

    # -- interview ---------------------------------------------------

    def run_interview(self, episode: Mapping[str, Any]) -> dict[str, Any]:
        """Replay the episode's owner turns through the real Interview thread."""
        from fastapi.testclient import TestClient

        from holdspeak.db import get_database, reset_database
        from holdspeak.kernel import runtime
        from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.thread_modes import seed_modes
        from holdspeak.services.thread_service import ThreadService
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        material = episode["material"]
        reset_database()
        db = get_database(self.home / f"{episode['id'].lower()}-interview.db")
        seed_modes(db)
        self._seed_route(db)
        if material.get("project"):
            ProjectService(db).create_project(
                OWNER, {"name": str(material["project"]), "description": "Phase 200 evaluation episode"}
            )
        broker = runtime._configure(db)
        token = "phase200-eval"
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
            auth_token=token,
        )
        turns: list[dict[str, Any]] = []
        state: dict[str, Any] = {}
        error = ""
        try:
            with TestClient(server.app, headers={"Authorization": f"Bearer {token}"}) as client:
                created = client.post(
                    "/api/threads",
                    json={"title": f"Phase 200 {episode['id']}", "recipe_id": INTERVIEW_MODE_ID},
                )
                if created.status_code != 201:
                    raise RuntimeError(f"thread create failed: {created.status_code} {created.text}")
                thread_id = created.json()["id"]

                prompts = [
                    str(turn.get("text", ""))
                    for turn in material.get("prior_turns", [])
                    if turn.get("role") == "owner"
                ]
                if material.get("prompt"):
                    prompts.append(str(material["prompt"]))

                detail: dict[str, Any] = {}
                for text in prompts:
                    posted = client.post(f"/api/threads/{thread_id}/turns", json={"text": text})
                    if posted.status_code != 201:
                        raise RuntimeError(f"turn failed: {posted.status_code} {posted.text}")
                    message_id = posted.json()["assistant_message_id"]
                    deadline = time.monotonic() + 180
                    while time.monotonic() < deadline:
                        detail = client.get(f"/api/threads/{thread_id}").json()
                        message = next((m for m in detail["messages"] if m["id"] == message_id), None)
                        if message and (message.get("completed_at") or message.get("aborted_at")):
                            break
                        time.sleep(0.2)
                    else:
                        raise TimeoutError("an Interview turn exceeded 180 seconds")
                    answer = "\n".join(
                        part.get("text") or "" for part in message["parts"] if part["kind"] == "text"
                    )
                    turns.append({
                        "owner": text,
                        "assistant": answer,
                        "error": message.get("error_json"),
                        "egress": message.get("egress_scope"),
                    })
                    if message.get("error_json"):
                        error = json.dumps(message["error_json"], default=str)
                        break
                state = (detail or {}).get("interview", {}) or {}
        finally:
            for event in list(ThreadService._active_turns.values()):
                event.set()
            runtime._dispose(broker)
            reset_database()

        answer = turns[-1]["assistant"] if turns else ""
        facts = state.get("facts") or {}
        return {
            "text": answer,
            "questions": _questions_in(answer),
            "fields": _fields_from_facts(facts),
            "claims": [],
            "decisions": [],
            "turns": turns,
            "interview_facts": facts,
            "interview_suggestions": list((state.get("suggestions") or {}).keys()),
            "error": error,
        }

    # -- meeting -----------------------------------------------------

    def run_meeting(self, episode: Mapping[str, Any]) -> dict[str, Any]:
        """Run the real plugin chain over the episode's transcript."""
        import holdspeak.db as hsdb
        from holdspeak.db import Database, reset_database
        from holdspeak.meeting_plugins import build_bound_meeting_plugin_host, run_meeting_plugin_chain
        from holdspeak.meeting_session import MeetingState, TranscriptSegment

        material = episode["material"]
        meeting_id = f"eval-{episode['id'].lower()}"
        reset_database()
        db = Database(self.home / f"{episode['id'].lower()}-meeting.db")
        started = datetime(2026, 6, 15, 10, 0, 0)
        segments = [
            TranscriptSegment(
                text=str(segment.get("text", "")),
                speaker=str(segment.get("speaker", "")),
                start_time=float(index * 60),
                end_time=float(index * 60 + 50),
            )
            for index, segment in enumerate(material.get("segments", []))
        ]
        state = MeetingState(
            id=meeting_id,
            started_at=started,
            ended_at=started + timedelta(minutes=30),
            title=str(material.get("meeting", episode["title"])),
            tags=[],
            segments=segments,
        )
        db.meetings.save_meeting(state)
        meeting = db.meetings.get_meeting(meeting_id)

        # The product's own installed host: the real builtin plugins, the real
        # project detector, the real disabled-plugin disposition.
        wrapper = _AdmittedHost(build_bound_meeting_plugin_host(), self._meeting_engine)

        with patch.object(hsdb, "get_database", lambda *a, **k: db), \
             patch("holdspeak.intel_queue.get_database", lambda *a, **k: db):
            summary = run_meeting_plugin_chain(db, meeting, profile="balanced", host=wrapper)

        artifacts = {row.artifact_type: row for row in db.plugins.list_artifacts(meeting_id)}
        decisions = list((getattr(artifacts.get("decisions"), "structured_json", None) or {}).get("decisions", []))
        open_questions = list(
            (getattr(artifacts.get("decisions"), "structured_json", None) or {}).get("open_questions", [])
        )
        action_items = list(
            (getattr(artifacts.get("action_items"), "structured_json", None) or {}).get("action_items", [])
        )
        reset_database()

        first_action = action_items[0] if action_items else {}
        fields: dict[str, Any] = {
            "decision": (decisions[0].get("decision") if decisions else None),
            # The extraction path carries no acceptance axis. Producing a
            # decision at all is an assertion that one was taken.
            "decision_acceptance": ("asserted" if decisions else None),
            "action_owner": first_action.get("owner") if action_items else None,
            "due_date": first_action.get("due") if action_items else None,
        }
        text = " ".join(
            [
                *(str(row.get("decision", "")) for row in decisions),
                *(str(row.get("rationale") or "") for row in decisions),
                *(str(row.get("task", "")) for row in action_items),
                *(str(question) for question in open_questions),
            ]
        )
        return {
            "text": text,
            "questions": list(open_questions),
            "fields": fields,
            "claims": [],
            "decisions": [
                {"id": "", "text": str(row.get("decision", "")), "state": "", "current": True}
                for row in decisions
            ],
            "action_items": action_items,
            "plugin_statuses": summary.get("plugin_statuses", {}),
            "artifacts_saved": summary.get("artifacts_saved", 0),
            "error": "",
        }

    def _meeting_engine(self) -> Any:
        """The provider leaf the plugin dispatch runs on.

        The product's own endpoint engine on both paths: under ``--engine
        canned`` the endpoint is the local stub server, so the provider client
        and its egress guard are still the real ones.
        """
        from holdspeak.intel.engine import MeetingIntel

        return MeetingIntel(
            provider="cloud",
            cloud_model=self.model or "canned",
            cloud_base_url=self.endpoint,
        )

    # -- update ------------------------------------------------------

    def run_update(self, episode: Mapping[str, Any]) -> dict[str, Any]:
        """Draft a grounded Project update over the episode's evidence."""
        from holdspeak.db import Database, reset_database
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_update_service import ProjectUpdateService

        reset_database()
        db = Database(self.home / f"{episode['id'].lower()}-update.db")
        project_id, ref_map = _seed_update_material(db, episode)

        collector = ProjectEvidenceCollector(db)
        delta = ProjectDeltaService(db, collector)
        projects = ProjectService(db, delta_service=delta)

        # The route is seeded on both paths: the model drafter resolves an
        # assignment for `project.update_draft` before it reaches any engine,
        # and a canned run must clear the same gate the live one does.
        self._seed_route(db)
        from holdspeak.kernel import runtime

        # The real broker on both paths: the model drafter resolves its own
        # assignment, builds the product's engine and reaches the selected
        # endpoint, which under --engine canned is the local stub.
        broker = runtime._configure(db)

        service = ProjectUpdateService(db, project_service=projects, delta_service=delta, broker=broker)
        try:
            drafted = service.draft_update(OWNER, project_id, generator="model")
        finally:
            runtime._dispose(broker)
            reset_database()

        claims = json.loads(drafted.get("claims_json") or "[]")
        unknowns = [unknown for claim in claims for unknown in (claim.get("unknowns") or [])]
        return {
            "text": drafted.get("body_md", ""),
            "questions": [],
            "fields": _fields_from_unknowns(unknowns),
            "claims": claims,
            "decisions": [],
            "unknowns": unknowns,
            "ref_map": ref_map,
            "generator": drafted.get("generator", ""),
            "generator_host": drafted.get("generator_host", ""),
            "generator_model": drafted.get("generator_model", ""),
            "source_manifest": json.loads(drafted.get("source_manifest_json") or "{}"),
            "error": "",
        }


class _AdmittedHost:
    """A host wrapper that mints one admitted dispatch handle per plugin.

    ``run_meeting_plugin_chain`` with no admission passes ``dispatch=None``,
    which the real host refuses for every ``llm`` plugin -- correctly, since a
    plugin may not reach a model without a handle the host minted over an
    engine a claimed child built.  The evaluation driver is not the intel
    queue, so it mints that handle the way the test rig does: through a REAL
    kernel submit/decide/claim.  Every authority check on the path stays the
    product's own; only the provider leaf is selectable.
    """

    def __init__(self, host: Any, engine_factory: Any) -> None:
        self._host = host
        self._engine_factory = engine_factory

    def execute_chain(
        self,
        plugin_chain: Any,
        *,
        context: Any,
        meeting_id: str,
        window_id: str,
        transcript_hash: str,
        defer_heavy: bool,
        dispatch: Any = None,
    ) -> list[Any]:
        from tests.unit.plugin_dispatch_rig import admitted_engine, unbind

        results = []
        for plugin_id in plugin_chain:
            engine, dispatch_context = admitted_engine(engine=self._engine_factory())
            try:
                with self._host.issued_dispatch(engine) as handle:
                    results.append(
                        self._host.execute(
                            plugin_id,
                            context=context,
                            meeting_id=meeting_id,
                            window_id=window_id,
                            transcript_hash=transcript_hash,
                            defer_heavy=defer_heavy,
                            dispatch=handle,
                        )
                    )
            finally:
                unbind(engine, dispatch_context)
        return results


# ── Seeding one update episode's evidence inventory ───────────────────


def _row_id(prefix: str, slug: str, ordinal: int) -> str:
    """A deterministic 36-character row id: same episode, same ids, every run."""
    return f"{prefix}_{slug}_{ordinal:04d}".ljust(36, "0")[:36]


def _item_type(source: Mapping[str, Any]) -> str:
    ref = f"{source.get('ref', '')} {source.get('title', '')}".lower()
    if "risk" in ref:
        return "risk"
    if "board" in ref or "depend" in ref:
        return "dependency"
    if "decision" in ref:
        return "milestone"
    return "workstream"


def _seed_update_material(db: Any, episode: Mapping[str, Any]) -> tuple[str, dict[str, str]]:
    """The episode's material, written into the tables the drafter reads.

    A revoked or failed source is deliberately NOT written: an unavailable
    source is not evidence, and the drafter must reach the same conclusion
    from the inventory it can actually read.

    Returns the project id and the map from the episode's source refs to the
    refs the product will cite, so a citation invariant can name the episode's
    source and still judge the run's own claims.
    """
    ref_map: dict[str, str] = {}
    material = episode["material"]
    slug = episode["id"].lower().replace("-", "")
    project_id = f"proj_{slug}"
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision, created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, 5, ?, ?)""",
            (project_id, str(material.get("project", episode["title"])), NOW_ISO, NOW_ISO),
        )

        ordinal = 0
        for source in material.get("sources", []):
            if str(source.get("state", "")) in {"revoked", "failed"}:
                continue
            ordinal += 1
            item_id = _row_id("pitem", slug, ordinal)
            ref_map[str(source.get("ref", ""))] = f"item:{item_id}"
            fields = source.get("fields") or {}
            lifecycle = str(fields.get("status") or "active")
            title = f"{source.get('title', source.get('ref', 'source'))} ({source.get('version', 'unknown')}): {source.get('text', '')}"
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)""",
                (
                    item_id,
                    project_id,
                    _item_type(source),
                    title.strip(),
                    lifecycle,
                    float(ordinal),
                    NOW_ISO,
                    NOW_ISO,
                ),
            )

        for correction in material.get("corrections", []):
            ordinal += 1
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, 'workstream', ?, 'active', NULL, NULL, ?, ?, ?)""",
                (
                    _row_id("pitem", slug, ordinal),
                    project_id,
                    f"Correction stated on {correction.get('stated_at', 'an earlier day')}: "
                    f"{correction.get('field')} is {correction.get('right')}, "
                    f"correcting the earlier {correction.get('wrong')}.",
                    float(ordinal),
                    NOW_ISO,
                    NOW_ISO,
                ),
            )

        decisions = material.get("prior_decisions") or []
        if decisions:
            review_id = _row_id("prev", slug, 1)
            conn.execute(
                """INSERT INTO project_reviews
                   (id, project_id, status, source_manifest_json, opened_at)
                   VALUES (?, ?, 'open', '{}', ?)""",
                (review_id, project_id, NOW_ISO),
            )
            for index, decision in enumerate(decisions, start=1):
                proposal_id = _row_id("pprop", slug, index)
                ref_map[str(decision.get("id", index))] = f"decision:{proposal_id}"
                state = str(decision.get("state", "accepted"))
                marker = ""
                if state == "superseded":
                    marker = f" (superseded by {decision.get('superseded_by', 'a later decision')})"
                conn.execute(
                    """INSERT INTO project_proposals
                       (id, project_id, review_window_key, proposal_kind, target_ref,
                        title, lifecycle, created_at)
                       VALUES (?, ?, ?, 'observation_attention', ?, ?, ?, ?)""",
                    (
                        proposal_id,
                        project_id,
                        review_id,
                        f"decision:{decision.get('id', index)}",
                        f"{decision.get('id')}: {decision.get('text', '')}{marker}",
                        "accepted" if state == "accepted" else "open",
                        NOW_ISO,
                    ),
                )

        source_id = _row_id("psrc", slug, 1)
        conn.execute(
            """INSERT OR IGNORE INTO project_sources
               (id, project_id, source_ref, label, semantic_role,
                enabled, revision, created_at, updated_at)
               VALUES (?, ?, 'watch:phase200-eval', 'Episode material', 'pull_request',
                       1, 0, ?, ?)""",
            (source_id, project_id, NOW_ISO, NOW_ISO),
        )
        conn.execute(
            """INSERT OR IGNORE INTO project_observations
               (id, project_id, source_id, observation_kind,
                observed_at, captured_at, fact_json, content_hash)
               VALUES (?, ?, ?, 'snapshot_transition', ?, ?, '{}', '')""",
            (_row_id("pobs", slug, 1), project_id, source_id, NOW_ISO, NOW_ISO),
        )
    return project_id, ref_map


# ── Normalisation helpers ─────────────────────────────────────────────


def _questions_in(text: str) -> list[str]:
    lines = []
    for chunk in str(text or "").replace("\n", " ").split("? "):
        candidate = chunk.strip()
        if candidate and not candidate.endswith("?"):
            candidate += "?"
        if candidate.endswith("?") and len(candidate) > 4:
            lines.append(candidate)
    return lines if str(text or "").strip().find("?") >= 0 else []


def _fields_from_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Interview facts, keyed by their own label so a field check can find them."""
    fields: dict[str, Any] = {}
    for value in (facts or {}).values():
        if not isinstance(value, Mapping):
            continue
        label = str(value.get("label") or value.get("key") or "").strip().lower().replace(" ", "_")
        if label:
            fields[label] = value.get("value")
    return fields


#: A typed unknown's type, and the field names it answers for.
_UNKNOWN_TYPE_HINTS = {
    "deadline": ("date", "deadline", "due", "when"),
    "name": ("owner", "name", "identity", "reviewer"),
    "number": ("budget", "headcount", "count", "number", "amount", "price"),
}


def _fields_from_unknowns(unknowns: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Typed unknowns the drafter recorded, expressed as unknown field values."""
    fields: dict[str, Any] = {}
    for unknown in unknowns:
        kind = str(unknown.get("type", ""))
        for hint in _UNKNOWN_TYPE_HINTS.get(kind, ()):  # a coarse but honest mapping
            fields.setdefault(hint, {"unknown": kind})
    return fields


@contextmanager
def evaluation_hub(
    *,
    home: Path,
    engine: str,
    endpoint: str = "",
    model: str = "",
    canned: Mapping[str, Any] | None = None,
) -> Iterator[EvaluationHub]:
    """An isolated evaluation session. Yields the hub with its route resolved."""
    from holdspeak.config import Config
    from holdspeak.kernel import runtime

    config = Config()
    config.control_mode = "yolo"
    source = CannedSource(canned or {}) if engine == "canned" else None
    server: CannedModelServer | None = None

    with patch.object(Config, "load", return_value=config), \
         patch.object(runtime, "_mode", return_value="yolo"):
        try:
            if source is not None:
                server = CannedModelServer(source, model=model or "canned").start()
                endpoint = server.base_url
                model = model or "canned"
            hub = EvaluationHub(
                home=Path(home), engine=engine, endpoint=endpoint, model=model, canned=source
            )
            hub.probe_route()
            yield hub
        finally:
            if server is not None:
                server.stop()
