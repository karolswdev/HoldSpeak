"""Record complete list/detail pairs from the existing isolated producers.

The glass must not pair one rig's detail with another rig's master. These
are the same real engine replies and service operations the older face used.
No provider is called and no HTTP success answer is written by hand.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from tests.integration.program_rig import Rig


def test_program_window_seats_replay_complete_real_producer_pairs(tmp_path, monkeypatch):
    from holdspeak.services import program_service as module
    from scripts import record_program_fixtures as old
    from tests.integration import test_desk_program_shape as shapes
    from tests.integration import test_desk_program_plan as plans

    lists, captured, rigs, engines, texts = {}, {}, [], {}, {}
    original_client = shapes._client
    # Register restoration before the older standalone recorder assigns it.
    monkeypatch.setattr(module, "default_program_service", module.default_program_service)

    def keep(wire, client):
        if not isinstance(wire, dict):
            return
        program = wire.get("program", wire)
        if isinstance(program, dict) and program.get("id") and isinstance(program.get("steps"), list):
            response = client.get("/api/programs")
            assert response.status_code == 200, response.text
            lists[f"{program['id']}:{program['revision']}"] = response.json()
            engines[program["id"]] = client.get(f"/api/programs/{program['id']}/shape").json()
            texts[program["id"]] = client.get(f"/api/programs/{program['id']}/text").json()

    class CaptureClient:
        def __init__(self, client):
            self.client = client

        def get(self, path, **kw):
            response = self.client.get(path, **kw)
            if response.status_code == 200 and path != "/api/programs":
                keep(response.json(), self.client)
            return response

        def post(self, path, **kw):
            response = self.client.post(path, **kw)
            if response.status_code < 300:
                keep(response.json(), self.client)
            return response

        def __getattr__(self, key):
            return getattr(self.client, key)

    def client(rig, patch):
        return CaptureClient(original_client(rig, patch))

    def fixture(name, answer, _root):
        captured[name] = answer
        return answer

    for suite in (shapes, plans):
        monkeypatch.setattr(suite, "_client", client)
        monkeypatch.setattr(suite, "_fixture", fixture)
    shapes.test_shape_over_rest_preview_apply_yolo_and_overturn(tmp_path / "shape", monkeypatch)
    plans.test_plan_draft_over_rest_apply_and_split(tmp_path / "plan", monkeypatch)
    plans.test_a_three_goal_paste_proposes_three_programs_and_apply_all_links_them(tmp_path / "split", monkeypatch)

    def rig(*args, **kw):
        result = Rig(*args, **kw)
        rigs.append(result)
        return result

    original_get, original_press = old._get, old._press
    monkeypatch.setattr(old, "Rig", rig)
    monkeypatch.setattr(old, "_client", lambda rig: original_client(rig, monkeypatch))
    import holdspeak.principals as principals
    monkeypatch.setattr(principals, "agent_credentials", principals.agent_credentials)

    def get(client, path):
        answer = original_get(client, path)
        keep(answer, client)
        return answer

    def press(client, path, body, method="post"):
        answer = original_press(client, path, body, method)
        keep(answer, client)
        return answer

    monkeypatch.setattr(old, "_get", get)
    monkeypatch.setattr(old, "_press", press)
    root = tmp_path / "readers"
    root.mkdir()
    captured["limited"] = old.record_limited(root)
    captured["race"] = old.record_race(root)
    captured.update(old.record_requirements(root))
    captured.update(old.record_adjust(root))
    captured.update(old.record_todo(root))
    captured.update(old.record_lane(root))
    captured.update(old.record_family(root))
    captured.update(old.record_proposals(root))
    from tests.unit.test_reach_packages import _core, _briefing, _ref
    from tests.integration.program_rig import OWNER
    reach_rig, reach_id, reach_item = _core(tmp_path / "briefing")
    briefing = _briefing(reach_rig)
    reach_client = original_client(reach_rig, monkeypatch)
    before = reach_client.get(f"/api/programs/{reach_id}").json()
    keep(before, reach_client)
    made = briefing.make(OWNER, [_ref(reach_id, reach_item)])
    opened = reach_client.get(f"/api/programs/{reach_id}").json()
    keep(opened, reach_client)
    captured["briefing"] = {"program": before, "opened": opened, "made": made,
                             "revoked": briefing.revoke(OWNER, made["id"])}
    # Every candidate has its own question and step revision.
    from tests.integration.test_program_race import _race
    choice_rig = Rig(tmp_path / "race-choice")
    choice_id = _race(choice_rig, control="secure")
    choice_rig.service.start(OWNER, choice_id)
    for step in [choice_rig.step(choice_id, 1), *choice_rig.step(choice_id, 1)["contenders"]]:
        choice_rig.agent.finish(step["launch_id"], {f"{step['id']}.py": "green\n"})
    choice_rig.tick(3)
    choice_client = original_client(choice_rig, monkeypatch)
    pending = choice_client.get(f"/api/programs/{choice_id}").json()
    keep(pending, choice_client)
    item = next(item for item in pending["your_turn_items"] if item["kind"] == "race")
    raw = choice_rig.service._program(choice_id)
    binding = choice_rig.service._answer_binding(raw, choice_rig.service._step(raw, item["step_id"]))
    picked = choice_client.post(f"/api/programs/{choice_id}/steps/{item['step_id']}/decide", json={"kind":"race", "choice":"pick", "reason":"Keep this result.", "binding":binding})
    assert picked.status_code == 200, picked.text
    keep(picked.json(), choice_client)
    captured["race_choice"] = {"program": pending, "picked": picked.json(), "step_id":item["step_id"]}
    from tests.integration import test_desk_program_audit as audits
    audit_clients = []
    def audit_client(rig, patch):
        result = client(rig, patch)
        audit_clients.append(result)
        return result
    def audit_fixture(name, answer, _root):
        keep(answer, audit_clients[-1].client)
        captured[name] = answer
        return answer
    monkeypatch.setattr(audits, "_client", audit_client)
    monkeypatch.setattr(audits, "_fixture", audit_fixture)
    audits.test_audit_files_findings_dedupes_and_proposes_a_fix_program(tmp_path / "audit", monkeypatch)
    from types import SimpleNamespace
    from tests.integration.test_desk_program_from_action import _action
    action_rig = Rig(tmp_path / "action-seat")
    monkeypatch.setattr(action_rig.service,"_project_source",lambda _id:SimpleNamespace(primary_path=str(action_rig.repo)))
    action = _action(action_rig,"Keep the action proof with its work.")
    action_client = original_client(action_rig,monkeypatch)
    made_action = action_client.post("/api/programs/from-action",json={"action_id":action})
    assert made_action.status_code == 201,made_action.text
    action_id = made_action.json()["id"]
    unbound = action_client.get(f"/api/programs/{action_id}").json()
    keep(unbound,action_client)
    captured["action_unbound"] = unbound
    added_requirement = action_client.post(f"/api/programs/{action_id}/requirements",json={"text":"Keep the action proof.","kind":"word"})
    assert added_requirement.status_code == 201,added_requirement.text
    keep(added_requirement.json(),action_client)
    captured["editable_requirement"] = added_requirement.json()
    image = None
    for service_rig in rigs:
        program = captured["program.requirements.json"]
        if service_rig.service.store.get_program(program["id"]):
            row = next(row for step in program["steps"] for row in step["requirements"]
                       if row["evidence"].get("kind") == "shot")
            response = old._client(service_rig).get(row["evidence"]["url"])
            assert response.status_code == 200, response.text
            image = {"type": response.headers["content-type"], "base64": base64.b64encode(response.content).decode()}
    assert image
    out = {"lists": lists, "wires": captured, "shot": image, "engines": engines, "texts": texts}
    for key in ("limited", "race", "program.requirements.json", "program.adjust.json"):
        program = captured[key]
        assert any(row["id"] == program["id"] for row in lists[f"{program['id']}:{program['revision']}"]["programs"])
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path = Path(__file__).resolve().parents[2] / "web/src/desk/programs/__fixtures__/program.visual10.json"
        path.write_text(json.dumps(out, sort_keys=True) + "\n")


def test_program_fixture_producer_replays_owner_actions(tmp_path, monkeypatch):
    from holdspeak.services import program_service
    import holdspeak.principals as principals
    from scripts import record_program_fixtures as recorder
    service_factory = program_service.default_program_service
    credentials = principals.agent_credentials
    # The standalone recorder assigns both globals directly. Restore them
    # before another hub or launch can use this test's service or credentials.
    with monkeypatch.context() as patch:
        patch.setattr(program_service, "default_program_service", service_factory)
        patch.setattr(principals, "agent_credentials", credentials)
        fixtures = recorder.record(tmp_path)
    assert program_service.default_program_service is service_factory
    assert principals.agent_credentials is credentials
    recorder._check(fixtures)
    recorder._check_text(fixtures)
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        for name, answer in fixtures.items():
            (recorder.OUT / name).write_text(json.dumps(answer,indent=2,sort_keys=True)+"\n")
