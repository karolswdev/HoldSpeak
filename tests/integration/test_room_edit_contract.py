"""The Room's declared edit metadata survives both real HTTP writes and read-back."""
from scripts.record_room_wires import edit14
from tests.integration.test_desk_project_room import _hub


def test_room_edit_fields_and_claim_subject_over_http(tmp_path, monkeypatch):
    with _hub(tmp_path, monkeypatch) as hub:
        wire = edit14(hub, monkeypatch)
        current = wire["saved"]["update"]
        claim = current["editable_claims"][0]
        edit = {"span_id":claim["span_id"], "text":claim["text"], "values":{**claim["values"], "subject":"Replacement"}}
        before = hub.db.project_updates.get_update(current["id"])
        for binding in (None, {}, {"id":"other", "revision":"old"}):
            payload = {"claim_edits":[edit]}
            if binding is not None:
                payload["binding"] = binding
            response = hub.client.put(f"/api/updates/{current['id']}", json=payload)
            assert response.status_code == 409, response.text
            assert response.json()["code"] == "answer_stale"
            assert hub.db.project_updates.get_update(current["id"]) == before
