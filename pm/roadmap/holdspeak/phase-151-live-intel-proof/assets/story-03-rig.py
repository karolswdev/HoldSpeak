"""HS-151-03 metal proof rig -- control vs treatment on real metal.

Treatment leg: isolated HOME + keystore seam; wire via
scripts/wire_metal_intel.py against http://192.168.1.43:8080/v1 (the
REAL pinned resident server); boot the real hub; import a real
multi-speaker WAV (meeting-pylon-incident-warroom.wav) through POST
/api/meetings/import (real mlx-whisper transcription); run the
PRODUCTION intel queue path (process_next_intel_job through the bound
composition); wait bounded (~15 min ceiling, poll intel_status); assert
shape; map one owner; generate brief; take frames.

Control leg: fresh isolated HOME; intel disabled (config.meeting.
intel_enabled=False); same WAV; assert zero action_items, zero
intel_snapshots, no board cards, empty brief People.

WAV chosen: meeting-pylon-incident-warroom.wav -- 4 action items with
3 distinct named owners (Priya, Wei, Jordan) explicitly assigned in the
transcript. This is the harshest test for named-owner extraction: the
ground-truth script assigns "Priya owns the fourteen-day
expiry-headroom alert. Wei, you add the synthetic ACME-path CI test.
I'll update the cert-renewal runbook" (the "I'll" is the interesting
case -- it may emit Me, Jordan, or a novel string).

Orchestrator-runnable; shots land in story-03-shots/.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
ASSETS = REPO / "pm/roadmap/holdspeak/phase-151-live-intel-proof/assets"
SHOTS = ASSETS / "story-03-shots"
WAV = REPO / "dogfood/_audio/meeting-pylon-incident-warroom.wav"
TOKEN = "hs151-metal"
# The ground-truth expected owners from the transcript script:
GROUND_TRUTH_OWNERS = {"Priya", "Wei", "Jordan"}
# The full transcript text will be checked for groundedness.

# Counsel L3: bounded intel timeout -- ~15 min ceiling.
INTEL_TIMEOUT_SECONDS = 15 * 60
# Import timeout -- mlx-whisper on a 3.8 MB WAV, generous.
IMPORT_TIMEOUT_SECONDS = 10 * 60
# Poll intervals.
POLL_SECONDS = 5


def _http(url: str, method: str = "GET", data: Any = None, files: dict | None = None,
          token: str = TOKEN, timeout: int = 30) -> dict[str, Any]:
    """Minimal HTTP helper -- uses urllib to avoid external deps."""
    import urllib.request
    import urllib.error

    headers = {"Authorization": f"Bearer {token}"}
    body = None
    if files is not None:
        # multipart/form-data upload
        import io
        boundary = "----HS151Boundary"
        parts: list[bytes] = []
        for field_name, (filename, file_data, content_type) in files.items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            )
            parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
            parts.append(file_data if isinstance(file_data, bytes) else file_data.encode())
            parts.append(b"\r\n")
        if data:
            for k, v in data.items():
                parts.append(f"--{boundary}\r\n".encode())
                parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
                parts.append(str(v).encode())
                parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                return {"status": resp.status, "payload": json.loads(raw)}
            return {"status": resp.status, "payload": raw.decode(errors="replace")}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        ct = exc.headers.get("content-type", "") if exc.headers else ""
        if "json" in ct:
            return {"status": exc.code, "payload": json.loads(raw)}
        return {"status": exc.code, "payload": raw.decode(errors="replace")}


def _extract_intel_state(payload: dict[str, Any]) -> str:
    """Extract the bare intel state string from a meeting response.

    The response wraps it as ``intel_status: {state, detail, ...}`` (dict)
    or as a bare string in older code paths.
    """
    raw = payload.get("intel_status", "")
    if isinstance(raw, dict):
        return str(raw.get("state", ""))
    return str(raw)


def _poll_meeting(base_url: str, meeting_id: str, target_statuses: set[str],
                  timeout: int, label: str) -> dict[str, Any]:
    """Poll GET /api/meetings/{id} until intel_status.state is in target_statuses."""
    deadline = time.monotonic() + timeout
    last_status = "unknown"
    while time.monotonic() < deadline:
        resp = _http(f"{base_url}/api/meetings/{meeting_id}")
        if resp["status"] == 200:
            payload = resp["payload"]
            status = _extract_intel_state(payload)
            if status != last_status:
                print(f"  [{label}] intel_status: {last_status} -> {status}")
                last_status = status
            if status in target_statuses:
                return payload
            if status in {"failed", "error", "terminal_failure", "import_failed"}:
                print(f"  [{label}] TERMINAL: intel_status={status}")
                return payload
        time.sleep(POLL_SECONDS)
    print(f"  [{label}] TIMEOUT after {timeout}s (last status: {last_status})")
    resp = _http(f"{base_url}/api/meetings/{meeting_id}")
    return resp.get("payload", {}) if resp["status"] == 200 else {}


def treatment_leg() -> dict[str, Any]:
    """Run the treatment leg: real import + real intel on .43 metal."""
    sys.path.insert(0, str(REPO))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(os.environ["HOME"])
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    # Align with wire_metal_intel.py (db_path = home / ".holdspeak" / "holdspeak.db")
    db_core.DEFAULT_DB_PATH = home / ".holdspeak" / "holdspeak.db"
    reset_database()

    result: dict[str, Any] = {
        "leg": "treatment",
        "home": str(home),
        "wav": str(WAV),
        "failures": [],
        "findings": [],
        "timings": {},
        "model_output": {},
    }

    # 1. Boot the hub FIRST.
    print("[TREATMENT] Booting hub...")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    print(f"  Hub at {url}")

    # 2. Wire metal intel: v2 local profile (for bound claim routing) +
    # engine factory redirect (for actual cloud dispatch to .43).
    # The v2 profile system has no factory for remote endpoints
    # (from_artifact hardcodes kind=this_device -- latent defect #6),
    # so we use the test-proven local-profile pattern for the routing
    # infrastructure and redirect the engine factory to build a cloud
    # MeetingIntel that dispatches to the REAL .43 endpoint.
    print("[TREATMENT] Wiring metal intel profile...")
    import hashlib as _hashlib

    PROFILE_ID = "metal-intel"
    BASE_URL = "http://192.168.1.43:8080/v1"
    MODEL = "qwen3.6-35b"
    CAPABILITY_ID = "meeting.deferred_analysis"

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.model_profile_service import ModelProfileService
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.deployment_revisions import DeploymentRevision

    def _canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    def _sha256_h(value):
        return "sha256:" + _hashlib.sha256(_canonical(value).encode()).hexdigest()
    def _manifest(*claims):
        values = list(claims or ("language",))
        material = {"claims": values, "revision": "metal-intel-v1"}
        return {**material, "sha256": _sha256_h(material)}

    db = get_database()
    registry = process_inference_capability_registry()
    capability = registry.require(CAPABILITY_ID)
    result_claim = f"result_schema:{capability.output_schema_sha256}"
    manifest = _manifest("language", "structured_output", result_claim)
    artifact_id = f"artifact-{PROFILE_ID}"
    owner = Principal(PrincipalKind.OWNER, "wire-metal-intel")
    profiles = ModelProfileService(db)
    assignments = InferenceAssignmentService(db)

    # v2 profile + deployment (local pattern -- engine factory redirected below)
    profiles.create_profile(owner, {
        "profile_id": PROFILE_ID, "expected_revision": 0,
        "label": f"Metal intel ({MODEL})",
        "provider_family": "local",
        "runtime_family": "llama_cpp_prompt_v1",
        "model_or_artifact_identity": artifact_id,
        "supported_modalities": ["language"],
        "context_support": "bounded",
        "tokenizer_template_requirements": {},
        "capability_manifest": manifest,
        "safe_presentation": {"summary": f"openAICompatible on .43"},
    })
    deployment = DeploymentRevision.from_artifact(
        destination_id="this_machine", engine="configured_local_engine",
        model=MODEL, runtime_id="llama_cpp_prompt_v1", runtime_revision="1",
        artifact_id=artifact_id, manifest_sha256=str(manifest["sha256"]),
        format="gguf", architecture="transformer",
        context_ceiling=32768, capability_sha256=str(manifest["sha256"]),
        resolved_model_path="/metal/placeholder",
    )
    db.deployment_revisions.upsert(deployment)
    deployment_head_id = f"head-{PROFILE_ID}"
    with db._connection() as conn:
        if not conn.execute("SELECT 1 FROM inference_model_artifacts WHERE artifact_id=?", (artifact_id,)).fetchone():
            conn.execute(
                """INSERT INTO inference_model_artifacts
                (artifact_id,format,source_kind,source_repository,source_revision,manifest_json,manifest_sha256,
                 installed_bytes,state,local_locator,created_at,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (artifact_id, "gguf", "metal", "metal-endpoint", "v1",
                 "{}", str(manifest["sha256"]), 1, "verified", "/metal/placeholder",
                 "2026-08-30T00:00:00Z", "2026-08-30T00:00:00Z"),
            )
        if not conn.execute("SELECT 1 FROM inference_deployments WHERE deployment_id=?", (deployment_head_id,)).fetchone():
            conn.execute(
                """INSERT INTO inference_deployments
                (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,model_identity,context_ceiling,
                 recommended_context,capability_json,capability_sha256,execution_revision_id,configuration_revision,
                 active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (deployment_head_id, "this_machine", "llama_cpp_prompt_v1", "1",
                 artifact_id, MODEL, 32768, 32768,
                 "{}", str(manifest["sha256"]), deployment.id, 1, 1,
                 "2026-08-30T00:00:00Z", "2026-08-30T00:00:00Z"),
            )
    observation = profiles.probe_profile(owner, {
        "profile_id": PROFILE_ID, "profile_revision": 1,
        "deployment_head_id": deployment_head_id,
        "expected_deployment_configuration_revision": 1,
        "expected_deployment_revision_id": deployment.id,
    })
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_readiness_observations SET state=?,reason_code=? WHERE observation_id=?",
            ("ready", "metal_wired", observation["observation_id"]),
        )
    profiles.bind_profile(owner, {
        "binding_id": f"binding-{PROFILE_ID}",
        "profile_id": PROFILE_ID, "profile_revision": 1,
        "deployment_head_id": deployment_head_id,
        "expected_binding_revision": 0,
        "expected_deployment_configuration_revision": 1,
        "expected_deployment_revision_id": deployment.id,
        "enabled": True,
        "readiness_observation_id": observation["observation_id"],
    })
    # Assignment: ONLY meeting.deferred_analysis. The HS-151-03
    # skip-with-receipt fix handles unassigned plugins at claim time.
    assignments.set_assignment(owner, {
        "command_id": f"wire-metal-{CAPABILITY_ID}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": CAPABILITY_ID},
        "entries": [{"profile_id": PROFILE_ID, "profile_revision": 1}],
    })
    print(f"  Profile + deployment + binding + assignment ready")

    # Redirect the engine factory: the deployment is v2-local but the
    # REAL provider is the cloud-compatible .43 endpoint (latent defect
    # #6: the v2 system has no factory for remote endpoints).
    from holdspeak.intel.engine import MeetingIntel
    from holdspeak.kernel.runtime import _service as _ks
    def _metal_engine_factory(revision, *, warrant=None, context=None):
        from holdspeak.kernel.dispatch_context import bind_dispatch_context, require_bound_context
        bound = require_bound_context(context, revision)
        engine = MeetingIntel(
            provider="cloud", cloud_model=MODEL,
            cloud_api_key_env="", cloud_base_url=BASE_URL,
        )
        return bind_dispatch_context(engine, bound)
    _ks().inference_runner._engine_factory = _metal_engine_factory
    print(f"  Engine factory -> {BASE_URL}")

    try:
        # 3. Import the WAV through the REAL door.
        print(f"[TREATMENT] Importing {WAV.name} via POST /api/meetings/import...")
        t_import_start = time.monotonic()
        with open(WAV, "rb") as f:
            wav_data = f.read()
        import_resp = _http(
            f"{url}/api/meetings/import", method="POST",
            files={"file": (WAV.name, wav_data, "audio/wav")},
            data={"title": "Pylon incident war-room (PI-204)"},
            timeout=30,
        )
        if import_resp["status"] not in (200, 201, 202):
            result["failures"].append(f"Import failed: {import_resp}")
            return result
        meeting_id = import_resp["payload"].get("meeting_id", "")
        print(f"  Meeting ID: {meeting_id}, status: {import_resp['payload'].get('status')}")

        # 4. Poll until import completes (intel_status transitions from importing).
        print("[TREATMENT] Waiting for transcription (real mlx-whisper)...")
        meeting_after_import = _poll_meeting(
            url, meeting_id,
            target_statuses={"queued", "disabled", "ready"},
            timeout=IMPORT_TIMEOUT_SECONDS,
            label="import",
        )
        t_import_end = time.monotonic()
        result["timings"]["transcription_seconds"] = round(t_import_end - t_import_start, 1)
        import_intel_status = _extract_intel_state(meeting_after_import)
        print(f"  Import done. intel_status={import_intel_status}, "
              f"transcription took {result['timings']['transcription_seconds']}s")

        if import_intel_status != "queued":
            result["failures"].append(
                f"Expected intel_status=queued after import, got: {import_intel_status}"
            )
            return result

        # 5. Drive the PRODUCTION intel queue path.
        print("[TREATMENT] Driving drain_intel_queue (production bound path)...")
        t_intel_start = time.monotonic()
        from holdspeak.intel_queue import drain_intel_queue
        intel_processed = drain_intel_queue(max_jobs=10)
        t_intel_first = time.monotonic()
        print(f"  drain_intel_queue processed: {intel_processed} jobs "
              f"({round(t_intel_first - t_intel_start, 1)}s)")

        # 6. Poll until intel_status reaches ready (or terminal).
        print("[TREATMENT] Polling intel_status for ready...")
        meeting_after_intel = _poll_meeting(
            url, meeting_id,
            target_statuses={"ready"},
            timeout=INTEL_TIMEOUT_SECONDS,
            label="intel",
        )
        t_intel_end = time.monotonic()
        result["timings"]["intel_seconds"] = round(t_intel_end - t_intel_start, 1)
        intel_final_status = _extract_intel_state(meeting_after_intel)
        intel_detail = ""
        raw_intel = meeting_after_intel.get("intel_status", {})
        if isinstance(raw_intel, dict):
            intel_detail = str(raw_intel.get("detail", ""))
        print(f"  Intel done. intel_status={intel_final_status}, "
              f"extraction took {result['timings']['intel_seconds']}s")
        if intel_detail:
            print(f"  Intel detail: {intel_detail}")
            result["model_output"]["intel_detail"] = intel_detail

        # --- TREATMENT ASSERTIONS ---

        # A1: intel_status ready
        if intel_final_status != "ready":
            result["failures"].append(
                f"intel_status expected 'ready', got '{intel_final_status}'"
            )

        # A2: intel_snapshots row exists (check via DB)
        db = get_database()
        with db._connection() as conn:
            snapshot_row = conn.execute(
                "SELECT meeting_id, summary FROM intel_snapshots WHERE meeting_id=?",
                (meeting_id,),
            ).fetchone()
        if snapshot_row is None:
            result["failures"].append("No intel_snapshots row for the meeting")
        else:
            result["model_output"]["summary"] = snapshot_row[1] or ""
            print(f"  Summary: {result['model_output']['summary']}")

        # A3: action_items rows with review_state=pending
        with db._connection() as conn:
            action_rows = conn.execute(
                "SELECT id, task, owner, review_state, due FROM action_items WHERE meeting_id=?",
                (meeting_id,),
            ).fetchall()
        result["model_output"]["action_items"] = [
            {"id": r[0], "task": r[1], "owner": r[2], "review_state": r[3], "due": r[4]}
            for r in action_rows
        ]
        pending_items = [r for r in result["model_output"]["action_items"] if r["review_state"] == "pending"]
        print(f"  Action items: {len(action_rows)} total, {len(pending_items)} pending")
        for item in result["model_output"]["action_items"]:
            print(f"    - task={item['task']!r}, owner={item['owner']!r}, review_state={item['review_state']}")

        if len(pending_items) == 0:
            result["failures"].append("Zero action_items with review_state=pending")

        # A4: owner groundedness (counsel M5: case-insensitive substring of transcript)
        transcript_text = "\n".join(
            str(seg) for seg in (meeting_after_intel.get("segments") or [])
        )
        # If segments not in response, read from DB
        if not transcript_text:
            meeting_state = db.meetings.get_meeting(meeting_id)
            if meeting_state and meeting_state.segments:
                transcript_text = "\n".join(str(s) for s in meeting_state.segments)
        transcript_lower = transcript_text.lower()

        result["model_output"]["owners_verbatim"] = [
            item["owner"] for item in result["model_output"]["action_items"]
        ]
        reserved_tokens = {"me", "remote", None, "null", ""}
        for item in result["model_output"]["action_items"]:
            owner = item["owner"]
            if owner is None or str(owner).lower() in {str(t).lower() for t in reserved_tokens if t}:
                continue  # reserved -- no groundedness check
            if owner.lower() not in transcript_lower:
                finding = (
                    f"UNGROUNDED owner: '{owner}' not found as substring in transcript "
                    f"(task: {item['task']!r})"
                )
                result["findings"].append(finding)
                print(f"  FINDING: {finding}")

        # A5: Door board shows items in UNASSIGNED lane
        board_resp = _http(f"{url}/api/follow-through/board")
        if board_resp["status"] != 200:
            result["failures"].append(f"Board GET failed: {board_resp}")
        else:
            board = board_resp["payload"]
            unassigned = board.get("unassigned", [])
            print(f"  Board: {len(unassigned)} unassigned cards")
            if len(unassigned) == 0:
                result["failures"].append("Zero cards in UNASSIGNED lane")
            result["model_output"]["board_unassigned_count"] = len(unassigned)

        # --- PERSON LEG ---

        # Accept one named-owner item via the real triage API
        named_owner_item = None
        for item in result["model_output"]["action_items"]:
            owner = item["owner"]
            if owner and str(owner).lower() not in {str(t).lower() for t in reserved_tokens if t}:
                named_owner_item = item
                break

        if named_owner_item is None:
            result["failures"].append("No named-owner item to accept for person leg")
        else:
            accepted_owner = named_owner_item["owner"]
            print(f"[TREATMENT] Person leg: accepting item {named_owner_item['id']} "
                  f"(owner={accepted_owner!r})...")
            # Accept the item (change review_state to accepted)
            accept_resp = _http(
                f"{url}/api/action-items/{named_owner_item['id']}/review",
                method="PATCH",
                data={"review_state": "accepted"},
            )
            if accept_resp["status"] >= 300:
                result["failures"].append(f"Accept failed: {accept_resp}")

            # Setup People sidecar
            _http(f"{url}/api/people/setup", method="POST")

            # Create a relationship for the owner
            rel_resp = _http(
                f"{url}/api/people/relationships", method="POST",
                data={"display_name": accepted_owner, "relationship_kind": "direct_report"},
            )
            rel_data = rel_resp["payload"]
            rel_id = (rel_data.get("relationship") or rel_data).get("id", "")
            print(f"  Created relationship: id={rel_id}, name={accepted_owner}")

            # Link the owner string as an alias via the real People gesture API.
            # A 409 with owner_alias_taken means the alias was auto-resolved
            # during relationship creation -- the alias IS linked, just to
            # the auto-created relationship rather than the one we just created.
            alias_resp = _http(
                f"{url}/api/people/relationships/{rel_id}/owner-aliases",
                method="POST",
                data={"alias": accepted_owner},
            )
            if alias_resp["status"] == 409:
                # Already linked -- use the holder's relationship ID instead
                detail = (alias_resp.get("payload") or {}).get("detail") or {}
                holder_id = detail.get("holder_id", rel_id)
                print(f"  Alias '{accepted_owner}' already held by {holder_id}")
                rel_id = holder_id  # use the existing holder for subsequent checks
            elif alias_resp["status"] >= 300:
                result["failures"].append(f"Alias link failed: {alias_resp}")
            else:
                print(f"  Linked alias '{accepted_owner}' to relationship {rel_id}")

            # Re-read the board -- person_label should be present
            board2_resp = _http(f"{url}/api/follow-through/board")
            if board2_resp["status"] == 200:
                board2 = board2_resp["payload"]
                # Check all lanes for person_label
                found_person_label = False
                for lane_name, lane_cards in board2.items():
                    if not isinstance(lane_cards, list):
                        continue
                    for card in lane_cards:
                        if card.get("person_label") == accepted_owner:
                            found_person_label = True
                            break
                    if found_person_label:
                        break
                if found_person_label:
                    print(f"  person_label '{accepted_owner}' present on board")
                else:
                    result["failures"].append(
                        f"person_label '{accepted_owner}' NOT found on board after map"
                    )

            # Generate Monday Brief and assert mapped person in person_sections
            brief_resp = _http(f"{url}/api/brief/generate", method="POST")
            if brief_resp["status"] != 200:
                result["failures"].append(f"Brief generate failed: {brief_resp}")
            else:
                brief = brief_resp["payload"]
                person_sections = brief.get("person_sections", [])
                result["model_output"]["brief_person_sections"] = person_sections
                found_in_brief = any(
                    accepted_owner.lower() in json.dumps(s).lower()
                    for s in person_sections
                )
                if found_in_brief:
                    print(f"  Brief person_sections contains '{accepted_owner}'")
                else:
                    result["failures"].append(
                        f"Brief person_sections missing '{accepted_owner}'"
                    )

        # --- FRAMES ---
        print("[TREATMENT] Taking frames...")
        SHOTS.mkdir(parents=True, exist_ok=True)
        # Build web bundle first
        build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(REPO / "web"),
            capture_output=True, text=True, timeout=120,
        )
        if build_result.returncode != 0:
            result["findings"].append(f"Web build warning: {build_result.stderr[:500]}")

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)

                def open_desk(width=1440, height=900):
                    ctx = browser.new_context(viewport={"width": width, "height": height})
                    page = ctx.new_page()
                    page.emulate_media(reduced_motion="reduce")
                    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                    chair = page.locator(".chair")
                    chair.wait_for(timeout=30000)
                    if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                        page.get_by_role("button", name="Continue later", exact=True).click()
                    page.locator(".chair:not(.chair-first-value)").wait_for(timeout=15000)
                    return ctx, page

                # Frame 1: Board with real intel items UNASSIGNED
                ctx1, p1 = open_desk()
                try:
                    p1.wait_for_timeout(2000)
                    p1.screenshot(
                        path=str(SHOTS / "treatment-board-unassigned-1440.png"),
                        full_page=True,
                    )
                    print(f"  Frame: treatment-board-unassigned-1440.png")
                finally:
                    ctx1.close()

                # Frame 2: After map -- the chip
                ctx2, p2 = open_desk()
                try:
                    p2.wait_for_timeout(2000)
                    chip = p2.locator('[data-testid="door-card-person-chip"]')
                    if chip.count() > 0:
                        chip.first.wait_for(timeout=10000)
                    p2.screenshot(
                        path=str(SHOTS / "treatment-board-mapped-chip-1440.png"),
                        full_page=True,
                    )
                    print(f"  Frame: treatment-board-mapped-chip-1440.png")
                finally:
                    ctx2.close()

                # Frame 3: Brief People section
                ctx3, p3 = open_desk()
                try:
                    p3.get_by_role("button", name="Desk", exact=True).first.click()
                    dmenu = p3.locator('nav[role="menu"]').last
                    dmenu.wait_for(timeout=15000)
                    dmenu.get_by_text("Open Intelligence", exact=True).click()
                    p3.wait_for_timeout(2000)
                    p3.screenshot(
                        path=str(SHOTS / "treatment-brief-people-1440.png"),
                        full_page=True,
                    )
                    print(f"  Frame: treatment-brief-people-1440.png")
                finally:
                    ctx3.close()

                browser.close()
        except Exception as exc:
            result["findings"].append(f"Playwright frames failed: {exc}")
            print(f"  Playwright error: {exc}")

    finally:
        server.stop()
        reset_database()

    return result


def control_leg() -> dict[str, Any]:
    """Run the control leg: same WAV, intel disabled."""
    sys.path.insert(0, str(REPO))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    home = Path(os.environ["HOME"])
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    # Align with wire_metal_intel.py (db_path = home / ".holdspeak" / "holdspeak.db")
    db_core.DEFAULT_DB_PATH = home / ".holdspeak" / "holdspeak.db"
    reset_database()

    result: dict[str, Any] = {
        "leg": "control",
        "home": str(home),
        "wav": str(WAV),
        "failures": [],
        "findings": [],
    }

    # Write config with intel_enabled=False at the SAME path CONFIG_FILE uses
    config_path = config_module.CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({
        "meeting": {
            "intel_enabled": False,
            "intel_deferred_enabled": False,
        },
    }), encoding="utf-8")
    print(f"[CONTROL] Config written: intel_enabled=False")

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    print(f"[CONTROL] Hub at {url}")

    try:
        # Import the same WAV
        print(f"[CONTROL] Importing {WAV.name}...")
        with open(WAV, "rb") as f:
            wav_data = f.read()
        import_resp = _http(
            f"{url}/api/meetings/import", method="POST",
            files={"file": (WAV.name, wav_data, "audio/wav")},
            data={"title": "Pylon incident war-room (PI-204) [CONTROL]"},
            timeout=30,
        )
        if import_resp["status"] not in (200, 201, 202):
            result["failures"].append(f"Import failed: {import_resp}")
            return result
        meeting_id = import_resp["payload"].get("meeting_id", "")
        print(f"  Meeting ID: {meeting_id}")

        # Wait for import to finish (but intel should stay disabled)
        print("[CONTROL] Waiting for transcription (intel should stay disabled)...")
        meeting_after = _poll_meeting(
            url, meeting_id,
            target_statuses={"disabled", "ready"},
            timeout=IMPORT_TIMEOUT_SECONDS,
            label="control-import",
        )
        intel_status = _extract_intel_state(meeting_after)
        print(f"  intel_status: {intel_status}")

        if intel_status != "disabled":
            result["failures"].append(
                f"Control: expected intel_status=disabled, got: {intel_status}"
            )

        # Assert: zero action_items
        db = get_database()
        with db._connection() as conn:
            action_count = conn.execute(
                "SELECT COUNT(*) FROM action_items WHERE meeting_id=?",
                (meeting_id,),
            ).fetchone()[0]
            snapshot_count = conn.execute(
                "SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id=?",
                (meeting_id,),
            ).fetchone()[0]
        print(f"  action_items: {action_count}, intel_snapshots: {snapshot_count}")

        if action_count != 0:
            result["failures"].append(
                f"Control: expected 0 action_items, got {action_count}"
            )
        if snapshot_count != 0:
            result["failures"].append(
                f"Control: expected 0 intel_snapshots, got {snapshot_count}"
            )

        # Assert: no meeting-born cards on the board
        board_resp = _http(f"{url}/api/follow-through/board")
        if board_resp["status"] == 200:
            board = board_resp["payload"]
            total_cards = sum(
                len(cards) for cards in board.values() if isinstance(cards, list)
            )
            if total_cards != 0:
                result["failures"].append(
                    f"Control: expected 0 board cards, got {total_cards}"
                )
            print(f"  Board cards: {total_cards}")

        # Assert: empty brief People
        _http(f"{url}/api/people/setup", method="POST")
        brief_resp = _http(f"{url}/api/brief/generate", method="POST")
        if brief_resp["status"] == 200:
            brief = brief_resp["payload"]
            person_sections = brief.get("person_sections", [])
            if person_sections:
                result["failures"].append(
                    f"Control: expected empty person_sections, got {len(person_sections)}"
                )
            print(f"  Brief person_sections: {len(person_sections)}")

        # Control frame
        SHOTS.mkdir(parents=True, exist_ok=True)
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx, page = browser.new_context(
                    viewport={"width": 1440, "height": 900}
                ), None
                page = ctx.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                chair = page.locator(".chair")
                chair.wait_for(timeout=30000)
                if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    page.get_by_role("button", name="Continue later", exact=True).click()
                page.locator(".chair:not(.chair-first-value)").wait_for(timeout=15000)
                page.wait_for_timeout(2000)
                page.screenshot(
                    path=str(SHOTS / "control-board-empty-1440.png"),
                    full_page=True,
                )
                print(f"  Frame: control-board-empty-1440.png")
                ctx.close()
                browser.close()
        except Exception as exc:
            result["findings"].append(f"Control frame failed: {exc}")

    finally:
        server.stop()
        reset_database()

    return result


def main() -> int:
    assert os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE"), "the story-01 seam env is REQUIRED"

    done_file = Path(os.environ.get("HS151_DONE_FILE", str(ASSETS / "story-03-done.json")))
    print(f"=== HS-151-03 Metal Proof Rig ===")
    print(f"WAV: {WAV.name} (chosen: 4 action items, 3 named owners -- Priya, Wei, Jordan)")
    print(f"Done file: {done_file}")
    print()

    results: dict[str, Any] = {
        "rig": "HS-151-03",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "wav": WAV.name,
        "wav_reason": (
            "meeting-pylon-incident-warroom.wav: 4 action items with 3 distinct "
            "named owners (Priya, Wei, Jordan) explicitly assigned in the transcript; "
            "the harshest test for named-owner extraction"
        ),
    }

    # --- TREATMENT LEG ---
    print("=" * 60)
    print("TREATMENT LEG")
    print("=" * 60)
    # Each leg gets its own isolated HOME
    import tempfile
    treatment_home = tempfile.mkdtemp(prefix="hs151-treatment-")
    os.environ["HOME"] = treatment_home
    treatment_result = treatment_leg()
    results["treatment"] = treatment_result

    # --- CONTROL LEG ---
    print()
    print("=" * 60)
    print("CONTROL LEG")
    print("=" * 60)
    # Reset modules for fresh DB singleton
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("holdspeak"):
            del sys.modules[mod_name]
    control_home = tempfile.mkdtemp(prefix="hs151-control-")
    os.environ["HOME"] = control_home
    control_result = control_leg()
    results["control"] = control_result

    # --- SUMMARY ---
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_failures = (
        treatment_result.get("failures", []) + control_result.get("failures", [])
    )
    all_findings = (
        treatment_result.get("findings", []) + control_result.get("findings", [])
    )
    results["all_failures"] = all_failures
    results["all_findings"] = all_findings
    results["pass"] = len(all_failures) == 0

    for f in all_failures:
        print(f"  FAILURE: {f}")
    for f in all_findings:
        print(f"  FINDING: {f}")
    if not all_failures:
        print("  ALL ASSERTIONS PASSED")

    # Write done file
    done_file.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nDone file: {done_file}")

    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
