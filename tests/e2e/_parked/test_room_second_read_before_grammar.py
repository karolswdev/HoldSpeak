"""Parked 2026-11-11: the Room update face retired. Its failed handoff now runs
in room.grammar.app.test.tsx on producer replies; S8 warning/dispatch is kept
in send.app.test.tsx and test_channel_send_contract.py.
"""
from pathlib import Path
from typing import Any
import json
import pytest
from tests.e2e.test_send_glass import TestSendGlass as _SendRig, StandIns, SHOTS, SIZES, ROOM, T


class TestRoomBeforeGrammar(_SendRig):
    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_room_pick_when_the_update_read_fails(self, width: int) -> None:
        """replaces: tests/e2e/test_philo13_15_send_to_glass.py::TestSendToGlass::test_room_pick_when_the_update_read_fails

        Astra C5 check, condition 1: the menu's latest-update read succeeds, the Room's own
        read of that update fails. The pick keeps the handoff and shows CANNOT READ LATEST
        UPDATE + Retry in the Room's SEND well; Retry (the real read) recovers to the well."""
        self._session(width, lambda si, folder: self._room_second_read_fails(si, folder))

    def _room_second_read_fails(self, si: StandIns, folder: Path) -> None:
        page = self.page
        preview_wires: list[dict[str, Any]] = []

        def capture_preview(response: Any) -> None:
            if response.request.method != "POST" or "/api/channels/preview" not in response.url:
                return
            try:
                answer = response.json()
            except Exception:  # noqa: BLE001
                return
            if isinstance(answer, dict):
                preview_wires.append(answer)

        page.on("response", capture_preview)
        # Use the real update producer with an untouched model claim so this
        # existing Room handoff case exercises Send S8 at both canvas sizes
        # without inventing a hub fixture.
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_update_service import ProjectUpdateService

        project_id = "p-send-s8"
        self.db.projects.create_project(project_id=project_id, name="Unchecked delivery")
        updates = ProjectUpdateService(self.db, project_service=ProjectService(self.db))
        owner = Principal(PrincipalKind.OWNER, "karol")
        model_body = "## Progress\n\n- **[UNVERIFIED]** The rollout is complete.\n"
        model_claims = json.dumps([{
            "span_id": "s_progress_0", "text": "The rollout is complete.",
            "refs": [], "section": "progress", "kind": "inference",
            "support": "unknown", "acceptance": "unreviewed", "verified": False,
        }])

        def model(_service: Any, _principal: Any, _det_claims: Any, _det_sections: Any,
                  _det_body_md: Any, known_names: Any = (), memory: Any = None) -> tuple[str, str, str, str, str]:
            return model_body, model_claims, "model:browser_s8", "192.0.2.123:8080", "s8-test-model"

        self.monkeypatch.setattr(ProjectUpdateService, "_draft_with_model", model)
        draft = updates.draft_update(owner, project_id, generator="model")
        updates.publish_update(owner, draft["id"])
        update_ref = f"project_update:{draft['id']}"
        from holdspeak.services.channel_contract import render_update
        rendered = render_update(self.db, draft["id"])
        assert rendered.preview_warning == "Not checked yet: no claim in this update was accepted", {
            "body": rendered.body_md, "claims": self.db.project_updates.get_update(draft["id"])["claims_json"],
        }
        si.project_id = project_id

        self._open_surface("open-project-memory", f"project:{project_id}", ROOM)
        assert self._send_to(ROOM) == "Send to"           # the menu's read: known, the latest update
        si.set_hold("failed")                              # the Room's own read of that update fails
        self._pick("Team updates")
        fail = page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]")
        fail.wait_for(timeout=T)
        assert "Cannot read latest update" in fail.inner_text(), fail.inner_text()
        assert page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc^='project_update:']").count() == 0
        self._wait(600)
        for sel in ("[data-testid=room-latest-unreadable]", "[data-testid=room-latest-unreadable-retry]"):
            box = page.locator(f"[id='{ROOM}'] {sel}").bounding_box()
            assert box and box["y"] >= 0 and box["y"] + box["height"] <= SIZES[self.width], (sel, box)
        self._glass("C5-17a")
        self._shot("C5-17a-room-second-read-fails")
        si.set_hold(None)
        self._tap(page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable-retry]"), 900)
        page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='{update_ref}'] "
                     "[data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        assert page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]").count() == 0
        self._glass("C5-17b")
        self._shot("C5-17b-room-second-read-retry")

        # S8: the published unchecked words remain in the frozen preview, the
        # warning is visible above them, and the owner's actual press sends to
        # the private FILE folder and leaves a saved receipt in the hub DB.
        well = page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='{update_ref}']")
        warning = "Not checked yet: no claim in this update was accepted"
        assert any((answer.get("preview") or {}).get("warning") == warning for answer in preview_wires), json.dumps(preview_wires, indent=2)
        fields = well.locator("[data-testid=send-preview-field]").all_inner_texts()
        assert any(warning in field for field in fields), fields
        preview_text = well.locator("[data-testid=send-preview-body]").inner_text()
        assert "The rollout is complete." in preview_text
        send = page.locator(f"[id='{ROOM}'] [data-testid=send-verb]")
        assert send.is_enabled()
        self._shot("S8-unchecked-preview")
        send.click()
        sent = page.locator(f"[id='{ROOM}'] [data-testid=send-sent]")
        sent.wait_for(timeout=T)
        self._wait(600)
        rows = self._db_sends(update_ref)
        assert len(rows) == 1 and rows[0]["state"] == "sent", rows
        assert rows[0]["proof"]["unchecked"] is True
        assert rows[0]["proof"]["warning"] == warning
        path = Path(rows[0]["proof"]["path"])
        assert path.parent.resolve() == folder.resolve() and path.read_text().endswith("The rollout is complete.\n"), path
        (SHOTS / f"S8-unchecked-facts-{self.width}.json").write_text(json.dumps({
            "width": self.width, "document_ref": update_ref, "warning": warning,
            "preview": preview_text, "receipt": rows[0], "path": str(path),
            "file": path.read_text(),
        }, indent=2) + "\n")
        self._shot("S8-unchecked-sent")
