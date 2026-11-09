# PARKED 2026-11-09 (door/own-choice-park-waist): resolve_thought_placement is parked: the Thought runs through the engine door.
# Moved from tests/unit/test_inference_targets.py; its helpers are still there.

from tests.unit.test_inference_targets import *  # noqa: F401,F403
from holdspeak.inference_targets import resolve_thought_placement  # parked: no longer exists


def test_thought_placement_uses_its_selected_target_and_blank_means_this_device(
    rig, monkeypatch, tmp_path
) -> None:
    db, _ = rig
    db.profiles.upsert(
        profile_id="openrouter-qwen",
        name="OpenRouter Qwen",
        kind="openAICompatible",
        base_url="https://openrouter.ai/api/v1",
        model="qwen/qwen3.8-27b",
        requires_key=False,
    )
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="openrouter-qwen")
        ),
    )
    selected = resolve_thought_placement(db)
    assert selected.target.id == "openrouter-qwen"
    assert selected.target.model == "qwen/qwen3.8-27b"

    local = tmp_path / "local.gguf"
    local.touch()
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id=None),
            meeting=SimpleNamespace(intel_realtime_model=str(local)),
        ),
    )
    assert resolve_thought_placement(db).target.id == "this_machine"

