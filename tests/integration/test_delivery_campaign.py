"""HS-94-10 — the bounded Delivery Runtime campaign, as a CI-less-local test.

This wraps ``scripts/phase94_delivery_campaign.run_campaign(bounded=True)``:
the same real hub over real HTTP, a real second OS process linking as a
delivery node, real tmux panes, real git, and the vendored ``dw`` — trimmed
of only the slowest leg (the launch journey) so it stays a bounded, green,
deterministic run. It asserts the machine-verifiable heart of the story:
the north-star journeys, the §13 fault matrix, poll economy, posture
invariance, zero duplicate/wrong-target, the self-attempt exactly-once, and
the audit/privacy census (every command accounted, no leaks).

Skips honestly when tmux is not on the machine (the terminal legs need it).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
for _p in (str(REPO_ROOT), str(SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None,
    reason="the delivery campaign's terminal legs require tmux",
)


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> dict:
    from phase94_delivery_campaign import run_campaign

    workspace = tmp_path_factory.mktemp("hs94-campaign")
    return run_campaign(bounded=True, workspace=workspace)


def test_four_north_star_journeys(report) -> None:
    journeys = report["journeys"]
    # observe remote work, browse evidence, steer a live coder — all over
    # the real hub. (launch is the bounded-skipped leg; the full script
    # proves it.)
    assert journeys["observe"]["pass"] is True, journeys["observe"]
    assert journeys["evidence"]["pass"] is True, journeys["evidence"]
    assert journeys["steer"]["pass"] is True, journeys["steer"]
    assert journeys["steer"]["outcome"] == "delivered"
    assert journeys["steer"]["landed_count"] == 1


def test_fault_matrix_honest_states(report) -> None:
    faults = {f["fault"]: f for f in report["faults"]}
    reconcile = faults["node_kill_reconcile"]["results"]
    assert reconcile["never_claimed"] == "not_executed"
    assert reconcile["lost_after_claim"] == "unknown"
    assert reconcile["after_node_reset"] == "indeterminate_after_node_reset"
    assert reconcile["local_reconcile"] == "complete"
    assert faults["generation_mismatch"]["pass"] is True
    assert faults["expired"]["outcome"] == "command_expired"
    assert faults["out_of_order"]["outcome"] == "sequence_conflict"
    assert faults["out_of_order"]["landed"] == 0
    assert faults["source_failure_lkg"]["degraded_status"] == "stale"
    assert faults["source_failure_lkg"]["retained_projects"] is True
    assert faults["link_loss_cursor_resume"]["no_duplicate_seq"] is True
    assert faults["link_loss_cursor_resume"]["contiguous"] is True


def test_poll_economy_flat_with_client_count(report) -> None:
    poll = report["poll_economy"]
    assert poll["one_client_calls"] > 0
    assert poll["ten_client_calls"] == poll["one_client_calls"]


def test_posture_changes_interruption_only(report) -> None:
    posture = report["posture"]
    assert posture["pass"] is True, posture
    assert posture["yolo_promptless"] is True
    assert posture["normal_via_grant"] is True
    assert posture["basis_differs"] is True
    assert posture["payload_binding_honoured"] is True
    assert posture["policy_version_invariant"] is True
    assert posture["audit_invariant"] is True


def test_zero_duplicate_or_wrong_target(report) -> None:
    dedup = report["dedup"]
    assert dedup["unique_command_ids"] is True
    assert dedup["wrong_target_hit"] is False
    assert dedup["pass"] is True


def test_hs_94_10_proves_itself(report) -> None:
    self_attempt = report["self_attempt"]
    assert self_attempt["exact_count"] == 1
    assert self_attempt["has_live_terminal"] is True
    assert self_attempt["receipt_outcome"] == "delivered"


def test_census_accounted_and_leak_free(report) -> None:
    census = report["census"]
    assert census["accounted"]["all_accounted"] is True, census["accounted"]["unaccounted"]
    assert census["accounted"]["issued"] > 0
    assert census["clean"] is True, census["leaks"]


def test_compat_consumer_census_is_measured(report) -> None:
    compat = report["compat"]
    assert "/api/missioncontrol/" in compat["consumers"]
    assert "/api/coders/" in compat["consumers"]
    # a census measures; it never invents a deletion.
    assert compat["pass"] is True
