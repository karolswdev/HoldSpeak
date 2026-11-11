"""Failed-send identity has no retry effect until a frozen retry is supported."""
from holdspeak.services.channel_contract import FileChannel, Outcome
from tests.unit.test_channel_send_contract import hub
from tests.unit._philo10_send import source, destination, prepare, send


def test_failed_identity_refuses_with_a_source_preview_action_and_never_uses_an_edited_destination(hub,tmp_path,monkeypatch):
    document=source(hub)
    original=destination(hub,tmp_path/"original")
    prepared=prepare(hub,document,original)["send"]
    attempts=[]
    def refused(_self,row,*_a,**_kw):
        attempts.append(row["id"])
        return Outcome("failed","permission_denied")
    monkeypatch.setattr(FileChannel,"dispatch",refused)
    failed=send(hub,{"send_id":prepared["id"],"command_id":"review9b-failed"}).json()["send"]
    assert failed["state"] == "failed"
    other=destination(hub,tmp_path/"changed")
    answer=send(hub,{"send_id":failed["id"],"document_ref":document,"destination_id":other,
                     "preview_digest":failed["payload_digest"],"command_id":"review9b-retry"})
    assert answer.status_code == 409, answer.text
    assert answer.json()["code"] == "failed_retry_requires_preview", answer.text
    assert attempts == [failed["id"]]
    assert not list((tmp_path/"changed").iterdir())
