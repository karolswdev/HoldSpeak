"""Read PHILO-4-04 rig observations; never change the retained observations."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ARRIVAL = ("decisions", "changed", "broke", "waiting")


def latest(snapshot):
    read = next(row for row in snapshot["api_reads"] if row["path"] == "/api/brief/latest")
    assert read["status"] == 200, read
    return read["payload"]


def verify(path):
    record = json.loads(Path(path).read_text())
    assert record["verdict"] == "pass" and record["complete"], record.get("notes")
    assert record["viewport"] in (1440, 393)
    before, after = record["before"], record["after"]
    saved, handled = latest(before), latest(after)
    assert saved["id"] == handled["id"] == record["variables"]["first_brief_id"]
    assert saved["headline"] == handled["headline"] == record["variables"]["first_headline"]
    assert saved["sections"] == handled["sections"], "historical item fields changed"
    assert saved["generated_at"] == handled["generated_at"]
    items = [item for section in ARRIVAL for item in handled["sections"].get(section, [])]
    assert items and not handled["is_empty"]
    states = {item["id"]: handled["shelf"].get(item["id"]) for item in items}
    assert all(state in ("acknowledged", "deferred") for state in states.values()), states
    assert set(states.values()) == {"acknowledged", "deferred"}, states
    assert f"ALL {len(items)} HANDLED" in after["text"]
    assert after["target_present"] and after["visible"]
    hit = after["hit_test"]
    assert hit["in_viewport"] and hit["all_owned"]
    assert len(hit["samples"]) == 9 and all(p["owned"] for p in hit["samples"])
    assert hit["rect"]["w"] > 0 and hit["rect"]["h"] > 0
    assert before["brief_db"]["brief"] == after["brief_db"]["brief"]
    assert before["brief_db"]["items"] == after["brief_db"]["items"]
    db_shelf = {row["item_id"]: row["state"] for row in after["brief_db"]["shelf"]}
    assert all(db_shelf[item_id] == state for item_id, state in states.items())
    provenance = record["provenance"]
    assert Path(provenance["db_path"]).resolve().is_relative_to(
        Path(provenance["hub"]["home"]).resolve()
    ), "walk database escaped its isolated HOME"
    answer = after["trigger_response"]
    assert answer["method"] == "POST" and answer["path"].endswith("/shelf")
    assert answer["status"] == 200
    body = answer["body"]
    assert body["state"] == "deferred" and states[body["item_id"]] == "deferred"
    assert answer["path"] == f"/api/brief/items/{body['item_id']}/shelf"
    assert body["item_id"] not in saved["shelf"]
    assert len(saved["shelf"]) == len(items) - 1
    assert not before["target_present"], "the line appeared before all rows were handled"
    return {
        "run_id": record["run_id"], "case_id": record["case_id"],
        "viewport": record["viewport"], "verdict": "PASS",
        "revision": provenance["revision"], "dirty": provenance["dirty"],
        "brief_id": handled["id"], "headline": handled["headline"],
        "arrival_rows": len(items), "handled_states": states,
        "headline_and_stored_items_unchanged": True,
        "stored_shelf_matches_face": True, "isolated_db": provenance["db_path"],
        "handled_line_geometry": hit["rect"], "all_nine_hit_points_owned": True,
        "initial_feedback": {key: record["initial_feedback"].get(key) for key in
                             ("elapsed_s", "text", "predicate_satisfied", "reading")},
        "terminal_outcome": record["terminal_outcome"],
    }


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Pass the retained observation.json paths"
    print(json.dumps([verify(path) for path in sys.argv[1:]], indent=2))
