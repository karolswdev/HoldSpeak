"""PHILO-5-03 pair fences.

The durable values in these rows come from the real ``PrimitiveService``
producer. The surrounding dictionaries copy the observation shape emitted by
``graph_walk.py``: named operation records, named HTTP paths, and stage slots.
They intentionally exercise missing-stage and mutation reds in the pair
verifier itself.
"""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.primitive_service import PrimitiveService
from scripts.philo5_pairs import build_pairs, compare_pair


OWNER = Principal(PrincipalKind.OWNER, "owner")


def _decision(db_path: Path, title: str = "One service layer") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    service = PrimitiveService(Database(db_path))
    created = service.create_decision(
        OWNER, title=title, status="proposed", context_markdown="source from the real producer",
        decision_markdown="retain the one service layer",
    )
    before = service.get_decision(OWNER, created["id"])
    updated = service.update_decision(OWNER, created["id"], status="accepted")
    after = service.get_decision(OWNER, created["id"])
    return created, before, after


def _op_decision(created: dict[str, Any], before: dict[str, Any], after: dict[str, Any], *, mode: str = "none") -> dict[str, Any]:
    return {
        "run_id": "op-run", "duration_s": 0.25, "provenance": {"engine_mode": mode},
        "restart": {"action": "restart_hub", "meeting_before": {"meeting_id": "meeting-chain"},
                     "meeting_after": {"meeting_id": "meeting-chain"}, "summary_retained": True,
                     "receipt_retained": True, "meeting_identity_retained": True},
        "setup": [
            {"kind": "op", "name": "decision.create", "domain_response": created},
            {"kind": "op", "name": "decision.read", "domain_response": before},
            {"kind": "op", "name": "decision.update", "domain_response": after},
        ],
        "before": {"op": {"kind": "op", "name": "decision.read", "domain_response": before}},
        "after": {
            "op": {"kind": "op", "name": "decision.read", "domain_response": after},
            "op_reads": [{"kind": "op", "name": "decision.read", "domain_response": after}],
        },
    }


def _browser_decision(created: dict[str, Any], before: dict[str, Any], after: dict[str, Any], *, mode: str = "none") -> dict[str, Any]:
    return {
        "run_id": "browser-run", "verdict": "pass", "viewport": 1440,
        "provenance": {"engine_mode": mode},
        "restart": {"action": "restart_hub", "meeting_before": {"meeting_id": "meeting-chain"},
                     "meeting_after": {"meeting_id": "meeting-chain"}, "summary_retained": True,
                     "receipt_retained": True, "meeting_identity_retained": True},
        "setup": [
            {"kind": "api", "method": "POST", "path": "/api/decisions", "response": {"decision": created}, "status": 201},
        ],
        "before": {"api_reads": [{"method": "GET", "path": f"/api/decisions/{before['id']}", "status": 200, "payload": before}]},
        "after": {"api_reads": [{"method": "GET", "path": f"/api/decisions/{after['id']}", "status": 200, "payload": after}]},
    }


def _pair(op: dict[str, Any], browser: dict[str, Any], pair_id: str = "case.closure.chain.s4_decision_recorded") -> dict[str, Any]:
    return {"pair_id": pair_id, "op": {"observation": op}, "browser": {"observation": browser}}


def test_real_producer_decision_projection_ignores_generated_ids_but_requires_created_at(tmp_path: Path) -> None:
    op_created, op_before, op_after = _decision(tmp_path / "op.db")
    browser_created, browser_before, browser_after = _decision(tmp_path / "browser.db")
    result = compare_pair(_pair(_op_decision(op_created, op_before, op_after),
                                _browser_decision(browser_created, browser_before, browser_after)))
    assert result["verdict"] == "pass", result["checks"]
    assert any(row["name"] == "created_at_stable_within_run" and row["status"] == "pass" for row in result["checks"])


def test_skewed_final_title_is_a_durable_projection_red(tmp_path: Path) -> None:
    op_created, op_before, op_after = _decision(tmp_path / "op.db")
    browser_created, browser_before, browser_after = _decision(tmp_path / "browser.db")
    browser_after = {**browser_after, "title": "Mutated durable title"}
    result = compare_pair(_pair(_op_decision(op_created, op_before, op_after),
                                _browser_decision(browser_created, browser_before, browser_after)))
    assert result["verdict"] == "fail"
    assert any(row["name"] == "decision.title" and row["status"] == "fail" for row in result["checks"])


def test_created_at_changed_within_a_run_is_red(tmp_path: Path) -> None:
    op_created, op_before, op_after = _decision(tmp_path / "op.db")
    browser_created, browser_before, browser_after = _decision(tmp_path / "browser.db")
    browser_after = {**browser_after, "created_at": "2099-01-01T00:00:00Z"}
    result = compare_pair(_pair(_op_decision(op_created, op_before, op_after),
                                _browser_decision(browser_created, browser_before, browser_after)))
    assert result["verdict"] == "fail"
    assert any(row["name"] == "created_at_stable_within_run" and row["status"] == "fail" for row in result["checks"])


def test_operation_slot_keeps_name_and_unnamed_domain_dict_is_blocked(tmp_path: Path) -> None:
    created, before, after = _decision(tmp_path / "op.db")
    op = _op_decision(created, before, after)
    op["setup"] = []
    op["before"] = {}
    op["after"]["op"] = {"domain_response": after}
    browser_created, browser_before, browser_after = _decision(tmp_path / "browser.db")
    result = compare_pair(_pair(op, _browser_decision(browser_created, browser_before, browser_after)))
    assert result["verdict"] == "blocked"
    assert any(row["name"] == "op.meeting_reads" or row["name"] == "op_engine_mode" for row in result["checks"])


def _refusal_pair(*, op_text: str, browser_text: str, shelf: bool = False) -> dict[str, Any]:
    family = "case.j10.brief_item_shelf.refused" if shelf else "case.a1.decision_face_create.opens_and_reopens"
    if shelf:
        op_trigger = {"kind": "op", "name": "brief.shelf.write", "refusal": {"error": op_text},
                      "envelope": {"result": {"isError": True}}}
        browser_trigger = {"kind": "api", "method": "POST", "path": "/api/brief/items/item-1/shelf",
                           "status": 422, "response": {"detail": browser_text}}
        brief = {"id": "brief-1", "sections": {"decisions": [{"id": "item-1", "text": "Shelf item",
                                                                    "source_ref": "decision:decision-1"}]}}
        before = {"brief_id": "brief-1", "shelf": {"item-1": "acknowledged"}}
        after = copy.deepcopy(before)
        op = {"run_id": "op", "duration_s": 0.1, "provenance": {"engine_mode": "none"},
              "trigger": op_trigger, "before": {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": brief},
                                                                  {"kind": "op", "name": "brief.shelf.read", "domain_response": before}]},
              "after": {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": brief},
                                         {"kind": "op", "name": "brief.shelf.read", "domain_response": after}]}}
        browser = {"run_id": "browser", "viewport": 393, "verdict": "pass", "provenance": {"engine_mode": "none"},
                   "trigger": browser_trigger,
                   "before": {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "status": 200, "payload": brief},
                                                {"method": "GET", "path": "/api/brief/shelf", "status": 200, "payload": before}]},
                   "after": {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "status": 200, "payload": brief},
                                              {"method": "GET", "path": "/api/brief/shelf", "status": 200, "payload": after}]}}
    else:
        created, before_saved, after_saved = _decision(Path(tempfile.mkdtemp()) / "refusal.db", title="Keep it")
        durable = {"decisions": [copy.deepcopy(after_saved)]}
        op_trigger = {"kind": "op", "name": "decision.create", "refusal": {"error": op_text},
                      "envelope": {"result": {"isError": True}}}
        browser_trigger = {"kind": "api", "method": "POST", "path": "/api/decisions", "status": 400,
                           "response": {"error": browser_text}}
        op = {"run_id": "op", "duration_s": 0.1, "provenance": {"engine_mode": "none"},
              "setup": [{"kind": "op", "name": "decision.create", "domain_response": created},
                        {"kind": "op", "name": "decision.update", "domain_response": after_saved}],
              "trigger": op_trigger,
              "before": {"op_reads": [{"kind": "op", "name": "decision.read", "domain_response": before_saved},
                                        {"kind": "op", "name": "decision.list", "domain_response": copy.deepcopy(durable)}]},
              "after": {"op_reads": [{"kind": "op", "name": "decision.read", "domain_response": after_saved},
                                       {"kind": "op", "name": "decision.list", "domain_response": copy.deepcopy(durable)}]}}
        browser = {"run_id": "browser", "viewport": 1440, "verdict": "pass", "provenance": {"engine_mode": "none"},
                   "setup": [{"kind": "api", "method": "POST", "path": "/api/decisions", "status": 201,
                              "response": {"decision": copy.deepcopy(created)}}],
                   "trigger": browser_trigger,
                   "before": {"api_reads": [{"method": "GET", "path": f"/api/decisions/{before_saved['id']}", "status": 200, "payload": {"decision": copy.deepcopy(before_saved)}},
                                               {"method": "GET", "path": "/api/decisions", "status": 200, "payload": copy.deepcopy(durable)}]},
                   "after": {"api_reads": [{"method": "GET", "path": f"/api/decisions/{after_saved['id']}", "status": 200, "payload": {"decision": copy.deepcopy(after_saved)}},
                                              {"method": "GET", "path": "/api/decisions", "status": 200, "payload": copy.deepcopy(durable)}]}}
    return {"pair_id": family, "op": {"observation": op}, "browser": {"observation": browser}}


def test_refusal_reads_original_trigger_and_requires_unchanged_durable_read() -> None:
    result = compare_pair(_refusal_pair(op_text="invalid decision status: bogus", browser_text="invalid decision status"))
    assert result["verdict"] == "pass", result["checks"]
    changed = _refusal_pair(op_text="invalid decision status: bogus", browser_text="invalid decision status")
    changed["browser"]["observation"]["after"]["api_reads"][1]["payload"]["decisions"][0]["title"] = "changed"
    assert compare_pair(changed)["verdict"] == "fail"


def test_shelf_refusal_retains_transport_origins_and_old_shelf() -> None:
    result = compare_pair(_refusal_pair(op_text="Invalid arguments: state shelved is not enum", browser_text="Unknown shelf state: shelved", shelf=True))
    assert result["verdict"] == "pass", result["checks"]
    checks = {row["name"]: row for row in result["checks"]}
    assert checks["op.refusal_origin"]["refusal_origin"] == "transport_schema"
    assert checks["op.registry_reached"]["registry_reached"] is False
    missing = _refusal_pair(op_text="Invalid arguments: state shelved is not enum", browser_text="Unknown shelf state: shelved", shelf=True)
    missing["op"]["observation"]["before"]["op_reads"] = [row for row in missing["op"]["observation"]["before"]["op_reads"] if row.get("name") != "brief.latest"]
    missing["browser"]["observation"]["after"]["api_reads"] = [row for row in missing["browser"]["observation"]["after"]["api_reads"] if row.get("path") != "/api/brief/latest"]
    missing_result = compare_pair(missing)
    assert missing_result["verdict"] == "blocked"
    assert any(row["name"] == "durable_unchanged" and row["status"] == "blocked" for row in missing_result["checks"])


def test_missing_restart_flags_block_even_when_meeting_reads_match() -> None:
    meeting = {"id": "m", "title": "Meeting", "transcription_status": "complete", "duration": 3,
               "segments": [{"start_time": 0, "end_time": 3}], "intel": {"summary": "kept"},
               "intel_status": {"state": "ready"}, "run_receipt": {"meeting_id": "m", "job_id": "j",
               "outcome": "succeeded", "attempts": [{"host": "192.168.1.43"}]}}
    def obs(mode: str) -> dict[str, Any]:
        return {"run_id": mode, "duration_s": 1, "viewport": 1440, "provenance": {"engine_mode": mode},
                "after": {"op_reads": [{"kind": "op", "name": "meeting.read", "domain_response": meeting}],
                          "api_reads": [{"method": "GET", "path": "/api/meetings/m", "payload": meeting}]},
                "restart": {"meeting_before": {"meeting_id": "m"}, "meeting_after": {"meeting_id": "m"}}}
    result = compare_pair({"pair_id": "case.closure.chain.s3_same_summary_after_restart",
                           "op": {"observation": obs("none")}, "browser": {"observation": obs("none")}})
    assert result["verdict"] in {"blocked", "fail"}
    assert any(row["name"] == "restart.op.summary_retained" and row["status"] == "blocked" for row in result["checks"])


def test_summary_receipt_wrong_lan_host_is_blocked() -> None:
    meeting = {"id": "m", "title": "Meeting", "transcription_status": "complete", "duration": 3,
               "segments": [{"start_time": 0, "end_time": 3}], "intel": {"summary": "kept"},
               "intel_status": {"state": "ready"}, "run_receipt": {"meeting_id": "m", "job_id": "j",
               "outcome": "succeeded", "attempts": [{"host": "10.0.0.4"}]}}
    def obs(browser: bool) -> dict[str, Any]:
        if browser:
            return {"run_id": "b", "viewport": 1440,
                    "provenance": {"engine_mode": "none"},
                    "after": {"api_reads": [{"method": "GET", "path": "/api/meetings/m", "payload": meeting}]}}
        return {"run_id": "o", "duration_s": 1, "provenance": {"engine_mode": "none"},
                "after": {"op_reads": [{"kind": "op", "name": "meeting.read", "domain_response": meeting}]}}
    result = compare_pair({"pair_id": "case.closure.chain.s2_summary_with_host",
                           "op": {"observation": obs(False)}, "browser": {"observation": obs(True)}})
    assert result["verdict"] == "blocked"
    assert any(row["name"] == "browser.receipt_lan_identity" and row["status"] == "blocked" for row in result["checks"])


def _brief_obs(*, first: str, final: str, decision_id: str, mode: str = "none", source_ref: str | None = None,
               browser: bool = False) -> dict[str, Any]:
    first_payload = {"id": first, "headline": "Brief", "generated_at": "2026-09-24T22:00:00Z",
                     "sections": {"decisions": []}}
    decision = {"id": decision_id, "title": "Keep it", "status": "proposed",
                "decision_markdown": "retain the durable body", "context_markdown": "real producer context",
                "created_at": "2026-09-24T22:00:00Z"}
    item = {"id": "item-final", "text": "Review decision: Keep it", "source_ref": source_ref or f"decision:{decision_id}",
            "created_at": decision["created_at"]}
    final_payload = {"id": final, "headline": "Brief", "generated_at": "2026-09-24T22:00:00Z",
                     "sections": {"decisions": [item]}}
    if browser:
        return {"run_id": "browser", "viewport": 1440, "verdict": "pass", "provenance": {"engine_mode": mode},
                "variables": {"first_brief_id": first, "decision_id": decision_id},
                "setup": [{"kind": "api", "method": "POST", "path": "/api/brief/generate", "response": first_payload},
                          {"kind": "api", "method": "POST", "path": "/api/decisions", "response": {"decision": decision}}],
                "after": {"api_reads": [{"method": "GET", "path": f"/api/decisions/{decision_id}", "payload": {"decision": decision}},
                                            {"method": "GET", "path": "/api/brief/latest", "payload": final_payload}]}}
    return {"run_id": "op", "duration_s": 1, "provenance": {"engine_mode": mode},
            "variables": {"first_brief_id": first, "decision_id": decision_id},
            "setup": [{"kind": "op", "name": "brief.generate", "domain_response": first_payload},
                      {"kind": "op", "name": "decision.create", "domain_response": decision}],
            "after": {"op_reads": [{"kind": "op", "name": "decision.read", "domain_response": decision},
                                     {"kind": "op", "name": "brief.latest", "domain_response": final_payload}]}}


def test_next_day_requires_distinct_briefs_and_decision_source_ref() -> None:
    pair = {"pair_id": "case.a3.brief_next_day.new_id_with_the_decision",
            "op": {"observation": _brief_obs(first="brief-1", final="brief-2", decision_id="decision-1")},
            "browser": {"observation": _brief_obs(first="brief-a", final="brief-b", decision_id="decision-a", browser=True)}}
    assert compare_pair(pair)["verdict"] == "pass"
    pair["browser"]["observation"]["after"]["api_reads"][1]["payload"]["sections"]["decisions"][0]["source_ref"] = "decision:other"
    assert compare_pair(pair)["verdict"] == "blocked"


def test_same_day_needs_two_generate_read_stages() -> None:
    op = _brief_obs(first="brief-1", final="brief-1", decision_id="decision-1")
    browser = _brief_obs(first="brief-a", final="brief-a", decision_id="decision-a", browser=True)
    # Same-day idempotence has a durable read before the second generate and
    # a durable read after it. Keep the generated payload unchanged in this
    # producer/read chain so the content and generated_at fences are real.
    op_first = copy.deepcopy(op["setup"][0]["domain_response"])
    op["before"] = {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": copy.deepcopy(op_first)}]}
    op["after"]["op_reads"][1]["domain_response"] = copy.deepcopy(op_first)
    browser_first = copy.deepcopy(browser["setup"][0]["response"])
    browser["before"] = {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "payload": copy.deepcopy(browser_first)}]}
    browser["after"]["api_reads"][1]["payload"] = copy.deepcopy(browser_first)
    result = compare_pair({"pair_id": "case.j10.route_generate_again.same_day_same_id",
                           "op": {"observation": op}, "browser": {"observation": browser}})
    assert result["verdict"] == "pass"
    op["setup"] = []
    assert compare_pair({"pair_id": "case.j10.route_generate_again.same_day_same_id",
                         "op": {"observation": op}, "browser": {"observation": browser}})["verdict"] == "blocked"


def test_shelf_item_must_belong_to_final_brief() -> None:
    brief = {"id": "brief", "sections": {"decisions": [{"id": "item-valid", "title": "A"}, {"id": "item-two", "title": "B"}]}}
    shelf = {"brief_id": "brief", "shelf": {"item-outside": "acknowledged"}}
    def run(browser: bool) -> dict[str, Any]:
        if browser:
            return {"run_id": "b", "viewport": 393, "provenance": {"engine_mode": "none"},
                    "after": {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "payload": brief},
                                                {"method": "GET", "path": "/api/brief/shelf", "payload": shelf}]}}
        return {"run_id": "o", "duration_s": 1, "provenance": {"engine_mode": "none"},
                "after": {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": brief},
                                         {"kind": "op", "name": "brief.shelf.read", "domain_response": shelf}]}}
    result = compare_pair({"pair_id": "case.j10.brief_item_shelf.acknowledged",
                           "op": {"observation": run(False)}, "browser": {"observation": run(True)}})
    assert result["verdict"] in {"blocked", "fail"}


def test_shelf_id_must_belong_to_final_brief() -> None:
    brief = {"id": "brief", "sections": {"decisions": [{"id": "item-valid", "title": "A"}]}}
    shelf = {"brief_id": "old-brief", "shelf": {"item-valid": "acknowledged"}}
    def run(browser: bool) -> dict[str, Any]:
        if browser:
            return {"run_id": "b", "viewport": 393, "provenance": {"engine_mode": "none"},
                    "after": {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "payload": brief},
                                                {"method": "GET", "path": "/api/brief/shelf", "payload": shelf}]}}
        return {"run_id": "o", "duration_s": 1, "provenance": {"engine_mode": "none"},
                "after": {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": brief},
                                         {"kind": "op", "name": "brief.shelf.read", "domain_response": shelf}]}}
    result = compare_pair({"pair_id": "case.j10.brief_item_shelf.acknowledged",
                           "op": {"observation": run(False)}, "browser": {"observation": run(True)}})
    assert result["verdict"] == "fail"


def test_all_two_handled_requires_ack_and_defer_labels() -> None:
    brief = {"id": "brief", "sections": {"decisions": [
        {"id": "item-ack", "text": "Graph walk triage headline Ack"},
        {"id": "item-defer", "text": "Graph walk triage headline Defer"},
    ], "raw": [{"id": "raw-item", "text": "hidden raw"}],
    "hidden": [{"id": "hidden-item", "text": "Ack"}], "this_week": [{"id": "week-item", "text": "Defer"}]}}
    shelf = {"brief_id": "brief", "shelf": {"item-ack": "acknowledged", "item-defer": "deferred"}}
    def run(browser: bool) -> dict[str, Any]:
        if browser:
            return {"run_id": "b", "viewport": 393, "provenance": {"engine_mode": "none"},
                    "after": {"api_reads": [{"method": "GET", "path": "/api/brief/latest", "payload": brief},
                                                {"method": "GET", "path": "/api/brief/shelf", "payload": shelf}]}}
        return {"run_id": "o", "duration_s": 1, "provenance": {"engine_mode": "none"},
                "after": {"op_reads": [{"kind": "op", "name": "brief.latest", "domain_response": brief},
                                         {"kind": "op", "name": "brief.shelf.read", "domain_response": shelf}]}}
    result = compare_pair({"pair_id": "case.philo404.arrival_triaged_headline.all_handled",
                           "op": {"observation": run(False)}, "browser": {"observation": run(True)}})
    assert result["verdict"] == "pass", result["checks"]
    bad = copy.deepcopy(shelf)
    bad["shelf"]["item-defer"] = "acknowledged"
    bad_op = run(False)
    bad_op["after"]["op_reads"][1]["domain_response"] = bad
    bad_result = compare_pair({"pair_id": "case.philo404.arrival_triaged_headline.all_handled",
                               "op": {"observation": bad_op}, "browser": {"observation": run(True)}})
    assert bad_result["verdict"] == "fail"


def test_breakage_source_failure_gets_a_new_brief_scoped_item_id() -> None:
    old_db = {"brief": {"id": "old-brief"},
              "items": [{"id": "old-break", "brief_id": "old-brief", "source_ref": "pipeline-event:failure-1"}],
              "shelf": [{"item_id": "old-break", "brief_id": "old-brief", "state": "acknowledged"}]}
    decision = {"id": "decision-1", "title": "Breakage decision", "status": "proposed",
                "decision_markdown": "retain the old failure", "context_markdown": "real producer context",
                "created_at": "2026-09-24T22:00:00Z"}
    final = {"id": "new-brief", "shelf": {}, "sections": {"decisions": [{"id": "decision-item", "text": "Review decision", "source_ref": "decision:decision-1",
                                                                  "created_at": decision["created_at"]}],
                                                      "broke": [{"id": "brief-break-pipeline-new-brief-failure-1", "brief_id": "new-brief", "text": "same failure",
                                                                 "detail": "not_found: missing source", "source_ref": "pipeline-event:failure-1"}]}}
    def run(browser: bool) -> dict[str, Any]:
        restart = {"action": "restart_hub", "meeting_before": {"meeting_id": "m"}, "meeting_after": {"meeting_id": "m"},
                   "summary_retained": True, "receipt_retained": True, "meeting_identity_retained": True}
        if browser:
            return {"run_id": "b", "viewport": 1440,
                    "provenance": {"engine_mode": "none", "clock": {"tz": "UTC", "producer_clock_reads": ["advance_days=0 now=2026-09-24T17:00:00"]}},
                    "variables": {"first_brief_id": "old-brief"}, "restart": restart,
                    "before": {"brief_db": copy.deepcopy(old_db)},
                        "setup": [{"kind": "api", "method": "POST", "path": "/api/decisions", "status": 201,
                                    "response": {"decision": decision}}],
                        "after": {"brief_db": copy.deepcopy(old_db),
                            "api_reads": [{"method": "GET", "path": f"/api/decisions/{decision['id']}", "status": 200,
                                           "payload": {"decision": decision}},
                                           {"method": "GET", "path": "/api/brief/latest", "payload": copy.deepcopy(final)}]}}
        return {"run_id": "o", "duration_s": 1,
                "provenance": {"engine_mode": "none", "clock": {"tz": "UTC", "producer_clock_reads": ["advance_days=0 now=2026-09-24T17:00:00"]}},
                "variables": {"first_brief_id": "old-brief"}, "restart": restart,
                "before": {"brief_db": copy.deepcopy(old_db)}, "after": {"brief_db": copy.deepcopy(old_db),
                    "op_reads": [{"kind": "op", "name": "decision.read", "domain_response": decision},
                                      {"kind": "op", "name": "brief.latest", "domain_response": copy.deepcopy(final)}]},
                "setup": [{"kind": "op", "name": "decision.create", "domain_response": decision}]}
    pair = {"pair_id": "case.closure.chain.s5_next_day_brief_with_breakage",
            "op": {"observation": run(False)}, "browser": {"observation": run(True)}}
    assert compare_pair(pair)["verdict"] == "pass"
    pair["browser"]["observation"]["after"]["api_reads"][1]["payload"]["sections"]["broke"][0]["id"] = "old-break"
    assert compare_pair(pair)["verdict"] in {"blocked", "fail"}
    rows_changed = copy.deepcopy(pair)
    rows_changed["browser"]["observation"]["after"]["api_reads"][1]["payload"]["sections"]["broke"][0]["id"] = "brief-break-pipeline-new-brief-failure-1"
    rows_changed["browser"]["observation"]["after"]["api_reads"][1]["payload"]["sections"]["broke"][0]["detail"] = "not_found: another source"
    row_result = compare_pair(rows_changed)
    assert row_result["verdict"] == "fail"
    assert any(row["name"] == "next_day.breakage_causes" and row["status"] == "fail" for row in row_result["checks"])


def test_thought_save_requires_increased_revisions_body_and_cursor() -> None:
    def thought(revision: int, body: str, stamp: str) -> dict[str, Any]:
        return {"thought": {"id": "thought-1", "working_revision": revision, "aggregate_revision": revision,
                             "raw_id": "raw-1", "raw_sha256": "raw-hash-1",
                             "working_note": {"id": "note-1", "body_markdown": body, "last_modified": stamp}},
                "workbench": {"workspace_cursor": {"thought_id": "thought-1", "aggregate_revision": revision}}}
    def run(browser: bool) -> dict[str, Any]:
        before, after = thought(1, "before", "2026-01-01T00:00:00Z"), thought(2, "saved", "2026-01-01T00:00:01Z")
        if browser:
            reads = [{"method": "GET", "path": "/api/thoughts/thought-1", "payload": before},
                     {"method": "GET", "path": "/api/thoughts/thought-1/workbench", "payload": before}]
            final = [{"method": "GET", "path": "/api/thoughts/thought-1", "payload": after},
                     {"method": "GET", "path": "/api/thoughts/thought-1/workbench", "payload": after}]
            return {"run_id": "b", "viewport": 1440, "provenance": {"engine_mode": "none"},
                    "setup": [{"kind": "api", "method": "POST", "path": "/api/thoughts", "response": before},
                              {"kind": "api", "method": "PATCH", "path": "/api/thoughts/thought-1/working", "response": after}],
                    "before": {"api_reads": reads}, "after": {"api_reads": final}}
        return {"run_id": "o", "duration_s": 1, "provenance": {"engine_mode": "none"},
                "setup": [{"kind": "op", "name": "thought.create", "domain_response": before},
                          {"kind": "op", "name": "thought.read", "domain_response": before},
                          {"kind": "op", "name": "thought.save", "domain_response": after}],
                "before": {"op_reads": [{"kind": "op", "name": "thought.read", "domain_response": before}]},
                "after": {"op_reads": [{"kind": "op", "name": "thought.read", "domain_response": after},
                                         {"kind": "op", "name": "thought.workbench.read", "domain_response": after}]}}
    result = compare_pair({"pair_id": "case.j11.thought_keep.receipt_time",
                           "op": {"observation": run(False)}, "browser": {"observation": run(True)}})
    assert result["verdict"] == "pass", result["checks"]
    bad = run(False)
    bad["after"]["op_reads"][0]["domain_response"]["thought"]["working_revision"] = 1
    bad_result = compare_pair({"pair_id": "case.j11.thought_keep.receipt_time",
                               "op": {"observation": bad}, "browser": {"observation": run(True)}})
    assert bad_result["verdict"] == "fail"


def test_real_replayed_mix_is_blocked_and_face_verdict_stays_independent(tmp_path: Path) -> None:
    oc, ob, oa = _decision(tmp_path / "o.db")
    bc, bb, ba = _decision(tmp_path / "b.db")
    browser = _browser_decision(bc, bb, ba, mode="real")
    browser["verdict"] = "fail"
    browser["face_verdict"] = "fail"
    result = compare_pair(_pair(_op_decision(oc, ob, oa, mode="replayed"), browser))
    assert result["verdict"] == "blocked"
    assert result["face_verdict"] == "fail"


def test_build_pairs_uses_actual_paths_and_cli_shape(tmp_path: Path) -> None:
    oc, ob, oa = _decision(tmp_path / "o.db")
    bc, bb, ba = _decision(tmp_path / "b.db")
    op_path, browser_path = tmp_path / "op.json", tmp_path / "browser.json"
    op_path.write_text(__import__("json").dumps(_op_decision(oc, ob, oa)), encoding="utf-8")
    browser_path.write_text(__import__("json").dumps(_browser_decision(bc, bb, ba)), encoding="utf-8")
    output = tmp_path / "pairs.json"
    index = build_pairs({"pairs": [{"pair_id": "case.closure.chain.s4_decision_recorded",
                                     "op": str(op_path), "browser": str(browser_path)}]}, output=output)
    assert index["counts"]["pass"] == 1
    assert output.exists()
