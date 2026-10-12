"""React ambient Qlippy and HUD locks."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_qlippy_is_react_owned_and_never_autonomous() -> None:
    source = (REPO / "web/src/components/AmbientLayer.tsx").read_text()
    assert "function Qlippy" in source
    assert 'subscribe("*"' in source
    assert "actuator_proposed" in source
    assert "Approve" in source and "Decline" in source and "Dismiss" in source
    assert "apiFetch" in source
    assert "useEffect" in source


def test_ambient_layer_carries_preview_queue_waveform_and_theater() -> None:
    source = (REPO / "web/src/components/AmbientLayer.tsx").read_text()
    for component in ("PreviewCard", "QueueHud", "Waveform", "GenerationTheater"):
        assert f"function {component}" in source
    assert "wake_preview" in source and "audio_level" in source and "intel_status" in source


def test_motion_and_mascot_art_are_local() -> None:
    css = (REPO / "web/src/styles/react-app.css").read_text()
    assert "ambient-qlippy" in css and "qlippy-face" in css
    assert "prefers-reduced-motion" in css
    assert (REPO / "web/public/qlippy").is_dir()
