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
