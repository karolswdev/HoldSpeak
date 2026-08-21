from __future__ import annotations

import json
import hashlib
import asyncio
import re
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.mcp.families import thought as thought_family
from holdspeak.mcp import resources
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ServiceError, ValidationError
from holdspeak.services.refinement_application_service import RefinementApplicationService
from holdspeak.services.refinement_coordinator import RefinementCoordinator
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID, RefinementThoughtService, _TERMINAL_CODE_CATEGORY,
    _closed_terminal_code,
)


OWNER = Principal(PrincipalKind.OWNER, "workbench-owner")


@pytest.fixture
def rig(tmp_path):
    db = Database(tmp_path / "workbench.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = RefinementThoughtService(db)
    thought = service.create(OWNER, request_id="capture", raw_text="Launch ownership", source={"kind":"typed"})
    return db, service, thought


def _review(db: Database, service: RefinementThoughtService, thought: dict, suffix: str = "workbench",
            placement: dict | None = None) -> str:
    reserved = service.reserve_refinement(
        OWNER, thought["id"], request_id="ask-"+suffix,
        expected_aggregate_revision=thought["aggregate_revision"],
        expected_working_revision=thought["working_revision"],
        expected_attachment_revision=thought["attachment_revision"],
    )
    ask_id = reserved["attempts"][0]["ask_invocation_id"]
    op_id, receipt_id, stage_id = "op_"+suffix, "receipt_"+suffix, "stage_"+suffix
    service.before_physical_dispatch(reserved["id"])(op_id, ask_id, 1)
    card = json.dumps({"kind":"question","question":"Who owns launch?","reason":"Name one owner."})
    placement = placement or {"target_id":"this_machine","target_name":"This device","target_kind":"this_device",
                              "boundary":"same_device","owner":"you","transport":"in_process",
                              "data_classes":["instruction","selected_context","grounding","generated_output"],
                              "engine":"scripted","model":"Scripted","fallback_reason":None}
    scope = "private_network" if placement["boundary"] == "private_network" else "local"
    egress = {"scope":scope, **({"host":"192.168.1.50"} if scope == "private_network" else {})}
    payload = json.dumps({"output":card,"actual_placement":placement,"egress":egress})
    with db._connection() as conn:
        conn.execute("INSERT INTO kernel_operations(operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,delegator_kind,delegator_identity,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (op_id,"req_"+suffix,"idem_"+suffix,"inference.invoke",1,"owner","workbench-owner","invocation:"+ask_id,"node:test","sha256:x","v","test","succeeded",1,ask_id,"","","","",1.0,1.0))
        conn.execute("INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
                     (receipt_id,op_id,"succeeded","succeeded","projection-stage:"+stage_id,1.0))
        conn.execute("INSERT INTO kernel_projection_stages(stage_id,invocation_id,operation_id,kind,projection_json,projection_sha256,result_ref,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (stage_id,ask_id,op_id,"ask-result","{}","sha256:x","projection-stage:"+stage_id,"PUBLISHED",1.0,1.0))
        conn.execute("INSERT INTO ask_results(projection_stage_id,invocation_id,operation_id,receipt_id,payload_json,created_at) VALUES(?,?,?,?,?,?)",
                     (stage_id,ask_id,op_id,receipt_id,payload,1.0))
    current = service.reconcile(OWNER, thought["id"], expected_aggregate_revision=thought["aggregate_revision"], invocation_id=reserved["id"])
    return current["continuity"]["review_result_id"]


def test_projection_is_zero_write_coherent_and_placement_is_historical(rig):
    db, service, thought = rig
    historical = {"target_id":"prof_historical","target_name":"Historical LAN",
                  "target_kind":"private_endpoint","boundary":"private_network","owner":"you",
                  "transport":"https","data_classes":["instruction","selected_context","grounding","generated_output"],
                  "engine":"openai_compatible","model":"old-model","fallback_reason":None}
    db.profiles.upsert(profile_id="prof_historical", name="Historical LAN", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="old-model", requires_key=False)
    review_id = _review(db, service, thought, placement=historical)
    with db._connection() as conn:
        before = "\n".join(conn.iterdump())
    db.profiles.upsert(profile_id="prof_historical", name="Now cloud", kind="openAICompatible",
                       base_url="https://api.changed.example/v1", model="new-model", requires_key=False)
    with db._connection() as conn:
        after_profile_change = "\n".join(conn.iterdump())
    workbench = service.get_workbench(OWNER, thought["id"], inference_available=True,
                                      intended_placement={"target_id":"this_machine","readiness":"ready"})
    with db._connection() as conn:
        after_projection = "\n".join(conn.iterdump())
    assert after_projection == after_profile_change
    assert before != after_profile_change
    assert workbench["workspace_state"] == "question"
    assert workbench["actions"]["primary"] == {"kind":"answer_and_continue","review_result_id":review_id}
    assert workbench["review"]["placement"]["state"] == "available"
    assert workbench["review"]["placement"]["actual_placement"]["target_name"] == "Historical LAN"
    assert workbench["review"]["placement"]["actual_placement"]["model"] == "old-model"
    assert workbench["review"]["placement"]["egress"] == {"scope":"private_network","host":"192.168.1.50"}
    assert workbench["workspace_cursor"]["thought_id"] == thought["id"]


def test_unavailable_ai_projects_direct_configuration_recovery(rig):
    _db, service, thought = rig
    workbench = service.get_workbench(OWNER, thought["id"], inference_available=False)

    assert workbench["workspace_state"] == "idle"
    assert workbench["inference"]["availability"] == "unavailable"
    assert workbench["actions"]["primary"] == {"kind":"configure_ai"}
    assert workbench["actions"]["state"] == [{"kind":"configure_ai"}]
    assert "complete" in workbench["actions"]["ambient"]


def test_cursor_forgery_refuses_before_mutation_and_legacy_absence_survives(rig):
    _db, service, thought = rig
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    forged = dict(cursor, continuity_revision=cursor["continuity_revision"] + 1)
    with pytest.raises(ConflictError) as error:
        service.update_working(OWNER, thought["id"], expected_aggregate_revision=1,
                               expected_working_revision=1, body_markdown="lost",
                               workspace_cursor=forged)
    assert error.value.code == "workspace_cursor_conflict"
    assert service.get(OWNER, thought["id"])["working_note"]["body_markdown"] == "Launch ownership"
    updated = service.update_working(OWNER, thought["id"], expected_aggregate_revision=1,
                                     expected_working_revision=1, body_markdown="legacy")
    assert updated["working_note"]["body_markdown"] == "legacy"


def test_atomic_answer_continue_replays_effect_and_child_with_fresh_cursor(rig):
    db, service, thought = rig
    review_id = _review(db, service, thought)
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    epoch = service.claim_refinement_host("workbench-host", "test", lease_seconds=30)
    claim = {"target_id":"test","target_kind":"this_device","boundary":"same_device",
             "engine":"scripted","model":"scripted","readiness":"ready","reason":""}
    result = service.answer_and_continue_with_dispatch_claim(
        OWNER, thought["id"], review_id, command_id="continue-one", answer="Mina.",
        expected_aggregate_revision=1, expected_working_revision=1,
        expected_attachment_revision=0, workspace_cursor=cursor,
        dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch, admission_claim=claim,
    )
    current, receipt, child, created = result
    assert created and current["working_note"]["body_markdown"].endswith("Answer: Mina.")
    assert receipt["effect"]["append_utf8_end"] > receipt["effect"]["append_utf8_start"]
    assert receipt["child_invocation_id"] == child["id"]
    fresh = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    replay = service.answer_and_continue_with_dispatch_claim(
        OWNER, thought["id"], review_id, command_id="continue-one", answer="Mina.",
        expected_aggregate_revision=1, expected_working_revision=1,
        expected_attachment_revision=0, workspace_cursor=fresh,
        dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch, admission_claim=claim,
    )
    assert replay[1] == receipt and replay[2]["id"] == child["id"] and replay[3] is False
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM refinement_answer_continue_commands").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM refinement_invocations WHERE thought_id=?", (thought["id"],)).fetchone()[0] == 2


def test_composite_empty_answer_and_unready_admission_refuse_without_append(rig):
    db, service, thought = rig
    review_id = _review(db, service, thought)
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    epoch = service.claim_refinement_host("workbench-host", "test", lease_seconds=30)
    with pytest.raises(ValidationError):
        service.answer_and_continue_with_dispatch_claim(
            OWNER, thought["id"], review_id, command_id="empty", answer="  ",
            expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0, workspace_cursor=cursor,
            dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch,
            admission_claim={"target_id":"test","target_kind":"this_device","boundary":"same_device",
                             "engine":"x","model":"x","readiness":"ready","reason":""})
    with pytest.raises(ConflictError) as unavailable:
        service.answer_and_continue_with_dispatch_claim(
            OWNER, thought["id"], review_id, command_id="unready", answer="Mina",
            expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0, workspace_cursor=cursor,
            dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch,
            admission_claim={"target_id":"test","target_kind":"this_device","boundary":"same_device",
                             "engine":"x","model":"x","readiness":"missing","reason":"gone"})
    assert unavailable.value.code == "refinement_continuation_unavailable"
    assert service.get(OWNER, thought["id"])["working_note"]["body_markdown"] == "Launch ownership"


def test_catalogue_has_eighteen_tools_and_workbench_original_resources():
    assert len(thought_family.TOOLS) == 18
    tools = {tool["name"]:tool for tool in thought_family.TOOLS}
    assert all(tool["inputSchema"]["additionalProperties"] is False for tool in tools.values())
    assert tools["thought.answer_and_continue"]["inputSchema"]["required"][-1] == "workspace_cursor"
    for unchanged in ("thought.create","thought.adopt_note","thought.get_default_context",
                      "thought.replace_default_context","thought.list_context"):
        assert "workspace_cursor" not in tools[unchanged]["inputSchema"]["properties"]
    templates = {item["uriTemplate"] for item in resources.list_resources()["resourceTemplates"]}
    assert "holdspeak://thoughts/{thought_id}/workbench" in templates
    assert "holdspeak://thoughts/{thought_id}/original" in templates


@pytest.mark.parametrize("initial,answer", [("", "Mina"), ("Launch ownership", "Mïna 🚀")])
def test_add_to_note_persists_exact_append_effect_and_replays_original_hub(rig, initial, answer):
    db, service, thought = rig
    if initial != "Launch ownership":
        thought = service.update_working(
            OWNER, thought["id"], expected_aggregate_revision=1,
            expected_working_revision=1, body_markdown=initial,
        )
    review_id = _review(db, service, thought)
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    current, receipt = service.review_action(
        OWNER, thought["id"], review_id, request_id="add-only", action="answer",
        answer=answer, expected_aggregate_revision=thought["aggregate_revision"],
        expected_working_revision=thought["working_revision"], expected_attachment_revision=0,
        workspace_cursor=cursor,
    )
    effect = receipt["effect"]
    body = current["working_note"]["body_markdown"].encode("utf-8")
    assert body[effect["append_utf8_start"]:effect["append_utf8_end"]].decode().endswith("Answer: " + answer)
    assert hashlib.sha256(body).hexdigest() == effect["body_sha256"]
    old_hub = effect["committed_post_cursor"]["hub_id"]
    with db._connection() as conn:
        conn.execute("UPDATE refinement_workspace_identity SET hub_id='hub_replacement' WHERE id=1")
    replay, replay_receipt = service.review_action(
        OWNER, thought["id"], review_id, request_id="add-only", action="answer",
        answer=answer, expected_aggregate_revision=thought["aggregate_revision"],
        expected_working_revision=thought["working_revision"], expected_attachment_revision=0,
        workspace_cursor={"hub_id":"hub_replacement","thought_id":thought["id"],
                          "aggregate_revision":current["aggregate_revision"],
                          "continuity_revision":effect["committed_post_cursor"]["continuity_revision"]},
    )
    assert replay["working_note"] == current["working_note"]
    assert replay_receipt == receipt
    assert replay_receipt["effect"]["committed_post_cursor"]["hub_id"] == old_hub


def test_add_to_note_replay_rejects_forged_effect_even_with_rehashed_json(rig):
    db, service, thought = rig
    review_id = _review(db, service, thought)
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    current, _receipt = service.review_action(
        OWNER, thought["id"], review_id, request_id="add-forge", action="answer",
        answer="Mina", expected_aggregate_revision=1, expected_working_revision=1,
        expected_attachment_revision=0, workspace_cursor=cursor,
    )
    with db._connection() as conn:
        row = conn.execute("SELECT append_effect_json FROM refinement_review_actions WHERE request_id='add-forge'").fetchone()
        forged = json.loads(row["append_effect_json"]); forged["append_utf8_start"] += 1
        raw = json.dumps(forged, sort_keys=True, separators=(",", ":"))
        conn.execute("UPDATE refinement_review_actions SET append_effect_json=?,append_effect_sha256=? WHERE request_id='add-forge'",
                     (raw, hashlib.sha256(raw.encode()).hexdigest()))
    with pytest.raises(ConflictError) as error:
        service.review_action(
            OWNER, thought["id"], review_id, request_id="add-forge", action="answer",
            answer="Mina", expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0,
            workspace_cursor=service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"],
        )
    assert error.value.code == "refinement_review_action_integrity"
    assert current["working_note"]["body_markdown"].endswith("Answer: Mina")


def test_composite_replay_rejects_repointed_valid_action_and_child(rig):
    db, service, thought = rig
    review_id = _review(db, service, thought)
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    epoch = service.claim_refinement_host("workbench-host", "test", lease_seconds=30)
    claim = {"target_id":"test","target_kind":"this_device","boundary":"same_device",
             "engine":"scripted","model":"scripted","readiness":"ready","reason":""}
    _current, _receipt, original_child, _ = service.answer_and_continue_with_dispatch_claim(
        OWNER, thought["id"], review_id, command_id="linked-command", answer="Mina",
        expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
        workspace_cursor=cursor, dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch,
        admission_claim=claim,
    )
    with db._connection() as conn:
        original_action = conn.execute("SELECT action_id FROM refinement_answer_continue_commands WHERE command_id='linked-command'").fetchone()[0]
    other = service.create(OWNER, request_id="capture-other", raw_text="Other", source={"kind":"typed"})
    other_review = _review(db, service, other, "other")
    service.review_action(OWNER, other["id"], other_review, request_id="other-action", action="answer",
                          answer="Else", expected_aggregate_revision=1, expected_working_revision=1,
                          expected_attachment_revision=0)
    with db._connection() as conn:
        other_action = conn.execute("SELECT action_id FROM refinement_review_actions WHERE request_id='other-action'").fetchone()[0]
        conn.execute("UPDATE refinement_answer_continue_commands SET action_id=? WHERE command_id='linked-command'", (other_action,))
    fresh = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    with pytest.raises(ConflictError) as action_error:
        service.answer_and_continue_with_dispatch_claim(
            OWNER, thought["id"], review_id, command_id="linked-command", answer="Mina",
            expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
            workspace_cursor=fresh, dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch,
            admission_claim=claim)
    assert action_error.value.code == "answer_continue_integrity"
    other_current = service.get(OWNER, other["id"])
    other_child = service.reserve_refinement(
        OWNER, other["id"], request_id="other-child",
        expected_aggregate_revision=other_current["aggregate_revision"],
        expected_working_revision=other_current["working_revision"], expected_attachment_revision=0)
    with db._connection() as conn:
        conn.execute("UPDATE refinement_answer_continue_commands SET action_id=?,child_invocation_id=? WHERE command_id='linked-command'",
                     (original_action, other_child["id"]))
    with pytest.raises(ConflictError) as child_error:
        service.answer_and_continue_with_dispatch_claim(
            OWNER, thought["id"], review_id, command_id="linked-command", answer="Mina",
            expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
            workspace_cursor=fresh, dispatch_host_id="workbench-host", dispatch_lease_epoch=epoch,
            admission_claim=claim)
    assert child_error.value.code == "answer_continue_integrity"
    assert original_child["thought_id"] == thought["id"]


@pytest.mark.parametrize("mutation", [
    lambda p: {**p, "egress":{"scope":"internet"}},
    lambda p: {**p, "egress":{"scope":"local","host":"é"}},
    lambda p: {**p, "actual_placement":{**p["actual_placement"], "data_classes":["instruction","instruction"]}},
    lambda p: {**p, "actual_placement":{**p["actual_placement"], "boundary":"cloud"}},
    lambda p: {**p, "actual_placement":{**p["actual_placement"], "target_id":"é"}},
])
def test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable(rig, mutation):
    _db, service, _thought = rig
    valid = {"actual_placement":{"target_id":"this_machine","target_name":"This device",
             "target_kind":"this_device","boundary":"same_device","owner":"you",
             "transport":"in_process","data_classes":["instruction"],"engine":"scripted",
             "model":"Scripted","fallback_reason":None},"egress":{"scope":"local"}}
    assert service._strict_review_provenance(json.dumps(valid))["state"] == "available"
    assert service._strict_review_provenance(json.dumps(mutation(valid))) == {"state":"unavailable"}


@pytest.mark.parametrize(("code","category","retryable"), [
    ("owner_answered","owner_terminal",False),
    ("thought_completed","owner_terminal",False),
    ("scheduler_lost_before_dispatch","retryable",True),
    ("provider_unavailable","retryable",True),
    ("restart_bound_outcome_unknown","indeterminate",False),
    ("ask_result_unpublished","indeterminate",False),
    ("refinement_result_invalid","integrity",False),
    ("unknown_terminal_code","integrity",False),
])
def test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable(code, category, retryable):
    source = "unknown_new_code" if code == "unknown_terminal_code" else code
    assert RefinementThoughtService._terminal_status(source) == {
        "code":code,"category":category,"retryable":retryable,
    }


def test_terminal_write_sites_and_dynamic_ingress_use_the_closed_vocabulary():
    source = Path("holdspeak/services/refinement_thought_service.py").read_text()
    persisted_literals = set(re.findall(r"terminal_code='([a-z_]+)'", source))
    assert persisted_literals <= set(_TERMINAL_CODE_CATEGORY)
    assert {"shutdown_before_dispatch","thought_missing_during_recovery",
            "restart_bound_outcome_unknown","refinement_result_stale","retry_plan_invalid",
            "retry_child_missing_after_plan","orphaned_before_dispatch_binding",
            "refinement_result_invalid","kernel_operation_missing","ask_result_unpublished"} <= persisted_literals
    assert _closed_terminal_code("new_unruled_provider_literal") == "unknown_terminal_code"
    assert _TERMINAL_CODE_CATEGORY["failed"] == "retryable"


def test_duplicate_dispatch_and_cancellation_callbacks_are_continuity_noops(rig):
    _db, service, thought = rig
    invocation = service.reserve_refinement(
        OWNER, thought["id"], request_id="callback-invocation",
        expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    hook = service.before_physical_dispatch(invocation["id"])
    ask_id = invocation["attempts"][0]["ask_invocation_id"]
    hook("op-callback", ask_id, 1)
    after_first = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    hook("op-callback", ask_id, 1)
    after_replay = service.get_workbench(OWNER, thought["id"], inference_available=True)["workspace_cursor"]
    assert after_replay == after_first

    service2_thought = service.create(OWNER, request_id="cancel-capture", raw_text="Cancel", source={"kind":"typed"})
    epoch = service.claim_refinement_host("cancel-host", "test", lease_seconds=30)
    claimed, _ = service.reserve_refinement_with_dispatch_claim(
        OWNER, service2_thought["id"], request_id="cancel-invocation",
        expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
        dispatch_host_id="cancel-host", dispatch_lease_epoch=epoch,
        admission_claim={"target_id":"test","target_kind":"this_device","boundary":"same_device",
                         "engine":"scripted","model":"scripted","readiness":"ready","reason":""})
    service.stop_refinement_with_owner(OWNER, service2_thought["id"], invocation_id=claimed["id"],
                                       expected_aggregate_revision=1)
    service.observe_host_cancellation("cancel-host", epoch, claimed["id"], "cancelled")
    cancelled_once = service.get_workbench(OWNER, service2_thought["id"], inference_available=True)["workspace_cursor"]
    service.observe_host_cancellation("cancel-host", epoch, claimed["id"], "different-late-value")
    cancelled_twice = service.get_workbench(OWNER, service2_thought["id"], inference_available=True)["workspace_cursor"]
    assert cancelled_twice == cancelled_once


def test_continuation_refusal_returns_fresh_workbench_without_answer_leak(rig):
    db, service, thought = rig
    review_id = _review(db, service, thought)
    class RefusingCoordinator:
        accepting = True
        def admission_claim(self):
            return {"target_id":"this_machine","target_kind":"this_device","boundary":"same_device",
                    "engine":"configured_local_engine","model":"","readiness":"unavailable","reason":"missing"}
        async def answer_and_continue(self, *_args, **_kwargs):
            raise ServiceError("refinement_continuation_unavailable",
                               "Couldn't start the next turn. Your answer is still here. Add it to the Note.",
                               context={"status":409,"readiness":"unavailable"})
    app = RefinementApplicationService(db, coordinator=RefusingCoordinator())
    cursor = service.get_workbench(OWNER, thought["id"], inference_available=False)["workspace_cursor"]
    with pytest.raises(ServiceError) as error:
        asyncio.run(app.answer_and_continue(
            OWNER, thought_id=thought["id"], review_result_id=review_id,
            command_id="refused-command", answer="TOP SECRET ANSWER",
            expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0, workspace_cursor=cursor))
    assert error.value.code == "refinement_continuation_unavailable"
    assert error.value.context["workbench"]["actions"]["primary"]["kind"] == "answer_review"
    assert "TOP SECRET ANSWER" not in json.dumps(error.value.context)
    assert service.get(OWNER, thought["id"])["working_note"]["body_markdown"] == "Launch ownership"


def test_dispatch_hook_refuses_replaced_host_epoch_for_initial_and_composite_child(rig):
    _db, service, thought = rig
    claim = {"target_id":"test","target_kind":"this_device","boundary":"same_device",
             "engine":"scripted","model":"scripted","readiness":"ready","reason":""}
    epoch = service.claim_refinement_host("epoch-host", "test", lease_seconds=30)
    invocation, _ = service.reserve_refinement_with_dispatch_claim(
        OWNER, thought["id"], request_id="epoch-initial", expected_aggregate_revision=1,
        expected_working_revision=1, expected_attachment_revision=0,
        dispatch_host_id="epoch-host", dispatch_lease_epoch=epoch, admission_claim=claim)
    service.claim_refinement_host("epoch-host", "test", lease_seconds=30)
    with pytest.raises(ValidationError) as initial_error:
        service.before_physical_dispatch(invocation["id"])(
            "op-old-epoch", invocation["attempts"][0]["ask_invocation_id"], 1)
    assert initial_error.value.code == "refinement_host_lease_expired"

    second = service.create(OWNER, request_id="epoch-composite-capture", raw_text="Second", source={"kind":"typed"})
    review_id = _review(_db, service, second, "epoch-composite")
    cursor = service.get_workbench(OWNER, second["id"], inference_available=True)["workspace_cursor"]
    child_epoch = service.claim_refinement_host("child-epoch-host", "test", lease_seconds=30)
    _current, _receipt, child, _ = service.answer_and_continue_with_dispatch_claim(
        OWNER, second["id"], review_id, command_id="epoch-child", answer="Mina",
        expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
        workspace_cursor=cursor, dispatch_host_id="child-epoch-host",
        dispatch_lease_epoch=child_epoch, admission_claim=claim)
    service.claim_refinement_host("child-epoch-host", "test", lease_seconds=30)
    with pytest.raises(ValidationError) as child_error:
        service.before_physical_dispatch(child["id"])(
            "op-old-child-epoch", child["attempts"][0]["ask_invocation_id"], 1)
    assert child_error.value.code == "refinement_host_lease_expired"


def test_default_same_id_readiness_change_refuses_initial_and_composite_before_writes(rig, monkeypatch):
    db, service, thought = rig
    from holdspeak.inference_targets import resolve_placement
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    target = resolve_placement(db).target
    claim = {"target_id":target.id,"target_kind":target.kind,"boundary":target.boundary,
             "engine":target.engine,"model":target.model,"readiness":target.readiness_state,
             "reason":target.readiness_reason}
    epoch = service.claim_refinement_host("default-host", "web", lease_seconds=30)
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness",
                        lambda: ("unavailable", "model disappeared"))
    with pytest.raises(ConflictError) as initial_error:
        service.reserve_refinement_with_dispatch_claim(
            OWNER, thought["id"], request_id="default-race-initial",
            expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
            dispatch_host_id="default-host", dispatch_lease_epoch=epoch,
            admission_claim=claim, validate_current_admission=True)
    assert initial_error.value.code == "refinement_continuation_unavailable"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM refinement_invocations WHERE thought_id=?", (thought["id"],)).fetchone()[0] == 0

    review_thought = service.create(OWNER, request_id="default-race-capture", raw_text="Race", source={"kind":"typed"})
    review_id = _review(db, service, review_thought, "default-race")
    cursor = service.get_workbench(OWNER, review_thought["id"], inference_available=True)["workspace_cursor"]
    with pytest.raises(ConflictError) as composite_error:
        service.answer_and_continue_with_dispatch_claim(
            OWNER, review_thought["id"], review_id, command_id="default-race-composite",
            answer="Mina", expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0, workspace_cursor=cursor,
            dispatch_host_id="default-host", dispatch_lease_epoch=epoch,
            admission_claim=claim, validate_current_admission=True)
    assert composite_error.value.code == "refinement_continuation_unavailable"
    assert service.get(OWNER, review_thought["id"])["working_note"]["body_markdown"] == "Race"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM refinement_answer_continue_commands").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM refinement_review_actions").fetchone()[0] == 0


def test_process_only_cursor_race_returns_fresh_workbench_and_one_cas_retry_saves_draft(rig):
    db, service, thought = rig
    app = RefinementApplicationService(db, coordinator=None)
    stale = service.get_workbench(OWNER, thought["id"], inference_available=False)["workspace_cursor"]
    invocation = service.reserve_refinement(
        OWNER, thought["id"], request_id="save-race-reserve",
        expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    ask_id = invocation["attempts"][0]["ask_invocation_id"]
    service.before_physical_dispatch(invocation["id"])("op-save-race", ask_id, 1)
    draft = "Draft survives the process-only cursor race"
    with pytest.raises(ConflictError) as conflict:
        app.update_working(
            OWNER, thought_id=thought["id"], expected_aggregate_revision=1,
            expected_working_revision=1, body_markdown=draft, workspace_cursor=stale)
    assert conflict.value.code == "workspace_cursor_conflict"
    fresh = conflict.value.context["workbench"]["workspace_cursor"]
    assert fresh["aggregate_revision"] == stale["aggregate_revision"]
    assert fresh["continuity_revision"] > stale["continuity_revision"]
    assert service.get(OWNER, thought["id"])["working_note"]["body_markdown"] == "Launch ownership"
    saved = app.update_working(
        OWNER, thought_id=thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, body_markdown=draft, workspace_cursor=fresh)
    assert saved["thought"]["working_note"]["body_markdown"] == draft
    assert saved["thought"]["aggregate_revision"] == 2
    assert saved["thought"]["working_revision"] == 2


@pytest.mark.parametrize("configured_path", [None, "/definitely/missing/holdspeak-model.gguf"])
def test_missing_local_model_path_refuses_initial_and_composite_with_fresh_workbench_zero_writes(
        rig, monkeypatch, configured_path):
    db, service, thought = rig
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path",
                        lambda: configured_path)
    from holdspeak.inference_targets import this_machine_target
    target = this_machine_target()
    assert target.readiness_state == "unavailable"
    if configured_path is None:
        assert target.deployment.model_path is None
    else:
        assert target.deployment.model_path == configured_path

    async def exercise():
        coordinator = RefinementCoordinator(db)
        await coordinator.start()
        app = RefinementApplicationService(db, coordinator=coordinator)
        try:
            with pytest.raises(ServiceError) as initial:
                await app.refine(
                    OWNER, thought_id=thought["id"], request_id="missing-model-initial",
                    expected_aggregate_revision=1, expected_working_revision=1,
                    expected_attachment_revision=0)
            assert initial.value.code == "refinement_continuation_unavailable"
            assert initial.value.context["workbench"]["inference"]["availability"] == "unavailable"
            review_thought = service.create(
                OWNER, request_id="missing-model-review", raw_text="Review", source={"kind":"typed"})
            review_id = _review(db, service, review_thought, "missing-model")
            cursor = service.get_workbench(
                OWNER, review_thought["id"], inference_available=False)["workspace_cursor"]
            with pytest.raises(ServiceError) as continuation:
                await app.answer_and_continue(
                    OWNER, thought_id=review_thought["id"], review_result_id=review_id,
                    command_id="missing-model-composite", answer="Mina",
                    expected_aggregate_revision=1, expected_working_revision=1,
                    expected_attachment_revision=0, workspace_cursor=cursor)
            assert continuation.value.code == "refinement_continuation_unavailable"
            assert continuation.value.context["workbench"]["actions"]["primary"]["kind"] == "answer_review"
            assert service.get(OWNER, review_thought["id"])["working_note"]["body_markdown"] == "Review"
            with db._connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM refinement_invocations WHERE thought_id=?", (thought["id"],)).fetchone()[0] == 0
                assert conn.execute("SELECT COUNT(*) FROM refinement_answer_continue_commands").fetchone()[0] == 0
                assert conn.execute("SELECT COUNT(*) FROM refinement_review_actions").fetchone()[0] == 0
        finally:
            await coordinator.shutdown()
    asyncio.run(exercise())
