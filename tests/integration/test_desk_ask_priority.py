"""Ask goes first (Betterment Q2): the hub half.

The face half is ``web/src/desk/__tests__/ask.app.test.tsx``.

RECON (asking/RECON.md step 8): the LAN server has one slot; meeting analysis
and memory work held it, and Ask this project ran out its 60 s deadline twice
(100 s) with no words.  Now a foreground turn holds its engine while it runs:
background calls start no new call on that engine until the turn ends, and
an Ask still waiting after 5 s on an engine that background work holds says
so, naming the job.

The rig is the real kernel broker and route chain with fixture engines at the
runner seam (``tests/unit/test_desk_ask_ai.py``).
"""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.engine_lanes import LANES, background_label, engine_key, lane
from holdspeak.kernel.inference_runner import ServiceContract

from tests.unit.test_desk_ask_ai import OWNER, _assign, _seed_routes, hub  # noqa: F401  (fixture)

ANSWER = "This week you owe Mira one thing: feedback on her cutover design doc, due Friday."


class _GatedEngine:
    """Answers when ``release`` is set; records when each call started."""

    active_provider = "fixture"

    def __init__(self, model: str, release: threading.Event, started: list[float], plan: list[Any]) -> None:
        self.active_model = model
        self._release, self._started, self._plan = release, started, plan

    def run_prompt(self, **_kw: Any) -> str:
        self._started.append(time.monotonic())
        step = self._plan.pop(0) if self._plan else ANSWER
        if isinstance(step, Exception):
            raise step
        self._release.wait(10)
        return step

    def run_prompt_stream(self, **_kw: Any) -> Any:  # pragma: no cover - Ask is not streamed
        raise AssertionError("not streamed")


def _lan(hub: Any, release: threading.Event, started: list[float], plan: list[Any] | None = None) -> str:
    """Ask on the LAN engine; returns that engine's lane key."""
    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-first-lan")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _GatedEngine(
        str(rev.model), release, started, plan if plan is not None else [])
    with hub.db._connection() as conn:
        row = conn.execute(
            """SELECT b.deployment_revision_id FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                WHERE h.profile_id='glass-lan'"""
        ).fetchone()
    return str(row["deployment_revision_id"])


def _background_request(revision: str, contract: str = "meeting.deferred.analysis") -> Any:
    return SimpleNamespace(
        deployment_revision=revision,
        definition_origin=ServiceContract(contract, "1", ""),
    )


def _ask(hub: Any, events: list[dict[str, Any]] | None = None, invocation_id: str | None = None) -> dict[str, Any]:
    from holdspeak.services.ask_service import AskService

    service = AskService(hub.db, broker=hub.broker,
                         progress=(events.append if events is not None else None))
    return asyncio.run(service.ask(OWNER, "What do I owe Mira this week?", invocation_id=invocation_id))


# The face test mints its id from crypto.randomUUID; it replays this one.
FACE_INVOCATION = "ask_" + "a" * 32
WIRES = Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire"


def test_background_work_waits_while_an_ask_holds_the_engine(hub) -> None:
    release, started = threading.Event(), []
    revision = _lan(hub, release, started)
    runner = hub.broker.inference_runner
    background_started: list[float] = []

    def meeting_analysis() -> None:
        # The meeting worker's next call, on the same engine (the runner gate).
        while not LANES.holds(engine_key(hub.db, revision)):
            time.sleep(0.01)
        with lane(runner._database, _background_request(revision)):
            background_started.append(time.monotonic())

    result: dict[str, Any] = {}
    asker = threading.Thread(target=lambda: result.update(_ask(hub)))
    worker = threading.Thread(target=meeting_analysis)
    asker.start()
    worker.start()
    time.sleep(0.5)
    assert started and background_started == []           # the Ask runs; the job waits
    release.set()
    asker.join(10)
    worker.join(10)
    assert result["output"] == ANSWER
    assert background_started                             # it resumed when the turn ended
    assert not LANES.holds(engine_key(hub.db, revision))


def test_background_work_on_another_engine_does_not_wait(hub) -> None:
    release, started = threading.Event(), []
    _lan(hub, release, started)
    runner = hub.broker.inference_runner
    asker = threading.Thread(target=lambda: _ask(hub))
    asker.start()
    while not started:
        time.sleep(0.01)
    t0 = time.monotonic()
    with lane(runner._database, _background_request("dep2_another_server")):
        waited = time.monotonic() - t0
    release.set()
    asker.join(10)
    assert waited < 0.2


def test_an_ask_on_a_busy_engine_says_so_after_five_seconds(hub, monkeypatch, tmp_path) -> None:
    import holdspeak.services.ask_service as ask_module

    assert ask_module.BUSY_AFTER_SECONDS == 5.0
    monkeypatch.setattr(ask_module, "BUSY_AFTER_SECONDS", 0.2)   # the same check, sooner
    release, started = threading.Event(), []
    revision = _lan(hub, release, started)
    events: list[dict[str, Any]] = []
    # Meeting analysis is in flight on the LAN engine (one slot).
    answered: dict[str, Any] = {}
    with LANES.background(engine_key(hub.db, revision), background_label(_background_request(revision))):
        asker = threading.Thread(target=lambda: answered.update(_ask(hub, events, FACE_INVOCATION)))
        asker.start()
        deadline = time.monotonic() + 5
        while not events and time.monotonic() < deadline:
            time.sleep(0.02)
    release.set()
    asker.join(10)
    [busy] = [event for event in events if event["state"] == "busy"]
    assert busy["job"] == "meeting analysis"
    assert busy["engine"] == {"model": "qwen3.8-27b", "boundary": "private_network"}
    assert busy["invocation_id"].startswith("ask_")
    # The other engines that can answer, never the busy one.
    assert {other["profile_id"] for other in busy["alternatives"]} == {"glass-cloud", "glass-local"}
    assert answered["output"] == ANSWER

    from tests.unit.test_desk_speak import _record
    _record("ask.busy.wire", {"busy": busy, "answer": answered}, tmp_path,
            "tests/integration/test_desk_ask_priority.py::test_an_ask_on_a_busy_engine_says_so_after_five_seconds",
            folder=WIRES)


def test_an_ask_on_a_free_engine_sends_no_busy_event(hub, monkeypatch) -> None:
    import holdspeak.services.ask_service as ask_module

    monkeypatch.setattr(ask_module, "BUSY_AFTER_SECONDS", 0.1)
    release, started = threading.Event(), []
    _lan(hub, release, started)
    events: list[dict[str, Any]] = []
    asker = threading.Thread(target=lambda: _ask(hub, events))
    asker.start()
    time.sleep(0.4)
    release.set()
    asker.join(10)
    assert [event for event in events if event["state"] == "busy"] == []


def test_a_second_attempt_is_said(hub, tmp_path) -> None:
    from holdspeak.kernel.provider_signals import ProviderKnownNoGenerationTransient

    release, started = threading.Event(), []
    release.set()
    _lan(hub, release, started, plan=[ProviderKnownNoGenerationTransient("429"), ANSWER])
    events: list[dict[str, Any]] = []
    result = _ask(hub, events, FACE_INVOCATION)
    assert result["output"] == ANSWER
    retries = [event for event in events if event["state"] == "retry"]
    assert retries and retries[0]["attempt"] == 1 and retries[0]["of"] >= 1

    from tests.unit.test_desk_speak import _record
    _record("ask.retry.wire", {"retry": retries[0]}, tmp_path,
            "tests/integration/test_desk_ask_priority.py::test_a_second_attempt_is_said",
            folder=WIRES)


@pytest.mark.parametrize(("contract", "label"), [
    ("meeting.deferred.analysis", "meeting analysis"),
    ("memory.extract", "memory work"),
    ("memory.page", "memory work"),
    ("ask.answer", ""),
    ("chat.turn", ""),
])
def test_background_jobs_are_named(contract, label) -> None:
    assert background_label(_background_request("dep", contract)) == label


def test_another_engine_answers_this_one_ask_and_settings_stay(hub) -> None:
    """The face's "Use … for this one": a one-run assignment (scope
    ``invocation``) and the Ask under that identity."""
    from holdspeak.services.ask_service import AskService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    release, started = threading.Event(), []
    release.set()
    _lan(hub, release, started)
    invocation = "ask_" + "1" * 32
    InferenceAssignmentService(hub.db).set_assignment(OWNER, {
        "command_id": f"ask-elsewhere-{invocation}",
        "expected_revision": 0,
        "scope": {"kind": "invocation", "invocation_id": invocation, "capability_id": "ask.answer"},
        "entries": [{"profile_id": "glass-local", "profile_revision": 1}],
    })
    result = asyncio.run(AskService(hub.db, broker=hub.broker).ask(
        OWNER, "What do I owe Mira this week?", invocation_id=invocation))
    assert result["route"]["lamp"] == "local"
    # His own choice for Ask is unchanged.
    later = asyncio.run(AskService(hub.db, broker=hub.broker).ask(OWNER, "And next week?"))
    assert later["route"]["lamp"] == "private_network"
