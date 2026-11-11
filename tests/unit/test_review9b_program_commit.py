"""A Program commit press binds the held request and the shown change."""
from pathlib import Path
import pytest
# Load the declared-operation registry before its Program contribution.
import holdspeak.operations
from holdspeak.program_operations import _decide_web
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import Rig, OWNER
from tests.integration.test_program_run import _held_step


def setup(tmp_path, monkeypatch):
    rig=Rig(tmp_path)
    pid,step=_held_step(rig,"normal")
    rig.gate.hold_commit(step["launch_id"])
    rig.tick()
    shown=next(item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "commit")
    decide=rig.gate.decide
    def live_decision(ident,**kw):
        if not any(row["proposal_id"] == ident for rows in rig.gate.holds.values() for row in rows):
            raise RuntimeError("the gate hold ended")
        return decide(ident,**kw)
    monkeypatch.setattr(rig.gate,"decide",live_decision)
    commits=[]
    monkeypatch.setattr(rig.runner,"commit_worktree",lambda *a: commits.append(a) or "a"*40)
    monkeypatch.setattr(rig.service,"_tick_now",lambda *_:None)
    return rig,pid,step,shown.get("commit_binding"),commits


def press(rig,pid,step,binding,choice="allow"):
    return _decide_web(rig.service,OWNER,{"program_id":pid,"step_id":step["id"],"kind":"commit", "choice":choice,
                                          "expected_commit_binding":binding})

@pytest.mark.parametrize("choice",["allow","not_now"])
def test_a_replaced_hold_refuses_the_old_answer(tmp_path, monkeypatch, choice):
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    rig.gate.expire(step["launch_id"]); rig.gate.hold_commit(step["launch_id"],"replacement")
    fresh=rig.service.store.get_step(step["id"])
    fresh["facts"]["held_commit"]["proposal_id"]="replacement"
    rig.service.store.save_step(fresh)
    with pytest.raises(ProgramRefused) as refusal: press(rig,pid,step,binding,choice)
    assert refusal.value.code == "commit_changed"
    assert not commits and not rig.gate.decisions


def test_an_ended_hold_never_falls_back_to_committing_the_current_worktree(tmp_path,monkeypatch):
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    rig.gate.expire(step["launch_id"])
    with pytest.raises(ProgramRefused) as refusal: press(rig,pid,step,binding)
    assert refusal.value.code == "commit_changed"
    assert not commits and not rig.gate.decisions


def test_a_change_after_the_displayed_commit_refuses_the_answer(tmp_path,monkeypatch):
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    worktree=Path(rig.service.store.get_step(step["id"])["worktree"])
    (worktree/"README.md").write_text("a replacement change\n")
    with pytest.raises(ProgramRefused) as refusal: press(rig,pid,step,binding)
    assert refusal.value.code == "commit_changed"
    assert not commits and not rig.gate.decisions


def test_the_current_displayed_hold_keeps_the_allow_path(tmp_path,monkeypatch):
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    press(rig,pid,step,binding)
    assert [(ident,allowed) for ident,allowed,_ in rig.gate.decisions] == [("gate-1",True)]
    assert not commits


@pytest.mark.parametrize("change", ["executable", "symlink"])
def test_untracked_file_type_and_execution_changes_refuse_the_shown_commit(tmp_path,monkeypatch,change):
    rig,pid,step,_binding,commits=setup(tmp_path,monkeypatch)
    file=Path(rig.service.store.get_step(step["id"])["worktree"])/"new-tool"
    file.write_text("a-target")
    binding=next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "commit").get("commit_binding")
    if change == "executable":
        file.chmod(0o755)
    else:
        file.unlink(); file.symlink_to("a-target")
    with pytest.raises(ProgramRefused) as refusal:
        press(rig,pid,step,binding)
    assert refusal.value.code == "commit_changed"
    assert not commits and not rig.gate.decisions


def test_an_agent_gets_no_owner_commit_proof_and_cannot_use_a_copied_proof(tmp_path,monkeypatch):
    from holdspeak.principals import Principal, PrincipalKind
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    agent=Principal(PrincipalKind.AGENT,"untrusted-agent")
    assert all("commit_binding" not in item for item in rig.service.get(agent,pid)["your_turn_items"])
    with pytest.raises(ProgramRefused) as refusal:
        _decide_web(rig.service,agent,{"program_id":pid,"step_id":step["id"],"kind":"commit","choice":"allow","expected_commit_binding":binding})
    assert refusal.value.code == "owner_required"
    assert not commits and not rig.gate.decisions


@pytest.mark.parametrize("via", ["page", "telegram"])
def test_a_saved_commit_package_keeps_its_hold_binding(tmp_path,monkeypatch,via):
    from holdspeak.services.briefing_service import BriefingService
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    briefing=BriefingService(rig.db,programs=lambda:rig.service)
    item=next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "commit")
    ref=f"program:{pid}:{item['id']}"
    made=briefing.make(OWNER,[ref])
    question=briefing.read(made["token"])["items"][0]["binding"]
    rig.gate.expire(step["launch_id"]); rig.gate.hold_commit(step["launch_id"],"replacement")
    fresh=rig.service.store.get_step(step["id"])
    fresh["facts"]["held_commit"]["proposal_id"]="replacement"
    rig.service.store.save_step(fresh)
    with pytest.raises(ProgramRefused) as refusal:
        briefing.answer_package(made["id"],ref,"allow",via=via,binding=question)
    assert getattr(refusal.value,"code",None) == "commit_changed"
    assert not commits and not rig.gate.decisions


@pytest.mark.parametrize("changed", [False, True])
def test_a_phone_choice_uses_the_original_message_binding_without_a_new_client_field(tmp_path,monkeypatch,changed):
    from holdspeak.phone import actions
    from holdspeak.phone.service import PhoneService
    from holdspeak.services.briefing_service import BriefingService
    rig,pid,step,binding,commits=setup(tmp_path,monkeypatch)
    briefing=BriefingService(rig.db,programs=lambda:rig.service)
    monkeypatch.setattr(actions,"_briefing",lambda db:briefing)
    phone=PhoneService(rig.db)
    monkeypatch.setattr(phone,"_quiet",lambda:True)
    message=phone.send_from_desk("Allow the commit?",origin_ref=f"program_step:{step['id']}:commit",program_step_id=step["id"])
    shown=phone.messages()["messages"][0]["actions"]
    assert shown["expected_commit_binding"] == binding
    from holdspeak.principals import Principal, PrincipalKind
    agent=Principal(PrincipalKind.AGENT,"reader")
    assert "expected_commit_binding" not in phone.messages(principal=agent)["messages"][0]["actions"]
    event=phone.events.page(include_owner_binding=False)["events"][0]
    assert "expected_commit_binding" not in event["data"]["message"]["actions"]
    assert phone.events.page()["events"][0]["data"]["message"]["actions"]["expected_commit_binding"] == binding
    if changed:
        rig.gate.expire(step["launch_id"]); rig.gate.hold_commit(step["launch_id"],"replacement")
        fresh=rig.service.store.get_step(step["id"])
        fresh["facts"]["held_commit"]["proposal_id"]="replacement"
        rig.service.store.save_step(fresh)
        assert phone.messages()["messages"][0]["actions"] == shown
        with pytest.raises(ProgramRefused) as refusal:
            phone.decide(message["id"],"allow")
        assert refusal.value.code == "commit_changed"
        assert not commits and not rig.gate.decisions
    else:
        assert phone.decide(message["id"],"allow")["decided"]
        assert [(ident,allowed) for ident,allowed,_ in rig.gate.decisions] == [("gate-1",True)]
