"""Owner pick 2026-10-05 (route in footer), hardened by Astra's #875 review.

The lamp a turn wears is the LEAST PRIVATE attempt that was SENT (any send
phase past dispatch), read from the turn's route execution receipt, never the
admitted plan; the receipt token always belongs to the route shown; one
classifier (``intel.providers.egress_boundary``) decides every endpoint.
The thread and Ask cases run the REAL route chain (admission, the fallback
controller, the receipt) with fixture engines."""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db.core import Database
from holdspeak.inference_locality import deployment_lamp, least_private, served_route
from holdspeak.intel.providers import egress_boundary
from holdspeak.loopback_http import endpoint_lamp
from holdspeak.services.ask_service import AskService


# ── one classifier ──────────────────────────────────────────────────────────

HOSTS = [
    "localhost", "localhost.", "127.0.0.1", "127.0.0.1.", "[::1]", "box.local",
    "box.local.", "localhost.localdomain", "x.localhost", "192.168.1.43",
    "10.0.0.5", "169.254.1.1", "api.openai.com", "8.8.8.8",
]


@pytest.mark.parametrize("host", HOSTS)
def test_every_lamp_is_the_one_egress_verdict(host) -> None:
    url = f"http://{host}:8080/v1"
    verdict = egress_boundary(base_url=url)
    assert endpoint_lamp(url) == verdict
    assert deployment_lamp("private_network", url) == verdict
    assert deployment_lamp("external_service", url) == verdict
    assert deployment_lamp("same_device", url) == verdict


# ── served_route over a receipt ─────────────────────────────────────────────


def _deployment(db: Database, rid: str, *, boundary: str, endpoint: str = "", node: str = "", model: str = "m") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO deployment_revisions (id,destination_id,kind,engine,model,boundary,endpoint,node)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (rid, "dest", "endpoint", "openai_compatible", model, boundary, endpoint, node),
        )


@pytest.fixture()
def db(tmp_path):
    db = Database(tmp_path / "route.db")
    _deployment(db, "lan", boundary="private_network", endpoint="http://192.168.1.43:8080/v1", model="qwen3.8-27b")
    _deployment(db, "loop", boundary="private_network", endpoint="http://127.0.0.1:11434/v1", model="qwen3.5-4b")
    _deployment(db, "loopdot", boundary="private_network", endpoint="http://localhost.:11434/v1", model="qwen3.5-4b")
    _deployment(db, "cloud", boundary="external_service", endpoint="https://api.openai.com/v1", model="gpt-5-mini")
    _deployment(db, "inproc", boundary="same_device", model="Qwen3.5 4B")
    _deployment(db, "mesh", boundary="private_mesh", node="studio-mac", model="qwen-mesh")
    return db


def _attempt(rid: str, boundary: str, phase: str = "provider_returned", aid: str = "") -> dict:
    return {"attempt_id": aid or f"a-{rid}", "deployment_revision_id": rid, "boundary": boundary, "send_phase": phase}


def _won(rid: str, boundary: str) -> dict:
    return {"execution_id": "exec-0000a91f", "attempts": [_attempt(rid, boundary)], "winning_attempt_id": f"a-{rid}"}


@pytest.mark.parametrize(
    ("rid", "boundary", "lamp", "host", "model"),
    [
        ("lan", "private_network", "private_network", "192.168.1.43", "qwen3.8-27b"),
        ("loop", "private_network", "local", "", "qwen3.5-4b"),
        # #855 and the one classifier: "localhost." is never LOCAL; the LAN.
        ("loopdot", "private_network", "private_network", "localhost.", "qwen3.5-4b"),
        ("cloud", "external_service", "cloud", "api.openai.com", "gpt-5-mini"),
        ("inproc", "same_device", "local", "", "Qwen3.5 4B"),
        ("mesh", "private_mesh", "mesh", "studio-mac", "qwen-mesh"),
    ],
)
def test_the_sent_deployment_names_the_route(db, rid, boundary, lamp, host, model) -> None:
    with db._connection() as conn:
        assert served_route(conn, _won(rid, boundary)) == {
            "lamp": lamp, "host": host, "model": model, "receipt": "exec-0000a91f", "fallback": False,
        }


def test_a_cloud_send_is_never_hidden_behind_a_local_fallback(db) -> None:
    receipt = {
        "execution_id": "exec-1",
        "attempts": [_attempt("cloud", "cloud", "provider_no_generation"), _attempt("inproc", "local")],
        "winning_attempt_id": "a-inproc",
    }
    with db._connection() as conn:
        route = served_route(conn, receipt)
    assert (route["lamp"], route["host"], route["model"], route["fallback"]) == ("cloud", "api.openai.com", "gpt-5-mini", True)


def test_no_sent_attempt_no_lamp(db) -> None:
    receipt = {"execution_id": "exec-2", "attempts": [_attempt("lan", "private_network", "pre_send")]}
    with db._connection() as conn:
        assert served_route(conn, receipt)["lamp"] == ""
        assert served_route(conn, {"attempts": []})["lamp"] == ""


def test_not_a_route_receipt_returns_none(db) -> None:
    with db._connection() as conn:
        assert served_route(conn, {"id": "receipt_test", "outcome": "succeeded"}) is None
        assert served_route(conn, None) is None


def test_least_private_pass_keeps_its_own_receipt() -> None:
    cloud = {"lamp": "cloud", "host": "api.openai.com", "model": "c", "receipt": "exec-cloud", "fallback": False}
    local = {"lamp": "local", "host": "", "model": "l", "receipt": "exec-local", "fallback": False}
    assert least_private([cloud, local]) is cloud
    assert least_private([local, {**local, "lamp": ""}]) is local
    assert least_private([{**local, "lamp": ""}]) is None


def test_the_ask_projection_names_the_leg_that_answered(db) -> None:
    route = {"entries": [{"ordinal": 1, "profile_id": "p1", "deployment_revision_id": "lan", "boundary": "private_network"}]}
    result = AskService._routed_projection(
        SimpleNamespace(_db=db), {"output": "answer"}, {"lens": "Ask", "context_ids": [], "context_titles": []},
        None, route, route_leg_ordinal=1,
    )
    assert result["egress"] == {"scope": "private_network", "host": "192.168.1.43"}
    assert result["actual_placement"]["boundary"] == "private_network"


# ── the real route chain: thread turns and the Ask ──────────────────────────


def _hub(tmp_path: Path, profiles: list[str]):
    from holdspeak.deployment_revisions import DeploymentRevision
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    endpoints = {"cloud": ("external_service", "https://api.openai.com/v1"), "local": ("same_device", "")}
    db = Database(tmp_path / "hub.db")
    original = DeploymentRevision.__dict__["from_artifact"]
    for pid in profiles:
        boundary, endpoint = endpoints[pid]

        def with_endpoint(cls, *, _endpoint=endpoint, **kw):
            return original.__func__(cls, **{**kw, "endpoint": _endpoint})

        DeploymentRevision.from_artifact = classmethod(with_endpoint)
        try:
            _profile(db, pid, model=f"{pid}-model", boundary=boundary, claims=(
                "language", _result_claim("chat.turn"), _result_claim("ask.answer"),
                _result_claim("thought.interview"), _result_claim("speech.intent_classify")))
        finally:
            DeploymentRevision.from_artifact = original
    return db, _configure(db)


def _assign(db, pids: list[str], n: int) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER

    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"route-{n}", "expected_revision": n - 1,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": p, "profile_revision": 1} for p in pids],
    })


def _executions(db) -> list[str]:
    with db._connection() as conn:
        return [r["id"] for r in conn.execute("SELECT id FROM inference_route_executions ORDER BY rowid")]


def _turn(svc, db, frames, *, abort_after=None, before=None):
    from tests.unit.test_phase143_inference_assignments import OWNER

    if before is not None:
        original = svc._run_streaming_turn
        svc._run_streaming_turn = lambda **kw: (before(kw), original(**kw))[1]
    tid = svc.create(title="Cutover risks")["id"]
    turn = asyncio.run(svc.start_turn(OWNER, tid, "Explain the risks."))
    if abort_after is not None:
        assert abort_after[0].wait(10)
        svc.abort(tid)
        abort_after[1].set()
    end = time.monotonic() + 20
    while time.monotonic() < end and not any(t == "thread_turn_done" for t, _ in frames):
        time.sleep(0.05)
    done = [d for t, d in frames if t == "thread_turn_done"][-1]
    msg = db.threads.get_message(turn["assistant_message_id"])
    wire = [m for m in svc.get(tid)["messages"] if m["id"] == msg.id][0]
    return done, msg, wire


class _Engine:
    active_provider = "fixture"

    def __init__(self, rev, script):
        self.active_model = rev.model
        self._script = script

    def run_prompt_stream(self, **_kw):
        yield from self._script(self.active_model)

    def run_prompt(self, **_kw):
        return "".join(d.text for d in self._script(self.active_model) if d.kind == "text")


def test_thread_fallback_after_a_cloud_send_shows_cloud(tmp_path) -> None:
    from holdspeak.kernel.inference_stream import Delta
    from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
    from holdspeak.services.thread_service import ThreadService

    db, broker = _hub(tmp_path, ["cloud", "local"])
    _assign(db, ["cloud", "local"], 1)

    def script(model):
        if model == "cloud-model":
            raise ProviderPermanentNoGeneration()
        yield Delta(kind="text", text="answer")
        yield Delta(kind="done")

    broker.inference_runner._engine_factory = lambda rev, **kw: _Engine(rev, script)
    frames: list = []
    done, msg, wire = _turn(ThreadService(db, broker=broker, broadcast=lambda t, d: frames.append((t, d))), db, frames)
    [execution] = _executions(db)
    assert (done["egress"], done["host"], done["model"], done["fallback"]) == ("cloud", "api.openai.com", "cloud-model", True)
    assert done["route_receipt_id"] == execution
    assert (msg.egress_scope, msg.egress_host, msg.egress_receipt_id, msg.egress_fallback) == ("cloud", "api.openai.com", execution, True)
    assert (wire["egress_scope"], wire["egress_receipt_id"], wire["egress_fallback"]) == ("cloud", execution, True)


def test_thread_cancel_before_dispatch_has_no_route(tmp_path) -> None:
    from holdspeak.services.thread_service import ThreadService

    db, broker = _hub(tmp_path, ["cloud"])
    _assign(db, ["cloud"], 1)
    broker.inference_runner._engine_factory = lambda rev, **kw: pytest.fail("no engine may run")
    frames: list = []
    svc = ThreadService(db, broker=broker, broadcast=lambda t, d: frames.append((t, d)))
    done, msg, wire = _turn(svc, db, frames, before=lambda kw: kw["cancel_event"].set())
    assert done["egress"] == "" and done["route_receipt_id"] == ""
    assert (msg.egress_scope, msg.egress_receipt_id) == ("", "")
    started = [d for t, d in frames if t == "thread_turn_started"][-1]
    assert started["egress"] == ""


def test_thread_partial_cancel_keeps_the_real_receipt(tmp_path) -> None:
    from holdspeak.kernel.inference_stream import Delta
    from holdspeak.services.thread_service import ThreadService

    db, broker = _hub(tmp_path, ["cloud"])
    _assign(db, ["cloud"], 1)
    started, release = threading.Event(), threading.Event()

    def script(model):
        yield Delta(kind="text", text="partial ")
        started.set()
        assert release.wait(10)
        yield Delta(kind="text", text="answer")
        yield Delta(kind="done")

    broker.inference_runner._engine_factory = lambda rev, **kw: _Engine(rev, script)
    frames: list = []
    svc = ThreadService(db, broker=broker, broadcast=lambda t, d: frames.append((t, d)))
    done, msg, wire = _turn(svc, db, frames, abort_after=(started, release))
    [execution] = _executions(db)
    assert done["outcome"] == "aborted"
    assert done["receipt_id"] == execution and done["route_receipt_id"] == execution
    assert msg.receipt_id == execution and msg.egress_receipt_id == execution
    assert wire["receipt_id"] == execution
    assert done["egress"] == "cloud"


def test_thread_multipass_pairs_the_route_with_its_own_receipt(tmp_path) -> None:
    from holdspeak.kernel.inference_stream import Delta
    from holdspeak.services.thread_service import ThreadService

    db, broker = _hub(tmp_path, ["cloud", "local"])
    _assign(db, ["cloud"], 1)

    def script(model):
        if model == "cloud-model":
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "tool-1", "type": "function", "function": {"name": "desk.list", "arguments": "{}"}}]})
            _assign(db, ["local"], 2)  # the next pass is admitted on LOCAL
        else:
            yield Delta(kind="text", text="Here are the results.")
        yield Delta(kind="done")

    broker.inference_runner._engine_factory = lambda rev, **kw: _Engine(rev, script)
    frames: list = []
    svc = ThreadService(db, broker=broker, broadcast=lambda t, d: frames.append((t, d)),
                        tool_dispatch_fn=lambda name, args, principal: {"items": []})
    done, msg, wire = _turn(svc, db, frames)
    cloud_pass, local_pass = _executions(db)
    assert done["egress"] == "cloud" and done["model"] == "cloud-model"
    assert done["route_receipt_id"] == cloud_pass
    assert done["receipt_id"] == local_pass
    assert (msg.egress_scope, msg.egress_receipt_id) == ("cloud", cloud_pass)
    assert wire["egress_receipt_id"] == cloud_pass


def test_a_failed_ask_keeps_where_its_bytes_went(tmp_path) -> None:
    from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
    from holdspeak.services.errors import ServiceError
    from holdspeak.web.routes.primitives.ask import _error
    from tests.unit.test_phase143_inference_assignments import OWNER

    db, broker = _hub(tmp_path, ["cloud"])
    broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="cloud"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="cloud"))))

    class Failed:
        active_provider, active_model = "fixture", "cloud-model"

        def run_prompt(self, **_kw):
            raise ProviderPermanentNoGeneration()

    broker.inference_runner._engine_factory = lambda rev, **kw: Failed()
    with pytest.raises(ServiceError) as caught:
        asyncio.run(AskService(db, broker=broker).ask(OWNER, "What are the risks?"))
    response = _error(caught.value)
    assert response.status_code == 409
    import json

    body = json.loads(response.body)
    [execution] = _executions(db)
    assert body["route"] == {"lamp": "cloud", "host": "api.openai.com", "model": "cloud-model",
                             "receipt": execution, "fallback": False}


def test_an_answered_ask_carries_its_receipt_route(tmp_path) -> None:
    from tests.unit.test_phase143_inference_assignments import OWNER

    db, broker = _hub(tmp_path, ["cloud"])
    broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="cloud"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="cloud"))))

    class Answer:
        active_provider, active_model = "fixture", "cloud-model"

        def run_prompt(self, **_kw):
            return "The cutover is on 17 October."

    broker.inference_runner._engine_factory = lambda rev, **kw: Answer()
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "When is the cutover?"))
    [execution] = _executions(db)
    assert result["route"] == {"lamp": "cloud", "host": "api.openai.com", "model": "cloud-model",
                               "receipt": execution, "fallback": False}
    assert result["egress"] == {"scope": "cloud", "host": "api.openai.com"}
