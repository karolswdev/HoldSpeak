"""HS-94-06 against a real tmux server.

The stream half: a real pane's output arrives as a snapshot plus
sequenced deltas with the ANSI bytes intact. The command half: a full
envelope travels hub-service → node-processor → the REAL chokepoint
into the real pane, the duplicate returns the same Receipt with the
text landing exactly once, and the YOLO posture types promptless into
a registered target. Skips honestly when tmux is not on this machine.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid

import pytest

from holdspeak.coder_steering import arm, clear_grants, peek_pane
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.terminal import TerminalStreamService, TerminalTargetRegistry

pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None, reason="tmux is required for the live terminal proof"
)

KEY = "claude:hs94-live"


@pytest.fixture
def live_pane():
    session = f"hs94-term-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session, "bash --norc --noprofile"],
        check=True,
        timeout=10,
    )
    try:
        pane = subprocess.run(
            ["tmux", "list-panes", "-t", session, "-F", "#{pane_id}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        time.sleep(0.5)
        yield session, pane
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], timeout=10)


@pytest.fixture(autouse=True)
def _fresh_grants():
    clear_grants()
    yield
    clear_grants()


def _rig(tmp_path, *, mode="neutral"):
    targets = TerminalTargetRegistry()
    audit_rows: list[dict] = []
    processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=NodeReceiptLedger(tmp_path / "ledger.db"),
        audit=lambda **kw: audit_rows.append(kw) or len(audit_rows),
    )
    db = Database(tmp_path / "hub.db")
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: mode,
    )
    return targets, service, audit_rows


def test_live_stream_snapshot_then_ansi_delta(live_pane) -> None:
    session, pane = live_pane
    targets = TerminalTargetRegistry()
    stream = TerminalStreamService(targets)
    issued = targets.issue(f"pane:{pane}")
    assert issued["status"] == "issued"
    assert issued["pane_id"] == pane

    snap = stream.read(issued["target_id"], issued["target_generation"])
    assert snap["status"] == "snapshot"
    assert snap["ansi"] is True
    base_sequence = snap["sequence"]

    marker = f"ansi-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "tmux",
            "send-keys",
            "-t",
            pane,
            f"printf '\\033[1;31m{marker}\\033[0m\\n'",
            "Enter",
        ],
        check=True,
        timeout=10,
    )
    time.sleep(0.6)

    out = stream.read(
        issued["target_id"], issued["target_generation"], resume_sequence=base_sequence
    )
    assert out["status"] == "deltas", out
    joined = "".join(d["data"] for d in out["deltas"])
    assert marker in joined
    # tmux re-emits SGR state as it captured it; the escapes themselves
    # must cross untouched (peek strips them, the stream must NOT).
    assert "\x1b[31m" in joined and "\x1b[0m" in joined
    assert [d["sequence"] for d in out["deltas"]] == list(
        range(base_sequence + 1, out["sequence"] + 1)
    )

    # Caught up: the same sequence answers not_modified until output moves.
    idle = stream.read(
        issued["target_id"], issued["target_generation"], resume_sequence=out["sequence"]
    )
    assert idle["status"] == "not_modified"


def test_live_command_envelope_types_once_and_reconciles(live_pane, tmp_path) -> None:
    session, pane = live_pane
    targets, service, audit_rows = _rig(tmp_path)
    armed = arm(KEY, f"{session}:0.0")
    assert armed["status"] == "armed"
    issued = targets.issue(f"{session}:0.0")
    assert issued["pane_id"] == pane

    marker = f"steer-{uuid.uuid4().hex[:8]}"
    command_id = str(uuid.uuid4())
    request = {
        "command_id": command_id,
        "target_id": issued["target_id"],
        "target_generation": issued["target_generation"],
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {"text": marker, "session_key": KEY, "submit": False},
        "expected_sequence": 1,
    }
    first = service.submit(request)
    assert first["receipt"]["state"] == "succeeded"
    assert first["receipt"]["outcome"] == "delivered"
    assert first["receipt"]["applied_sequence"] == 1
    assert first["receipt"]["authority_basis"] == "scoped_grant"

    # The lost-response retry: same command_id, the SAME receipt back.
    retry = service.submit(request)
    assert retry["duplicate"] is True
    assert retry["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]

    time.sleep(0.4)
    seen = "\n".join(peek_pane(pane, lines=50)["lines"])
    assert seen.count(marker) == 1  # at most once, for real
    assert audit_rows[0]["outcome"] == "delivered"

    joined = service.receipt(command_id)
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert joined["payload_head"] == marker


def test_live_yolo_posture_types_promptless_into_registered_target(
    live_pane, tmp_path
) -> None:
    session, pane = live_pane
    targets, service, _ = _rig(tmp_path, mode="yolo")
    issued = targets.issue(f"{session}:0.0")
    marker = f"yolo-{uuid.uuid4().hex[:8]}"
    out = service.submit(
        {
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": marker, "session_key": KEY, "submit": False},
        }
    )
    assert out["receipt"]["outcome"] == "delivered"
    assert out["receipt"]["authority_basis"] == "control_posture"
    time.sleep(0.4)
    assert marker in "\n".join(peek_pane(pane, lines=50)["lines"])


def test_live_recycled_pane_refuses_revokes_and_types_nothing(
    live_pane, tmp_path
) -> None:
    session, pane = live_pane
    targets, service, _ = _rig(tmp_path)
    armed = arm(KEY, f"{session}:0.0")
    assert armed["status"] == "armed"
    issued = targets.issue(f"{session}:0.0")

    # Recycle: kill the window's pane and put a new one at the address.
    subprocess.run(["tmux", "kill-pane", "-t", pane], timeout=10)
    subprocess.run(
        ["tmux", "new-window", "-t", session, "bash --norc --noprofile"],
        timeout=10,
    )
    time.sleep(0.3)

    out = service.submit(
        {
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": "must never land", "session_key": KEY, "submit": False},
            "expected_sequence": 1,
        }
    )
    receipt = out["receipt"]
    assert receipt["state"] == "refused"
    assert receipt["outcome"] in ("generation_mismatch", "target_gone")
    from holdspeak.coder_steering import active_grants

    if receipt["outcome"] == "generation_mismatch":
        assert receipt["revoked"] is True
        assert active_grants() == {}
