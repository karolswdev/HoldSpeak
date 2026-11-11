"""Program answers require the question custody at each external boundary."""
import pytest

from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import OWNER
from tests.integration.test_program_answer_binding import _seed
from tests.integration.test_desk_programs import _client


@pytest.mark.parametrize("method,path,body", [
    ("POST", "steps/{sid}/decide", {"kind":"core","choice":"go_on"}),
    ("POST", "requirements/r/decide", {"choice":"met"}),
    ("POST", "proposals/1/decide", {"choice":"add"}),
    ("POST", "park", {}), ("POST", "close", {}),
    ("DELETE", "steps/{sid}", {}),
    ("POST", "text", {"dry_run":False}),
    ("POST", "text", {"dry_run":None,"preview":False}),
    ("POST", "rounds/Architecture/answer", {"answer":"Keep it"}),
    ("POST", "rounds/Architecture/decide", {"choice":"skip"}),
    ("POST", "checkpoints/1/start-from", {}),
])
def test_http_question_operations_refuse_an_omitted_binding(tmp_path, monkeypatch, method, path, body):
    rig, pid, sid = _seed(tmp_path)
    client = _client(rig, monkeypatch, bound=False)
    before = rig.program(pid)
    response = client.request(method, f"/api/programs/{pid}/{path.format(sid=sid)}", json=body)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "answer_stale"
    assert response.json()["detail"] == "This question changed. Read it again."
    assert rig.program(pid) == before


@pytest.mark.parametrize("surface", ["page", "digest", "phone", "telegram", "call"])
def test_token_answer_and_agent_text_cannot_use_an_unbound_command_path(tmp_path, surface):
    from tests.unit.test_reach_packages import _core
    rig, pid, item = _core(tmp_path)
    sid = item["step_id"]
    before = rig.program(pid)
    for answer in (
        lambda: rig.service.decide(OWNER, pid, sid, kind="core", choice="go_on", via=surface),
        lambda: rig.service.answer_agent(OWNER, pid, sid, "Keep it", via=surface),
    ):
        with pytest.raises(ProgramRefused) as refused:
            answer()
        assert refused.value.code == "answer_stale"
        assert refused.value.detail == "This question changed. Read it again."
        assert rig.program(pid) == before


def test_a_checkpoint_binding_is_consumed_before_a_second_start(tmp_path, monkeypatch):
    from tests.unit.test_program_checkpoint_reach import _started, _pinned
    rig, pid, step = _started(tmp_path)
    rig.service.checkpoint(OWNER, pid, step["id"], "First pin")
    row = _pinned(rig, pid)[0]
    binding = rig.service._answer_binding(rig.service._program(pid), None)
    client = _client(rig, monkeypatch, bound=False)
    url = f"/api/programs/{pid}/checkpoints/{row['id']}/start-from"
    before = rig.program(pid)
    first = client.post(url, json={"binding":binding})
    assert first.status_code == 200, first.text
    after = rig.program(pid)
    second = client.post(url, json={"binding":binding})
    assert second.status_code == 409 and second.json()["code"] == "answer_stale"
    assert rig.program(pid) == after
    import os, json
    from pathlib import Path
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path = Path(__file__).resolve().parents[2] / "web/src/desk/programs/__fixtures__/program.start-fit.json"
        path.write_text(json.dumps({"program":before,"checkpoint_id":row["id"],"answer":first.json()},sort_keys=True)+"\n")


def test_lowering_approval_cannot_move_to_replacement_text(tmp_path):
    rig, pid, sid = _seed(tmp_path)
    base = rig.service.text_get(OWNER,pid)["text"]
    first = base.replace("control secure", "control normal")
    replacement = base.replace("control secure", "control yolo")
    preview = rig.service.text_apply(OWNER,pid,first)
    other = rig.service.text_apply(OWNER,pid,replacement)
    assert preview["lowers"] == other["lowers"] and preview["lowers"]
    before = rig.program(pid)
    binding = rig.service._answer_binding(rig.service._program(pid),None)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.text_apply(OWNER,pid,replacement,dry_run=False,allow_lower=preview["lowers"],proposal_id=preview["proposal_id"])
    assert refused.value.code == "answer_stale"
    assert rig.program(pid) == before
    result = rig.service.text_apply(OWNER,pid,replacement,dry_run=False,allow_lower=other["lowers"],proposal_id=other["proposal_id"])
    assert result["applied"] and rig.program(pid)["control"] == "yolo"
    import os, json
    from pathlib import Path
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path = Path(__file__).resolve().parents[2] / "web/src/desk/programs/__fixtures__/program.review-fit.json"
        path.write_text(json.dumps({"program":before,"base":base,"first_text":first,"second_text":replacement,"first":preview,"second":other,"applied":result,"binding":binding},sort_keys=True)+"\n")


@pytest.mark.parametrize("kind", ["item", "digest"])
def test_token_page_and_digest_refuse_an_omitted_question_binding(tmp_path, monkeypatch, kind):
    from tests.integration.test_desk_reach import _rig, Clock
    rig, pid, client = _rig(tmp_path, monkeypatch, Clock())
    item = rig.program(pid)["your_turn_items"][0]
    ref = f"program:{pid}:{item['id']}"
    made = client.post("/api/reach/packages", json={"refs":[ref],"kind":kind}).json()
    shown = client.get(f"/api/b/{made['token']}").json()["items"][0]
    assert shown["binding"]["program_id"] == pid
    before = rig.program(pid)
    response = client.post(f"/api/b/{made['token']}/answer", json={"ref":ref,"choice":"go_on"})
    assert response.status_code == 409 and response.json()["code"] == "answer_stale", response.text
    assert response.json()["detail"] == "This question changed. Read it again."
    assert rig.program(pid) == before


def test_owner_mcp_text_preview_alias_cannot_omit_its_apply_binding(tmp_path,monkeypatch):
    from holdspeak.mcp.families import program as family
    from holdspeak.services import program_service as module
    rig,pid,_sid=_seed(tmp_path)
    monkeypatch.setattr(module,"default_program_service",lambda db=None:rig.service)
    text=rig.service.text_get(OWNER,pid)["text"]
    before=rig.program(pid)
    with pytest.raises(ProgramRefused) as refusal:
        family.dispatch("program.text_apply",{"program_id":pid,"text":text,"dry_run":None,"preview":False},OWNER)
    assert refusal.value.code == "answer_stale"
    assert rig.program(pid) == before
