# PARKED 2026-11-09 (door/meeting-kernel): these cases drove the route bundle's
# Stop handoff (``request_stop_handoff``, the queue's reserve-inert evidence
# provider, settlement, activation and unknown-outcome recovery). The live Meeting
# no longer has a bundle: Stop stops its door jobs (``engine_door.stop``), ends the
# parent cancelled and queues the owed work with one upsert
# (tests/unit/test_meetings_live_cutover.py). The provider and the queue's
# reconcile step were removed with it.
# Moved from tests/unit/test_meeting_deferred_admission.py.

from tests.unit.test_meeting_deferred_admission import *  # noqa: F401,F403
from tests.unit.test_meeting_deferred_admission import _queue_rig, _saved_stop_meeting  # noqa: F401
from holdspeak.services.inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY  # noqa: F401
from holdspeak.services.inference_parent_route_bundle_service import InferenceParentRouteBundleService  # noqa: F401
from tests.unit.test_engines_fallback_controller import _broker_child  # noqa: F401


def _live_stop_bundle(
    broker: Any,
    state: MeetingState,
    provider: Any,
    *,
    route_specs: tuple[dict[str, str], ...] | None = None,
):
    bundles = InferenceParentRouteBundleService(
        broker,
        broker.inference_adoption_service,
        handoff_evidence_providers=(provider,),
    )
    started = bundles.start(
        OWNER,
        command_id=f"c3-live-bundle:{state.id}",
        parent_kind="meeting.session",
        definition_ref=f"meeting:{state.id}:intel",
        definition_revision="c3-test",
        input_snapshot={"meeting_id": state.id},
        deadline_at=2_000_000_000.0,
        routes=route_specs or ({
            "key": "deferred-analysis",
            "capability_id": "meeting.deferred_analysis",
            "invocation_id": state.id,
        },),
    )
    return bundles, started


def test_stop_handoff_post_commit_cancels_do_not_serially_delay_stop(tmp_path, monkeypatch):
    """Four slow provider cancels cannot hold the already-fenced Stop response."""
    db, broker, _engine, _host, _requests = _queue_rig(
        tmp_path,
        monkeypatch,
        plugins=("requirements_extractor",),
        chain=("requirements_extractor",),
    )
    state = _saved_stop_meeting(db, "m-c3-stop-latency")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    route_specs = (
        {"key": "analysis", "capability_id": "meeting.deferred_analysis", "invocation_id": state.id},
        {"key": "bookmark", "capability_id": "meeting.bookmark_label", "invocation_id": state.id},
        {"key": "title", "capability_id": "meeting.auto_title", "invocation_id": state.id},
        {"key": "plugin", "capability_id": "meeting.plugin.requirements_extractor", "invocation_id": state.id},
    )
    bundles, started = _live_stop_bundle(
        broker, state, provider, route_specs=route_specs,
    )
    controller = broker.inference_adoption_service.controller
    for member in started["bundle"]["members"]:
        capability = member["capability_id"]
        admitted = broker.inference_adoption_service.admit_on_frozen_route(
            OWNER,
            command_id=f"c3-latency-admit:{member['key']}",
            route_plan_id=member["route_plan_id"],
            capability_id=capability,
            operation_id=f"c3-latency-operation:{member['key']}",
            payload={"transcript": "we shipped the fix"},
            reserved_output_tokens=16,
        )
        reservation = controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"c3-latency-reserve:{member['key']}",
            execution_id=admitted["execution"]["id"],
        )["reservation"]
        controller.claim_reservation(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"claim-{reservation['attempt_id']}",
            reservation=reservation,
        )
        child_id = _broker_child(broker, reservation, suffix=f"c3-latency-{member['key']}")
        controller.bind_admitted_child(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"bind-{reservation['attempt_id']}",
            attempt_id=reservation["attempt_id"],
            child_operation_id=child_id,
        )
        controller.mark_dispatch_intent(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"dispatch-{reservation['attempt_id']}",
            attempt_id=reservation["attempt_id"],
        )

    completed: list[str] = []
    all_cancelled = threading.Event()
    release_cancels = threading.Event()
    lock = threading.Lock()

    def slow_cancel(invocation_id: str) -> str:
        # A provider cancel that does not return until the test lets it. A
        # wall-clock budget (the old 0.2 s sleep and "Stop in < 0.5 s") failed
        # on a loaded machine; the order of events cannot.
        assert release_cancels.wait(120), "the test never released the cancels"
        with lock:
            completed.append(invocation_id)
            if len(completed) == 4:
                all_cancelled.set()
        return "delayed"

    monkeypatch.setattr(broker.inference_runner, "cancel", slow_cancel)
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )

    assert effect["state"] == "pending_physical_settlement"
    # Stop returned while every provider cancel was still held: the response is
    # only the durable fence/reservation transaction, and no cancel, serial or
    # not, can delay it.
    assert completed == []
    release_cancels.set()
    assert all_cancelled.wait(timeout=120)
    assert len(completed) == 4


def test_stop_provider_known_settlement_activates_normal_bound_queue_claim(tmp_path, monkeypatch):
    """C3 activates the production reservation only into C1's ordinary claim."""
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-known")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)

    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "committed"
    with db._connection() as conn:
        reserved = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        events = conn.execute(
            "SELECT event_kind,outcome FROM intel_job_attempts WHERE job_id=? ORDER BY id",
            (effect["evidence_ref"],),
        ).fetchall()
    assert reserved is not None and tuple(reserved) == ("queued", "queued")
    assert [tuple(event) for event in events] == [
        ("handoff_reserved", "reserved"), ("handoff_activated", "activated"),
    ]

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert engine.analyzed and requests
    with db._connection() as conn:
        # The activated evidence row entered the real C1/C2 descriptor and bundle
        # claim machinery; this is not a direct provider execution route.
        claim = conn.execute(
            """SELECT parent_operation_id,bundle_id,event_kind FROM intel_job_attempts
                 WHERE meeting_id=? AND event_kind='claim'""",
            (state.id,),
        ).fetchone()
    assert claim is not None and claim["parent_operation_id"] and claim["bundle_id"]


def test_settled_stop_handoff_skipped_by_owner_never_unknown_recovers(tmp_path, monkeypatch):
    """A valid post-settlement Skip remains terminal queue truth."""
    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-settled-skip")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "committed"
    assert db.intel.skip_remaining_intel(state.id) == "skipped"
    assert db.intel.admit_unknown_stop_handoff_recoveries() == 0
    with db._connection() as conn:
        skipped = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        descendants = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE origin_job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()[0]
    assert skipped is not None and tuple(skipped) == ("skipped", "terminal")
    assert descendants == 0


def test_stop_provider_unknown_dispatch_keeps_reservation_and_fresh_admits(tmp_path, monkeypatch):
    """Unknown physical disposition never activates the old job, even on restart."""
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-unknown")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)
    route = started["bundle"]["members"][0]
    admitted = broker.inference_adoption_service.admit_on_frozen_route(
        OWNER,
        command_id=f"c3-live-child:{state.id}",
        route_plan_id=route["route_plan_id"],
        capability_id="meeting.deferred_analysis",
        operation_id=f"c3-live-child-operation:{state.id}",
        payload={"transcript": "we shipped the fix"},
        reserved_output_tokens=16,
    )
    controller = broker.inference_adoption_service.controller
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"c3-live-reserve:{state.id}",
        execution_id=admitted["execution"]["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="c3-unknown")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
        child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "pending_physical_settlement"

    # A provider-owned reserve is not ordinary queue work: neither generic
    # recovery verb may rewrite it while the live route can still egress, and the
    # existing recovery glass must not advertise those verbs.
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    recovery_service = MeetingIntelService(db)
    recovery_before_settlement = recovery_service.get_recovery(None, state.id)
    assert recovery_before_settlement["actions"] == {"retry": False, "skip": False}
    assert db.intel.request_intel_retry(state.id) == "reserved"
    assert db.intel.skip_remaining_intel(state.id) == "reserved"
    from holdspeak.services.errors import ConflictError

    with pytest.raises(ConflictError, match="awaiting Stop settlement") as retry_refused:
        recovery_service.retry_recovery(OWNER, state.id)
    with pytest.raises(ConflictError, match="awaiting Stop settlement") as skip_refused:
        recovery_service.skip_recovery(OWNER, state.id)
    assert retry_refused.value.code == skip_refused.value.code == "reserved"
    with db._connection() as conn:
        reserved = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        assert reserved is not None and tuple(reserved) == ("reserved", "reserved")
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE origin_job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()[0] == 0

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is False
    assert requests == []

    controller.reconcile_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"c3-live-reconcile:{state.id}",
        attempt_id=reservation["attempt_id"],
    )

    from holdspeak.intel_queue import process_next_intel_job

    # Fresh service construction at the ordinary queue boundary observes the
    # durable terminal, leaves the original reserve inert, and writes both
    # sides of the unknown-recovery ledger before any fresh egress is possible.
    assert process_next_intel_job() is True
    with db._connection() as conn:
        old = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        fresh = conn.execute(
            """SELECT job_id,origin_job_id,status,displaced_work FROM intel_jobs
                 WHERE origin_job_id=?""",
            (effect["evidence_ref"],),
        ).fetchone()
        ledger = conn.execute(
            """SELECT job_id,origin_job_id,event_kind,outcome FROM intel_job_attempts
                 WHERE meeting_id=? AND event_kind IN
                     ('handoff_outcome_unknown','handoff_unknown_recovery')
                 ORDER BY id""",
            (state.id,),
        ).fetchall()
    assert old is not None and tuple(old) == ("reserved", "reserved")
    assert fresh is not None and fresh["status"] == "queued"
    assert json.loads(fresh["displaced_work"])["recovery_origin_job_id"] == effect["evidence_ref"]
    assert [tuple(event) for event in ledger] == [
        (effect["evidence_ref"], None, "handoff_outcome_unknown", "reserved"),
        (fresh["job_id"], effect["evidence_ref"], "handoff_unknown_recovery", "queued"),
    ]
    assert requests == []

    # A second worker turn performs the normal C1 claim and bound execution only
    # for the fresh lineage leaf; restart/reconcile cannot double-activate it.
    assert process_next_intel_job() is True
    assert engine.analyzed and len(requests) == 1
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='handoff_activated'",
            (effect["evidence_ref"],),
        ).fetchone()[0] == 0
