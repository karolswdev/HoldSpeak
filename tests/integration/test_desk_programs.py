"""PG16 on the Programs rig: decisions from a Program (design §9b).

His Skip, a rule's Skip above NOTE, and a merge by rule each become ONE
proposed decision record: the reason, the rule and the level in its
context, linked to the Program and to the step's PR, filed to the Project.
The Room's decisions section carries it under ``proposed`` with its Program
and PR; the Program's checkpoint and Decided for you rows carry its id;
``decision_record.list`` filters by program. The NOTE rule's Skip (the
noise filter) proposes nothing. A withdrawn record comes back as the same
record (one per checkpoint).
No auto-confirm: the record stays proposed.

The face half replays the answers recorded here
(``web/src/desk/programs/__fixtures__/program.skip_decision.json`` and
``room.decisions.proposed.json``; ``HOLDSPEAK_WIRE_WRITE=1`` rewrites them,
else this test fences their shape).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.services import program_service as program_module
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.project_service import ProjectService
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

FIXTURES = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "programs" / "__fixtures__"


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    return type(value).__name__


def _fixture(name: str, answer: Any, tmp_path: Path) -> Any:
    """The hub's own answer, stored for the face (never typed by hand)."""
    scrubbed = json.loads(re.sub(re.escape(str(tmp_path)), "/tmp/rig", json.dumps(answer)))
    path = FIXTURES / name
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(json.loads(path.read_text())) == _shape(scrubbed), f"{name}: not the hub's shape"
    return scrubbed


def _client(rig: Rig, monkeypatch) -> TestClient:
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    return TestClient(app)


def _rig(tmp_path: Path, control: str) -> tuple[Rig, str]:
    rig = Rig(tmp_path)
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    pid = rig.service.create(
        OWNER, title="The words wave", goal="Plain words.", repository=str(rig.repo),
        check_command=f"sh {FAKE_CHECK}", template="build-and-review", control=control,
        reviewer_profile="codex-default", project_id="proj-holdspeak",
    )["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Dock words", "brief": "Plain words on the Dock.", "owns": ["web/src/desk/dock/words.ts"]},
    ])
    rig.service.start(OWNER, pid)
    return rig, pid


def _review(rig: Rig, pid: str, words: str) -> None:
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"web/src/desk/dock/words.ts": "export {};\n"})
    rig.tick(2)  # the check, then the reviewer starts
    for record in rig.ledger.list():
        if record.get("helper_of"):
            rig.words[record["launch_id"]] = words
            rig.states[record["launch_id"]] = {"state": "done", "turn_id": "r"}
    rig.tick(2)


def _record(rig: Rig, record_id: str) -> dict[str, Any]:
    record = DecisionRecordService(rig.db).get(OWNER, record_id)
    assert record is not None, record_id
    return record


def test_a_skip_is_a_proposed_decision_in_the_room_with_its_program_and_pr(tmp_path, monkeypatch) -> None:
    rig, pid = _rig(tmp_path, "secure")
    client = _client(rig, monkeypatch)
    _review(rig, pid, "MUST: none\nSHOULD: sentence case the title\nNOTE: the old name stays in a comment")
    step = rig.step(pid, 1)
    assert step["state"] == "findings", step["state"]
    should = next(f for f in step["findings"] if f["level"] == "SHOULD")
    note = next(f for f in step["findings"] if f["level"] == "NOTE")

    # The NOTE rule skipped the note (every level): the noise filter, no record.
    assert note["decision"] == "skip" and not note.get("decision_record_id")
    decided = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "finding_note")
    assert decided["decision_record_id"] is None
    assert not ProjectService(rig.db).room(OWNER, "proj-holdspeak")["decisions"]["proposed"]
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(mcp_tools, "get_database", lambda: rig.db)
    assert mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER) == []

    # His Overturn: the finding is his again (nothing to withdraw).
    rig.service.overturn(OWNER, pid, decided["id"])

    # His Skip of the note: a proposed record, his reason.
    answer = client.post(f"/api/programs/{pid}/steps/{step['id']}/decide", json={
        "kind": "finding", "choice": "skip", "finding_id": note["id"], "reason": "The comment helps a reader"})
    assert answer.status_code == 200, answer.text
    note_record = answer.json()["decision_record_id"]
    assert note_record
    again = _record(rig, note_record)
    assert "Reason: The comment helps a reader" in again["rationale"] and "Decided by: you" in again["rationale"]
    assert "Control: Secure" in again["rationale"] and "Rule:" not in again["rationale"]
    assert again["status"] == "proposed" and again["lifecycle"] == "active"

    # His Skip of the SHOULD: a second record; every finding is decided, so the PR opens.
    answer = client.post(f"/api/programs/{pid}/steps/{step['id']}/decide", json={
        "kind": "finding", "choice": "skip", "finding_id": should["id"], "reason": "The title is a proper name"})
    assert answer.status_code == 200, answer.text
    should_record = answer.json()["decision_record_id"]
    assert should_record and should_record != note_record
    step = rig.step(pid, 1)
    assert step["state"] in ("pr_open", "merge_ask") and step["pr"]["url"], step["state"]

    record = _record(rig, should_record)
    assert record["decision_text"] == "Skip this should finding on step 1: sentence case the title"
    assert record["title"] == "Skip: sentence case the title"
    assert {(w["work_type"], w["work_ref"]) for w in record["work"]} == {
        ("program", pid), ("pr", step["pr"]["url"])}
    assert {(s["source_type"], s["source_ref"]) for s in record["sources"]} == {("project", "proj-holdspeak")}

    # The checkpoint row of his Skip names the record.
    lines = {c["line"]: c for c in rig.program(pid)["checkpoints"]}
    assert lines["Skip: sentence case the title"]["decision_record_id"] == should_record

    # The Room: both proposed, with the Program and the PR; not in the decided items.
    decisions = ProjectService(rig.db).room(OWNER, "proj-holdspeak")["decisions"]
    assert decisions["state"] == "ok"
    assert not decisions["items"]
    rows = {row["id"]: row for row in decisions["proposed"]}
    assert set(rows) == {should_record, note_record}
    assert rows[should_record]["text"] == "Skip: sentence case the title"
    assert rows[should_record]["program"] == {"id": pid, "title": "The words wave"}
    assert rows[should_record]["prs"] == [{"number": step["pr"]["number"], "url": step["pr"]["url"]}]

    # MCP: decision_record.list by program.
    listed = mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER)
    assert {row["id"] for row in listed} == set(rows)
    assert all(row["status"] == "proposed" for row in listed)

    _fixture("program.skip_decision.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    _fixture("room.decisions.proposed.json", decisions, tmp_path)


def test_a_merge_by_rule_is_a_proposed_decision_with_its_rule(tmp_path, monkeypatch) -> None:
    rig, pid = _rig(tmp_path, "normal")
    _review(rig, pid, "MUST: none")
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done"), step["state"]
    merge = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "merge")
    assert merge["decision_record_id"]
    record = _record(rig, merge["decision_record_id"])
    assert record["status"] == "proposed"
    assert record["title"] == f"Merge PR #{step['pr']['number']}: Dock words"
    assert "Rule: Normal merges on a green check and a passed review" in record["rationale"]
    assert "Reason: Check green, review passed" in record["rationale"]
    assert ("pr", step["pr"]["url"]) in {(w["work_type"], w["work_ref"]) for w in record["work"]}
    # One record per merge: another tick writes nothing new.
    rig.tick(2)
    # The id is the checkpoint's: proposing again is the same record; a
    # withdrawn record comes back as the same record.
    from types import SimpleNamespace

    from holdspeak.services import program_decisions

    program = rig.service.store.get_program(pid)
    stored = rig.service.store.get_step(step["id"])
    outcome = SimpleNamespace(rule="Normal merges on a green check and a passed review")
    assert rig.service.propose_merge(program, stored, outcome) == merge["decision_record_id"]
    program_decisions.withdraw(rig.db, merge["decision_record_id"])
    assert DecisionRecordService(rig.db).get(OWNER, merge["decision_record_id"]) is None
    assert rig.service.propose_merge(program, stored, outcome) == merge["decision_record_id"]
    assert _record(rig, merge["decision_record_id"])["status"] == "proposed"
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(mcp_tools, "get_database", lambda: rig.db)
    assert [row["id"] for row in mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER)] == [
        merge["decision_record_id"]]
