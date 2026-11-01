"""PG-DIRECTION DIR8: the call that decides, through the hub's Calls service.

The phone half is the fake ai-phone CLI (a real separate process,
``tests/fixtures/fake_ai_phone.py``), as ``test_calls_turn.py``; the Program
is the rig's (a real core question from a step that touched a file no step
owns), served to the call by ``DeskHeld`` and to the MCP dispatch by
``default_program_service``.

- "What waits on me?" is the hub's own script (no model turn): the package,
  "go on", the read back, "yes"; the ledger says "decided on a call" and the
  call's line links its transcript Note. The turns are recorded to
  ``tests/fixtures/calls.decide.json`` (``HOLDSPEAK_WIRE_WRITE=1``), with the
  Needs you row the call read and the ledger it left.

The model's way (a held ``program.decide`` from the call's turn) is proven in
``tests/unit/test_calls_decide.py``: a rig Program's tick leaves the rig hub's
call turn with no engine, so it does not run here (see the lane report).
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tests.integration.program_rig import FAKE_CHECK, OWNER as RIG_OWNER, Rig
from tests.integration.test_calls_turn import REMOTE, _fake, _said, _service, _write_config
from tests.unit.test_desk_ask_ai import hub  # noqa: F401  (fixture)

pytestmark = pytest.mark.timeout(180, method="thread")

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "calls.decide.json"
NOW = datetime(2026, 10, 31, 12, 10).astimezone()


def _core(tmp_path: Path) -> tuple[Rig, str]:
    rig = Rig(tmp_path / "rig")
    pid = rig.service.create(RIG_OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="normal")["id"]
    rig.service.plan(RIG_OWNER, pid, steps=[{"title": "Owned", "brief": "Store the stall reason.",
                                             "owns": ["src/a.py"]}])
    rig.service.start(RIG_OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    assert [item["kind"] for item in rig.service.needs_you_items()] == ["core"]
    return rig, pid


def _wire(rig: Rig, monkeypatch: pytest.MonkeyPatch, service: Any) -> None:
    from holdspeak.calls.decide import DeskHeld
    from holdspeak.services import program_service

    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")
    monkeypatch.setattr(program_service, "default_program_service", lambda db=None: rig.service)
    from holdspeak.services.reach_service import ReachService

    reach = ReachService(rig.db, programs=lambda: rig.service, clock=lambda: NOW.isoformat())
    service.configure(held=lambda: DeskHeld(rig.db, programs=lambda: rig.service, reach=lambda: reach,
                                            now=lambda: NOW))


class _NoModel:
    active_provider = "fixture"

    def __init__(self, model: str) -> None:
        self.active_model = model

    def run_prompt_stream(self, **_kw: Any) -> Any:
        raise AssertionError("a call that decides by the hub's script runs no model turn")


def test_what_waits_on_me_is_read_chosen_read_back_and_decided_on_a_call(hub, monkeypatch, tmp_path) -> None:
    from holdspeak.services.needs_you_membership import program_items

    rig, pid = _core(tmp_path)
    _write_config(control_mode="normal")
    heard = ["Blue heron.", "What waits on me?", "Go on.", "Yes.", "That's all, thanks."]
    state = _fake(tmp_path, monkeypatch, [{"kind": "incoming", "remote": REMOTE},
                                          *({"kind": "heard", "text": text} for text in heard)])
    service = _service(hub, monkeypatch, lambda model: _NoModel(model), [])
    _wire(rig, monkeypatch, service)
    row = program_items(rig.service.needs_you_items())[0]

    assert asyncio.run(service.serve_once(wait=5)) == "call"

    said = _said(state)
    assert said[0] == "Hello. Say your passphrase."
    # The owner's BRIEF RULE (2026-10-31): the page's lines, in the page's order.
    assert said[2].startswith("Overnight on the home box, step 1. Goal: "), said[2]
    assert "Let the step go on with this, or park it?" in said[2]
    assert said[2].endswith("Say Go on, Park, or later.")
    assert said[3] == ("You said Go on for step 1 of Overnight on the home box: the step goes on with this change. "
                       "Say yes to decide, or no.")
    assert said[4:] == ["Decided.", "That is all. One decided.", "Goodbye."], said
    assert rig.service.needs_you_items() == []
    ledger = [r for r in reversed(rig.service.store.list_checkpoints(pid)) if r.get("via") == "call"]
    assert ledger[0]["line"].startswith("Go on: ") and ledger[0]["line"].endswith(" · decided on a call")
    assert ledger[1]["line"].startswith("Asked on a call 12:10 · Go on, decided · transcript: Call · ")
    [call] = service.list()
    note_ref = call["note_ref"]
    assert note_ref and ledger[1]["undo"] == {"note_ref": note_ref, "because": {
        "rule": "asked_on_call", "kind": "core", "words": "a question", "via": "call"}}
    note = hub.db.notes.get(note_ref.split(":", 1)[1]).body_markdown
    assert "You said Go on for step 1" in note and "blue heron" not in note.lower()
    assert call["results"][-1]["effect"] == "decided"

    recorded = {
        "_note": "Recorded from the Calls rig by tests/integration/test_calls_program_decide.py; "
                 "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit a field a test reads.",
        "needs_you_row": {key: row[key] for key in ("why", "title", "group") if key in row},
        "turns": [{"who": "you" if t["who"] == "caller" else "holdspeak", "text": t["text"]}
                  for t in service.get(call["id"])["transcript"]],
        "ledger": [{"line": r["line"].split(" · transcript")[0], "via": r["via"]} for r in ledger],
    }
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        FIXTURE.write_text(json.dumps(recorded, indent=2, ensure_ascii=False) + "\n")
    stored = json.loads(FIXTURE.read_text())
    assert [t["text"] for t in stored["turns"]] == [t["text"] for t in recorded["turns"]]
    assert [r["line"][:40] for r in stored["ledger"]] == [r["line"][:40] for r in recorded["ledger"]]
