"""A Program's desk step: display requests, in order, through the MCP port.

The brief is a JSON list of {op, args}. Only mark, say and scroll are work;
press belongs to the owner. Request ids and answers stay on the step. No
connected Desk leaves one Needs-you row; its next presence resumes the step
on the normal Program tick. A hub restart can replay only display work.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from ..principals import Principal, PrincipalKind
from .errors import NotFound
from .program_definitions import ProgramRefused

WAIT = "Open the Desk to see this result."


def requests(body: str) -> list[dict[str, Any]]:
    try:
        rows = json.loads(body)
    except (TypeError, ValueError):
        raise ProgramRefused("desk_requests_invalid", "A Desk step needs a JSON list of display requests.", status=400) from None
    if not isinstance(rows, list) or not rows or len(rows) > 20:
        raise ProgramRefused("desk_requests_invalid", "A Desk step needs 1 to 20 display requests.", status=400)
    from .. import operations
    schemas = {d.name.removeprefix("desk."): d.tool_schema for d in operations.DESK_DISPLAY_OPERATIONS
               if d.name in {"desk.mark", "desk.say", "desk.scroll"}}
    from jsonschema import validate, ValidationError

    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("op"), str) or row["op"] not in schemas or set(row) - {"op", "args"}:
            raise ProgramRefused("desk_request_forbidden", "A Program can mark, say or scroll. A press is yours.", status=400)
        try:
            args = row.get("args", {})
            validate(args, schemas[row["op"]])
            field = "words" if row["op"] == "say" else "target"
            if not args[field].strip():
                raise ValidationError(f"{field} is empty")
        except ValidationError:
            raise ProgramRefused("desk_requests_invalid", "The display request needs valid words or a target.", status=400) from None
    return rows


def connected() -> bool:
    from ..desk_presence import is_connected
    return is_connected()


def _port(service: Any) -> Any:
    from .. import operations
    from ..runtime import composition
    from .desk_window_service import DeskWindowService

    try:
        runtime = composition.current()
    except composition.NoRuntimeError:
        runtime = None
    if runtime is not None and runtime.db is service.db and runtime.operations is not None:
        return runtime.operations
    # Partial compositions (the service rig) use their database, never the
    # owner's default database or a second live runtime.
    windows = runtime.desk_window_service if runtime is not None and runtime.db is service.db else None
    return operations.bind({"desk_window_service": windows or DeskWindowService(service.db)},
                           operations.DESK_DISPLAY_OPERATIONS)


def advance(runner: Any, program: Mapping[str, Any], step: dict[str, Any]) -> None:
    service = runner.service
    rows = requests(step.get("brief_markdown") or "")  # validate again after an owner edit
    if step["state"] == "ready":
        service.transition(program, step, "briefed")
    if step["state"] == "briefed":
        service.transition(program, step, "working")
    facts = dict(step.get("facts") or {})
    display = dict(facts.get("desk") or {})
    answers = list(display.get("answers") or [])
    port = _port(service)
    # Never inherit the runner's owner identity. A Program has work rights.
    principal = Principal(PrincipalKind.AGENT, f"program:{program['id']}")

    def keep() -> None:
        facts["desk"] = display
        if facts != step.get("facts"):
            step["facts"] = facts
            service._save(step)

    def wait(line: str) -> None:
        keep()
        if step["state"] != "waiting" or step.get("held_reason") != line:
            service.transition(program, step, "waiting", held_reason=line)

    completed = sum(answer.get("done") is True for answer in answers)
    while completed < len(rows):
        pending = display.get("request_id")
        if pending:
            try:
                answer = port.invoke(principal, "desk.request.read", {"request_id": pending})
            except NotFound:
                # In-memory requests disappear on hub restart. Replaying a
                # display request is safe; Programs never replay a press.
                display.pop("request_id", None)
                pending = None
            else:
                if not answer.get("answered"):
                    if connected():
                        port.invoke(principal, "desk.request.replay", {"request_id": pending})
                    wait("The Desk has not answered yet." if connected() else WAIT)
                    return
                answers.append(answer)
                display.update(answers=answers)
                display.pop("request_id", None)
                keep()
                if not answer.get("done"):
                    reason = str(answer.get("reason") or "The Desk could not show this result.")
                    service.transition(program, step, "failed", report=reason, line=reason)
                    return
                completed += 1
                continue
        if not connected():
            wait(WAIT)
            return
        if step["state"] == "waiting":
            service.transition(program, step, "working")
        row = rows[completed]
        sent = port.invoke(principal, f"desk.{row['op']}", dict(row.get("args") or {}))
        display["request_id"] = sent["request_id"]
        keep()
    if step["state"] == "waiting":
        service.transition(program, step, "working")
    service.transition(program, step, "done", report="Shown on the Desk.", line="Shown on the Desk")
