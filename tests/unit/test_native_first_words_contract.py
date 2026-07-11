"""HS-92-03 locks for the canonical native paired-desktop first-value path."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "apple/App/MeetingCapture/DeskDioramaStage.swift"
DICTATE = ROOT / "apple/App/MeetingCapture/CompanionMesh.swift"


def _between(source: str, start: str, end: str) -> str:
    return source.split(start, 1)[1].split(end, 1)[0]


def test_desktop_choice_presents_real_dictation_and_never_starts_a_meeting() -> None:
    source = STAGE.read_text(encoding="utf-8")
    desktop_choice = _between(source, "onDesktop: {", "onClose:")
    assert "presentDictationWorkroom()" in desktop_choice
    assert "dictationWorkroom = DioWorkroomRoute" in source
    assert "startCapture" not in desktop_choice
    assert "stopCapture" not in desktop_choice
    assert ".fullScreenCover(item: $dictationWorkroom)" in source
    assert "DioWorkroomContainer" in source
    assert "NavigationStack { DictateView() }" in source


def test_release_commits_one_remote_delivery_without_local_meeting_creation() -> None:
    source = DICTATE.read_text(encoding="utf-8")
    stop = _between(source, "func stopAndDeliver() async {", "func preview(")
    deliver = _between(source, "func deliver(_ text:", "#if targetEnvironment(simulator)")

    # MainActor serializes release events; listening is cleared before the first
    # suspension, so a duplicate release returns at the guard.
    assert stop.index("guard listening else { return }") < stop.index("listening = false")
    assert stop.index("listening = false") < stop.index("await WhisperKitTranscriber")
    assert deliver.count("sendRemoteDictation(") == 1
    assert "target: .focused" in deliver
    assert "deliveryID: deliveryID" in deliver
    assert "persistRecovery(text: text" in deliver
    assert "Meeting(" not in stop
    assert "Meeting(" not in deliver


def test_named_destination_is_visible_before_and_after_delivery() -> None:
    source = DICTATE.read_text(encoding="utf-8")
    assert 'Text(model.macName)' in source
    assert 'Text("SENT TO \\(model.macName.uppercased())")' in source
    assert "line.delivered ? \"checkmark.circle.fill\"" in source


def test_native_failures_keep_an_editable_recovery_draft() -> None:
    source = DICTATE.read_text(encoding="utf-8")
    assert '@Published var recoveryText = ""' in source
    assert "TextEditor(text: $model.recoveryText)" in source
    assert 'Button("Retry")' in source
    assert 'Button("Copy")' in source
    assert 'Button("Setup")' in source
    assert "DictationRecoveryStore" in source
    assert "recoveryStore.load()" in source
    assert "clearRecovery()" in source
    assert "DictationAudioRecoveryStore" in source
    assert "audioRecoveryStore.save(chunks)" in source
    assert "audioRecoveryStore.load()" in source
    assert "dictation-recovery.pcm16" in source
    for category in (
        "permissionDenied", "missingModel", "rejectedToken",
        "deliveryConflict", "unreachableDesktop", "noSpeech",
    ):
        assert category in source
