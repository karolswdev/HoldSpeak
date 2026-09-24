"""Check retained PHILO-4-02 observations without changing the observations."""
import datetime as dt
import json
from pathlib import Path
import sys


def read(snapshot, path):
    row = next(row for row in snapshot["api_reads"] if row["path"] == path)
    assert row["status"] == 200, row
    return row["payload"]


def verify(path):
    record = json.loads(Path(path).read_text())
    assert record["case_id"] in (
        "case.closure.chain.s5_next_day_brief_has_it",
        "case.closure.chain.s5_next_day_brief_with_breakage",
    )
    assert record["verdict"] == "pass" and record["complete"], record["notes"]
    before, after = record["before"], record["after"]
    assert after["observe_at"] == "[data-testid=arrival-brief-row]"
    assert after["target_present"] and after["visible"]
    hit = after["hit_test"]
    assert hit["in_viewport"] and hit["all_owned"]
    assert len(hit["samples"]) == 9 and all(p["owned"] for p in hit["samples"])
    assert hit["rect"]["w"] > 0 and hit["rect"]["h"] > 0
    clearance = after.get("arrival_clearance")
    if record["viewport"] == 393:
        assert clearance, "retain the measured capture bar and CSS clearance"
        bar_height = clearance["capture_bar"]["h"]
        assert float(clearance["scroll_padding_bottom"].removesuffix("px")) >= bar_height
        assert float(clearance["end_margin_bottom"].removesuffix("px")) >= bar_height
    first = read(before, "/api/brief/latest")
    second = read(after, "/api/brief/latest")
    assert first["id"] == record["variables"]["first_brief_id"]
    assert first["id"] != second["id"]
    assert dt.datetime.fromisoformat(second["generated_at"]).date() == (
        dt.datetime.fromisoformat(first["generated_at"]).date() + dt.timedelta(days=1)
    )
    assert first["shelf"] == {} and sum(map(len, first["sections"].values())) > 0
    assert before["brief_db"] == after["brief_db"], "day-one durable rows changed"
    assert before["brief_db"]["brief"]["id"] == first["id"]
    assert before["brief_db"]["items"] and before["brief_db"]["shelf"] == []
    answer = after["trigger_response"]
    assert (answer["method"], answer["path"], answer["status"]) == (
        "POST", "/api/brief/generate", 200
    )
    assert answer["body"]["id"] == second["id"]
    decision = read(after, f"/api/decisions/{record['variables']['decision_id']}")["decision"]
    first_row = second["sections"]["decisions"][0]
    assert first_row["source_ref"] == f"decision:{decision['id']}"
    assert first_row["created_at"] == decision["created_at"]
    assert first_row["text"] == "Review decision: Keep summary retrieval on the local desk"
    assert first_row["text"] in after["text"]
    provenance = record["provenance"]
    assert provenance["engine_mode"] == "real"
    assert Path(provenance["db_path"]).resolve().is_relative_to(
        Path(provenance["hub"]["home"]).resolve()
    )
    restarts = provenance["restarts"]
    assert len(restarts) == 1
    for key in ("same_db_path", "summary_retained", "receipt_retained", "meeting_identity_retained"):
        assert restarts[0][key] is True, key
    meeting = read(after, f"/api/meetings/{record['variables']['meeting_id']}")
    assert meeting["intel"]["summary"] == record["variables"]["persisted_summary"]
    assert meeting["run_receipt"]["attempts"][0]["host"] == "192.168.1.43"
    breakage = None
    if record["case_id"].endswith("with_breakage"):
        assert provenance["clock"]["tz"].startswith("Etc/GMT")
        assert dt.datetime.fromisoformat(first["generated_at"]).hour >= 17
        failed = next(step for step in record["setup"] if step.get("path") ==
                      "/api/decisions/philo402-deliberately-absent")
        assert failed["status"] == 404 and failed["method"] == "GET"
        old = first["sections"]["broke"]
        new = second["sections"]["broke"]
        assert len(old) == len(new) == 1, (old, new)
        assert old[0]["text"] == new[0]["text"] == "DecisionLifecycleService.get_decision failed"
        assert old[0]["source_ref"] == new[0]["source_ref"]
        assert old[0]["source_ref"].startswith("pipeline-event:")
        assert old[0]["id"] != new[0]["id"]
        assert first["id"] in old[0]["id"] and second["id"] in new[0]["id"]
        breakage = {"source_ref": old[0]["source_ref"], "day_one_id": old[0]["id"],
                    "day_two_id": new[0]["id"], "process_timezone": provenance["clock"]["tz"]}
    return {
        "run_id": record["run_id"], "viewport": record["viewport"], "verdict": "PASS",
        "first_brief": {"id": first["id"], "generated_at": first["generated_at"],
                        "items": len(before["brief_db"]["items"]), "shelf": first["shelf"]},
        "new_brief": {"id": second["id"], "generated_at": second["generated_at"]},
        "decision": {"position": 1, "text": first_row["text"],
                     "created_at": first_row["created_at"], "rect": hit["rect"],
                     "in_viewport": hit["in_viewport"], "all_owned": hit["all_owned"]},
        "old_brief_rows_and_triage_unchanged": True,
        "summary_receipt_and_identity_retained_after_restart": True,
        "breakage_rows": len(second["sections"]["broke"]),
        "breakage_proof": breakage,
        "arrival_clearance": clearance,
        "initial_feedback_s": record["initial_feedback"]["elapsed_s"],
        "terminal_reading": record["terminal_outcome"]["reading"],
    }


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Pass retained observation.json paths"
    print(json.dumps([verify(path) for path in sys.argv[1:]], indent=2))
