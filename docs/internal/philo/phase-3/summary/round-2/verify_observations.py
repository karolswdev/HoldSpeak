"""Audit the six retained round-two rig observations; no hub or owner data."""
import hashlib
import json
from pathlib import Path

root = Path.cwd()
proof = root / "docs/internal/philo/phase-3/summary/round-2"
shots = root / "pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2"
paths = sorted(shots.glob("*/observation.json"))
expected = {(f"case.j6.run_summary.{case}", width) for case in ("intel_failed", "retrying", "summary_text") for width in (1440, 393)}
seen = set()
rows = []
for path in paths:
    data = json.loads(path.read_text())
    pair = (data["case_id"], data["viewport"])
    assert pair in expected and pair not in seen, pair
    seen.add(pair)
    assert data["complete"] and data["verdict"] == "pass", path
    assert not data["console_errors"], path
    provenance = data["provenance"]
    assert provenance["frontend_build"]["index_sha256"] == "812d35c43631f655e5441c9087786e3d03ef477cd0557561b65850fe8171ce05"
    assert "graph-walk-home-" in provenance["hub"]["home"]
    assert "graph-walk-home-" in provenance["db_path"]
    fixture = next(step for step in data["setup"] if step["kind"] == "fixture")
    assert fixture["completion_wait"]["matched"]
    assert all(fixture["completion_wait"]["field_matches"].values())
    assert data["before"]["windows"] == [], path
    assert data["trigger"]["selector"] == "[data-testid=arrival-run-intel]"
    assert data["trigger"]["done"]
    assert not any(step.get("selector") == "[data-testid=arrival-run-intel]" and step.get("action") == "click" for step in data["setup"])
    after = data["after"]
    assert after["hit_test"]["all_owned"], path
    meeting = next(read["payload"] for read in after["api_reads"] if read["path"].startswith("/api/meetings/"))
    assert meeting["id"] == data["variables"]["meeting_id"]
    assert meeting["intel_model_host"] == "192.168.1.43"
    assert meeting["run_receipt"]["meeting_id"] == meeting["id"]
    assert data["terminal_outcome"]["within_bound"]
    counts = None
    if pair[0].endswith("summary_text"):
        assert provenance["engine_mode"] == "real"
        assert not provenance["boundary_substitutions"]
        identity = provenance["engine_identity"]
        assert identity["expected_model_seen"] and identity["status"] == 200
        assert identity["models"] == [{"id": "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf", "owned_by": "llamacpp"}]
        assert meeting["intel"]["summary"].strip()
    else:
        state = "FAILED" if pair[0].endswith("intel_failed") else "RETRYING"
        assert provenance["engine_mode"] == "replayed"
        assert after["text"] == f"{state}\nLAST ATTEMPT · 192.168.1.43 · LAN\nLAST ERROR · PROVIDER FAILED"
        assert meeting["intel_job"]["last_error"] == "PROVIDER FAILED"
        counts = next(read["payload"] for read in after["api_reads"] if read["path"] == "/api/intel/summary")
        assert counts["running_jobs"] == 0
        assert counts["queued_jobs"] == (0 if state == "FAILED" else 1)
        assert counts["failed_jobs"] == (1 if state == "FAILED" else 0)
        assert counts["scheduled_retry_jobs"] == (0 if state == "FAILED" else 1)
    artifacts = []
    for artifact in [path, *(root / shot for shot in data["shots"])]:
        assert artifact.stat().st_size > 0, artifact
        artifacts.append({"path": str(artifact.relative_to(root)), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()})
    rows.append({"case": pair[0], "width": pair[1], "run": data["run_id"], "meeting_id": meeting["id"], "words": meeting["transcriptWords"], "first_satisfied_s": data["terminal_outcome"]["first_satisfied_at_s"], "queue_counts": counts, "artifacts": artifacts})
    print(pair, "pass", meeting["transcriptWords"], "words", data["terminal_outcome"]["first_satisfied_at_s"], "seconds", counts or "real LAN engine")
assert seen == expected
assert hashlib.sha256((root / "tests/fixtures/philo3_architect_meeting.wav").read_bytes()).hexdigest() == "165ea9755d028ff3dc2b9fa85dd4c48f4db3220855906e0ffeed4a35919d47b2"
(proof / "observations-index.json").write_text(json.dumps(rows, indent=2) + "\n")
print("Six actual case/width pairs pass; all shots retained; import completion, single Run, closed setup window, plain causes, settled counts and real ready-engine identity verified.")
print("Astra also inspected all before/after/framed shots. Fold defaults and refresh continuity are rendered-fence evidence; owner usefulness remains partial.")
