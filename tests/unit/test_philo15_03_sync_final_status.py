"""PHILO-15-03 (Astra r1 #1): a final transcription status survives sync.

The decoder kept only `record_only`; a producer-made `failed` (or `complete`)
became `active` on the peer, so the peer waited on work that had ended. The
rows here are made by the real import worker and merged by the real
`SyncService.push` -> `_merge_meetings`.
"""
from __future__ import annotations

from holdspeak.db import Database
from holdspeak.services.sync_service import SyncService
from tests.unit.test_philo15_03_import_final_status import _Explodes, _Words, _import
from tests.unit.test_phase143_inference_assignments import OWNER


def _through_sync(source: Database, tmp_path) -> Database:
    destination = Database(tmp_path / "peer.db")
    payload = SyncService(source).pull(OWNER)
    SyncService(destination).push(OWNER, payload)
    return destination


def test_a_failed_import_stays_failed_on_the_peer(tmp_path):
    source, meeting_id = _import(tmp_path, lambda _cfg: _Explodes())
    assert source.meetings.get_meeting(meeting_id).transcription_status == "failed"

    peer = _through_sync(source, tmp_path).meetings.get_meeting(meeting_id)

    assert peer is not None
    assert peer.intel_status == "import_failed"
    assert peer.transcription_status == "failed"
    assert peer.transcription_status_detail == {
        "reason_code": "import_failed", "cause": "UNEXPECTED ERROR",
    }


def test_a_complete_import_stays_complete_on_the_peer(tmp_path):
    source, meeting_id = _import(tmp_path, lambda _cfg: _Words())

    peer = _through_sync(source, tmp_path).meetings.get_meeting(meeting_id)

    assert peer.transcription_status == "complete"
    assert peer.transcription_status_detail is None
