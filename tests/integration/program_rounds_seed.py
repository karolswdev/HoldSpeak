"""The Program the interview-round replies were recorded on (PG-LANG LANG9).

Journey J1 (PROGRAM-JOURNEYS-2026-10-31.md, "Two paragraphs to a shipped
change") at station 3: its Program in Drafting with the planning draft of
LANG6 applied. The draft is the REAL recorded planner reply
(tests/fixtures/program_plan_reply.json, case ``j1``), replayed through the
planner's ``invoke_fn`` seam on a rig whose repository holds the owned files
at the recorded sizes. ``scripts/record_program_round_reply.py`` builds this
Program and records the real engine's questions and shaped answers;
``tests/unit/test_program_rounds.py`` and the route tests build the SAME
Program and replay them through the runner. Change it only with a new
recording.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from holdspeak.services import program_planner, program_rounds
from tests.integration.program_plan_seed import CASES, create
from tests.integration.program_rig import OWNER, Rig

PLAN = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_plan_reply.json").read_text(encoding="utf-8"))

#: J1's own answers (the journey's station 3 and 7), used when the engine offers no choice.
J1_ANSWERS = {"Architecture": "In the aftercare, after Stop.", "Verification": "Both: a measured run, and I try it."}


def _first_choice(service: Any, pid: str, name: str) -> str:
    row = next(item for item in service.store.list_rounds(pid) if item["name"] == name)
    question = program_rounds.waiting(row) or {}
    return (question.get("choices") or [None])[0] or J1_ANSWERS[name]


def _answer(name: str):
    def call(service: Any, pid: str, _steps: list) -> dict:
        return program_rounds.answer(service, OWNER, pid, name, None, choice=_first_choice(service, pid, name))
    return call


def _apply(service: Any, pid: str, outs: list) -> dict:
    """Apply: the rows of the last answer, as the face sends them (no engine call)."""
    last = next(out for out in reversed(outs) if out.get("source", "").startswith("round:"))
    applied = service.text_apply(OWNER, pid, last["allowed_text"], dry_run=False, base=last["base"])
    assert applied["applied"], applied
    return {"state": "applied", "applied": True}


#: The face's sequence, recorded once (each step one hub call; the engine is
#: called by ``next`` and ``answer``). ``tests/integration/
#: test_desk_program_rounds.py`` walks the same over REST.
SEQUENCE = [
    ("architecture.next", lambda service, pid, _s: program_rounds.ask(service, OWNER, pid, "Architecture")),
    ("architecture.answer", _answer("Architecture")),
    ("architecture.next2", lambda service, pid, _s: program_rounds.ask(service, OWNER, pid, "Architecture")),
    ("architecture.apply", _apply),
    ("architecture.skip_question", lambda service, pid, _s: program_rounds.skip_question(service, OWNER, pid, "Architecture")),
    ("architecture.done", lambda service, pid, _s: program_rounds.decide(service, OWNER, pid, "Architecture", "done")),
    ("product.next", lambda service, pid, _s: program_rounds.ask(service, OWNER, pid, "Product")),
    ("product.skip", lambda service, pid, _s: program_rounds.decide(service, OWNER, pid, "Product", "skip")),
    ("stack.next", lambda service, pid, _s: program_rounds.ask(service, OWNER, pid, "Stack")),
    ("stack.skip", lambda service, pid, _s: program_rounds.decide(service, OWNER, pid, "Stack", "skip")),
    ("verification.next", lambda service, pid, _s: program_rounds.ask(service, OWNER, pid, "Verification")),
    ("verification.answer", _answer("Verification")),
    ("verification.done", lambda service, pid, _s: program_rounds.decide(service, OWNER, pid, "Verification", "done")),
]


def drafted(rig: Rig) -> str:
    """J1 in Drafting with its recorded draft applied (station 2 → 3). The
    rig's engine is wired first (the planner resolves it; the draft's replies
    come through ``invoke_fn``, not the engine)."""
    case = PLAN["cases"]["j1"]
    pid = create(rig, CASES["j1"], file_bytes=case["file_bytes"])
    replies = [row["reply_text"] for row in case["exchanges"]]
    model = PLAN["engine"]["model"]
    result = program_planner.plan(rig.service, OWNER, pid, budget=CASES["j1"]["budget"],
                                  invoke_fn=lambda _payload: (replies.pop(0), model))
    answer = rig.service.text_apply(OWNER, pid, _allowed(rig, pid, result), dry_run=False, base=result.base_text)
    assert answer["applied"], answer
    return pid


def _allowed(rig: Rig, pid: str, result: Any) -> str:
    from holdspeak.services.program_text import allowed_model, parse_program_text, render

    return render(allowed_model(parse_program_text(result.base_text), parse_program_text(result.proposed_text),
                                result.rows))
