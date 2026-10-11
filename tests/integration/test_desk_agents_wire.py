"""The Agents / Conductor / Needs-you gate wire on a real hub (the test diet,
2026-10-11).

Each test boots a real hub on an isolated HOME (``tests/e2e/glass_infra._boot``,
no browser), seeds it with the SAME producers the browser test it replaces
used (``tests/e2e/agents_lane_rig.py``, ``tests/e2e/conductor_rig.py``, the
product seed), reads the hub's routes over HTTP and asserts the facts the
browser test asserted on the wire. The face half moved to vitest
(``web/src/desk/__tests__/*.app.test.tsx``), which renders the faces on the
hub's OWN answers, captured here.

The wire fence (SCAR LAW: a test double that lies about the field a check
reads proves nothing). Every captured answer is stored under
``web/src/desk/__tests__/wire/<name>.wire.json`` and the vitest successors
read those files as their ``apiFetch`` answers. This file reads the same
routes again on every run and fails when the stored answer's SHAPE (every
key, at every depth, and its JSON type) is not the hub's shape: a field the
face reads that the hub stopped serving, or a field invented in the stored
file, turns this red. ``HOLDSPEAK_WIRE_WRITE=1`` rewrites the stored files
(scrubbed of this run's temporary paths and port).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot

pytestmark = pytest.mark.timeout(240)

REPO = Path(__file__).resolve().parents[2]
WIRE_DIR = REPO / "web" / "src" / "desk" / "__tests__" / "wire"


# ── the wire fence ─────────────────────────────────────────────────────


def _shape(value: Any) -> Any:
    """The JSON shape: dict keys at every depth, list element shapes, and
    each leaf's JSON type (``null`` kept as itself)."""
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _same_shape(stored: Any, live: Any, at: str = "$") -> list[str]:
    """Where the stored shape is not the live one. A ``null`` on either side
    matches any value: what this Mac has installed (an agent's path and
    version) is null on another machine, and that is not a lie about a field."""
    if stored == "null" or live == "null":
        return []
    if isinstance(stored, dict) and isinstance(live, dict):
        diffs = [f"{at}.{key}: only in the stored answer" for key in stored.keys() - live.keys()]
        diffs += [f"{at}.{key}: only in the hub's answer" for key in live.keys() - stored.keys()]
        for key in stored.keys() & live.keys():
            diffs += _same_shape(stored[key], live[key], f"{at}.{key}")
        return diffs
    if isinstance(stored, list) and isinstance(live, list):
        if len(stored) != len(live):
            return [f"{at}: {len(stored)} stored rows, {len(live)} on the hub"]
        return [d for i, (a, b) in enumerate(zip(stored, live)) for d in _same_shape(a, b, f"{at}[{i}]")]
    return [] if stored == live else [f"{at}: stored {stored}, hub {live}"]


def _scrub(value: Any, tmp_path: Path, url: str) -> Any:
    """This run's temporary paths, port, checkout and user out of the stored answer."""
    text = json.dumps(value)
    for real in {str(tmp_path), str(tmp_path.resolve())}:
        # The hub may report the folder in another case (macOS: /T/ and /t/).
        text = re.sub(re.escape(real), "/tmp/rig", text, flags=re.IGNORECASE)
    text = text.replace(str(REPO), "/repo")
    text = re.sub(r"/Users/[^/\"]+", "/Users/me", text)
    text = text.replace(url, "http://127.0.0.1:8765")
    return json.loads(text)


def _fence(name: str, payload: Any, tmp_path: Path, url: str) -> None:
    """The stored answer has the hub's shape (or is rewritten on request)."""
    scrubbed = _scrub(payload, tmp_path, url)
    path = WIRE_DIR / f"{name}.wire.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        path.write_text(json.dumps({
            "_": f"The hub's own answer, captured by {Path(__file__).relative_to(REPO)}; "
                 "HOLDSPEAK_WIRE_WRITE=1 rewrites it.",
            "captured_at": stamp,
            "wire": scrubbed,
        }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = json.loads(path.read_text())["wire"]
    diffs = _same_shape(_shape(stored), _shape(scrubbed))
    assert not diffs, (
        f"{path.name}: the stored answer is not the hub's shape "
        f"(rewrite it with HOLDSPEAK_WIRE_WRITE=1 and read the diff): {diffs[:10]}"
    )


# ── the hub ────────────────────────────────────────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A real hub on an isolated HOME with every agent store inside it (the
    lane glass's own paths)."""
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    from tests.e2e import agents_lane_rig as rig

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=rig.TOKEN)
    try:
        yield url
    finally:
        server.stop()


def _get(url: str, path: str) -> Any:
    from tests.e2e.agents_lane_rig import TOKEN, _http

    status, body = _http(url, "GET", path, TOKEN)
    assert status == 200, (path, status, body)
    return body


def _decide(url: str, proposal_id: str, decision: str) -> Any:
    from tests.e2e.agents_lane_rig import TOKEN, _http

    status, body = _http(url, "POST", f"/api/gate/proposals/{proposal_id}/decide", TOKEN, {"decision": decision})
    assert status == 200, body
    return body


LONG_CMD = (
    "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = "
)
LONG_CMD = LONG_CMD + "7" * (198 - len(LONG_CMD) - 1) + "'"


# ── the roster ─────────────────────────────────────────────────────────


def test_the_roster_reads_every_seeded_agent(hub: str, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_agents_roster_glass.py::test_roster_lists_the_floor_agents_and_no_blank_delivery_tab
    (the hub half: the product seed's agents are served by /api/recipes, not
    deleted; the face half is agents.app.test.tsx)."""
    from holdspeak.db import get_database
    from holdspeak.db.seed import apply_seed

    apply_seed(get_database())
    body = _get(hub, "/api/recipes")
    names = {str(row["name"]) for row in body["recipes"] if not row.get("deleted")}
    assert {"Chase", "Desk", "Draft"} <= names, names
    _fence("recipes.seed", body, tmp_path, hub)
    # No repository work and no PR receipts on a seeded desk: the Delivery
    # wing's two reads are empty.
    _fence("delivery-prs.empty", _get(hub, "/api/delivery/prs"), tmp_path, hub)
    sessions = _get(hub, "/api/coders/sessions?include_ended=false")
    assert sessions["sessions"] == [] and sessions["flights"] == [], sessions
    _fence("coders-sessions.empty", sessions, tmp_path, hub)


# ── the held call (Needs you, the shade) ──────────────────────────────


def _hold(url: str, credential: str, proposal_id: str, worktree: str, command: str) -> dict:
    """What the gate hook sends for one call outside the worktree
    (``coder_gate.redact_call``: the hash, the 120-char head, the length)."""
    from holdspeak.coder_gate import redact_call
    from tests.e2e.agents_lane_rig import _http

    call = redact_call({"command": command})
    status, body = _http(url, "POST", "/api/gate/proposals", credential, {
        "id": proposal_id, "tool": "Bash", "args_sha256": call.sha256, "args_head": call.head,
        "args_len": call.length, "cwd": worktree, "ttl_seconds": 600,
        "classification": {"scope": "outside", "rule": "path_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": worktree, "proposal_id": proposal_id,
                           "args_sha256": call.sha256},
    })
    assert status == 200, body
    return body


def test_a_held_call_is_a_needs_row_and_the_owners_press_decides_it(hub: str, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it
    (the hub half: the hold, its Needs-you row with why it waits, the cut
    view, and Approve / Deny deciding the real proposal as the owner; the
    face half is needs-you.app.test.tsx on the answer captured here)."""
    import holdspeak.delivery.factory_launch as factory_launch
    from tests.e2e.agents_lane_rig import TOKEN, _http

    session = "claude:glass-r1"
    worktree = tmp_path / "wt"
    worktree.mkdir()
    factory_launch.LaunchLedger().record({
        "launch_schema": 1, "launch_id": "launch_glassr1", "state": "registered",
        "session_key": session, "profile_id": "claude-default", "source_id": "src_none",
        "worktree_id": "wt_none", "branch": "hs/action-glass", "session": "hs-glass",
    })
    status, issued = _http(hub, "POST", "/api/principals/agents", TOKEN, {"identity": session})
    assert status == 201, issued
    credential = issued["credential"]

    first = _hold(hub, credential, "toolu_glass_approve", str(worktree), "ls /etc")
    assert first["state"] == "held", first
    assert first["policy_snapshot"]["reason_code"] == "yolo_outside_own_worktree"
    cut = _hold(hub, credential, "toolu_glass_cut", str(worktree), LONG_CMD)
    assert cut["state"] == "held", cut

    # The owner's list (the shade) carries the cut view.
    listed = _get(hub, "/api/gate/proposals?state=held")
    cards = {p["id"]: p for p in listed["proposals"]}
    assert cards["toolu_glass_cut"]["args_cut"] is True and cards["toolu_glass_cut"]["args_hidden"] == 90
    assert cards["toolu_glass_approve"]["args_cut"] is False
    _fence("gate-proposals.held", listed, tmp_path, hub)

    # Needs you: one row per held call, why it waits, the whole command.
    needs = _get(hub, "/api/desk/needs-you")
    rows = {row["id"]: row for row in needs["items"] if row.get("kind") == "gate"}
    whole = rows["gate:toolu_glass_approve"]
    assert whole["holdReason"] == "OUTSIDE THE WORKTREE" and whole["command"] == "ls /etc"
    assert whole["argsCut"] is False and whole["why"] == "TO APPROVE"
    short = rows["gate:toolu_glass_cut"]
    assert short["argsCut"] is True and short["argsHidden"] == 90
    assert LONG_CMD.startswith(short["command"]) and len(short["command"]) == 108
    _fence("needs-you.gate", needs, tmp_path, hub)
    # The system shade's other reads on this desk (needs-you.app.test.tsx).
    _fence("desk-projections.attention", _get(
        hub, "/api/desk/projections?attention_state=needs_attention&offset=0&limit=4"), tmp_path, hub)
    _fence("dictation-corrections.empty", _get(hub, "/api/dictation/corrections"), tmp_path, hub)
    _fence("brief-latest.empty", _get(hub, "/api/brief/latest"), tmp_path, hub)
    _fence("door.empty", _get(hub, "/api/door"), tmp_path, hub)

    # Approve: the owner's press decides the real proposal; the row leaves.
    assert _decide(hub, "toolu_glass_approve", "approved")["state"] == "approved"
    read = _get(hub, "/api/gate/proposals/toolu_glass_approve")
    assert read["state"] == "approved" and read["decided_by"] != "control-mode", read
    after = {row["id"] for row in _get(hub, "/api/desk/needs-you")["items"]}
    assert "gate:toolu_glass_approve" not in after and "gate:toolu_glass_cut" in after

    # Deny: a second hold, decided the same way.
    second = _hold(hub, credential, "toolu_glass_deny", str(worktree), "cat /etc/hosts")
    assert second["state"] == "held"
    assert _decide(hub, "toolu_glass_deny", "denied")["state"] == "denied"
    assert _get(hub, "/api/gate/proposals/toolu_glass_deny")["state"] == "denied"


# ── the lane ───────────────────────────────────────────────────────────


def test_the_lane_reads_the_launchs_whole_work_and_the_gate_decides_its_held_call(hub: str, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393
    (the hub half: the lane route over the C2 seed serves the brief, the
    events, the commit and files, the PR with its checks, the ask and its
    drafted answer, and the held call; Approve through the gate route; a
    cut call is served cut. The face half is agents.app.test.tsx on the
    answers captured here)."""
    from tests.e2e.agents_lane_rig import KEY, PSQL, QUESTION, _seed, mint_held_call

    seed = _seed(tmp_path / "home")
    mint_held_call(hub, seed["worktree"])
    lane = _get(hub, "/api/agent/launches/launch_c2_runbook/lane")
    assert lane["launch"]["session_key"] == KEY
    assert lane["launch"]["origin_ref"] == {"kind": "action", "id": seed["item"]}
    assert lane["wait"]["question"] == QUESTION and lane["wait"]["kind"] == "TO ANSWER"
    assert lane["wait"]["draft"]["text"] == "Jordan owns it. Avery reviews."
    events = [e["event"] for e in lane["events"]]
    for event in ("SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "Notification"):
        assert event in events, events
    assert [c["subject"] for c in lane["worktree"]["commits"]] == ["Draft the ledger rollback runbook"]
    assert {f["path"] for f in lane["worktree"]["files"]} >= {"docs/ledger-rollback.md", "freeze.py"}
    pr = lane["follow_through"]["pr"]
    assert pr["number"] == 413 and len(pr["checks"]) == 7
    assert sum(c["state"] == "success" for c in pr["checks"]) == 6
    assert [(g["id"], g["state"]) for g in lane["gated"]] == [("toolu_psql", "held")]
    assert PSQL in lane["gated"][0]["args_head"]
    _fence("lane.c2", lane, tmp_path, hub)
    # The lane's title names the launch's item: the one agents read.
    flights = _get(hub, "/api/coders/sessions?include_ended=false")
    [flight] = [f for f in flights["flights"] if f["launch_id"] == "launch_c2_runbook"]
    assert flight["title"] == "Write the rollback runbook" and flight["session_key"] == KEY, flight
    _fence("coders-sessions.c2", flights, tmp_path, hub)
    # The lane's draft chip reads the assignments (agents.app.test.tsx).
    _fence("inference-assignments.empty", _get(hub, "/api/inference/assignments"), tmp_path, hub)

    # Approve from the rail: the real gate route decides it.
    assert _decide(hub, "toolu_psql", "approved")["state"] == "approved"
    assert _get(hub, "/api/gate/proposals/toolu_psql")["state"] == "approved"

    # A 198-char call the hook cuts: the lane serves the head and the cut.
    mint_held_call(hub, seed["worktree"], LONG_CMD, "toolu_cut")
    cut_lane = _get(hub, "/api/agent/launches/launch_c2_runbook/lane")
    [cut] = [g for g in cut_lane["gated"] if g["id"] == "toolu_cut"]
    assert cut["state"] == "held" and cut["args_cut"] is True and cut["args_hidden"] == 90, cut
    _fence("lane.c2-cut", cut_lane, tmp_path, hub)


def test_raw_reads_a_cut_call_whole_and_approves_it(hub: str, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo15_20_raw_approve_glass.py::test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393
    (the hub half: a cut call minted with its whole redacted text is served
    whole to the owner's Raw read, with why it waits; Approve decides it; an
    oversized call is kept as a part, never whole; Needs you names it cut.
    The face half is agents.app.test.tsx and needs-you.app.test.tsx)."""
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.coder_gate import redact_call
    from tests.e2e.agents_lane_rig import KEY, TOKEN, _http, _seed

    seed = _seed(tmp_path / "home")
    factory_launch.LaunchLedger().update("launch_c2_runbook", session_key=KEY)
    status, issued = _http(hub, "POST", "/api/principals/agents", TOKEN, {"identity": KEY})
    assert status == 201, issued

    def mint(command: str, proposal_id: str) -> None:
        call = redact_call({"command": command})
        assert call.full, "a cut call carries its whole redacted text"
        status, body = _http(hub, "POST", "/api/gate/proposals", issued["credential"], {
            "id": proposal_id, "tool": "Bash", "args_sha256": call.sha256, "args_head": call.head,
            "args_len": call.length, "args_full": call.full, "cwd": seed["worktree"], "ttl_seconds": 3600,
            "classification": {"scope": "outside", "rule": "cwd_outside_worktree", "read_rule": "",
                               "push_branch": "", "root": seed["worktree"], "proposal_id": proposal_id,
                               "args_sha256": call.sha256},
        })
        assert status == 200 and body["state"] == "held", body

    clone = "/private/var/folders/q7/T/hs-r2/.holdspeak/repositories/karolswdev/holdspeak-dayone-rehearsal-1558"
    command = (
        f"cd {clone} && pwd && echo \"---BRANCH---\" && git branch --show-current && echo \"---STATUS---\" "
        "&& git status && echo \"---LOG---\" && git log --oneline -5"
    )
    mint(command, "toolu_cut_1440")
    full = _get(hub, "/api/gate/proposals/toolu_cut_1440/command")
    assert full["command"] == command and full["whole"] is True, full
    assert full["hold_reason"].startswith("OUTSIDE THE WORKTREE"), full
    _fence("gate-command.whole", full, tmp_path, hub)

    # Needs you: the cut call is a row with no Approve (argsCut).
    rows = {row["id"]: row for row in _get(hub, "/api/desk/needs-you")["items"]}
    assert rows["gate:toolu_cut_1440"]["argsCut"] is True

    assert _decide(hub, "toolu_cut_1440", "approved")["state"] == "approved"
    assert _get(hub, "/api/gate/proposals/toolu_cut_1440")["state"] == "approved"

    # An oversized call is kept as a part: never whole, Deny only on Raw.
    huge = "cat > /tmp/hs_huge.txt <<'EOF'\n" + ("x" * 99 + "\n") * 660 + "EOF"
    mint(huge, "toolu_cut_huge")
    part = _get(hub, "/api/gate/proposals/toolu_cut_huge/command")
    assert part["whole"] is False and part["shown_chars"] < part["declared_chars"] == len(huge), {
        k: part[k] for k in ("whole", "shown_chars", "declared_chars")}
    _fence("gate-command.part", part, tmp_path, hub)


# ── the Conductor ──────────────────────────────────────────────────────


def test_the_conductor_reads_three_launches_and_the_ask(hub: str, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo14_c4_conductor_glass.py::test_the_conductor_drawer_at_1440_and_393
    (the hub half: the one agents read serves the C4 seed's three launches,
    the asking session with its question, the hub's launch count; the face
    half is conductor.app.test.tsx on the answers captured here)."""
    from tests.e2e.conductor_rig import QUESTION, _seed

    _seed(tmp_path / "home")
    sessions = _get(hub, "/api/coders/sessions?include_ended=false")
    launches = {f["launch_id"]: f for f in sessions["flights"]}
    assert set(launches) >= {"launch_c4_runbook", "launch_c4_recon", "launch_c4_flag"}, set(launches)
    assert launches["launch_c4_flag"]["pr"]["number"] == 412
    asking = [row["session"] for row in sessions["sessions"] if row["session"].get("question")]
    assert [s.get("question") for s in asking] == [QUESTION]
    _fence("coders-sessions.c4", sessions, tmp_path, hub)
    detect = _get(hub, "/api/onboarding/agents")
    assert {a["id"] for a in detect["agents"]} >= {"claude", "codex"}
    _fence("onboarding-agents.isolated", detect, tmp_path, hub)
    # Open on a launched agent reads its lane (Get Info and the lane window).
    _fence("lane.c4-runbook", _get(hub, "/api/agent/launches/launch_c4_runbook/lane"), tmp_path, hub)
