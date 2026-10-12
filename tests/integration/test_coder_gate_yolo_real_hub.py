"""PHILO-15 15 (B43): YOLO passes a here-document write in the agent's own
worktree and holds a ``/tmp`` write with its reason, through the REAL hook
(``coder_gate.run_hook`` over HTTP) and a REAL hub process (``holdspeak web``
on an isolated HOME; ``RealHub`` from the HS-104-03 threat model).

The launch is seeded the way a Hand to agent leaves it once its session
registered: the worktree in the delivery registry and a ``registered``
record in the launch ledger whose session key is the agent's credential.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from holdspeak.coder_gate import GateConfig, run_hook
from tests.integration.test_gate_threat_model import RealHub
import threading
import urllib.error
import urllib.request

SESSION = "yolo-session"
IDENTITY = f"codex:{SESSION}"
BRANCH = "hs/action-yolo"


@pytest.fixture
def hub(tmp_path: Path):
    worktree = tmp_path / "wt"
    (worktree / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", BRANCH, str(worktree)], check=True)
    worktree = worktree.resolve()
    real = RealHub(tmp_path)
    state = real.home / ".holdspeak"
    state.mkdir(parents=True)
    from holdspeak.delivery.factory_launch import LAUNCHES_SCHEMA
    from holdspeak.delivery.registry import DeliveryRegistry

    source, wt = DeliveryRegistry(path=state / "delivery_sources.json").register(str(worktree))
    (state / "agent_launches.json").write_text(json.dumps({
        "launches_schema": LAUNCHES_SCHEMA,
        "launches": [{
            "launch_id": "launch-yolo", "state": "registered", "session_key": IDENTITY,
            "source_id": source.source_id, "worktree_id": wt.worktree_id, "branch": BRANCH,
            "profile_id": "codex", "control_mode": "yolo",
        }],
    }), encoding="utf-8")
    real.start(issue_agent=False)
    status, issued = real._post_with_token("/api/principals/agents", {"identity": IDENTITY}, real.owner_token)
    assert status == 201, issued
    real.agent_token = issued["credential"]
    real.worktree = worktree
    try:
        yield real
    finally:
        real.stop()


def _hook(hub: RealHub, command: str, key: str, *, ttl: float = 3.0):
    payload = {
        "session_id": SESSION, "tool_name": "Bash", "tool_use_id": key,
        "tool_input": {"command": command}, "cwd": str(hub.worktree),
    }
    config = GateConfig(armed=True, repos={str(hub.worktree): ["Bash"]}, armed_paths=[str(hub.worktree)])
    return run_hook(
        payload, config=config, hub_url=hub.base, agent_credential=hub.agent_token,
        agent="codex", ttl_seconds=ttl,
    )


def _proposal(hub: RealHub, key: str) -> dict:
    for state in ("approved", "held", "denied", "expired"):
        for proposal in hub.get(f"/api/gate/proposals?state={state}").get("proposals", []):
            if proposal["id"] == key:
                return proposal
    raise AssertionError(f"no proposal {key}")


def test_a_heredoc_in_the_worktree_passes_and_a_tmp_write_waits_with_its_reason(hub: RealHub) -> None:
    write = "cat > CONTRIBUTING.md <<'EOF'\n# Contributing\n\n1. Branch from `main`.\nEOF"
    passed = _hook(hub, write, "toolu_heredoc")
    assert passed.deny is None, passed.deny
    approved = _proposal(hub, "toolu_heredoc")
    assert approved["state"] == "approved" and approved["decided_by"] == "control-mode"
    assert approved["operation"]["tool_call"]["scope"] == "inside"

    probe = 'echo "test write" > /tmp/hs_write_probe.txt && cat /tmp/hs_write_probe.txt'
    held = _hook(hub, probe, "toolu_tmp", ttl=2.0)
    assert held.deny and "expired" in held.deny  # it waited; nobody approved it
    proposal = _proposal(hub, "toolu_tmp")
    assert proposal["operation"]["tool_call"]["scope"] == "outside"
    assert proposal["hold_reason"] == "OUTSIDE THE WORKTREE · /tmp/hs_write_probe.txt"


def test_a_heredoc_pipe_and_an_unresolved_cd_wait_with_their_reasons(hub: RealHub) -> None:
    """Astra r1 on #998: both escapes, through the real hook and hub."""
    pipe = "tee local.py <<'EOF' | python3\nopen('../outside-pipe', 'w').write('review')\nEOF"
    assert "expired" in (_hook(hub, pipe, "toolu_pipe", ttl=2.0).deny or "")
    assert _proposal(hub, "toolu_pipe")["hold_reason"] == "RUNS CODE · python3"
    cd = "cd missing || cat > ../outside <<'EOF'\nx\nEOF"
    assert "expired" in (_hook(hub, cd, "toolu_cd", ttl=2.0).deny or "")
    assert _proposal(hub, "toolu_cd")["hold_reason"] == "FOLDER NOT RESOLVED · missing"
    assert not (hub.worktree.parent / "outside-pipe").exists()
    assert not (hub.worktree.parent / "outside").exists()


def test_a_target_the_head_does_not_show_is_never_stored(hub: RealHub) -> None:
    """A hook that sends a word past the 120-char head (or one redaction
    changed): the hub drops it before the store and the shown reason."""
    from holdspeak.coder_gate import redact_call

    secret = "ExampleCredential-k3y9Q"
    command = "echo " + "pad " * 40 + f"> /tmp/{secret}.txt"
    call = redact_call({"command": command})
    status, body = hub._post_with_token("/api/gate/proposals", {
        "id": "toolu_forged", "tool": "Bash", "args_sha256": call.sha256, "args_head": call.head,
        "args_len": call.length, "cwd": str(hub.worktree), "ttl_seconds": 60,
        "classification": {"scope": "outside", "rule": "redirect_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": str(hub.worktree), "proposal_id": "toolu_forged",
                           "args_sha256": call.sha256, "target": f"/tmp/{secret}.txt"},
    }, hub.agent_token)
    assert status == 200, body
    stored = _proposal(hub, "toolu_forged")
    assert secret not in json.dumps(stored), "not in the stored operation, the head or the reason"
    assert stored["hold_reason"] == "OUTSIDE THE WORKTREE"



def test_a_branch_past_the_head_is_never_the_target(hub: RealHub) -> None:
    """Astra r2 on #998 (P1-b): the hub's own override (another branch) is
    filtered too: a branch name past char 120 is omitted, never stored."""
    branch = "other-ExampleCredential-k3y9Q"
    command = "PAD=" + "p" * 130 + f" git push origin {branch}"
    held = _hook(hub, command, "toolu_push_pad", ttl=2.0)
    assert "expired" in (held.deny or "")
    stored = _proposal(hub, "toolu_push_pad")
    assert stored["operation"]["tool_call"]["rule"] == "git_push_other_branch"
    assert branch not in json.dumps(stored), "not in the stored operation, the head or the reason"
    assert stored["hold_reason"] == "PUSH TO ANOTHER BRANCH"
    assert stored["args_cut"] is True  # CUT: Deny + Open (Raw)


#: Astra's probes on #998 (her lock timed out at 300 s, so none ran): three
#: secrets of shapes redaction does not know, past char 120, and four escapes.
PAD = "# " + "padding " * 16 + "\n"
SECRET_PROBES = [
    ("toolu_p_env", f"cat > /tmp/review.env <<'EOF'\n{PAD}SESSION_COOKIE=review-only.synthetic-credential\nEOF",
     "review-only.synthetic-credential"),
    ("toolu_p_bearer", f"cat > /tmp/review.http <<'EOF'\n{PAD}Authorization: Bearer ExampleCredentialZz9\nEOF",
     "ExampleCredentialZz9"),
    # Astra's shape: the head redacts it; the target must not keep it whole.
    ("toolu_p_target", "cat > notes.md <<EOF\nsk-reviewSynthetic0123456789abcdefABCD$SUFFIX\nEOF",
     "reviewSynthetic0123456789abcdefABCD"),
]
ESCAPE_PROBES = [
    ("toolu_e_pipe", "tee local.py <<'EOF' | python3\nopen('../outside-pipe', 'w').write('review')\nEOF", "outside-pipe"),
    ("toolu_e_cd", "cd missing || cat > ../outside-cd <<'EOF'\nx\nEOF", "outside-cd"),
    ("toolu_e_env", "cat local.py | env python3", "outside-env"),
    ("toolu_e_link", "cat > out/outside-link <<'EOF'\nx\nEOF", "outside-link"),
]


@pytest.mark.parametrize("key, command, secret", SECRET_PROBES, ids=[k for k, _c, _s in SECRET_PROBES])
def test_astra_secret_probes(hub: RealHub, key: str, command: str, secret: str) -> None:
    held = _hook(hub, command, key, ttl=2.0)
    assert "expired" in (held.deny or "")
    stored = _proposal(hub, key)
    assert secret not in json.dumps(stored), "not in args_head, operation.tool_call.target or the reason"


@pytest.mark.parametrize("key, command, marker", ESCAPE_PROBES, ids=[k for k, _c, _m in ESCAPE_PROBES])
def test_astra_escape_probes(hub: RealHub, key: str, command: str, marker: str) -> None:
    (hub.worktree / "out").symlink_to(hub.worktree.parent) if not (hub.worktree / "out").exists() else None
    held = _hook(hub, command, key, ttl=2.0)
    assert "expired" in (held.deny or ""), "held, never passed"
    assert _proposal(hub, key)["operation"]["tool_call"]["scope"] in ("outside", "unparsed")
    assert not (hub.worktree.parent / marker).exists()


# ── merged from tests/integration/test_philo15_20_yolo_reads_real_hub.py ──
# PHILO-15 20: YOLO lets the agent read; Raw approves a cut call (B62, B63,
# B66), through the REAL hook (``coder_gate.run_hook`` over HTTP) and a REAL hub
# process (``holdspeak web`` on an isolated HOME), seeded as in lane 15.
#
# B62: the exact commands YOLO held in rehearsal 2 (BOUNCES-C) now pass; a
# config write, a push to another branch and a script outside the worktree
# still wait. B63: a cut held call is read whole by the owner (only) and
# approved there. B66: a Deny names the hold's reason to the agent.


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
    # Astra r1 on #1011 (P1-3): a test operand is a path.
    ('test -f "$(git rev-parse --show-toplevel)/../outside"', "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
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


def _mcp_read(hub: RealHub, uri: str, token: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{hub.base}/api/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": uri}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def _pipeline_rows_with(hub: RealHub, needle: str) -> int:
    import sqlite3

    found = 0
    for db in hub.home.rglob("*.db"):
        conn = sqlite3.connect(str(db))
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "pipeline_events" in tables:
                found += conn.execute(
                    "SELECT count(*) FROM pipeline_events WHERE args_summary LIKE ? OR result_summary LIKE ?",
                    (f"%{needle}%", f"%{needle}%"),
                ).fetchone()[0]
        finally:
            conn.close()
    return found


def test_the_whole_call_never_reaches_the_observer_or_an_agent(hub: RealHub) -> None:
    """Astra r1 on #1011 (P1-1): the observer recorded GateService.propose's
    payload and full_call's result into pipeline_events, which an agent read
    through MCP ``pipeline://events/recent/GateService``. A synthetic secret
    past char 120 (no known secret shape, so redaction keeps it) is in no
    pipeline row and in no agent read, after the owner's Raw read and a Deny."""
    secret = "SYNTH-k3y9Q-past-the-head-7Zt"
    command = "cat > /tmp/hs_observer_probe.txt <<'EOF'\n" + "padding line of the body\n" * 6 + f"{secret}\nEOF"
    thread, box = _held_in_thread(hub, command, "toolu_observer")
    whole = hub.get("/api/gate/proposals/toolu_observer/command")
    assert secret in whole["command"] and whole["whole"] is True  # the owner reads it whole
    status, _ = hub._post_with_token("/api/gate/proposals/toolu_observer/decide", {"decision": "denied"}, hub.owner_token)
    assert status == 200
    thread.join(timeout=10)
    assert box["decision"].deny

    assert _pipeline_rows_with(hub, "toolu_observer") > 0, "the observer did record the calls"
    assert _pipeline_rows_with(hub, secret) == 0
    # Iteration 2 on #1011: each read must SUCCEED and carry GateService
    # records (a refusal would prove nothing), for both principals and URIs.
    # The agent here holds a session credential, which reaches /api/mcp with
    # the Reach switch on (a launch credential reaches it from loopback with
    # the switch off); the switch is turned on so the agent's read is real.
    req = urllib.request.Request(
        f"{hub.base}/api/settings/remote", method="PUT", data=json.dumps({"enabled": True}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {hub.owner_token}"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
    for uri in ("pipeline://events/recent/GateService", "pipeline://events/recent"):
        for who, token in (("agent", hub.agent_token), ("owner", hub.owner_token)):
            status, body = _mcp_read(hub, uri, token)
            assert status == 200, (who, uri, status, body[:300])
            reply = json.loads(body)
            assert "error" not in reply, (who, uri, reply.get("error"))
            text = "".join(c.get("text", "") for c in reply["result"]["contents"])
            assert '"GateService"' in text and "toolu_observer" in text, (who, uri, text[:300])
            assert secret not in text and secret not in body, (who, uri)


def test_a_part_is_never_whole_and_is_deny_only(hub: RealHub) -> None:
    """Astra r1 on #1011 (P1-2): a 66,053-char command is kept as a part; the
    hub says so (``whole: false``, n OF m) and Raw offers Deny only."""
    command = "cat > /tmp/hs_huge.txt <<'EOF'\n" + ("x" * 99 + "\n") * 660 + "EOF"
    assert len(command) > 65_536
    thread, box = _held_in_thread(hub, command, "toolu_huge")
    read = hub.get("/api/gate/proposals/toolu_huge/command")
    assert read["whole"] is False
    assert read["declared_chars"] == len(command)
    assert read["shown_chars"] == len(read["command"]) < len(command)
    status, _ = hub._post_with_token("/api/gate/proposals/toolu_huge/decide", {"decision": "denied"}, hub.owner_token)
    assert status == 200
    thread.join(timeout=10)


def test_a_substitution_after_cd_is_read_where_it_runs(hub: RealHub, tmp_path) -> None:
    """Astra r1 on #1011 (P1-4), her probe through the real hook and hub:
    ``sub/secret`` links out of the worktree; the call waits."""
    outside = tmp_path / "outside-secret"
    outside.write_text("outside content\n", encoding="utf-8")
    (hub.worktree / "sub").mkdir()
    (hub.worktree / "sub" / "secret").symlink_to(outside)
    held = _hook(hub, 'cd sub && echo "$(cat secret)"', "toolu_cd_subst", ttl=2.0)
    assert held.deny and "expired" in held.deny
    assert _proposal(hub, "toolu_cd_subst")["hold_reason"] == "UNRESOLVED TARGET · $(cat secret)"
