"""Static cross-client locks for HS-93-01's visible subtraction."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "apple/App/MeetingCapture/DeskDioramaStage.swift"
APP = ROOT / "apple/App/MeetingCaptureApp.swift"


def _between(source: str, start: str, end: str) -> str:
    return source.split(start, 1)[1].split(end, 1)[0]


def test_flagship_desk_has_three_direct_daily_starts() -> None:
    source = STAGE.read_text(encoding="utf-8")
    starts = _between(source, "struct DioDailyStarts: View", "// THE ROUTE SHEET")

    assert '.accessibilityLabel("Dictate")' in starts
    assert '.accessibilityLabel("Record")' in source
    assert '.accessibilityLabel("Create")' in starts
    assert "onDictate" in starts and "onRecord" in starts
    assert "dictationWorkroom = DioWorkroomRoute" in source
    assert "startCapture(desktop: false)" in source


def test_native_create_is_one_progressive_five_choice_menu() -> None:
    source = STAGE.read_text(encoding="utf-8")
    starts = _between(source, "struct DioDailyStarts: View", "// THE ROUTE SHEET")
    level = _between(source, "@ViewBuilder private func level", "private func editingNoteBinding")

    for choice in (
        "Note · write or dictate",
        "Zone · place related items",
        "Knowledge · gather context",
        "Persona · save behavior",
        "Workflow · build repeatable steps",
    ):
        assert choice in starts
    assert "Menu {" in starts
    assert "New Note" not in level
    assert "New Knowledge" not in level
    assert "New Zone" not in level
    assert "workbenchWorkroom = DioWorkroomRoute" in source


def test_first_boot_is_task_first_and_does_not_teach_architecture() -> None:
    source = STAGE.read_text(encoding="utf-8")
    first_boot = _between(source, "struct DioFirstBoot: View", "// A long-press menu entry")

    assert 'Text("Start on your Desk")' in first_boot
    assert "Dictate text, record a meeting, or create a Desk item." in first_boot
    for removed in (
        "Your desk is ready",
        "Meetings become objects",
        "Your AI core waits below",
        "Tap to record your first meeting",
    ):
        assert removed not in source


def test_classic_fallback_names_coder_and_paired_boundaries_honestly() -> None:
    source = APP.read_text(encoding="utf-8")
    assert 'Text("Coder sessions")' in source
    assert 'Text("Live coding work")' in source
    assert 'Text("Agent Desk")' not in source
    assert 'Text("Your live agents")' not in source
    assert "ON-DEVICE · LOCAL MESH" not in source
    assert 'Text("PAIRED · \\(peers.displayName.uppercased())")' in source
