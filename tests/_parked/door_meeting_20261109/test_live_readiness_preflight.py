# PARKED 2026-11-09 (door/meeting-kernel): live readiness read the frozen route
# plan's preflight evidence (``inference_route_plan_preflight_evidence``) and kept a
# Meeting "queued" when its first leg's binding was not ready. The live Meeting no
# longer builds a route plan; the engine door has no preflight for any job (Ask,
# chat, dictation stages and the deferred queue run the same way): the first call
# runs on the assigned engine and once on the next engine of the chain.
# Moved from tests/unit/test_meetings_live_cutover.py.

from pathlib import Path

import pytest

from tests.unit.test_meetings_live_cutover import *  # noqa: F401,F403


def test_unavailable_frozen_live_member_stays_queued_not_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Live readiness reads frozen preflight eligibility rather than member presence."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_readiness_observations SET state='unavailable',reason_code='fault-injected-unavailable'"
        )
    state = session.start()
    assert session._route_bundle is not None
    assert state.intel_status == "queued"
    assert state.intel_status_detail == "Queued for later processing: binding_not_ready"


