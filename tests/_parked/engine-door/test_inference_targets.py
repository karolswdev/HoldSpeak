# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; asking a named target (inference_target_id) is gone.
# Moved from tests/unit/test_inference_targets.py; its helpers are still there.

from tests.unit.test_inference_targets import *  # noqa: F401,F403


def test_dead_endpoint_or_rejected_token_refuses_with_target_name(
    rig, monkeypatch
) -> None:
    db, client = rig
    profile = db.profiles.upsert(
        profile_id="vendor",
        name="Named vendor",
        kind="openAICompatible",
        base_url="https://example.com/v1",
        requires_key=False,
    )
    from holdspeak.intel.models import MeetingIntelError

    class Rejected:
        active_provider = "cloud"

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("401 rejected token")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **kwargs: Rejected(),
    )
    # A target is named by the unrouted Thought only; an answer runs on its
    # assignment through the engine door (test_ask_engine_door.py).
    import asyncio

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.ask_service import AskService
    from holdspeak.services.errors import ServiceError

    with pytest.raises(ServiceError) as refused:
        asyncio.run(AskService(db).ask(Principal(PrincipalKind.OWNER, "owner"), "go", inference_target_id=profile.id,
                                       operation_capability="thought.interview"))
    assert refused.value.context["status"] == 502
    assert refused.value.detail == "Destination 'Named vendor' refused the run: 401 rejected token"
    assert refused.value.context["alternate_target_id"] == "this_machine"
