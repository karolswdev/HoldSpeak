# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; the placement-based Ask path (a named target, the frozen placement claim, the v1 contract) is gone.
# Moved from tests/unit/test_placement_provenance.py; its helpers are still there.

from tests.unit.test_placement_provenance import *  # noqa: F401,F403


def test_ask_global_placement(ask_rig):
    """Ask with no overrides -> source 'global'."""
    _db, service = ask_rig
    result = asyncio.run(service.ask(OWNER, "hello", operation_capability=CLASSIC))
    assert "placement" in result, f"placement block missing from Ask result: {sorted(result)}"
    p = result["placement"]
    assert p["source"] == "global"
    assert p["effective_target_id"] == THIS_MACHINE_ID


def test_ask_invocation_placement(ask_rig):
    """Ask with explicit inference_target_id -> source 'invocation'."""
    _db, service = ask_rig
    result = asyncio.run(
        service.ask(OWNER, "hello", inference_target_id="ask_profile", operation_capability=CLASSIC)
    )
    assert result["placement"]["source"] == "invocation"
    assert result["placement"]["effective_target_id"] == "ask_profile"
