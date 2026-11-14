"""The Room's declared edit metadata survives both real HTTP writes and read-back."""
from scripts.record_room_wires import edit14
from tests.integration.test_desk_project_room import _hub


def test_room_edit_fields_and_claim_subject_over_http(tmp_path, monkeypatch):
    with _hub(tmp_path, monkeypatch) as hub:
        edit14(hub, monkeypatch)
