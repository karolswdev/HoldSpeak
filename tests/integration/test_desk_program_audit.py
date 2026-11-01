"""PG-LANG §13b JRN8 to JRN10 (journey J7, "A reviewer-only program").

The Audit template over the real engine (``program_rig``): each step reads
one surface and reports findings; nothing is built, checked or merged. The
findings become Door tasks by the Program's level (one task for one finding
across steps), the Program's wire carries the Findings board, and the MUST
findings make a fix Program in Drafting that only a Start starts. The
answers are stored for the face (``audit.board.json``, ``audit.fix.json``
under ``web/src/desk/programs/__fixtures__``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from holdspeak.mcp import palettes
from holdspeak.mcp.families import program as program_family
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from holdspeak.services.needs_you_membership import compose, program_items
from holdspeak.services.program_audit import RULES, parse
from tests.integration.program_rig import OWNER, Rig, git
from tests.integration.test_desk_programs import _client, _fixture
from tests.unit.test_program_service import _launch_principal

REPORT_1 = ("I read the Notes window at 1440 and 393.\n"
            "MUST: The Notes toolbar wraps at 520 · .tmp/evidence-shots/notes-520.png\n"
            "SHOULD: The Notes title is grey on grey · web/src/desk/notes/NotesWindow.tsx:41\n"
            "NOTE: Notes is fine at 393")
#: Step 2 finds the same toolbar defect in other words (case, an end mark).
REPORT_2 = ("I read the Programs window.\n"
            "- MUST: the notes toolbar wraps at 520. · .tmp/evidence-shots/programs-notes.png\n"
            "MUST: The Programs list cuts the title at 393 · web/src/desk/programs/ProgramList.tsx:88")


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:600])
    return response.json()


def _audit(rig: Rig, control: str = "yolo", steps: int = 2) -> str:
    pid = rig.service.create(OWNER, title="Desk audit", goal="Find what is wrong on the desk.",
                             repository=str(rig.repo), template="audit", control=control)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Notes window", "brief": "Audit the Notes window."},
                                        {"title": "Programs window", "brief": "Audit the Programs window."}][:steps])
    rig.service.start(OWNER, pid)
    rig.tick()
    return pid


def _tasks(rig: Rig) -> list[Any]:
    return [item for item in rig.db.meetings.list_action_items(include_completed=True)
            if getattr(item, "source_type", "") == "program_step"]


def _lines(rig: Rig, pid: str) -> list[str]:
    return [row["line"] for row in rig.program(pid)["checkpoints"]]


def _report(rig: Rig, monkeypatch, pid: str, ordinal: int, words: str) -> None:
    step = rig.step(pid, ordinal)
    agent = _launch_principal(monkeypatch, step["launch_id"])
    answer = rig.service.step_done(agent, pid, step["id"], words)
    assert answer["waits_for"] == "nothing: the engine files the findings"
    rig.tick()


def test_audit_files_findings_dedupes_and_proposes_a_fix_program(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    pid = _audit(rig)
    one = rig.step(pid, 1)
    assert one["gate"]["merge"] == "none" and one["gate"]["check"] is False and one["gate"]["review"] == "none"
    # The audit's track: BRIEF · WORK · REVIEW · FILE (nothing is checked or merged).
    assert one["stations"] == ["brief", "work", "review", "file"] and one["station"] == 1
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    assert rig.step(pid, 1)["state"] == "done" and rig.step(pid, 1)["station"] == 3
    assert "Audited · 3 findings · 1 MUST" in _lines(rig, pid)
    # YOLO files every finding, in his words, with the step as its origin.
    tasks = sorted(item.task for item in _tasks(rig))
    assert tasks == ["Must fix: The Notes toolbar wraps at 520 (.tmp/evidence-shots/notes-520.png)",
                     "Noted: Notes is fine at 393",
                     "Should fix: The Notes title is grey on grey (web/src/desk/notes/NotesWindow.tsx:41)"]
    assert all(item.source_ref.startswith(f"program_step:{one['id']}:finding:") for item in _tasks(rig))
    # Not every step reported: no fix program row yet.
    assert [item["kind"] for item in rig.program(pid)["your_turn_items"]] == []

    # Step 2 ends its turn with its findings as its last words (no step_done).
    two = rig.step(pid, 2)
    rig.words[two["launch_id"]] = REPORT_2
    rig.agent.end_turn(two["launch_id"])
    rig.tick()
    assert rig.step(pid, 2)["state"] == "done"
    assert len(_tasks(rig)) == 4  # the toolbar finding is one task for both steps
    wire = rig.program(pid)
    board = wire["findings_board"]
    assert board["head"] == "4 findings · 2 MUST" and (board["must"], board["should"], board["note"]) == (2, 1, 1)
    toolbar = board["rows"][0]
    assert toolbar["steps"] == [1, 2] and toolbar["words"] == "Must fix" and toolbar["filed"] is True
    assert toolbar["evidence"] == [".tmp/evidence-shots/notes-520.png", ".tmp/evidence-shots/programs-notes.png"]
    assert [row["level"] for row in board["rows"]] == ["MUST", "MUST", "SHOULD", "NOTE"]
    assert wire["state"] == "done" and wire["fix_program_id"] is None
    # The fix program row, on the desk and in Needs you.
    [row] = wire["your_turn_items"]
    assert row["kind"] == "fix_program" and row["choices"] == ["make", "skip"] and row["count"] == 2
    assert row["title"] == "A fix program from 2 MUST findings"
    assert row["brief"]["question"] == "Make a fix program from the MUST findings?"
    [needs] = [item for item in program_items(rig.service.needs_you_items()) if item["program"]["kind"] == "fix_program"]
    assert needs["why"] == "TO DECIDE" and needs["program"]["decide"].endswith(f"/steps/{row['step_id']}/decide")
    _fixture("audit.board.json", wire, tmp_path)

    # Make: a Drafting Program, one step per MUST, each with its Review
    # requirement, linked to the audit. It never starts by rule.
    made = _ok(client.post(f"/api/programs/{pid}/steps/{row['step_id']}/decide",
                           json={"kind": "fix_program", "choice": "make"}))
    fix = made["fix_program"]
    assert made["program"]["id"] == pid and made["program"]["fix_program_id"] == fix["id"]
    _fixture("audit.fix.json", made, tmp_path)
    assert fix["state"] == "drafting" and fix["origin_ref"] == f"program:{pid}" and fix["title"] == "Fix: Desk audit"
    assert [step["title"] for step in fix["steps"]] == ["The Notes toolbar wraps at 520",
                                                       "The Programs list cuts the title at 393"]
    reqs = rig.service.requirements(fix["id"])
    assert sorted(req["text"] for req in reqs if req.get("step_id")) == [
        "The Notes toolbar wraps at 520 is fixed", "The Programs list cuts the title at 393 is fixed"]
    assert all(req["kind"] == "review" for req in reqs if req.get("step_id"))
    assert fix["steps"][0]["origin_ref"].startswith("action:ai_")
    rig.tick(3)
    assert rig.program(fix["id"])["state"] == "drafting"
    after = rig.program(pid)
    assert after["fix_program_id"] == fix["id"] and after["your_turn_items"] == []
    again = client.post(f"/api/programs/{pid}/propose_fix")
    assert again.status_code == 409 and again.json()["code"] == "fix_made"


def test_an_audit_in_drafting_reads_its_surfaces(tmp_path, monkeypatch) -> None:
    """The Drafting face's answer: each step names the surface it reads (its
    ``owns``), and its track is the audit's; a build keeps the six."""
    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    pid = rig.service.create(OWNER, title="Desk audit", goal="Find what is wrong on the desk.",
                             repository=str(rig.repo), template="audit", control="secure")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Notes window", "brief": "Audit the Notes window.", "owns": ["web/src/desk/notes/"]},
        {"title": "Programs window", "brief": "Audit the Programs window.", "owns": ["web/src/desk/programs/"]}])
    wire = _ok(client.get(f"/api/programs/{pid}"))
    wire = wire.get("program", wire)
    assert wire["state"] == "drafting" and wire["template"] == "audit" and wire["findings_board"] is None
    assert [step["owns"] for step in wire["steps"]] == [["web/src/desk/notes/"], ["web/src/desk/programs/"]]
    assert all(step["stations"] == ["brief", "work", "review", "file"] and step["station"] == -1
               for step in wire["steps"])
    _fixture("audit.drafting.json", wire, tmp_path)
    build = rig.service.create(OWNER, title="A build", goal="Build it.", repository=str(rig.repo))["id"]
    rig.service.plan(OWNER, build, steps=[{"title": "One", "brief": "Do one."}])
    assert rig.step(build, 1)["stations"] == ["brief", "work", "check", "review", "pr", "merge"]


def test_propose_fix_over_mcp_and_its_refusals(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    assert TOOL_AUTHORITY["program.propose_fix"] == WORK
    assert "program.propose_fix" in palettes.resolve_palette(palettes.CONDUCTOR)
    pid = _audit(rig, steps=1)
    client = _client(rig, monkeypatch)
    none = client.post(f"/api/programs/{pid}/propose_fix")
    assert none.status_code == 409 and none.json()["code"] == "no_must_findings"
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    answer = program_family.dispatch("program.propose_fix", {"program_id": pid}, OWNER)
    assert answer["steps"] == 1 and answer["fix_program"]["state"] == "drafting"
    other = rig.service.create(OWNER, title="Build", repository=str(rig.repo), template="fast-cycle")["id"]
    refused = client.post(f"/api/programs/{other}/propose_fix")
    assert refused.status_code == 409 and refused.json()["code"] == "not_an_audit"


def test_audit_levels_file_by_rule_or_ask(tmp_path, monkeypatch) -> None:
    # Normal: MUST and SHOULD are filed; a NOTE stays in the program.
    rig = Rig(tmp_path / "normal")
    pid = _audit(rig, "normal", steps=1)
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    assert sorted(item.task.split(":")[0] for item in _tasks(rig)) == ["Must fix", "Should fix"]
    assert [row["filed"] for row in rig.program(pid)["findings_board"]["rows"]] == [True, True, False]

    # Secure: none by rule; one row asks him, File files all.
    rig = Rig(tmp_path / "secure")
    pid = _audit(rig, "secure", steps=1)
    # Secure holds every call of the step's agent; its report still lands.
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    assert _tasks(rig) == []
    items = rig.program(pid)["your_turn_items"]
    asks = {item["kind"]: item for item in items}
    # The live walk: Close is asked last, after the audit's own rows.
    assert [item["kind"] for item in items] == ["audit_file", "fix_program", "close"]
    assert asks["audit_file"]["title"] == "3 findings to file as Door tasks"
    assert asks["audit_file"]["choices"] == ["file", "skip"] and "fix_program" in asks
    # The face's answers: the wire, the rows in Needs you, and his File through the route.
    client = _client(rig, monkeypatch)
    _fixture("audit.secure.json", _ok(client.get(f"/api/programs/{pid}")), tmp_path)
    needs = [item for item in program_items(rig.service.needs_you_items())
             if item["program"]["kind"] in ("audit_file", "fix_program")]
    assert [item["why"] for item in needs] == ["TO DECIDE", "TO DECIDE"]
    # The route's own answer (`compose`, what GET /api/desk/needs-you serves).
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    answer_needs = compose(rig.db, OWNER, {"items": []})
    assert [row for row in answer_needs["items"] if row.get("source") == "program"]
    _fixture("needs_you.audit.json", answer_needs, tmp_path)
    answer = _ok(client.post(f"/api/programs/{pid}/steps/{asks['audit_file']['step_id']}/decide",
                             json={"kind": "audit_file", "choice": "file"}))
    _fixture("audit.filed.json", answer, tmp_path)
    assert answer["filed"] == 3 and len(_tasks(rig)) == 3
    assert "Filed 3 findings as Door tasks" in _lines(rig, pid)
    assert [item["kind"] for item in rig.program(pid)["your_turn_items"] if item["kind"] != "close"] == ["fix_program"]
    skip = rig.service.decide(OWNER, pid, asks["fix_program"]["step_id"], kind="fix_program", choice="skip")
    assert skip["program"]["fix_program_id"] is None
    assert [item["kind"] for item in rig.program(pid)["your_turn_items"] if item["kind"] != "close"] == []


def test_an_audit_commit_is_a_core_question_and_a_silent_turn_is_asked_then_parked(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _audit(rig)
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"README.md": "changed\n"}, message="An audit must not commit")
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] != "done"
    assert any(item["kind"] == "core" for item in rig.program(pid)["your_turn_items"])
    assert "A core question for you: an audit step made a commit; an audit changes nothing" in _lines(rig, pid)

    # Step 2 ends its turn with no findings and no report: asked once, then parked.
    two = rig.step(pid, 2)
    rig.words[two["launch_id"]] = "I looked around."
    rig.agent.end_turn(two["launch_id"])
    rig.tick()
    assert rig.prompts[-1][0] == two["launch_id"] and "report your findings" in rig.prompts[-1][1]
    assert rig.step(pid, 2)["state"] != "parked"
    rig.agent.end_turn(two["launch_id"])
    rig.tick()
    parked = rig.step(pid, 2)
    assert parked["state"] == "parked" and parked["parked_reason"] == "The audit ended twice with no report"


def test_no_findings_is_a_report(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = _audit(rig, steps=1)
    _report(rig, monkeypatch, pid, 1, "I read the Dock. No findings.")
    wire = rig.program(pid)
    assert rig.step(pid, 1)["state"] == "done" and "Audited · no findings" in _lines(rig, pid)
    assert wire["findings_board"] == {"head": "No findings", "total": 0, "must": 0, "should": 0, "note": 0,
                                      "rows": []}
    assert [item for item in wire["your_turn_items"] if item["kind"] == "fix_program"] == []


def test_the_audit_brief_says_read_only_and_how_to_report(tmp_path) -> None:
    from holdspeak.services.program_brief import compose

    rig = Rig(tmp_path)
    pid = _audit(rig, steps=1)
    text = compose(rig.db, rig.step(pid, 1)["id"])["text"]
    assert all(line in text for line in RULES)
    assert "Commit your work" not in text and "opens the pull request" not in text
    assert git(Path(rig.ledger.get(rig.step(pid, 1)["launch_id"])["worktree_path"]), "status", "--short") == ""


def test_parse_reads_the_three_levels_and_their_evidence() -> None:
    rows = parse("MUST: A · x.py:1\n* should - B\nnote — C\nMUST: none\nprose MUST: not at the start")
    assert [(row["level"], row["text"], row["evidence"]) for row in rows] == [
        ("MUST", "A", "x.py:1"), ("SHOULD", "B", ""), ("NOTE", "C", "")]
    assert rows[0]["key"] == parse("- must: a.")[0]["key"]
