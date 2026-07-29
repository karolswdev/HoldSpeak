from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak import desktop_typing
from holdspeak.db import get_database, reset_database
from holdspeak.desktop_typing import DesktopTypeRefused, type_text_from_owner_gesture
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.principals import Principal, PrincipalKind


class _Typer:
    def __init__(self, on_type: Any = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.on_type = on_type

    def type_text(
        self, text: str, *, target_profile: str | None = None, submit: bool = False
    ) -> None:
        if self.on_type is not None:
            self.on_type()
        self.calls.append(
            {"text": text, "target_profile": target_profile, "submit": submit}
        )


@pytest.fixture(autouse=True)
def _database(tmp_path, monkeypatch):
    reset_database()
    get_database(tmp_path / "desktop-type.db")
    kernel_runtime._broker = None
    kernel_runtime._database_id = None
    monkeypatch.setattr(desktop_typing, "_FOCUS", desktop_typing._FocusTracker())
    yield
    reset_database()
    kernel_runtime._broker = None
    kernel_runtime._database_id = None


def test_direct_gesture_executes_without_external_decision_and_journals_no_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(desktop_typing, "_focused_signature", lambda: "mac:42:editor")
    effect_states: list[str] = []

    def _observe_state() -> None:
        with get_database()._connection() as conn:
            row = conn.execute(
                "SELECT state FROM kernel_operations WHERE name='desktop.type_text' "
                "ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        effect_states.append(str(row["state"]))

    typer = _Typer(_observe_state)

    result = type_text_from_owner_gesture(
        "private dictated words",
        typer=typer,
        gesture="hold_release",
        target_profile="editor",
        submit=False,
    )

    assert typer.calls == [
        {"text": "private dictated words", "target_profile": "editor", "submit": False}
    ]
    assert effect_states == ["claimed"]
    assert result["state"] == "succeeded"
    native = result["native_receipt"]
    assert native["authority_basis"] == "direct_gesture"
    assert native["text_bytes"] == len("private dictated words".encode())
    assert native["payload_sha256"].startswith("sha256:")
    assert native["head"] == "desktop text 22 bytes submit=False"
    assert "private dictated words" not in json.dumps(native)

    owner = Principal(PrincipalKind.OWNER, "owner-session")
    readback = kernel_runtime._service().read(
        [f"operation:{result['operation_id']}"], "full", "committed", owner
    )
    encoded = json.dumps(readback, sort_keys=True)
    assert readback["objects"][0]["native_receipts"][0]["outcome"] == "succeeded"
    assert "private dictated words" not in encoded


def test_focus_generation_change_refuses_before_driver_and_receipts(monkeypatch) -> None:
    signatures = iter(("mac:42:editor", "mac:43:terminal"))
    monkeypatch.setattr(desktop_typing, "_focused_signature", lambda: next(signatures))
    typer = _Typer()

    with pytest.raises(DesktopTypeRefused) as caught:
        type_text_from_owner_gesture(
            "must not land",
            typer=typer,
            gesture="companion_send",
            submit=False,
            requested_target="agent_fallback",
        )

    assert caught.value.reason == "desktop_focus_generation_changed"
    assert typer.calls == []
    receipt = caught.value.receipt
    assert receipt["state"] == "refused"
    assert receipt["native_receipt"]["outcome"] == "desktop_focus_generation_changed"
    assert receipt["native_receipt"]["authority_basis"] == "direct_gesture"
    assert "must not land" not in json.dumps(receipt)


def test_agent_cannot_relabel_itself_as_direct_gesture(monkeypatch) -> None:
    monkeypatch.setattr(desktop_typing, "_focused_signature", lambda: "mac:42:editor")
    request_id = "00000000-0000-0000-0000-000000000042"
    raw = {
        "request_schema": 1,
        "request_id": request_id,
        "idempotency_key": "desktop-agent-refusal",
        "operation": {"name": "desktop.type_text", "version": 1},
        "subject_refs": [],
        "target": {"ref": "desktop-input:focus-1"},
        "arguments": {
            "text": "never type this",
            "submit": False,
            "expected_generation": "focus-1",
            "native_id": request_id,
            "gesture": "hold_release",
            "requested_target": "focused",
            "delivery_method": "test",
        },
        "placement": "node:local-desktop",
    }
    agent = Principal(PrincipalKind.AGENT, "agent:test")

    handle = kernel_runtime._service().submit(raw, agent)

    assert handle["state"] == "refused"
    assert handle["receipt"]["outcome"] == "desktop_type_text_owner_gesture_required"
