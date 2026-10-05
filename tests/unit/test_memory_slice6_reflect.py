"""Memory slice 6, backend: Ask and the chat turn reflect (MEMORY-DESIGN.md
§3.5, §5, §6, §8 row 6).

Ask and the chat turn ground, in order: the scope's served page sentences,
then its current and disputed observations (the served text only), then the
fused recall they already had.  ``memory.page`` joins the thread palettes.

Every source is written by its real producer.  Facts, observations and pages
come through the real extract, consolidate and page paths with the slice 4
and slice 5 deterministic engines.  Ask runs the real routed path (the real
assignment migration, adoption service, router and runner); the chat turn
runs the real hub, ThreadService, tool executor and MCP dispatch.  Only the
physical model leaf is replaced, and it records what it was sent.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from holdspeak.db import Database
from holdspeak.inference_memory_policy import memory_policy
from holdspeak.kernel.inference_stream import Delta
from holdspeak.kernel.runtime import _configure
from holdspeak.memory import pages as pages_module
from holdspeak.memory.retain import sweep
from holdspeak.services.memory_grounding import (
    REFLECT_NOTE, reflect_block, reflect_for, reflect_scopes,
)

from tests.unit.test_memory_slice4_observations import _desk, _filed_note, _learn
from tests.unit.test_memory_slice5_pages import (
    ATLAS, CHANGED, DESK, WITHDRAWALS, Pages, _built, _misattributing, _status_and_codename,
)
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

PAGE = "[MEMORY PAGE:"
OBSERVATIONS = "[MEMORY OBSERVATIONS:"


# ── Ask on the real routed path ─────────────────────────────────────────


class _AskEngine:
    """The physical leaf: records each user prompt it was sent."""

    active_provider = "fixture"
    active_model = "reflect-model"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def run_prompt(self, **kwargs: Any) -> str:
        self.prompts.append(str(kwargs.get("user_prompt") or ""))
        return "answer"


def _ask_rig(db: Database, *, ceiling: int = 32768) -> tuple[Any, _AskEngine]:
    from holdspeak.services.ask_service import AskService

    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")), context_ceiling=ceiling)
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    broker = _configure(db)
    broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-v2"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
    ))
    engine = _AskEngine()
    broker.inference_runner._engine_factory = lambda _revision, **_kw: engine
    return AskService(db, broker=broker), engine


def _ask(service: Any, engine: _AskEngine, question: str, scope: tuple[str, str], **kwargs: Any) -> str:
    grounding = {"refs": [f"project:{scope[1]}"]} if scope[0] == "project" else None
    result = asyncio.run(service.ask(OWNER, question, grounding, **kwargs))
    assert result["output"] == "answer" and result["route_execution_receipt"]["outcome"] == "succeeded"
    return engine.prompts[-1]


def _memory_part(prompt: str) -> str:
    """The pages and observations part of a sent prompt."""
    start = prompt.find(PAGE) if PAGE in prompt else prompt.find(OBSERVATIONS)
    end = prompt.find(REFLECT_NOTE)
    return prompt[start:end] if start >= 0 and end > start else ""


def test_ask_grounds_on_pages_then_observations_then_recall(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    _built(db)
    service, engine = _ask_rig(db)
    prompt = _ask(service, engine, "What about the Atlas launch?", ATLAS)
    page, observations, recall = prompt.find(PAGE), prompt.find(OBSERVATIONS), prompt.find("[NOTE:")
    assert 0 <= page < observations < prompt.find(REFLECT_NOTE) < recall, prompt
    part = _memory_part(prompt)
    assert "- Atlas launch is 2026-10-01. (note:n1)" in part          # a page sentence, its ref
    assert "- current: Atlas launch is 2026-10-01. (note:n1)" in part  # an observation, its ref
    # Plain context: no [REF:] line in the part (refs only where the Desk opens them).
    assert "[REF:" not in part
    # The best match to the question comes first among the observations.
    beliefs = part[part.find(OBSERVATIONS):]
    assert beliefs.find("launch") < beliefs.find("budget")


def test_ask_with_no_source_reflects_on_the_desk(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    _filed_note(db, "na", "Atlas codename is ZEPHYRATLAS.", "atlas")
    _built(db)
    service, engine = _ask_rig(db)
    part = _memory_part(_ask(service, engine, "When is lunch?", DESK))
    assert "the desk" in part and "Desk lunch is noon." in part
    assert "ZEPHYRATLAS" not in part  # a project's pages and beliefs are not the desk's


def test_reflect_scopes() -> None:
    assert reflect_scopes(["project:atlas", "note:n1", "project:atlas"], explicit=True) == [ATLAS]
    assert reflect_scopes([], explicit=False) == [DESK]
    assert reflect_scopes(["note:n1"], explicit=True) == []  # he named sources: grounding runs no memory pass


@pytest.mark.parametrize("writer", ["cites-right", "misattributes"])
@pytest.mark.parametrize("mode", WITHDRAWALS)
def test_a_withdrawn_page_sentence_or_observation_never_reaches_the_ask(
    tmp_path: Path, mode: str, writer: str, monkeypatch,
) -> None:
    """#843 and #848's classes at the Ask: delete, edit, exclude, refile and
    sensitive.  ``misattributes`` is the belt: a stored sentence carries the
    codename but cites the status input (written past the write check)."""
    db = _desk(tmp_path)
    scope, _ref, withdraw, kwargs = _status_and_codename(db, mode)
    _learn(db)
    pages = Pages()
    if writer == "misattributes":
        real = pages_module.validate_output
        monkeypatch.setattr(pages_module, "validate_output", lambda raw, labels: real(raw, list(labels)))
        pages.answer = _misattributing
    pages_module.write_page(db, pages, scope, pages_module.spec_for(scope[0], CHANGED))
    service, engine = _ask_rig(db)
    exclude = {"memory_exclude_refs": kwargs["exclude_refs"]} if kwargs else {}
    before = _memory_part(_ask(service, engine, "What is the status and the codename?", scope))
    assert "ZEPHYRSECRET" in before  # the codename's source is live: memory carries it
    withdraw()
    for step in (lambda: None, lambda: sweep(db), lambda: _learn(db)):
        step()
        prompt = _ask(service, engine, "What is the status and the codename?", scope, **exclude)
        assert "ZEPHYRSECRET" not in prompt
        part = _memory_part(prompt)
        assert PAGE in part and "status is approved" in part  # the rest stays


def test_project_a_ask_never_sees_project_b(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "na", "Atlas codename is ZEPHYRATLAS.", "atlas")
    _filed_note(db, "nh", "Harbor codename is QUOKKAHARBOR.", "harbor")
    _built(db)
    service, engine = _ask_rig(db)
    prompt = _ask(service, engine, "What is the codename?", ATLAS)
    part = _memory_part(prompt)
    assert PAGE in part and OBSERVATIONS in part and "ZEPHYRATLAS" in part
    assert "QUOKKAHARBOR" not in prompt
    prompt = _ask(service, engine, "What is the codename?", ("project", "harbor"))
    assert "QUOKKAHARBOR" in _memory_part(prompt) and "ZEPHYRATLAS" not in prompt


def _many_beliefs(db: Database, count: int = 40) -> None:
    for index in range(count):
        _filed_note(db, f"n{index:02d}", f"Atlas topic{index:02d} is value{index:02d}-" + "x" * 60 + ".", "atlas")
    _built(db)


def test_the_part_keeps_the_jobs_budget_and_the_pages_take_at_most_half(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _many_beliefs(db)
    memory = reflect_for("ask.answer", db, scopes=[ATLAS], query="topic")
    pages = [e for e in memory.excerpts if e.kind == "memory_page"]
    beliefs = [e for e in memory.excerpts if e.kind == "observation"]
    assert pages and beliefs
    budget = memory_policy("ask.answer").block_chars
    assert len(reflect_block(memory)) <= budget
    from holdspeak.services.memory_grounding import MemoryContext
    assert len(reflect_block(MemoryContext(tuple(pages)))) <= budget // 2
    # Whole sentences only: every page line is one stored sentence.
    for excerpt in pages:
        for line in excerpt.text.splitlines():
            assert line.startswith("- Atlas topic") and line.endswith("(note:" + line.split("(note:")[1])


def test_the_part_never_pushes_an_ask_over_its_route(tmp_path: Path) -> None:
    """An 8,192-token route: the Ask fits without the part, and not with all
    of it.  The part is cut (observations first) and the Ask runs."""
    db = _desk(tmp_path)
    _many_beliefs(db)
    service, engine = _ask_rig(db, ceiling=8192)
    question = "What about topic00? " + "Context words. " * 200
    prompt = _ask(service, engine, question, ATLAS)
    full = reflect_for("ask.answer", db, scopes=[ATLAS], query=question)
    sent = prompt.count("\n- ")
    assert 0 < len(_memory_part(prompt)) and sent < reflect_block(full).count("\n- ")
    with db._connection() as conn:
        row = conn.execute(
            "SELECT s.operation_id FROM inference_adoption_material_snapshots s WHERE s.capability_id='ask.answer'"
        ).fetchone()
    adoption = service._broker.inference_adoption_service
    admitted = adoption.admitted_payload(row["operation_id"])
    whole = {**admitted, "user_prompt": admitted["user_prompt"].replace(
        _memory_part(prompt) + REFLECT_NOTE, reflect_block(full))}
    assert adoption.payload_room_now(
        capability_id="ask.answer", operation_id=row["operation_id"], payload=whole,
        reserved_output_tokens=512, invocation_id=row["operation_id"]) < 0


@pytest.mark.parametrize("scope", [ATLAS, DESK])
def test_with_no_page_and_no_observation_the_ask_prompt_is_byte_identical(tmp_path: Path, scope) -> None:
    """The owner's case today: no extract, consolidate or page engine is
    assigned, so the sweep makes chunks and nothing else.  The prompt is
    the question, then main's grounding envelope, byte for byte."""
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas" if scope == ATLAS else None)
    sweep(db)
    service, engine = _ask_rig(db)
    question = "What about the Atlas launch?"
    prompt = _ask(service, engine, question, scope)
    grounding = {"refs": [f"project:{scope[1]}"]} if scope == ATLAS else None
    envelope, _echo = service._grounding(OWNER, grounding, question, capability_id="ask.answer")
    assert envelope and prompt == question + "\n\nGrounding:\n" + envelope
    assert "[MEMORY" not in prompt


# ── the chat turn on the real hub ───────────────────────────────────────


class _ChatEngine:
    """Records each pass; on pass 1 asks for ``self.tool`` when one is set."""

    active_provider = "fixture"
    active_model = "reflect-chat"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []
        self.tools_seen: list[Any] = []
        self.tool: Optional[tuple[str, dict]] = None

    def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, tools=None, **kw):
        msgs = [dict(m) for m in (messages or [])]
        self.calls.append(msgs)
        self.tools_seen.append(tools)
        if self.tool is not None and not any(m.get("role") == "tool" for m in msgs):
            name, args = self.tool
            yield Delta(kind="tool_calls", meta={"tool_calls": [{
                "id": "call_page_1", "name": name, "arguments": json.dumps(args),
            }]})
        else:
            yield Delta(kind="text", text="OK")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "OK"

    def run_prompt(self, **kw):
        return "OK"


@pytest.fixture
def hub(monkeypatch, tmp_path):
    """Isolated HOME, the real hub and kernel broker, a chat.turn engine."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.kernel.runtime import _service as _kernel_service
    from holdspeak.mcp.tools import dispatch as mcp_dispatch
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.thread_modes import seed_modes
    from holdspeak.services.thread_service import ThreadService
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people.key"))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", home / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
    )
    server.start()
    try:
        db = get_database()
        db.projects.create_project(project_id="atlas", name="Atlas")
        db.projects.create_project(project_id="harbor", name="Harbor")
        seed_modes(db)
        _profile(db, "reflect-chat", claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": "reflect-chat-assign", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": "reflect-chat", "profile_revision": 1}],
        })
        broker = _kernel_service()
        engine = _ChatEngine()
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine
        done: dict[str, threading.Event] = {}
        events: list = []

        def broadcast(kind: str, data: Any) -> None:
            events.append((kind, data))
            if kind == "thread_turn_done":
                done.setdefault(str(data.get("message_id")), threading.Event()).set()

        service = ThreadService(db, broadcast=broadcast, broker=broker, tool_dispatch_fn=mcp_dispatch)
        yield SimpleNamespace(db=db, svc=service, engine=engine, broker=broker, done=done, events=events)
    finally:
        server.stop()
        reset_database()


def _turn(hub: Any, text: str, *, refs: Optional[list[str]] = None, mode: Optional[str] = None,
          thread_id: Optional[str] = None) -> dict[str, Any]:
    if thread_id is None:
        thread_id = hub.svc.create(title="Reflect", recipe_id=mode)["id"] if mode else hub.svc.create(title="Reflect")["id"]
    started = len(hub.engine.calls)
    result = asyncio.run(hub.svc.start_turn(OWNER, thread_id, text, refs=refs))
    event = hub.done.setdefault(result["assistant_message_id"], threading.Event())
    if not event.wait(timeout=20.0):
        pytest.fail("turn did not emit thread_turn_done")
    outcome = [d for k, d in hub.events if k == "thread_turn_done"
               and d.get("message_id") == result["assistant_message_id"]][-1]
    return {**result, "thread_id": thread_id, "outcome": outcome.get("outcome"),
            "calls": hub.engine.calls[started:]}


def _system_texts(messages: list[dict[str, Any]]) -> list[str]:
    return [str(m.get("content") or "") for m in messages if m.get("role") == "system"]


def test_the_chat_turn_grounds_on_pages_then_observations_then_recall(hub) -> None:
    _filed_note(hub.db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(hub.db, "n2", "Atlas budget is 40k.", "atlas")
    _built(hub.db)
    turn = _turn(hub, "What about the Atlas launch?", refs=["project:atlas"])
    assert turn["outcome"] == "succeeded"
    systems = _system_texts(turn["calls"][0])
    memory = next(i for i, s in enumerate(systems) if s.startswith(PAGE))
    recall = next(i for i, s in enumerate(systems) if s.startswith("[NOTE:"))
    assert memory < recall
    block = systems[memory]
    assert block.find(PAGE) < block.find(OBSERVATIONS) < block.find(REFLECT_NOTE)
    assert "- Atlas launch is 2026-10-01. (note:n1)" in block


@pytest.mark.parametrize("mode", ["delete", "edit", "refile", "sensitive"])
def test_a_withdrawn_page_sentence_or_observation_never_reaches_the_chat_turn(hub, mode: str) -> None:
    db = hub.db
    scope, _ref, withdraw, _kwargs = _status_and_codename(db, mode)
    _learn(db)
    pages_module.write_page(db, Pages(), scope, pages_module.spec_for(scope[0], CHANGED))
    refs = [f"project:{scope[1]}"] if scope[0] == "project" else None
    before = _turn(hub, "What is the status and the codename?", refs=refs)
    assert "ZEPHYRSECRET" in json.dumps(before["calls"][0])
    withdraw()
    for step in (lambda: None, lambda: sweep(db), lambda: _learn(db)):
        step()
        turn = _turn(hub, "What is the status and the codename?", refs=refs)  # a fresh thread each time
        sent = json.dumps(turn["calls"][0])
        assert "ZEPHYRSECRET" not in sent
        assert any(s.startswith(PAGE) and "status is approved" in s for s in _system_texts(turn["calls"][0]))


def test_the_chat_turn_never_reads_its_own_thread_back_through_a_page(hub) -> None:
    """The thread is excluded, as the recall pass excludes it: a desk page
    sentence that rests on this thread's message is not served to it."""
    db = hub.db
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    thread = hub.svc.create(title="Planning")["id"]
    message = db.threads.append_message(thread, role="user")
    db.threads.append_part(message.id, kind="text", text="Desk codename is ZEPHYROWN.")
    _built(db)
    assert "ZEPHYROWN" in json.dumps(pages_module.read(db, "desk", "", CHANGED))
    turn = _turn(hub, "When is lunch?", thread_id=thread)
    systems = _system_texts(turn["calls"][0])
    assert any(s.startswith(PAGE) and "Desk lunch is noon." in s for s in systems)
    assert not any("ZEPHYROWN" in s for s in systems if s.startswith(PAGE))
    # Another thread reads it.
    other = _turn(hub, "When is lunch?")
    assert any("ZEPHYROWN" in s for s in _system_texts(other["calls"][0]) if s.startswith(PAGE))


@pytest.mark.parametrize("refs", [["project:atlas"], None])
def test_with_no_page_and_no_observation_the_chat_payload_is_byte_identical(hub, refs) -> None:
    _filed_note(hub.db, "n1", "Atlas launch is 2026-10-01.", "atlas" if refs else None)
    sweep(hub.db)
    """Against MAIN's output, recorded (``tests/fixtures/memory_slice6_main_chat.json``,
    from main 64d1e7126 on this same scenario): everything but the tools is
    byte-identical.  The tools are main's renderer output with the two
    changes this slice makes on purpose (memory.page added, the People
    operator note out of the chat rendering) and no other."""
    from holdspeak.mcp.families.people import MCP_ACCESS_NOTE

    main = json.loads((Path(__file__).parents[1] / "fixtures" / "memory_slice6_main_chat.json").read_text())
    _filed_note(hub.db, "n1", "Atlas launch is 2026-10-01.", "atlas" if refs else None)
    sweep(hub.db)
    turn = _turn(hub, "What about the Atlas launch?", refs=refs)
    adoption = hub.broker.inference_adoption_service
    admitted = adoption.admitted_payload(str(hub.db.threads.get_message(turn["assistant_message_id"]).operation_id))
    without_tools = {k: v for k, v in admitted.items() if k != "tools"}
    assert json.dumps(without_tools, sort_keys=True) == json.dumps(main["project" if refs else "desk"], sort_keys=True)
    assert "[MEMORY" not in json.dumps(admitted)
    tools = [t for t in admitted["tools"] if t["function"]["name"] != "memory.page"]
    assert len(tools) == len(admitted["tools"]) - 1
    expected_tools = json.loads(json.dumps(main["default_tools"]).replace(json.dumps(MCP_ACCESS_NOTE)[1:-1], ""))
    assert json.dumps(tools, sort_keys=True) == json.dumps(expected_tools, sort_keys=True)


def test_a_chase_turn_at_32k_with_memory_page_and_a_served_page_still_runs(hub) -> None:
    """Chase's palette (memory.page in it) at a 32k context: the turn is
    admitted and succeeds; the part is fitted to what is left."""
    _many_beliefs(hub.db, 12)
    turn = _turn(hub, "What about topic01?", refs=["project:atlas"], mode="hs-seed-mode-chase")
    assert turn["outcome"] == "succeeded", turn
    offered = {tool["function"]["name"] for tool in hub.engine.tools_seen[-1]}
    assert "memory.page" in offered and "people.commitment.transition" in offered


# ── memory.page, the chat tool ──────────────────────────────────────────


def test_memory_page_is_in_the_thread_palettes() -> None:
    from holdspeak.services import thread_modes
    from holdspeak.services.thread_tools import CHAT_PALETTE, tool_class, tool_sensitive

    assert "memory.page" in CHAT_PALETTE
    for tools in (thread_modes._DESK_TOOLS, thread_modes._CHASE_TOOLS):
        assert "memory.page" in tools
    # Plan has no People text to trim: the page would grow its palette.
    assert "memory.page" not in thread_modes._PLAN_TOOLS
    assert "memory.page" not in thread_modes._DRAFT_TOOLS
    assert (tool_class("memory.page"), tool_sensitive("memory.page")) == ("evidence_read", False)


def test_the_people_operator_note_leaves_the_chat_rendering_only() -> None:
    from holdspeak.mcp.families.people import MCP_ACCESS_NOTE, TOOLS as PEOPLE_TOOLS
    from holdspeak.services.thread_tools import tool_schemas_for

    rendered = {t["function"]["name"]: t["function"]["description"]
                for t in tool_schemas_for(frozenset(t["name"] for t in PEOPLE_TOOLS))}
    for tool in PEOPLE_TOOLS:
        if MCP_ACCESS_NOTE in tool["description"]:  # the MCP catalogue keeps it whole
            assert MCP_ACCESS_NOTE not in rendered[tool["name"]]
            assert "Leader-private prep is never returned." in rendered[tool["name"]]


def test_memory_page_runs_in_a_chat_turn_and_returns_only_served_sentences(hub) -> None:
    db = hub.db
    scope, _ref, withdraw, _kwargs = _status_and_codename(db, "delete")
    _learn(db)
    pages_module.write_page(db, Pages(), scope, pages_module.spec_for("project", CHANGED))
    withdraw()
    hub.engine.tool = ("memory.page", {"project_id": "atlas", "slug": CHANGED})
    turn = _turn(hub, "Read the Atlas page.")
    offered = [tool["function"]["name"] for tool in (hub.engine.tools_seen[-2] or [])]
    assert "memory.page" in offered
    results = [d for k, d in hub.events if k == "thread_tool_result" and d.get("name") == "memory.page"]
    assert results and results[-1]["outcome"] == "succeeded", results
    tool_messages = [m for m in turn["calls"][1] if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    page = json.loads(tool_messages[0]["content"])["page"]
    assert page["sentences"] and page["withheld"] >= 1
    assert all("Atlas status is approved." in s["text"] for s in page["sentences"])
    assert "ZEPHYRSECRET" not in json.dumps(turn["calls"])


# ── review round 1 (Astra, PR #850) ─────────────────────────────────────

#: Each thread palette's tool-schema bytes on MAIN (64d1e7126, before this
#: slice), measured with admission's own serializer (``_canonical``: sorted
#: keys, compact, ASCII).  Admission counts one token per byte, so no
#: palette may grow: a turn that fit on main must still fit.
MAIN_PALETTE_BYTES = {"default": 14871, "desk": 27680, "chase": 30959, "plan": 2875}


def test_no_thread_palette_grows_versus_main() -> None:
    from holdspeak.services import thread_modes
    from holdspeak.services.inference_adoption_service import _canonical
    from holdspeak.services.thread_tools import CHAT_PALETTE, tool_schemas_for

    palettes = {"default": CHAT_PALETTE, "desk": thread_modes._DESK_TOOLS,
                "chase": thread_modes._CHASE_TOOLS, "plan": thread_modes._PLAN_TOOLS}
    for name, tools in palettes.items():
        size = len(_canonical(tool_schemas_for(tools)).encode())
        assert size <= MAIN_PALETTE_BYTES[name], (name, size, MAIN_PALETTE_BYTES[name])


@pytest.mark.parametrize("size", [28300, 28850])
def test_a_plan_turn_main_admits_is_still_admitted(hub, size: int) -> None:
    """Astra's repro (28,300), and 28,850: the largest of 50-byte steps
    main admits in Plan (28,900 overflows on main).  Any growth of the
    Plan palette fails the second."""
    turn = _turn(hub, "Proceed. " + "a" * size, mode="hs-seed-mode-plan")
    assert turn["outcome"] == "succeeded" and len(turn["calls"]) == 1, turn


def test_every_pass_fits_the_part_again_so_a_continuation_never_overflows(hub) -> None:
    """Astra's repro: 32k, Plan, 40 desk beliefs, a long question, then a
    memory.search continuation.  Pass 1 carries the part; the continuation
    (with the tool exchange) refits it and runs, as main runs both."""
    for index in range(40):
        _filed_note(hub.db, f"n{index:02d}", f"Desk topic{index:02d} is value{index:02d}-" + "x" * 60 + ".", None)
    _built(hub.db)
    hub.engine.tool = ("memory.search", {"query": "ZZZNOTFOUNDZZZ"})
    turn = _turn(hub, "Proceed. " + "a" * 25500, mode="hs-seed-mode-plan")
    assert turn["outcome"] == "succeeded" and len(turn["calls"]) == 2, turn
    first, second = (json.dumps(call) for call in turn["calls"])
    assert "[MEMORY PAGE:" in first or "[MEMORY OBSERVATIONS:" in first  # the part was sent on pass 1
    assert second.count("\\n- ") < first.count("\\n- ")  # and it was cut to fit pass 2


@pytest.mark.parametrize("mode", ["delete", "edit", "refile", "sensitive"])
def test_a_memory_page_tool_result_is_never_replayed_on_a_later_turn(hub, mode: str) -> None:
    """Astra's repro: the page read with the chat tool on turn 1, the source
    withdrawn, then "Continue." in the same thread.  Turn 2 gets a stub that
    says to read the page again, never the stored text; the tool record
    (the receipt) stays as it was."""
    db = hub.db
    scope, _ref, withdraw, _kwargs = _status_and_codename(db, mode)
    _learn(db)
    pages_module.write_page(db, Pages(), scope, pages_module.spec_for(scope[0], CHANGED))
    hub.engine.tool = ("memory.page", {"scope": scope[0], "project_id": scope[1], "slug": CHANGED}
                       if scope[0] == "project" else {"scope": "desk", "slug": CHANGED})
    first = _turn(hub, "Proceed.")
    assert first["outcome"] == "succeeded" and "ZEPHYRSECRET" in json.dumps(first["calls"][-1])
    frozen = "\n".join(r.frozen_json or "" for r in db.threads.get_refs(first["thread_id"]))
    assert "ZEPHYRSECRET" not in frozen  # not the recall replay (out of scope, recorded)
    withdraw()
    hub.engine.tool = None
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert second["outcome"] == "succeeded"
    sent = second["calls"][0]
    assert not [m for m in sent if "ZEPHYRSECRET" in str(m.get("content", ""))]
    assert any(m["role"] == "tool" and "Call memory.page again" in m["content"] for m in sent)
    kept = [part.text for message in db.threads.list_path(first["thread_id"]) if message.role == "tool"
            for part in db.threads.get_parts(message.id)]
    assert any("ZEPHYRSECRET" in str(text) for text in kept)  # the receipt is kept
