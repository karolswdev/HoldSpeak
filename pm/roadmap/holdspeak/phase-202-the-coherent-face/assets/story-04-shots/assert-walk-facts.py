import json, sys
from pathlib import Path
p = str(Path(__file__).resolve().parent / "walk-facts.json")
d = json.load(open(p))
ok = True
for w in ("1440", "393"):
    live = d["live"][w]
    print(w, "live sections", live["section_labels"], "door", live["door_labels"])
    print(w, "live facts", repr(live["facts_line"]), "receipt", repr(live["footer_receipt"]), "SEG?", live["body_has_SEG"])
    ok &= "SUMMARY" in live["section_labels"] and "SUMMARY" in live["door_labels"]
    ok &= "INTELLIGENCE" not in live["section_labels"] + live["door_labels"]
    ok &= not live["body_has_SEG"] and live["facts_line"] == "Link · connected"
    ok &= live["footer_receipt"] in ("REC 00:00", "READY")
    me = d["meetings_empty"][w]
    print(w, "meetings headline", repr(me["headline"]), "empty", me["empty_lines"], "said-twice", me["no_meetings_yet_count"])
    ok &= me["no_meetings_yet_count"] == 1 and me["empty_lines"] == ["○ Record or import a meeting"]
    sh = d["settings_hub"][w]
    print(w, "settings chips", sh["chips"], "INTELLIGENCE?", sh["body_has_INTELLIGENCE"], "first row", sh["meetings_module_rows"][0])
    ok &= not sh["body_has_INTELLIGENCE"] and sh["meetings_module_rows"][0] == "Summary"
    print(w, "ask head", repr(d["ask"][w]["session_head"]))
    ok &= d["ask"][w]["session_head"] == "SESSION"
    sd = d["speak_door"][w]
    print(w, "speak runs row?", sd["has_runs_row"], "RAW READINESS?", sd["has_raw_readiness"], "Wire details?", sd["has_wire_details"])
    ok &= not sd["has_runs_row"] and sd["has_raw_readiness"] and not sd["has_wire_details"]
    sq = d["sequence"][w]
    print(w, "Edit Sequence?", sq["has_edit_sequence"], "Edit chain?", sq["has_edit_chain"])
    ok &= sq["has_edit_sequence"] and not sq["has_edit_chain"]
    fz = d["floor_zone"][w]
    print(w, "list face opened?", d["list_view_opened"][w], "door used", d.get("menu_door_used", {}).get(w))
    print(w, "zone names", fz["zone_aria_names"])
    print(w, "zero names", fz["zero_item_names"], "zero cells", fz["zero_item_cells"], "EMPTY cells", fz["empty_cells"])
    # Astra's condition 4: the list face is OBSERVED at both widths now.
    ok &= d["list_view_opened"][w] is True
    ok &= fz["zero_item_names"] == [] and fz["zero_item_cells"] == []
    ok &= len(fz["empty_cells"]) == 2
print("page_errors", d.get("page_errors"), "console_errors", d.get("console_errors"),
      "bad_responses", d.get("bad_responses"), "step_errors", d.get("step_errors"))
ok &= not d.get("page_errors") and not d.get("console_errors") and not d.get("bad_responses") and not d.get("step_errors")
print("VERDICT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
