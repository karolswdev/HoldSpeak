import json, pathlib, collections, hashlib
root = pathlib.Path.cwd()
x = json.loads((root / "docs/internal/philo/phase-3/summary/observations-index.json").read_text())
assert x["run_count"] == 60 and len(x["latest_complete_final"]) == 40
assert not x["errors"] and not x["missing_case_widths"]
counts = collections.Counter(i["run"]["verdict"] for i in x["latest_complete_final"])
assert counts == {"pass": 30, "blocked": 10}, counts
for r in x["runs"]:
    assert (root / r["observation_path"]).is_file()
    for shot in r["shots"]:
        assert (root / shot).stat().st_size > 0, shot
for i in x["latest_complete_final"]:
    if i["case_id"] == "case.j7.hub_restart.intel_retained":
        o = json.loads((root / i["run"]["observation_path"]).read_text())
        r = o["provenance"]["restarts"][0]
        assert r["stopped_pid"] != r["started_pid"]
        assert all(r[k] for k in ("same_db_path", "summary_retained", "receipt_retained", "meeting_identity_retained"))
    if i["case_id"] == "case.j6.run_summary.summary_text":
        o = json.loads((root / i["run"]["observation_path"]).read_text())
        assert o["provenance"]["engine_identity"]["expected_model_seen"]
        assert o["provenance"]["frontend_build"]["index_sha256"] == "3d79edd5157680ad696e3c312393b9e83feebf375da5e85181ac53c3d85496a6"
        assert o["after"]["hit_test"]["all_owned"]
        print(i["case_id"], i["viewport"], o["terminal_outcome"]["first_satisfied_at_s"], "seconds; real engine; raw summary visible")
assert hashlib.sha256((root/"tests/fixtures/philo3_architect_meeting.wav").read_bytes()).hexdigest() == "165ea9755d028ff3dc2b9fa85dd4c48f4db3220855906e0ffeed4a35919d47b2"
print("60 retained observations; 40 actual case-width pairs; 30 pass; 10 blocked; no missing pairs; all linked shots present")
print("Both restart identity records verified; synthetic WAV hash verified. Technical completion is separate from partial usefulness.")
