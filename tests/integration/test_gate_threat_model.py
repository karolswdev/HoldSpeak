"""HS-104-03 — the gate under attack: the hostile checklist, each item
a pinned test that bites on the naive design.

Items 1 and 6 use a REAL hub process (spawned, killed with SIGKILL,
restarted) — the two-process proof pattern from Phase 89/94, never a
mock. The rest attack the state machine and the hook through the
same seams an attacker on loopback would use.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from holdspeak.coder_gate import GateConfig, HookDecision, run_hook

REPO = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class RealHub:
    """A real ``holdspeak web`` process on an isolated HOME."""

    def __init__(self, tmp_path: Path) -> None:
        self.home = tmp_path / "hub-home"
        self.home.mkdir(parents=True, exist_ok=True)
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen | None = None
        self.owner_token = ""
        self.agent_token = ""

    def start(self, timeout: float = 60.0) -> None:
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
            cwd=str(REPO),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{self.base}/health", timeout=1):
                    config = json.loads(
                        (self.home / ".config" / "holdspeak" / "config.json").read_text()
                    )
                    self.owner_token = config["meeting"]["web_auth_token"]
                    status, issued = self._post_with_token(
                        "/api/principals/agents",
                        {"identity": "claude:threat-session"},
                        self.owner_token,
                    )
                    if status == 201:
                        self.agent_token = issued["credential"]
                        return
            except Exception:
                time.sleep(0.3)
        raise RuntimeError("hub did not come up")

    def kill_hard(self) -> None:
        """SIGKILL — the real crash, not a graceful stop."""
        assert self.proc is not None
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=10)
        self.proc = None

    def stop(self) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None

    def get(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    def _post_with_token(
        self, path: str, body: dict, token: str
    ) -> tuple[int, dict]:
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode() or "{}")

    def post(self, path: str, body: dict) -> tuple[int, dict]:
        token = self.agent_token if path == "/api/gate/proposals" else self.owner_token
        return self._post_with_token(path, body, token)


def _payload(cwd: str, key: str = "threat-1") -> dict:
    return {
        "session_id": "threat-session",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf build"},
        "cwd": cwd,
        "tool_use_id": key,
    }


def _armed(cwd: str) -> GateConfig:
    return GateConfig(armed=True, repos={cwd: ["Bash"]})


@pytest.mark.integration
def test_item1_and_6_restart_mid_hold_and_fail_closed_two_process(tmp_path) -> None:
    """Checklist 1 + 6, one continuous two-process run: the hub dies
    with a proposal held (SIGKILL, a real crash) — the polling hook
    DENIES; on restart the proposal is invalidated with an audit row
    and no longer renders as held."""
    hub = RealHub(tmp_path)
    hub.start()
    try:
        result: dict = {}

        def agent_side() -> None:
            result["decision"] = run_hook(
                _payload(str(tmp_path)),
                config=_armed(str(tmp_path)),
                hub_url=hub.base,
                ttl_seconds=60.0,
                agent_credential=hub.agent_token,
            )

        thread = threading.Thread(target=agent_side)
        thread.start()

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            held = hub.get("/api/gate/proposals?state=held")["proposals"]
            if held:
                break
            time.sleep(0.3)
        assert held and held[0]["id"] == "threat-1"

        hub.kill_hard()  # the crash, mid-hold

        thread.join(timeout=30)
        assert not thread.is_alive()
        decision: HookDecision = result["decision"]
        # Item 6: no code path allows on error.
        assert decision.deny is not None
        assert any(
            marker in decision.deny
            for marker in ("stopped answering", "unreachable", "decision read failed")
        )

        hub.start()  # the restart
        # Item 1: invalidated, audited, not decidable, not rendered held.
        proposal = hub.get("/api/gate/proposals/threat-1")
        assert proposal["state"] == "invalidated"
        assert "restarted" in (proposal["reason"] or "")
        events = [e["event"] for e in hub.get("/api/gate/audit")["entries"]]
        assert "invalidated" in events
        assert hub.get("/api/gate/proposals?state=held")["proposals"] == []
        status, _ = hub.post(
            "/api/gate/proposals/threat-1/decide", {"decision": "approved"}
        )
        assert status == 409  # nothing held pre-restart is decidable post-restart
    finally:
        hub.stop()


@pytest.mark.integration
def test_item2_replay_of_a_decided_proposal_real_http(tmp_path) -> None:
    """Checklist 2: an attacker on loopback re-POSTs an approved key —
    the hub returns the terminal state, mints nothing, and the audit
    shows one decision, two arrivals."""
    hub = RealHub(tmp_path)
    hub.start()
    try:
        body = {
            "id": "replay-1",
            "session_key": "claude:threat",
            "agent": "claude",
            "tool": "Bash",
            "args_sha256": "a" * 64,
            "args_head": "{}",
            "cwd": str(tmp_path),
            "ttl_seconds": 60,
        }
        status, first = hub.post("/api/gate/proposals", body)
        assert status == 200 and first["state"] == "held"
        hub.post("/api/gate/proposals/replay-1/decide", {"decision": "approved"})

        status, replay = hub.post("/api/gate/proposals", body)
        assert status == 200
        assert replay["state"] == "approved"  # terminal state served, no twin
        events = [e["event"] for e in hub.get("/api/gate/audit")["entries"]]
        assert events.count("approved") == 1
        assert events.count("re_arrival") == 1
        assert events.count("proposed") == 1
    finally:
        hub.stop()


@pytest.mark.integration
def test_item3_toctou_args_swap_refused_and_original_revoked(tmp_path) -> None:
    """Checklist 3: same key, different args hash — refused by name,
    the original invalidated, audit written. The human's Approve can
    never land on a payload the human never saw."""
    hub = RealHub(tmp_path)
    hub.start()
    try:
        body = {
            "id": "toctou-1",
            "session_key": "claude:threat",
            "agent": "claude",
            "tool": "Bash",
            "args_sha256": "a" * 64,
            "args_head": '{"command":"ls"}',
            "cwd": str(tmp_path),
            "ttl_seconds": 60,
        }
        hub.post("/api/gate/proposals", body)
        swapped = dict(body, args_sha256="b" * 64, args_head='{"command":"rm -rf /"}')
        status, response = hub.post("/api/gate/proposals", swapped)
        assert status == 409
        assert response["error"] == "args_mismatch"
        original = hub.get("/api/gate/proposals/toctou-1")
        assert original["state"] == "invalidated"  # refuse AND revoke
        # And the head the human WOULD have seen is still the original.
        assert original["args_head"] == '{"command":"ls"}'
        status, _ = hub.post("/api/gate/proposals/toctou-1/decide", {"decision": "approved"})
        assert status == 409  # nothing left to aim an Approve at
        events = [e["event"] for e in hub.get("/api/gate/audit")["entries"]]
        assert "args_mismatch" in events and "invalidated" in events
    finally:
        hub.stop()


def test_item7_unarmed_inertness_latency_budget(tmp_path) -> None:
    """Checklist 7: gate off — no proposal row, no audit row, no hub
    contact, and a pinned (generous) latency budget for the in-process
    fast path."""
    calls: list[str] = []

    def post(url, body, timeout):
        calls.append(url)
        return 200, {}

    started = time.perf_counter()
    decision = run_hook(
        _payload(str(tmp_path)),
        config=GateConfig(),
        http_post=post,
        http_get=lambda url, timeout: (200, {}),
    )
    elapsed = time.perf_counter() - started
    assert decision.deny is None
    assert calls == []
    assert elapsed < 0.25  # generous; the fast path is pure dict/path work


def test_item8_redaction_grep_census_over_the_gate_modules() -> None:
    """Checklist 8: no full-argument payload anywhere — the hub-side
    gate modules never name the full-payload fields, and the hook
    posts only the digest + bounded head."""
    for rel in ("holdspeak/db/gate.py", "holdspeak/web/routes/system/gate_routes.py"):
        code = "\n".join(
            line
            for line in (REPO / rel).read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        )
        assert "tool_input" not in code, f"{rel} touches the full payload"

    hook_src = (REPO / "holdspeak/coder_gate.py").read_text(encoding="utf-8")
    body_block = hook_src[hook_src.index("body = {") : hook_src.index("# Fail-closed")]
    assert "args_sha256" in body_block and "args_head" in body_block
    assert "tool_input" not in body_block  # the wire carries the redaction only


# Items 4 (expiry race, injectable clock) and 5 (double decision,
# first write wins) are pinned in tests/unit/test_coder_gate.py
# (test_expiry_race_exactly_one_terminal_state,
# test_double_decision_refused_with_standing_state,
# test_route_double_decision_409_names_standing). This module records
# their place in the checklist so the eight items read in one place.
def test_items4_and_5_are_pinned_in_the_unit_suite() -> None:
    text = (REPO / "tests/unit/test_coder_gate.py").read_text(encoding="utf-8")
    for name in (
        "test_expiry_race_exactly_one_terminal_state",
        "test_double_decision_refused_with_standing_state",
        "test_route_double_decision_409_names_standing",
    ):
        assert f"def {name}" in text
