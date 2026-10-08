"""PHILO-15 20: YOLO lets the agent read; Raw approves a cut call (B62, B63,
B66), through the REAL hook (``coder_gate.run_hook`` over HTTP) and a REAL hub
process (``holdspeak web`` on an isolated HOME), seeded as in lane 15.

B62: the exact commands YOLO held in rehearsal 2 (BOUNCES-C) now pass; a
config write, a push to another branch and a script outside the worktree
still wait. B63: a cut held call is read whole by the owner (only) and
approved there. B66: a Deny names the hold's reason to the agent.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from tests.integration.test_gate_threat_model import RealHub
from tests.integration.test_philo15_15_yolo_real_hub import _hook, _proposal, hub  # noqa: F401  (the fixture)

#: The calls YOLO held in rehearsal 2 (BOUNCES-C B62), word for word.
B62_READS = [
    "git config user.name; git config user.email",
    "command -v gh && gh --version",
    'bash tests/codeowners_test.sh; echo "exit=$?"',
    'git status --short && echo "HEAD=$(git rev-parse HEAD)"',
    "gh auth status",
    "gh pr view 4",
]


def _get_with_token(hub: RealHub, path: str, token: str) -> tuple[int, dict]:
    req = urllib.request.Request(f"{hub.base}{path}", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


@pytest.mark.parametrize("command", B62_READS)
def test_yolo_passes_the_agents_reads_and_its_own_test_run(hub: RealHub, command: str) -> None:
    key = f"toolu_read_{B62_READS.index(command)}"
    passed = _hook(hub, command, key)
    assert passed.deny is None, passed.deny
    approved = _proposal(hub, key)
    assert approved["state"] == "approved" and approved["decided_by"] == "control-mode"
    assert approved["operation"]["tool_call"]["scope"] == "inside"


@pytest.mark.parametrize(("command", "reason"), [
    ("git config user.name Bob", "SHARED GIT STATE"),
    ("git config --unset user.email", "SHARED GIT STATE"),
    ("git push origin other-branch", "PUSH TO ANOTHER BRANCH · other-branch"),
    ("bash /tmp/hs_outside_script.sh", "OUTSIDE THE WORKTREE · /tmp/hs_outside_script.sh"),
    ('echo "HEAD=$(git rev-parse HEAD)" > /tmp/hs_head.txt', "OUTSIDE THE WORKTREE · /tmp/hs_head.txt"),
    ('cat "$(git rev-parse --show-toplevel)/../x"', "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
])
def test_yolo_still_holds_writes_pushes_and_the_outside(hub: RealHub, command: str, reason: str) -> None:
    key = "toolu_hold_" + "".join(ch if ch.isalnum() else "_" for ch in command)[:48]
    held = _hook(hub, command, key, ttl=2.0)
    assert held.deny and "expired" in held.deny  # it waited; nobody approved it
    assert _proposal(hub, key)["hold_reason"] == reason


def _held_in_thread(hub: RealHub, command: str, key: str, ttl: float = 30.0):
    box: dict = {}
    thread = threading.Thread(target=lambda: box.update(decision=_hook(hub, command, key, ttl=ttl)))
    thread.start()
    for _ in range(100):
        listed = hub.get("/api/gate/proposals?state=held").get("proposals", [])
        if any(p["id"] == key for p in listed):
            break
        threading.Event().wait(0.1)
    else:
        raise AssertionError("the call never held")
    return thread, box


def test_raw_reads_a_cut_call_whole_and_approves_it(hub: RealHub) -> None:
    """B63: the hook sends the whole REDACTED call of a cut hold; the owner
    reads it whole (the agent may not), approves it there, and the hub drops
    it once decided."""
    secret = "sk-proj-abcdefghijklmnopqrstuvwxyz0123"
    tail = "TAIL-MARK-past-the-head"
    command = (
        f"OPENAI_API_KEY={secret} cat > /tmp/hs_raw_probe.txt <<'EOF'\n"
        + "line of the body that is long enough to cut the head\n" * 3
        + f"{tail}\nEOF"
    )
    thread, box = _held_in_thread(hub, command, "toolu_cut")
    listed = _proposal(hub, "toolu_cut")
    assert listed["args_cut"] is True and tail not in json.dumps(listed)

    whole = hub.get("/api/gate/proposals/toolu_cut/command")
    assert whole["whole"] is True and whole["state"] == "held"
    assert tail in whole["command"] and whole["command"].endswith("EOF")
    assert secret not in whole["command"], "redacted of secret shapes"
    assert whole["hold_reason"].startswith("OUTSIDE THE WORKTREE")

    status, body = _get_with_token(hub, "/api/gate/proposals/toolu_cut/command", hub.agent_token)
    assert status == 403, body
    status, body = _get_with_token(hub, "/api/gate/proposals/toolu_cut", hub.agent_token)
    assert status == 200 and tail not in json.dumps(body), "the agent's read never carries the whole call"

    status, decided = hub._post_with_token(
        "/api/gate/proposals/toolu_cut/decide", {"decision": "approved"}, hub.owner_token,
    )
    assert status == 200 and decided["state"] == "approved", decided
    thread.join(timeout=10)
    assert box["decision"].deny is None
    status, gone = _get_with_token(hub, "/api/gate/proposals/toolu_cut/command", hub.owner_token)
    assert status == 409 and gone["error"] == "not_held"


def test_a_deny_from_the_desk_names_the_reason_to_the_agent(hub: RealHub) -> None:
    """B66: the agent reads why (OUTSIDE THE WORKTREE · <path>) and that the
    owner decided, so it does not try the write another way."""
    thread, box = _held_in_thread(hub, "cat > /tmp/pr_body.md <<'EOF'\nbody\nEOF", "toolu_deny")
    status, decided = hub._post_with_token(
        "/api/gate/proposals/toolu_deny/decide", {"decision": "denied"}, hub.owner_token,
    )
    assert status == 200 and decided["reason"] == "OUTSIDE THE WORKTREE · /tmp/pr_body.md", decided
    thread.join(timeout=10)
    deny = box["decision"].deny
    assert deny.startswith("denied from the desk: OUTSIDE THE WORKTREE · /tmp/pr_body.md")
    assert "Do not try it again in a different form." in deny


def test_take_back_discards_a_queued_rebrief_with_a_receipt(hub: RealHub) -> None:
    """B67, through the real hub's route: the owner takes a queued Re-brief
    back (TAKEN BACK receipt, queue empty); a second press and an agent's
    press change nothing."""
    ledger = hub.home / ".holdspeak" / "agent_launches.json"
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    press = {"id": "press-b67", "text": "Re-brief: do not write outside the worktree.", "at": "2026-10-07T21:30:00Z",
             "key": "codex:yolo-session", "approval": {"principal": {"kind": "owner", "identity": "owner-session"},
                                                       "at": "2026-10-07T21:30:00Z", "command_id": "press-b67"}}
    doc["launches"][0]["queued_rebriefs"] = [press]
    ledger.write_text(json.dumps(doc), encoding="utf-8")
    route = "/api/agent/launches/launch-yolo/rebrief/press-b67/take-back"

    status, body = hub._post_with_token(route, {}, hub.agent_token)
    assert status == 403, body
    status, body = hub._post_with_token(route, {}, hub.owner_token)
    assert status == 200 and body["status"] == "taken_back", body
    assert body["receipt"]["state"] == "taken_back" and body["receipt"]["detail"] == "BY YOU"
    record = json.loads(ledger.read_text(encoding="utf-8"))["launches"][0]
    assert record["queued_rebriefs"] == []
    assert [r["state"] for r in record["rebriefs"]] == ["taken_back"]
    status, body = hub._post_with_token(route, {}, hub.owner_token)
    assert status == 409 and body["status"] == "not_queued"
