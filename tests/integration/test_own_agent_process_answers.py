"""The real process-input half of the moved own-agent browser walk.

The current Agents face is covered by agentsOwn.app.test.tsx; no native
browser gesture is involved in discovering and answering this private pane.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from tests.own_agents_rig import _start_fake, _wait_for_pane
from tests.unit.test_philo9_b1_connections import CountingRunner, _boot


def test_owner_started_process_receives_answer_and_permission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env, home = _start_fake(tmp_path, monkeypatch)
    hub = _boot(tmp_path, monkeypatch, CountingRunner(), CountingRunner())
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "on")

    def read(path: str) -> Any:
        answer = hub.client.get(path)
        assert answer.status_code == 200, answer.text
        return answer.json()

    def current(state: str) -> dict[str, Any]:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            result = read("/api/coders/own-agents")
            if any(row["screen"]["state"] == state for row in result["agents"]):
                return result
            time.sleep(0.1)
        raise AssertionError(f"private process did not reach {state}: {result}")

    try:
        captured_at = time.time()
        sessions = read("/api/coders/sessions?include_ended=false")
        detect = read("/api/onboarding/agents")
        asking = current("asks")
        agent = next(row for row in asking["agents"] if row["screen"]["state"] == "asks")
        assert "I found two places for the rollback flag" in json.dumps(agent)
        answer_body = {"pane_id": agent["pane_id"], "since": agent["screen"]["since"], "text": "config"}
        answered = hub.client.post("/api/coders/own-agents/answer", json=answer_body)
        assert answered.status_code == 200, answered.text
        _wait_for_pane(env, "Do you want to proceed?", 30)
        log = Path(home) / "fake-agent.log"
        assert "ANSWER RECEIVED: 'config'" in log.read_text()
        held = current("approve")
        agent = next(row for row in held["agents"] if row["screen"]["state"] == "approve")
        allow_body = {"pane_id": agent["pane_id"], "since": agent["screen"]["since"], "keys": ["Enter"]}
        allowed = hub.client.post("/api/coders/own-agents/answer", json=allow_body)
        assert allowed.status_code == 200, allowed.text
        deadline = time.monotonic() + 20
        while "PERMISSION KEY RECEIVED" not in log.read_text() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert "PERMISSION KEY RECEIVED" in log.read_text()
        if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
            path = Path(__file__).parents[2] / "web/src/desk/__tests__/fixtures/agents-own-process.json"
            path.write_text(json.dumps({"_source": f"{__file__}::test_owner_started_process_receives_answer_and_permission; HOLDSPEAK_WIRE_WRITE=1", "captured_at": captured_at, "sessions": sessions, "detect": detect, "asking": asking, "held": held, "answer_body": answer_body, "answered": answered.json(), "allow_body": allow_body, "allowed": allowed.json()}, indent=2) + "\n")
    finally:
        hub.client.close()
        subprocess.run(["tmux", "-f", "/dev/null", "kill-server"], env=env, check=False, capture_output=True, text=True)
