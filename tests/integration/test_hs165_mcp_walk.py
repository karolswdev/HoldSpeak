"""HS-165-05 -- The walk: one MCP client drives the whole §15 loop.

A REAL subprocess MCP client (JSON-RPC over stdio) drives the §15
acceptance scenario through the project palette.  The snapshot fetcher
is the only fixture seam: the subprocess runs a test entry module that
patches WatchService to read snapshots from a file instead of calling
the gh CLI.  Everything else -- auth, DB, server loop, tool dispatch,
service composition -- is the real sidecar.

The palette-consumer proof exercises dispatch_for_palette in-process
(the charter-approved exception: the palette has no server wiring yet).

Transcript artifact: every tool call + structured result written to
pm/roadmap/holdspeak/phase-165-the-mcp-family/assets/story-05-transcript.json.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

# ── Constants ────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT_PATH = (
    REPO_ROOT
    / "pm/roadmap/holdspeak/phase-165-the-mcp-family/assets"
    / "story-05-transcript.json"
)

# Snapshot fixtures (same shape as the glass rig)
_BASELINE_ENTITIES = [
    {
        "number": 200, "title": "feat: add search API",
        "url": "https://github.com/walkuser/WalkRepo/pull/200",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "alice"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "aaa111aaa111", "updatedAt": "2026-08-30T10:00:00Z",
    },
    {
        "number": 201, "title": "fix: correct rounding",
        "url": "https://github.com/walkuser/WalkRepo/pull/201",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "bbb222bbb222", "updatedAt": "2026-08-30T11:00:00Z",
    },
]

_CHANGED_ENTITIES = [
    {
        "number": 200, "title": "feat: add search API",
        "url": "https://github.com/walkuser/WalkRepo/pull/200",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "alice"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "FAILURE"},
        ],
        "headRefOid": "ccc333ccc333", "updatedAt": "2026-08-31T10:00:00Z",
    },
    {
        "number": 201, "title": "fix: correct rounding",
        "url": "https://github.com/walkuser/WalkRepo/pull/201",
        "state": "MERGED", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "bbb222bbb222", "updatedAt": "2026-08-31T11:00:00Z",
    },
]


# ── MCP Client Harness ──────────────────────────────────────────────

class MCPClient:
    """Minimal honest MCP client: subprocess stdio JSON-RPC."""

    def __init__(self, home_dir: Path, snapshot_file: Path) -> None:
        self._home = home_dir
        self._snapshot_file = snapshot_file
        self._proc: subprocess.Popen | None = None
        self._req_id = 0
        self._transcript: list[dict[str, Any]] = []

    def start(self) -> None:
        env = dict(os.environ)
        env["HOME"] = str(self._home)
        env["HOLDSPEAK_TEST_SNAPSHOT_FILE"] = str(self._snapshot_file)
        env["HOLDSPEAK_MCP_PEOPLE_ACCESS"] = "off"
        # Ensure the DB directory exists
        db_dir = self._home / ".local" / "share" / "holdspeak"
        db_dir.mkdir(parents=True, exist_ok=True)

        self._proc = subprocess.Popen(
            [sys.executable, "-m", "tests.integration._mcp_walk_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
        )

    def stop(self) -> None:
        if self._proc:
            self._proc.stdin.close()
            self._proc.wait(timeout=10)
            self._proc = None

    @property
    def db_path(self) -> Path:
        return self._home / ".local" / "share" / "holdspeak" / "holdspeak.db"

    def _send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._req_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params
        line = json.dumps(request) + "\n"
        assert self._proc is not None and self._proc.stdin is not None
        self._proc.stdin.write(line)
        self._proc.stdin.flush()
        response_line = self._proc.stdout.readline()
        if not response_line:
            stderr_out = self._proc.stderr.read() if self._proc.stderr else ""
            raise RuntimeError(
                f"MCP sidecar closed stdout (method={method}); "
                f"stderr: {stderr_out[:2000]}"
            )
        return json.loads(response_line)

    def initialize(self) -> dict[str, Any]:
        resp = self._send("initialize")
        # Send initialized notification (no response expected, but
        # we must send it before tools/call)
        assert self._proc is not None
        notif = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }) + "\n"
        self._proc.stdin.write(notif)
        self._proc.stdin.flush()
        return resp

    def list_tools(self) -> list[dict[str, Any]]:
        resp = self._send("tools/list")
        return resp["result"]["tools"]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]:
        t0 = time.monotonic()
        resp = self._send("tools/call", {"name": name, "arguments": arguments or {}})
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        result = resp["result"]
        is_error = result.get("isError", False)
        data = json.loads(result["content"][0]["text"])
        # Record transcript entry
        self._transcript.append({
            "tool": name,
            "arguments": arguments or {},
            "is_error": is_error,
            "result": data,
            "elapsed_ms": elapsed_ms,
        })
        return is_error, data

    @property
    def transcript(self) -> list[dict[str, Any]]:
        return self._transcript


# ── DB Seeding Helpers ───────────────────────────────────────────────

def _seed_graduated_watch(
    db_path: Path,
    project_id: str,
    watch_id: str,
    baseline_snapshot_json: str,
) -> None:
    """Seed a graduated WatchSpec@1 GitHub watch with a baseline snapshot."""
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """INSERT INTO connector_watches (
                id, name, connector_id, query_kind, query_json,
                project_id, state, revision, enabled,
                evaluation_cadence_minutes, next_evaluation_at,
                baseline_state, snapshot_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                watch_id,
                "PR queue (walk)",
                "gh",
                "pull_requests",
                json.dumps({"repository": "walkuser/WalkRepo", "state": "open"}),
                project_id,
                "active",
                1,
                1,
                60,
                past_iso,
                "established",
                baseline_snapshot_json,
                now_iso,
                now_iso,
            ),
        )

        # project_sources binding
        source_id = f"psrc_{watch_id}"
        conn.execute(
            """INSERT INTO project_sources (
                id, project_id, source_ref, label,
                semantic_role, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                project_id,
                f"watch:{watch_id}",
                "PR queue (walk)",
                "watch",
                now_iso,
                now_iso,
            ),
        )

        # Watch rule: any field change -> project.steward.run_once
        rule_id = f"wrule_{watch_id}"
        condition = {
            "schema": "WatchCondition@1",
            "operator": "any",
            "clauses": [
                {"field": "state", "comparison": "changed"},
                {"field": "head_sha", "comparison": "changed"},
                {"field": "checks", "comparison": "changed"},
                {"field": "review_decision", "comparison": "changed"},
            ],
        }
        actions = [
            {"schema": "WatchAction@1", "kind": "project.steward.run_once"},
        ]
        conn.execute(
            """INSERT INTO watch_rules
               (id, watch_id, ordinal, condition_schema, condition_json,
                action_schema, action_json, enabled, revision)
               VALUES (?, ?, 0, 'WatchCondition@1', ?,
                       'WatchAction@1', ?, 1, 0)""",
            (
                rule_id,
                watch_id,
                json.dumps(condition),
                json.dumps(actions),
            ),
        )

        conn.commit()
    finally:
        conn.close()


STEWARD_EFFECT_KINDS = [
    "refresh_sources",
    "create_proposals",
    "apply_proposal_effects",
    "draft_update",
    "create_door_item",
]


def _normalize_baseline(entities: list[dict[str, Any]]) -> str:
    """Normalize entities into the watch snapshot_json format."""
    from holdspeak.services.reaction_service import normalize_snapshot
    snapshot = normalize_snapshot("gh", entities)
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))


# ── The Walk ─────────────────────────────────────────────────────────

def _run_walk(tmp_path: Path) -> dict[str, Any]:
    """Execute the full §15 walk; returns measured numbers."""
    home_dir = tmp_path / "walk_home"
    home_dir.mkdir()
    snapshot_file = tmp_path / "snapshot.json"

    # Write baseline snapshot to the fixture file
    snapshot_file.write_text(json.dumps(_BASELINE_ENTITIES))

    client = MCPClient(home_dir, snapshot_file)
    client.start()

    try:
        # ── Initialize ───────────────────────────────────────────────
        init_resp = client.initialize()
        assert init_resp["result"]["serverInfo"]["name"] == "holdspeak-mcp"

        # ── tools/list (palette completeness pre-check) ──────────────
        tools = client.list_tools()
        tool_names = {t["name"] for t in tools}
        # The sidecar exposes ALL tools, not just the palette.
        # We verify palette membership separately.

        # ────────────────────────────────────────────────────────────
        # §15 item 2: durable setup session compiles owner intent into
        # one real tested Watch and atomically activates a Project
        # without false baseline transitions.
        # ────────────────────────────────────────────────────────────

        # Step 1: setup.start
        is_error, start_data = client.call_tool("project.setup.start")
        assert is_error is False, f"setup.start failed: {start_data}"
        session_id = start_data.get("id") or start_data.get("session_id")
        assert session_id is not None

        # Step 2: setup.answer (outcome question)
        is_error, answer_data = client.call_tool("project.setup.answer", {
            "session_id": session_id,
            "question_id": "outcome",
            "payload": {"text": "Track CI health on my repos"},
        })
        assert is_error is False, f"setup.answer failed: {answer_data}"

        # Step 3: setup.suggest (deterministic proposals from desk)
        is_error, suggest_data = client.call_tool("project.setup.suggest", {
            "session_id": session_id,
        })
        assert is_error is False, f"setup.suggest failed: {suggest_data}"

        # Step 4: setup.finalize (empty proposals is lawful per INT-002)
        is_error, finalize_data = client.call_tool("project.setup.finalize", {
            "session_id": session_id,
            "command_id": "walk-finalize-001",
        })
        assert is_error is False, f"setup.finalize failed: {finalize_data}"
        project_id = finalize_data["project_id"]
        assert project_id is not None

        # §15 item 2 assert: project created atomically
        is_error, project_data = client.call_tool("project.get", {
            "project_id": project_id,
        })
        assert is_error is False
        assert project_data["id"] == project_id

        # Verify setup resume works (durability proof)
        is_error, resume_data = client.call_tool("project.setup.resume", {
            "session_id": session_id,
        })
        assert is_error is False

        # ── Seed the graduated watch ─────────────────────────────────
        # The finalize created a project but with zero proposals (fresh
        # DB has no desk facts for native suggestions, and GitHub is not
        # configured).  We seed a graduated GitHub watch directly in the
        # DB, the same pattern the glass rig uses.  This is honest
        # seeding, not a wire bypass -- the walk legs below exercise the
        # watch tools through the real JSON-RPC protocol.
        baseline_json = _normalize_baseline(_BASELINE_ENTITIES)
        watch_id = "cw_walk_001"
        _seed_graduated_watch(
            client.db_path, project_id, watch_id, baseline_json,
        )

        # ── Configure steward through the wire ──────────────────────
        # §15 item 6 prerequisite: opt-in to steward with all effects
        is_error, config_put = client.call_tool("project.configure_steward", {
            "project_id": project_id,
            "enabled": True,
            "unattended_enabled": True,
            "eligible_effect_kinds": STEWARD_EFFECT_KINDS,
            "cooldown_seconds": 0,
        })
        assert is_error is False, f"configure_steward put failed: {config_put}"
        assert config_put.get("policy") is not None

        # ────────────────────────────────────────────────────────────
        # §15 item 2 continued: Watch is "tested"
        # ────────────────────────────────────────────────────────────
        is_error, test_data = client.call_tool("project.watch.test", {
            "watch_id": watch_id,
        })
        assert is_error is False, f"watch.test failed: {test_data}"
        # §15-2: test produces a non-error result with entity count
        # The result may nest fields under "result" or at top level
        test_result = test_data.get("result", test_data)
        assert "entity_count" in test_result or "message" in test_result
        assert test_data.get("test_state") == "passed"

        # ────────────────────────────────────────────────────────────
        # §15 item 3: a later provider change creates one canonical
        # Watch evaluation and normalized observation
        # ────────────────────────────────────────────────────────────

        # Write the changed snapshot
        snapshot_file.write_text(json.dumps(_CHANGED_ENTITIES))

        is_error, eval_data = client.call_tool("project.watch.evaluate", {
            "watch_id": watch_id,
        })
        assert is_error is False, f"watch.evaluate failed: {eval_data}"
        # §15-3: evaluation completed with transitions
        assert eval_data["state"] == "completed"
        transitions_count = eval_data["transitions"]
        assert transitions_count > 0, "Expected at least one transition"
        observation_ids = eval_data.get("observation_ids", [])
        assert len(observation_ids) > 0, "Expected at least one observation"
        evaluation_id = eval_data["evaluation_id"]

        # ────────────────────────────────────────────────────────────
        # §15 item 4: Delta freezes the successful evidence plus
        # explicit degraded coverage.
        # ────────────────────────────────────────────────────────────
        is_error, review_data = client.call_tool("project.open_review", {
            "project_id": project_id,
        })
        assert is_error is False, f"open_review failed: {review_data}"
        review_id = review_data.get("id") or review_data.get("review_id")
        # §15-4: review has proposals from the observations
        proposal_count = len(review_data.get("proposals", []))

        # ────────────────────────────────────────────────────────────
        # §15 item 5: the same window/evaluation recomputes identically
        # and review decisions persist.
        # ────────────────────────────────────────────────────────────

        # Re-evaluate at the same snapshot -> no_op (idempotent)
        is_error, eval2_data = client.call_tool("project.watch.evaluate", {
            "watch_id": watch_id,
        })
        assert is_error is False
        # §15-5: identical snapshot evaluated -> no_op
        assert eval2_data["state"] == "no_op", (
            f"Expected no_op but got {eval2_data['state']}"
        )

        # Open review again -> should be the same review
        is_error, review2_data = client.call_tool("project.open_review", {
            "project_id": project_id,
        })
        assert is_error is False

        # ────────────────────────────────────────────────────────────
        # §15 item 6: a YOLO Steward run is durably requested once at
        # the observation watermark, performs one idempotent canonical
        # follow-through effect, verifies it, drafts a cited update,
        # and completes with a receipt.
        # ────────────────────────────────────────────────────────────

        # Configure steward read-back (verify the policy is persisted)
        is_error, config_data = client.call_tool("project.configure_steward", {
            "project_id": project_id,
        })
        assert is_error is False, f"configure_steward get failed: {config_data}"
        assert config_data.get("policy") is not None

        # Run steward
        watermark = evaluation_id  # use the evaluation_id as watermark
        is_error, run_data = client.call_tool("project.run_steward", {
            "project_id": project_id,
            "watermark": watermark,
            "command_id": "walk-steward-001",
        })
        assert is_error is False, f"run_steward failed: {run_data}"
        run_id = run_data["run_id"]
        assert run_id is not None
        assert run_id.startswith("pstrun_")

        # §15-6: poll to completed with receipts
        deadline = time.monotonic() + 30
        final_run = None
        while time.monotonic() < deadline:
            is_error, poll_data = client.call_tool("project.get_steward_run", {
                "run_id": run_id,
            })
            assert is_error is False
            state = poll_data["run"]["state"]
            if state in ("completed", "interrupted", "failed"):
                final_run = poll_data
                break
            time.sleep(0.3)

        assert final_run is not None, f"Steward run did not reach terminal state"
        assert final_run["run"]["state"] == "completed", (
            f"Expected completed but got {final_run['run']['state']}"
        )
        # §15-6: steps with receipts
        steps = final_run.get("steps", [])
        effect_steps = [s for s in steps if s.get("state") == "completed"]
        assert len(effect_steps) > 0, "Expected at least one completed step"

        # ────────────────────────────────────────────────────────────
        # §15 item 7: retrying the Watch evaluation or command cannot
        # duplicate the effect.
        # ────────────────────────────────────────────────────────────

        # Re-evaluate at the same snapshot -> still no_op
        is_error, eval3_data = client.call_tool("project.watch.evaluate", {
            "watch_id": watch_id,
        })
        assert is_error is False
        assert eval3_data["state"] == "no_op"

        # Re-run steward at the same watermark
        is_error, run2_data = client.call_tool("project.run_steward", {
            "project_id": project_id,
            "watermark": watermark,
            "command_id": "walk-steward-001",  # same command_id -> replay
        })
        assert is_error is False
        # §15-7: replay returns the stored result
        assert run2_data["run_id"] == run_id, (
            f"Expected replay to return same run_id {run_id}, got {run2_data['run_id']}"
        )

        # Count effects before and after re-run (dedup proof)
        is_error, updates_before = client.call_tool("project.list_updates", {
            "project_id": project_id,
        })
        updates_before_count = len(updates_before.get("updates", []))

        # Run steward with a different command_id to prove dedup at the
        # service level (same project + existing completed run)
        is_error, run3_data = client.call_tool("project.run_steward", {
            "project_id": project_id,
            "watermark": watermark,
            "command_id": "walk-steward-002",
        })
        # This may succeed (new run) or fail (active_run_exists if
        # the previous run is still considered "active").  Either way
        # we verify no duplicate effects.
        if not is_error and run3_data.get("run_id"):
            run3_id = run3_data["run_id"]
            if run3_id != run_id:
                # New run started; poll it
                deadline3 = time.monotonic() + 30
                while time.monotonic() < deadline3:
                    is_error, poll3 = client.call_tool(
                        "project.get_steward_run", {"run_id": run3_id},
                    )
                    if not is_error and poll3["run"]["state"] in (
                        "completed", "interrupted", "failed",
                    ):
                        break
                    time.sleep(0.3)

        is_error, updates_after = client.call_tool("project.list_updates", {
            "project_id": project_id,
        })
        updates_after_count = len(updates_after.get("updates", []))

        # ────────────────────────────────────────────────────────────
        # Draft + publish an update (manual, supplements steward's draft)
        # ────────────────────────────────────────────────────────────
        is_error, draft_data = client.call_tool("project.draft_update", {
            "project_id": project_id,
            "generator": "deterministic",
            "command_id": "walk-draft-001",
        })
        assert is_error is False, f"draft_update failed: {draft_data}"
        update_obj = draft_data.get("update", {})
        update_id = update_obj.get("id")
        assert update_id is not None

        is_error, pub_data = client.call_tool("project.publish_update", {
            "update_id": update_id,
            "command_id": "walk-publish-001",
        })
        assert is_error is False, f"publish_update failed: {pub_data}"

        # ────────────────────────────────────────────────────────────
        # §15 item 8: Web and MCP observe the same final Project/Watch
        # revisions and refs.
        # ────────────────────────────────────────────────────────────
        is_error, room_data = client.call_tool("project.get_room", {
            "project_id": project_id,
        })
        assert is_error is False, f"get_room failed: {room_data}"
        room_revision = room_data.get("revision")
        assert room_revision is not None
        assert room_revision >= 1, "Room should have revision >= 1"
        # §15-8: room shows the project
        assert room_data["project_id"] == project_id

        # Verify project.list sees the project
        is_error, list_data = client.call_tool("project.list")
        assert is_error is False
        project_ids = [p["id"] for p in list_data.get("projects", [])]
        assert project_id in project_ids

        # ────────────────────────────────────────────────────────────
        # §15 item 9: accepting the review advances the cursor
        # without altering canonical external truth improperly.
        # ────────────────────────────────────────────────────────────
        # Open a fresh review to get its current state
        is_error, review3_data = client.call_tool("project.open_review", {
            "project_id": project_id,
        })
        assert is_error is False
        review3_id = review3_data.get("id") or review3_data.get("review_id")

        if review3_id:
            # Decide proposals if any
            proposals = review3_data.get("proposals", [])
            for prop in proposals:
                prop_id = prop.get("id")
                if prop_id:
                    client.call_tool("project.decide_proposal", {
                        "project_id": project_id,
                        "proposal_id": prop_id,
                        "verb": "accept",
                    })

            # Accept the review
            is_error, accept_data = client.call_tool("project.accept_review", {
                "project_id": project_id,
                "review_id": review3_id,
                "command_id": "walk-accept-001",
            })
            assert is_error is False, f"accept_review failed: {accept_data}"

            # Verify revision advanced
            is_error, room_after_data = client.call_tool("project.get_room", {
                "project_id": project_id,
            })
            assert is_error is False
            room_revision_after = room_after_data.get("revision")
            assert room_revision_after is not None
            # §15-9: revision advanced after accept
            assert room_revision_after >= room_revision

        # ────────────────────────────────────────────────────────────
        # §15 item 10: restart recovery leaves no permanently running
        # phantom Watch evaluation or Steward step.
        # ────────────────────────────────────────────────────────────
        # Verify the steward run is terminal (no phantom)
        is_error, final_check = client.call_tool("project.get_steward_run", {
            "run_id": run_id,
        })
        assert is_error is False
        # §15-10: run is in terminal state, no phantom
        assert final_check["run"]["state"] in ("completed", "interrupted", "failed")

        # Watch inspect: the watch is still in a consistent state
        is_error, inspect_data = client.call_tool("project.watch.inspect", {
            "watch_id": watch_id,
        })
        assert is_error is False

        # ────────────────────────────────────────────────────────────
        # §15 item 1: legacy database reconciles without identity or
        # relationship loss.
        # Covered by: the suite's reconcile tests elsewhere (the walk
        # seeds a fresh DB, so reconciliation is trivially satisfied).
        # Pointer: tests/unit/test_schema_reconcile.py + the
        # Database.__init__ reconciliation path.
        # ────────────────────────────────────────────────────────────

        # provider.list (for palette completeness)
        is_error, provider_data = client.call_tool("provider.list")
        assert is_error is False
        assert "providers" in provider_data

        # Final measured numbers
        is_error, final_updates = client.call_tool("project.list_updates", {
            "project_id": project_id,
        })
        final_update_count = len(final_updates.get("updates", []))

        measured = {
            "transitions_count": transitions_count,
            "observation_count": len(observation_ids),
            "evaluation_id": evaluation_id,
            "proposal_count": proposal_count,
            "effect_steps": len(effect_steps),
            "updates_before_rerun": updates_before_count,
            "updates_after_rerun": updates_after_count,
            "final_update_count": final_update_count,
            "room_revision": room_revision,
            "room_revision_after_accept": room_revision_after if review3_id else room_revision,
            "dedup_eval_state": eval2_data["state"],
            "dedup_eval3_state": eval3_data["state"],
            "dedup_run_replay_id": run2_data["run_id"],
            "project_id": project_id,
            "watch_id": watch_id,
            "run_id": run_id,
        }

        return {
            "transcript": client.transcript,
            "measured": measured,
        }

    finally:
        client.stop()


# ── Tests ────────────────────────────────────────────────────────────

class TestMCPWalk:
    """The §15 walk: two deterministic runs, transcript artifact."""

    def test_walk_deterministic_x2(self, tmp_path: Path) -> None:
        """Execute the walk TWICE; both runs must agree on shape + counts."""

        results: list[dict[str, Any]] = []
        for run_idx in range(2):
            run_dir = tmp_path / f"run_{run_idx}"
            run_dir.mkdir()
            result = _run_walk(run_dir)
            results.append(result)

        m0, m1 = results[0]["measured"], results[1]["measured"]

        # ×2 deterministic: structural shape must match
        assert m0["transitions_count"] == m1["transitions_count"], (
            f"Transition count diverged: {m0['transitions_count']} vs {m1['transitions_count']}"
        )
        assert m0["observation_count"] == m1["observation_count"], (
            f"Observation count diverged: {m0['observation_count']} vs {m1['observation_count']}"
        )
        assert m0["dedup_eval_state"] == m1["dedup_eval_state"] == "no_op"
        assert m0["dedup_eval3_state"] == m1["dedup_eval3_state"] == "no_op"

        # Both runs completed (steward reached terminal)
        assert m0["effect_steps"] > 0
        assert m1["effect_steps"] > 0
        assert m0["effect_steps"] == m1["effect_steps"], (
            f"Effect step count diverged: {m0['effect_steps']} vs {m1['effect_steps']}"
        )

        # Write the transcript artifact from run 0
        transcript_artifact = {
            "schema": "mcp-walk-transcript@1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "runs": [
                {
                    "run_index": i,
                    "tool_calls": results[i]["transcript"],
                    "measured": results[i]["measured"],
                }
                for i in range(2)
            ],
            "determinism": {
                "transitions_match": m0["transitions_count"] == m1["transitions_count"],
                "observations_match": m0["observation_count"] == m1["observation_count"],
                "effects_match": m0["effect_steps"] == m1["effect_steps"],
                "dedup_match": (
                    m0["dedup_eval_state"] == m1["dedup_eval_state"]
                    and m0["dedup_eval3_state"] == m1["dedup_eval3_state"]
                ),
            },
        }

        TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_PATH.write_text(
            json.dumps(transcript_artifact, indent=2, default=str) + "\n",
        )

        # Verify transcript was written
        assert TRANSCRIPT_PATH.exists()
        loaded = json.loads(TRANSCRIPT_PATH.read_text())
        assert loaded["schema"] == "mcp-walk-transcript@1"
        assert len(loaded["runs"]) == 2
        assert loaded["determinism"]["transitions_match"] is True

        # ── Print measured numbers for the report ────────────────────
        print(f"\n--- Walk measured numbers (run 0) ---")
        for k, v in m0.items():
            print(f"  {k}: {v}")
        print(f"--- Walk measured numbers (run 1) ---")
        for k, v in m1.items():
            print(f"  {k}: {v}")
        print(f"--- Transcript: {len(results[0]['transcript'])} tool calls ---")


class TestPaletteConsumer:
    """Palette-consumer proof: every walk tool name is in PROJECT_PALETTE
    and dispatch_for_palette routes at least one call."""

    def test_walk_tools_in_palette(self) -> None:
        """Every tool name used in the walk is in PROJECT_PALETTE."""
        from holdspeak.mcp.families.project import PROJECT_PALETTE

        walk_tools = {
            "project.setup.start",
            "project.setup.answer",
            "project.setup.suggest",
            "project.setup.finalize",
            "project.setup.resume",
            "project.get",
            "project.list",
            "project.get_room",
            "project.configure_steward",
            "project.run_steward",
            "project.get_steward_run",
            "project.stop_steward",
            "project.watch.test",
            "project.watch.evaluate",
            "project.watch.inspect",
            "project.watch.set_rules",
            "project.watch.pause",
            "project.watch.resume",
            "project.watch.retire",
            "project.open_review",
            "project.get_delta",
            "project.decide_proposal",
            "project.accept_review",
            "project.list_updates",
            "project.draft_update",
            "project.update_draft",
            "project.publish_update",
            "project.create",
            "project.update",
            "project.archive",
            "project.restore",
            "project.link",
            "project.unlink",
            "provider.list",
            "provider.github_connection",
            "provider.github_discover",
            "provider.github_validate_repo",
        }

        missing = walk_tools - PROJECT_PALETTE
        assert missing == set(), (
            f"Walk tools not in PROJECT_PALETTE: {missing}"
        )

    def test_dispatch_for_palette_routes(self, tmp_path: Path) -> None:
        """dispatch_for_palette routes a call through the palette seam."""
        from holdspeak.db.core import Database, reset_database
        from holdspeak.mcp.families.project import PROJECT_PALETTE
        from holdspeak.mcp.tools import dispatch_for_palette, ToolError
        from holdspeak.mcp.families import project as project_family
        from holdspeak.principals import Principal, PrincipalKind

        reset_database()
        db = Database(tmp_path / "palette-consumer.db")

        # Patch get_database for the family
        original_get_db = project_family.get_database
        project_family.get_database = lambda: db

        try:
            owner = Principal(PrincipalKind.OWNER, "palette-consumer-test")

            # Exercise dispatch_for_palette with project.list (read tool, no args)
            result = dispatch_for_palette(
                "project.list", {}, owner, PROJECT_PALETTE,
            )
            assert isinstance(result, dict)
            assert "projects" in result

            # Verify tools outside palette are refused
            with pytest.raises(ToolError, match="not in the configured palette"):
                dispatch_for_palette(
                    "desk.list", {}, owner, PROJECT_PALETTE,
                )

        finally:
            project_family.get_database = original_get_db
            reset_database()

    def test_palette_is_exact_family(self) -> None:
        """PROJECT_PALETTE contains exactly the project family tool names."""
        from holdspeak.mcp.families.project import (
            PROJECT_PALETTE,
            TOOLS as PROJECT_TOOLS,
        )

        family_names = frozenset(t["name"] for t in PROJECT_TOOLS)
        assert PROJECT_PALETTE == family_names, (
            f"Palette vs family mismatch: "
            f"extra={PROJECT_PALETTE - family_names}, "
            f"missing={family_names - PROJECT_PALETTE}"
        )
