"""Live model proof on an isolated database; synthetic interview content only."""
import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[4]
(root / ".tmp").mkdir(exist_ok=True)
sys.path.insert(0, str(root))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--endpoint", required=True, help="Existing compatible endpoint, including /v1")
parser.add_argument("--model", required=True, help="Actual endpoint model ID")
args = parser.parse_args()
original_expanduser = os.path.expanduser
with tempfile.TemporaryDirectory(prefix="holdspeak-live-interview-") as directory:
    isolated = Path(directory)
    def expanduser(path):
        value = os.fspath(path)
        if isinstance(value, str) and (value == "~" or value.startswith("~/")):
            return str(isolated) + value[1:]
        return original_expanduser(path)
    with patch.object(Path, "home", return_value=isolated), patch("os.path.expanduser", side_effect=expanduser):
        from fastapi.testclient import TestClient
        from holdspeak.db import get_database, reset_database
        from holdspeak.config import Config
        from holdspeak.kernel import runtime
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.model_library_service import ModelLibraryApplicationService
        from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
        from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.thread_modes import seed_modes
        from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
        from holdspeak.services.thread_service import ThreadService
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
        owner = Principal(PrincipalKind.OWNER, "live-interview-proof")
        reset_database()
        db = get_database(isolated / "live.db")
        seed_modes(db)
        config = Config()
        config.control_mode = "yolo"
        with patch.object(Config, "load", return_value=config), patch.object(runtime, "_mode", return_value="yolo"):
            setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: isolated)
            acquisition = InferenceAcquisitionApplicationService(db, setup_service=setup, model_root=isolated / "models", home_provider=lambda: isolated)
            ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).define_endpoint(owner, {
                "request_id": "live-proof-model", "profile_id": "interview-lan-proof",
                "expected_profile_revision": 0, "label": "Interview LAN proof",
                "provider_family": "private_endpoint", "model": args.model,
                "endpoint": args.endpoint, "requires_key": False,
            })
            InferenceAssignmentService(db).set_assignment(owner, {"command_id": "live-proof-assignment", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [{"profile_id": "interview-lan-proof", "profile_revision": 1}]})
            project = ProjectService(db).create_project(owner, {"name": "Delta migration", "description": "Synthetic test project for architecture decision preparation"})
            broker = runtime._configure(db)
            execute_stream = broker.inference_adoption_service.execute_stream
            def observed_execute(*args, **kwargs):
                counts = {}
                callback = kwargs["on_delta"]
                def observe(delta):
                    counts[delta.kind] = counts.get(delta.kind, 0) + 1
                    return callback(delta)
                result = execute_stream(*args, **{**kwargs, "on_delta": observe})
                print(json.dumps({"pass": counts, "outcome": result.get("outcome"), "output": (result.get("result") or {}).get("output"), "error": result.get("error"), "failure_receipt": result.get("receipt") if result.get("outcome") != "succeeded" else None}), flush=True)
                return result
            broker.inference_adoption_service.execute_stream = observed_execute
            server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}), auth_token="live-interview-proof")
            transcript = []
            try:
                with TestClient(server.app, headers={"Authorization": "Bearer live-interview-proof"}) as client:
                    response = client.post("/api/threads", json={"title": "Synthetic architect interview", "recipe_id": INTERVIEW_MODE_ID})
                    assert response.status_code == 201, response.text
                    tid = response.json()["id"]
                    prompts = [
                        "I want to recover architecture decision context before the weekly review. Delta migration is my project. Please explore this with me and remember the goal. Ask one useful question if you need clarification.",
                        "Reconstructing why a decision was made takes most of my time. I want a manual decision brief before the review, covering rationale, changed evidence, and unresolved questions. Use the actual Project records, save one useful suggestion, and distinguish missing decision sources from known facts.",
                        "Prepare the chosen manual decision brief for the Delta migration database-engine choice. Use actual available Project evidence, leave unknown rationale and changed evidence explicitly unfilled, and give me a useful review template to keep. This is draft preparation only.",
                    ]
                    chosen = None
                    for index, text in enumerate(prompts):
                        if index == 2:
                            state = detail["interview"]
                            chosen = next(s for s in state["suggestions"].values() if s["feasibility"] == "manual")
                            response = client.post(f"/api/threads/{tid}/interview", json={"command_id": "live-try-draft", "expected_revision": state["revision"], "event": {"kind": "disposition", "suggestion_id": chosen["id"], "disposition": "try"}})
                            assert response.status_code == 200, response.text
                        response = client.post(f"/api/threads/{tid}/turns", json={"text": text})
                        assert response.status_code == 201, response.text
                        message_id = response.json()["assistant_message_id"]
                        deadline = time.monotonic() + 180
                        detail = {}
                        while time.monotonic() < deadline:
                            detail = client.get(f"/api/threads/{tid}").json()
                            message = next(m for m in detail["messages"] if m["id"] == message_id)
                            if message.get("completed_at") or message.get("aborted_at"):
                                break
                            time.sleep(.25)
                        else:
                            raise RuntimeError("Live model turn exceeded 180 seconds")
                        tools = [p.get("meta_json", {}) for p in message["parts"] if p["kind"] == "tool_call"]
                        results = [{"id": p.get("tool_call_id"), "meta": p.get("meta_json"), "text": p.get("text")} for m in detail["messages"] if m["role"] == "tool" and m.get("parent_id") == message_id for p in m["parts"]]
                        record = {"user": text, "assistant": "\n".join(p["text"] or "" for p in message["parts"] if p["kind"] == "text"), "error": message.get("error_json"), "egress": message.get("egress_scope"), "receipt_id": message.get("receipt_id"), "tools": tools, "results": results, "stats": message.get("stats_json")}
                        transcript.append(record)
                        print(json.dumps(record), flush=True)
                        with db._connection() as conn:
                            rows = conn.execute("SELECT payload_json FROM inference_adoption_material_snapshots ORDER BY created_at").fetchall()
                        (root / ".tmp/interview-live-payloads.json").write_text(json.dumps([json.loads(row[0]) for row in rows], indent=2))
                        if message.get("error_json"):
                            break
                    state = detail.get("interview", {})
                    print(json.dumps({"facts": state.get("facts"), "suggestions": state.get("suggestions"), "model": args.model, "data": "synthetic", "runtime": "isolated hub/database; actual configured LAN endpoint"}), flush=True)
                    (root / ".tmp/interview-live-evidence.json").write_text(json.dumps({"transcript": transcript, "state": state}, indent=2))
                    assert all(not row["error"] for row in transcript)
                    assert all(row["assistant"].strip() for row in transcript)
                    assert state.get("facts"), "Live model did not record facts"
                    assert state.get("suggestions"), "Live model did not save a suggestion"
                    kept = client.post(f"/api/threads/{tid}/keep", json={"message_id": message_id, "as": "artifact"})
                    assert kept.status_code == 201, kept.text
                    revisit = client.post(f"/api/threads/{tid}/interview", json={"command_id": "live-revisit", "expected_revision": state["revision"], "event": {"kind": "section", "section": "decisions"}})
                    assert revisit.status_code == 200, revisit.text
                    assert revisit.json()["facts"] == state["facts"]
                    assert revisit.json()["suggestions"][chosen["id"]]["disposition"] == "try"
                    evidence = {"transcript": transcript, "state": revisit.json(), "kept": kept.json(), "model": args.model, "data": "synthetic", "result": "pass"}
                    (root / ".tmp/interview-live-evidence.json").write_text(json.dumps(evidence, indent=2))
                    print(json.dumps({"result": "pass", "kept": kept.json(), "revisit": "same facts and suggestion disposition"}), flush=True)
            finally:
                for event in list(ThreadService._active_turns.values()): event.set()
                runtime._dispose(broker)
                reset_database()
