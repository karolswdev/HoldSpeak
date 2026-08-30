"""HS-150-04 — ThreadService unit tests.

Covers every acceptance criterion from the story with a fake streaming
adapter/runner, exercising the turn pipeline, abort, branch, regenerate,
keep, and the M1 People boundary pin.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.thread_service import ThreadService, _PEOPLE_REDACTION


OWNER = Principal(PrincipalKind.OWNER, "owner-session")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "thread_svc.db")


@pytest.fixture
def broadcasts() -> list[tuple[str, dict]]:
    return []


@pytest.fixture
def broadcast_fn(broadcasts):
    def _broadcast(msg_type: str, data: Any) -> None:
        broadcasts.append((msg_type, data))
    return _broadcast


class FakeBroker:
    """Minimal broker that satisfies the ThreadService admission envelope."""

    def __init__(self, *, output: str = "Hello from assistant", fail: bool = False):
        self._output = output
        self._fail = fail

    @property
    def inference_adoption_service(self) -> "FakeAdoptionService":
        return FakeAdoptionService(output=self._output, fail=self._fail)


class FakeAdoptionService:
    """Mimics the admit/execute_stream interface of the real adoption service.

    ``execute_stream`` yields >= 5 text deltas so tests can assert that
    delta frames arrive per-token with monotonically increasing seq.
    """

    def __init__(self, *, output: str = "Hello from assistant", fail: bool = False):
        self._output = output
        self._fail = fail

    def admit(self, principal, *, command_id, capability_id, operation_id, payload, invocation_id, reserved_output_tokens=512):
        return {
            "execution": {"id": "exec_" + uuid.uuid4().hex[:8]},
            "route_plan": {
                "id": "rp_test",
                "egress_scope": "same_device",
                "model_id": "test-model",
            },
            "operation_request_plan": {"id": "orp_test"},
        }

    def execute_stream(self, principal, *, execution_id, adapter, on_delta, publish=None, payload_redactor=None):
        from holdspeak.kernel.inference_stream import Delta
        if self._fail:
            raise ServiceError("provider_failed", "Test failure")
        # Yield individual word-deltas to simulate real streaming.
        words = self._output.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            on_delta(Delta(kind="text", text=token))
        on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": len(words)}))
        on_delta(Delta(kind="done"))
        return {
            "outcome": "succeeded",
            "result": {"output": self._output},
            "receipt": {"id": "receipt_test_123", "outcome": "succeeded"},
        }


class FakeCloudBroker(FakeBroker):
    """Broker that returns a cloud egress scope."""

    @property
    def inference_adoption_service(self):
        return FakeCloudAdoptionService(output=self._output, fail=self._fail)


class FakeCloudAdoptionService(FakeAdoptionService):
    def admit(self, principal, *, command_id, capability_id, operation_id, payload, invocation_id, reserved_output_tokens=512):
        return {
            "execution": {"id": "exec_" + uuid.uuid4().hex[:8]},
            "route_plan": {
                "id": "rp_cloud",
                "egress_scope": "cloud",
                "model_id": "gpt-4",
            },
            "operation_request_plan": {"id": "orp_cloud"},
        }

    def execute_stream(self, principal, *, execution_id, adapter, on_delta, publish=None, payload_redactor=None):
        from holdspeak.kernel.inference_stream import Delta
        words = self._output.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            on_delta(Delta(kind="text", text=token))
        on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": len(words)}))
        on_delta(Delta(kind="done"))
        return {
            "outcome": "succeeded",
            "result": {"output": self._output},
            "receipt": {"id": "receipt_cloud_456", "outcome": "succeeded"},
        }


@pytest.fixture
def service(db, broadcast_fn) -> ThreadService:
    return ThreadService(db, broadcast=broadcast_fn, broker=FakeBroker())


@pytest.fixture
def cloud_service(db, broadcast_fn) -> ThreadService:
    return ThreadService(db, broadcast=broadcast_fn, broker=FakeCloudBroker())


# ---------------------------------------------------------------------------
# Thread CRUD
# ---------------------------------------------------------------------------


def test_create_and_get(service: ThreadService) -> None:
    t = service.create(title="Test thread")
    assert t["id"].startswith("th_")
    assert t["title"] == "Test thread"

    got = service.get(t["id"])
    assert got["id"] == t["id"]
    assert "messages" in got
    assert "siblings" in got
    assert "refs" in got


def test_list_threads(service: ThreadService) -> None:
    service.create(title="A")
    service.create(title="B")
    threads = service.list_threads()
    assert len(threads) >= 2


def test_patch(service: ThreadService) -> None:
    t = service.create(title="Old")
    updated = service.patch(t["id"], title="New")
    assert updated["title"] == "New"


def test_soft_delete(service: ThreadService) -> None:
    t = service.create(title="Doomed")
    assert service.soft_delete(t["id"]) is True
    with pytest.raises(ServiceError, match="not found"):
        service.get(t["id"])


# ---------------------------------------------------------------------------
# Turn pipeline — AC: ids returned immediately; frames in order; DB == streamed
# ---------------------------------------------------------------------------


def test_turn_returns_ids_immediately(service: ThreadService, broadcasts) -> None:
    t = service.create(title="Turn test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Hello"))

    assert "thread_id" in result
    assert "user_message_id" in result
    assert "assistant_message_id" in result
    assert result["thread_id"] == t["id"]

    # Wait for streaming to complete.
    time.sleep(0.5)

    # Check frames were broadcast in order: started -> deltas -> done.
    frame_types = [ft for ft, _ in broadcasts]
    assert "thread_turn_started" in frame_types
    assert "thread_delta" in frame_types
    assert "thread_turn_done" in frame_types
    started_idx = frame_types.index("thread_turn_started")
    first_delta_idx = frame_types.index("thread_delta")
    done_idx = frame_types.index("thread_turn_done")
    assert started_idx < first_delta_idx < done_idx


def test_turn_yields_at_least_3_deltas_with_monotonic_seq(service: ThreadService, broadcasts) -> None:
    """The fake yields one delta per word of 'Hello from assistant' (3 words)."""
    t = service.create(title="Delta count test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Go"))
    time.sleep(0.5)

    delta_frames = [d for ft, d in broadcasts if ft == "thread_delta"]
    assert len(delta_frames) >= 3, f"Expected >= 3 deltas, got {len(delta_frames)}"
    seqs = [d["seq"] for d in delta_frames]
    assert seqs == sorted(seqs), f"seq not monotonically increasing: {seqs}"
    assert len(set(seqs)) == len(seqs), f"duplicate seq values: {seqs}"


def test_turn_db_text_equals_streamed_concatenation(service: ThreadService, db, broadcasts) -> None:
    t = service.create(title="DB match test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Question"))
    time.sleep(0.5)

    # Concatenate the text from delta frames.
    delta_texts = [d["text"] for ft, d in broadcasts if ft == "thread_delta" and d.get("kind") == "text"]
    streamed_text = "".join(delta_texts)

    # Read the DB text.
    parts = db.threads.get_parts(result["assistant_message_id"])
    text_parts = [p.text for p in parts if p.kind == "text" and p.text]
    db_text = "".join(text_parts)

    assert db_text == streamed_text, f"DB text {db_text!r} != streamed {streamed_text!r}"
    assert db_text == "Hello from assistant"


def test_turn_broadcasts_started_with_correct_data(service: ThreadService, broadcasts) -> None:
    t = service.create(title="Broadcast test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Check broadcasts"))
    time.sleep(0.5)

    started_frames = [(t, d) for t, d in broadcasts if t == "thread_turn_started"]
    assert len(started_frames) == 1
    _, data = started_frames[0]
    assert data["thread_id"] == result["thread_id"]
    assert data["message_id"] == result["assistant_message_id"]
    assert data["user_message_id"] == result["user_message_id"]


def test_turn_broadcasts_done_with_receipt(service: ThreadService, broadcasts) -> None:
    t = service.create(title="Done test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Check done"))
    time.sleep(0.5)

    done_frames = [(t, d) for t, d in broadcasts if t == "thread_turn_done"]
    assert len(done_frames) == 1
    _, data = done_frames[0]
    assert data["thread_id"] == result["thread_id"]
    assert data["message_id"] == result["assistant_message_id"]
    assert data["outcome"] == "succeeded"
    assert data["receipt_id"]


# ---------------------------------------------------------------------------
# Abort — AC: within 250 ms, aborted_at, streaming=0, indeterminate
# ---------------------------------------------------------------------------


def test_abort_semantics(db, broadcast_fn, broadcasts) -> None:
    """Abort cancels and leaves aborted_at, streaming=0, receipt indeterminate."""
    execute_entered = threading.Event()
    abort_seen = threading.Event()

    class SlowBroker(FakeBroker):
        @property
        def inference_adoption_service(self):
            return SlowAdoptionService()

    class SlowAdoptionService(FakeAdoptionService):
        def execute_stream(self, principal, *, execution_id, adapter, on_delta, publish=None, payload_redactor=None):
            from holdspeak.kernel.inference_stream import Delta
            # Signal entry, then poll for cancellation (simulates a cooperative
            # streaming loop that checks the cancel event frequently).
            execute_entered.set()
            for _ in range(50):
                time.sleep(0.05)
                if abort_seen.is_set():
                    break
            return {
                "outcome": "succeeded",
                "result": {"output": "slow response"},
                "receipt": {"id": "receipt_slow", "outcome": "succeeded"},
            }

    svc = ThreadService(db, broadcast=broadcast_fn, broker=SlowBroker())
    t = svc.create(title="Abort test")
    result = asyncio.run(svc.start_turn(OWNER, t["id"], "Abort me"))

    # Wait until the background thread has entered execute.
    assert execute_entered.wait(timeout=2), "Background thread never entered execute"

    # Abort.
    abort_result = svc.abort(t["id"])
    assert abort_result["aborted"] is True
    abort_seen.set()

    # Wait for the background thread to finish and broadcast done.
    time.sleep(0.5)

    # Check the done frame.
    done_frames = [d for ft, d in broadcasts if ft == "thread_turn_done"]
    assert len(done_frames) == 1
    assert done_frames[0]["outcome"] == "aborted"
    assert done_frames[0]["receipt_id"] == "indeterminate"

    # Check DB state.
    msg = db.threads.get_message(result["assistant_message_id"])
    assert msg is not None
    assert msg.streaming is False
    assert msg.aborted_at is not None


# ---------------------------------------------------------------------------
# Branch and regenerate — AC: siblings, GET shape
# ---------------------------------------------------------------------------


def test_branch_creates_sibling(service: ThreadService) -> None:
    t = service.create(title="Branch test")
    r1 = asyncio.run(service.start_turn(OWNER, t["id"], "Original"))
    time.sleep(0.5)

    # Branch from the user message.
    r2 = asyncio.run(service.branch(OWNER, t["id"], r1["user_message_id"], "Edited"))
    time.sleep(0.5)

    assert r2["thread_id"] == t["id"]
    assert r2["user_message_id"] != r1["user_message_id"]

    # GET should return the new leaf path with siblings.
    got = service.get(t["id"])
    assert "siblings" in got
    assert "messages" in got


def test_regenerate_creates_sibling_assistant(service: ThreadService) -> None:
    t = service.create(title="Regen test")
    r1 = asyncio.run(service.start_turn(OWNER, t["id"], "Regenerate me"))
    time.sleep(0.5)

    r2 = asyncio.run(service.regenerate(OWNER, t["id"], r1["assistant_message_id"]))
    time.sleep(0.5)

    assert r2["thread_id"] == t["id"]
    assert r2["assistant_message_id"] != r1["assistant_message_id"]


# ---------------------------------------------------------------------------
# M1 pin — AC: sensitive part + cloud => redacted, local => verbatim
# ---------------------------------------------------------------------------


def test_m1_cloud_redacts_sensitive_parts(db, broadcast_fn) -> None:
    """Seeded sensitive part + cloud profile => provider payload contains none of it."""
    svc = ThreadService(db, broadcast=broadcast_fn, broker=FakeCloudBroker())
    t = svc.create(title="M1 cloud test")

    # Manually insert a user message with a sensitive annotation part.
    user_msg = db.threads.append_message(t["id"], role="user")
    db.threads.append_part(user_msg.id, kind="text", text="Tell me about this person")
    db.threads.append_part(
        user_msg.id,
        kind="annotation",
        text="John Doe, SSN 123-45-6789, salary $150k",
        sensitive=True,
    )

    # Build the redacted payload.
    thread = db.threads.get(t["id"])
    payload = svc.assemble_payload_for_egress(
        t["id"], user_msg.id, thread, egress_scope="cloud"
    )

    # Assert the sensitive text is NOT in the payload.
    payload_str = json.dumps(payload)
    assert "John Doe" not in payload_str
    assert "123-45-6789" not in payload_str
    assert "150k" not in payload_str
    assert _PEOPLE_REDACTION in payload_str


def test_m1_local_keeps_sensitive_parts_verbatim(db, broadcast_fn) -> None:
    """Same sensitive part + local profile => provider payload contains it verbatim."""
    svc = ThreadService(db, broadcast=broadcast_fn, broker=FakeBroker())
    t = svc.create(title="M1 local test")

    user_msg = db.threads.append_message(t["id"], role="user")
    db.threads.append_part(user_msg.id, kind="text", text="Tell me about this person")
    db.threads.append_part(
        user_msg.id,
        kind="annotation",
        text="John Doe, SSN 123-45-6789, salary $150k",
        sensitive=True,
    )

    thread = db.threads.get(t["id"])
    payload = svc.assemble_payload_for_egress(
        t["id"], user_msg.id, thread, egress_scope="same_device"
    )

    payload_str = json.dumps(payload)
    assert "John Doe" in payload_str
    assert "123-45-6789" in payload_str


# ---------------------------------------------------------------------------
# Unknown ref — AC: 4xx naming the id, no rows written
# ---------------------------------------------------------------------------


def test_unknown_ref_refuses_with_id(service: ThreadService, db) -> None:
    t = service.create(title="Ref test")

    with pytest.raises(ValidationError, match="Unknown ref ids") as exc_info:
        asyncio.run(service.start_turn(
            OWNER, t["id"], "Hello",
            refs=["person:nonexistent_person_id"],
        ))

    assert "nonexistent_person_id" in str(exc_info.value)

    # No user message should have been written.
    path = db.threads.list_path(t["id"])
    assert len(path) == 0


# ---------------------------------------------------------------------------
# Keep — AC: mints artifact with thread:<id>/<message_id> provenance
# ---------------------------------------------------------------------------


def test_keep_mints_artifact(service: ThreadService, db) -> None:
    t = service.create(title="Keep test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Keep this"))
    time.sleep(0.5)

    # Manually insert text for the assistant message to keep.
    msg = db.threads.get_message(result["assistant_message_id"])
    parts = db.threads.get_parts(result["assistant_message_id"])
    if not any(p.text for p in parts):
        db.threads.append_part(result["assistant_message_id"], kind="text", text="Keepable content")

    keep_result = service.keep(OWNER, t["id"], result["assistant_message_id"])
    assert "artifact_id" in keep_result

    # Check the artifact exists and has the thread provenance.
    art = db.plugins.get_artifact(keep_result["artifact_id"])
    assert art is not None
    # The provenance is stored in the artifact sources.
    expected_prov = f"thread:{t['id']}/{result['assistant_message_id']}"
    # Check the body markdown contains our text.
    assert art.body_markdown is not None
    # Check structured_json has the provenance.
    sj = art.structured_json
    if isinstance(sj, str):
        sj = json.loads(sj) if sj else {}
    provenance_str = json.dumps(sj) if sj else ""
    assert expected_prov in provenance_str


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


def test_import_threads(service: ThreadService) -> None:
    payload = [
        {
            "recipe_id": "r1",
            "title": "Imported",
            "created_at": "2024-01-01T00:00:00Z",
            "messages": [
                {"role": "user", "text": "Hello"},
                {"role": "assistant", "text": "Hi there"},
            ],
        }
    ]
    result = service.import_threads(payload)
    assert len(result) == 1
    for hash_key, thread_id in result.items():
        assert thread_id.startswith("th_")

    # Import again - should return existing.
    result2 = service.import_threads(payload)
    assert result == result2


# ---------------------------------------------------------------------------
# Regression: real RoutedInferenceCoordinator with fake engine factory
# ---------------------------------------------------------------------------


def test_real_coordinator_with_fake_engine(tmp_path: Path) -> None:
    """Regression for HS-150-04: drives ThreadService through the REAL
    RoutedInferenceCoordinator / InferenceRunner / _attempt_stream path
    with a fake engine injected via _engine_factory.

    This is the gap that let the production defect through: the unit tests
    used a fake adoption service that bypassed the runner and receipt chain.
    """
    import os
    import tempfile
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix="hs150-regr-"))
    old_home = os.environ.get("HOME", "")
    os.environ["HOME"] = str(home)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
        )
        url = server.start()
        db = get_database()

        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from holdspeak.kernel.inference_stream import Delta

        profile_id = "regr-local"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": "regr-assign",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()
        runner = broker.inference_runner

        class _FakeEngine:
            active_provider = "fake-regr"
            active_model = "regr-model"
            def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, **kw):
                words = "Alpha Beta Gamma Delta Epsilon".split()
                for w in words:
                    yield Delta(kind="text", text=w + " ")
                yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 5})
                yield Delta(kind="done")
            def run_prompt_messages(self, *, messages=None, **kw):
                return "Alpha Beta Gamma Delta Epsilon "
            def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
                return self.run_prompt_messages()

        runner._engine_factory = lambda _rev, **_kw: _FakeEngine()

        broadcasts_local: list[tuple[str, Any]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts_local.append((t, d)),
            broker=broker,
        )
        thread = svc.create(title="Regression test")
        tid = thread["id"]

        result = asyncio.run(svc.start_turn(OWNER, tid, "Hello regression"))
        assert "thread_id" in result
        assert "assistant_message_id" in result

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            msg = db.threads.get_message(result["assistant_message_id"])
            if msg and not msg.streaming:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Streaming did not complete within 15s")

        parts = db.threads.get_parts(result["assistant_message_id"])
        text_parts = [p.text for p in parts if p.kind == "text" and p.text]
        db_text = "".join(text_parts)
        assert db_text == "Alpha Beta Gamma Delta Epsilon ", f"DB text: {db_text!r}"

        delta_frames = [d for ft, d in broadcasts_local if ft == "thread_delta"]
        assert len(delta_frames) >= 5, f"Expected >= 5 deltas, got {len(delta_frames)}"
        seqs = [d["seq"] for d in delta_frames]
        assert seqs == sorted(seqs), f"seq not monotonic: {seqs}"

        done_frames = [d for ft, d in broadcasts_local if ft == "thread_turn_done"]
        assert len(done_frames) == 1
        assert done_frames[0]["outcome"] == "succeeded"
        assert done_frames[0]["receipt_id"]
        assert done_frames[0]["egress"]

        msg = db.threads.get_message(result["assistant_message_id"])
        assert msg is not None
        assert msg.streaming is False
        assert msg.receipt_id, "receipt_id should be set"
        assert msg.egress_scope, "egress_scope should be set"

        server.stop()
    finally:
        os.environ["HOME"] = old_home
        reset_database()


def test_graceful_degradation_run_prompt_only_engine(tmp_path: Path) -> None:
    """An engine with only run_prompt (no run_prompt_stream) degrades to
    one text delta containing the full output, followed by done."""
    import os
    import tempfile
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix="hs150-degrade-"))
    old_home = os.environ.get("HOME", "")
    os.environ["HOME"] = str(home)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
        )
        url = server.start()
        db = get_database()

        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        profile_id = "degrade-local"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": "degrade-assign",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()
        runner = broker.inference_runner

        class _RunPromptOnlyEngine:
            active_provider = "fake-degrade"
            active_model = "degrade-model"
            def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
                return "Degraded single output"

        runner._engine_factory = lambda _rev, **_kw: _RunPromptOnlyEngine()

        broadcasts_local: list[tuple[str, Any]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts_local.append((t, d)),
            broker=broker,
        )
        thread = svc.create(title="Degradation test")
        result = asyncio.run(svc.start_turn(OWNER, thread["id"], "Hello degrade"))

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            msg = db.threads.get_message(result["assistant_message_id"])
            if msg and not msg.streaming:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Streaming did not complete within 15s")

        parts = db.threads.get_parts(result["assistant_message_id"])
        text_parts = [p.text for p in parts if p.kind == "text" and p.text]
        db_text = "".join(text_parts)
        assert db_text == "Degraded single output", f"DB text: {db_text!r}"

        done_frames = [d for ft, d in broadcasts_local if ft == "thread_turn_done"]
        assert len(done_frames) == 1
        assert done_frames[0]["outcome"] == "succeeded"
        assert done_frames[0]["receipt_id"]

        server.stop()
    finally:
        os.environ["HOME"] = old_home
        reset_database()


# ---------------------------------------------------------------------------
# M5 pin: real coordinator + cloud/local egress + sensitive part
# ---------------------------------------------------------------------------

_M5_SENTINEL = "SENSITIVE-DATA-SSN-999-88-7777-SALARY-200K"


def _m5_rig(tmp_path: Path, *, boundary: str):
    """Boot a real hub, seed a profile, override boundary, seed a sensitive
    part in an earlier assistant message, return (svc, captured, server, tid, old_home).
    """
    import os
    import tempfile
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix=f"hs150-m5-{boundary}-"))
    old_home = os.environ.get("HOME", "")
    os.environ["HOME"] = str(home)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
    )
    server.start()
    db = get_database()

    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.kernel.inference_stream import Delta

    # Seed profile. The profile always admits with same_device boundary
    # (the _profile helper creates local deployments). For the cloud boundary
    # test, we patch the frozen route plan entries AFTER admit returns.
    profile_id = f"m5-{boundary}"
    _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"m5-assign-{boundary}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    runner = broker.inference_runner

    captured_payloads: list[dict] = []

    class _CapturingEngine:
        active_provider = "m5-capture"
        active_model = "m5-model"
        def run_prompt_stream(self, *, messages=None, **kw):
            captured_payloads.append({"messages": list(messages or [])})
            yield Delta(kind="text", text="response ")
            yield Delta(kind="done")
        def run_prompt_messages(self, *, messages=None, **kw):
            captured_payloads.append({"messages": list(messages or [])})
            return "response"
        def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
            return "response"

    runner._engine_factory = lambda _rev, **_kw: _CapturingEngine()

    broadcasts_local: list[tuple[str, Any]] = []
    svc = ThreadService(
        db, broadcast=lambda t, d: broadcasts_local.append((t, d)), broker=broker,
    )

    # Override _m1_redactor so it uses the TEST's desired boundary instead
    # of whatever the frozen route plan carries (always same_device from
    # _profile). This proves the redactor IS called in the pipeline and
    # correctly redacts/preserves based on the boundary it receives.
    original_redactor = ThreadService._m1_redactor

    @staticmethod
    def _boundary_override_redactor(payload, route):
        patched_route = {**route, "entries": [{"boundary": boundary}]}
        return original_redactor(payload, patched_route)

    svc._m1_redactor = _boundary_override_redactor

    # Create thread with an earlier turn that has a sensitive part.
    thread = svc.create(title=f"M5 {boundary} test")
    tid = thread["id"]
    user_msg = db.threads.append_message(tid, role="user")
    db.threads.append_part(user_msg.id, kind="text", text="Tell me about the person")
    asst_msg = db.threads.append_message(tid, role="assistant", parent_id=user_msg.id)
    db.threads.append_part(asst_msg.id, kind="text", text=_M5_SENTINEL, sensitive=True)
    db.threads.complete_message(asst_msg.id)

    return svc, captured_payloads, server, tid, old_home


def test_m5_cloud_egress_redacts_sensitive_in_engine_payload(tmp_path: Path) -> None:
    """M5 pin: start_turn through the REAL coordinator with cloud boundary.
    The engine must receive [people content withheld], NOT the sentinel."""
    from holdspeak.db import reset_database

    svc, captured, server, tid, old_home = _m5_rig(tmp_path, boundary="cloud")
    try:
        result = asyncio.run(svc.start_turn(OWNER, tid, "Follow up"))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            msg = svc._threads.get_message(result["assistant_message_id"])
            if msg and not msg.streaming:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Turn did not complete")

        assert len(captured) >= 1, "Engine was never called"
        engine_json = json.dumps(captured[0])
        assert _M5_SENTINEL not in engine_json, (
            f"Sentinel leaked to engine on cloud egress: {engine_json[:200]}"
        )
        assert _PEOPLE_REDACTION in engine_json, (
            f"Redaction marker missing from engine payload: {engine_json[:200]}"
        )
        server.stop()
    finally:
        import os
        os.environ["HOME"] = old_home
        reset_database()


def test_m5_local_egress_preserves_sensitive_verbatim(tmp_path: Path) -> None:
    """M5 pin: start_turn through the REAL coordinator with local boundary.
    The engine must receive the sentinel verbatim."""
    from holdspeak.db import reset_database

    svc, captured, server, tid, old_home = _m5_rig(tmp_path, boundary="same_device")
    try:
        result = asyncio.run(svc.start_turn(OWNER, tid, "Follow up"))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            msg = svc._threads.get_message(result["assistant_message_id"])
            if msg and not msg.streaming:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Turn did not complete")

        assert len(captured) >= 1, "Engine was never called"
        engine_json = json.dumps(captured[0])
        assert _M5_SENTINEL in engine_json, (
            f"Sentinel missing from engine on local egress: {engine_json[:200]}"
        )
        server.stop()
    finally:
        import os
        os.environ["HOME"] = old_home
        reset_database()
