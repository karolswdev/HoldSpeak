"""HS-107-01 boundary contract, preserved through the HS-107-02 reroute."""
from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction
from holdspeak.kernel.model import KernelRefused, OperationRequest
from holdspeak.kernel.process_input import ProcessInputCodec
from holdspeak.operation_policy import resolve_dictation_policy
from holdspeak.runtime.dictation_capture import DictationCaptureMixin

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "holdspeak" / "kernel" / "effect_ledger.json"
_AUDIO = np.zeros(16000, dtype=np.float32)


class _Typer:
    def __init__(self, events: list[Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.events = events

    def type_text(
        self, text: str, *, target_profile: str | None = None, submit: bool = False
    ) -> None:
        call = {"text": text, "target_profile": target_profile, "submit": submit}
        self.calls.append(call)
        if self.events is not None:
            self.events.append(("effect", call))


class _CaptureRig:
    def __init__(self, *, preview: bool = False) -> None:
        self.config = Config()
        self.config.control_mode = "neutral"
        self.config.dictation.preview_before_type = preview
        self.transcription_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.runtime_status: dict[str, Any] = {}
        self.events: list[Any] = []
        self.typer = _Typer(self.events)
        self.dictation_previews: dict[str, dict[str, Any]] = {}
        self.server = None
        self.text_processor = SimpleNamespace(process=self._process)

    def _ensure_transcriber_loaded(self) -> Any:
        return SimpleNamespace(transcribe=self._transcribe)

    def _transcribe(self, _audio: np.ndarray) -> str:
        self.events.append("transcribe")
        return "bounded words"

    def _process(self, text: str) -> str:
        self.events.append("punctuation")
        return text

    def _maybe_dispatch_voice_command(self, text: str, session: Any) -> None:
        return None

    def _maybe_run_dictation_pipeline(self, text: str, **_kwargs: Any) -> str:
        self.events.append("rewrite")
        return text

    def _try_tmux_agent_reply(self, text: str, session: Any) -> bool:
        return False

    def _paste_target_profile(self, session: Any) -> None:
        return None

    def _set_runtime_activity(self, *args: Any, **kwargs: Any) -> None:
        return None

    def _set_voice_state(self, *args: Any, **kwargs: Any) -> None:
        return None

    def _mark_first_dictation(self) -> None:
        return None

    _transcribe_and_type = DictationCaptureMixin._transcribe_and_type
    _arm_dictation_preview = DictationCaptureMixin._arm_dictation_preview
    consume_dictation_preview = DictationCaptureMixin.consume_dictation_preview
    type_dictation_preview = DictationCaptureMixin.type_dictation_preview


def test_ordinary_commit_is_one_final_desktop_effect() -> None:
    rig = _CaptureRig()

    rig._transcribe_and_type(_AUDIO)

    assert rig.events[:3] == ["transcribe", "punctuation", "rewrite"]
    assert rig.events[3][0] == "effect"
    assert rig.typer.calls == [
        {"text": "bounded words", "target_profile": None, "submit": False}
    ]
    snapshot, decision = resolve_dictation_policy(rig.config)
    assert decision.authority_basis == "direct_gesture"
    assert snapshot["operation"]["effect_class"] == "desktop/type_text"


def test_preview_commits_only_when_one_shot_type_is_consumed() -> None:
    rig = _CaptureRig(preview=True)

    rig._transcribe_and_type(_AUDIO)

    assert rig.typer.calls == []
    assert len(rig.dictation_previews) == 1
    assert rig.runtime_status["last_operation_policy"]["policy"]["authority_basis"] == (
        "configured_preview"
    )
    token = next(iter(rig.dictation_previews))

    assert rig.type_dictation_preview(token) == "bounded words"
    assert rig.typer.calls == [
        {"text": "bounded words", "target_profile": None, "submit": False}
    ]
    assert rig.type_dictation_preview(token) is None
    assert len(rig.typer.calls) == 1


def test_type_text_voice_command_effect_is_configured_payload_not_keyword() -> None:
    config = Config()
    config.dictation.macros = MacrosConfig(
        enabled=True,
        items=[VoiceMacro("standup", VoiceMacroAction("type_text", "## Standup"))],
    )
    typer = _Typer()
    rig = SimpleNamespace(
        config=config,
        typer=typer,
        _paste_target_profile=lambda _session: "editor",
        _set_runtime_activity=lambda *args, **kwargs: None,
    )

    result = DictationCaptureMixin._maybe_dispatch_voice_command(rig, "standup", None)

    assert result is not None and result.ok and result.kind == "type_text"
    assert typer.calls == [
        {"text": "## Standup", "target_profile": "editor", "submit": False}
    ]


def test_remote_focused_send_commits_without_submit() -> None:
    typer = _Typer()
    rig = SimpleNamespace(
        typer=typer,
        config=Config(),
        _focused_target_profile=lambda: "editor",
        _mark_first_dictation=lambda: None,
    )

    result = DictationCaptureMixin._deliver_remote_dictation_focused(rig, "remote words")

    assert result["delivered"] is True
    assert result["method"] == "desktop.type_text"
    assert result["target"].startswith("desktop-input:")
    assert result["operation_id"].startswith("op_")
    assert typer.calls == [
        {"text": "remote words", "target_profile": "editor", "submit": False}
    ]


def test_remote_agent_send_resolves_to_targeted_submit(monkeypatch) -> None:
    sent: list[dict[str, Any]] = []
    session = SimpleNamespace(tmux_pane="remote:3.1", session_id="s3")
    monkeypatch.setattr(
        "holdspeak.agent_context.get_recent_awaiting_agent_session",
        lambda **_kwargs: session,
    )

    def _submit(**kwargs: Any) -> dict[str, Any]:
        sent.append(kwargs)
        return {"operation_id": "op_remote", "command_id": "cmd_remote"}

    monkeypatch.setattr(
        "holdspeak.delivery.direct_gesture_input.submit_process_input_from_owner_gesture",
        _submit,
    )
    rig = SimpleNamespace(
        typer=None,
        state_lock=threading.Lock(),
        runtime_status={},
        _mark_first_dictation=lambda: None,
        _agent_tmux_pane=lambda candidate: candidate.tmux_pane,
    )
    rig._try_tmux_agent_reply = lambda text, candidate: (
        DictationCaptureMixin._try_tmux_agent_reply(rig, text, candidate)
    )

    result = DictationCaptureMixin._deliver_remote_dictation(rig, "remote answer")

    assert result == {
        "delivered": True,
        "method": "process.input",
        "target": "remote:3.1",
    }
    assert sent == [
        {
            "pane": "remote:3.1",
            "text": "remote answer",
            "session_key": "s3",
            "agent": "",
        }
    ]


def test_dictation_to_agent_is_process_input_with_submit(monkeypatch) -> None:
    sent: list[dict[str, Any]] = []

    def _submit(**kwargs: Any) -> dict[str, Any]:
        sent.append(kwargs)
        return {"operation_id": "op_19", "command_id": "cmd_19"}

    monkeypatch.setattr(
        "holdspeak.delivery.direct_gesture_input.submit_process_input_from_owner_gesture",
        _submit,
    )
    rig = SimpleNamespace(
        state_lock=threading.Lock(),
        runtime_status={},
        _agent_tmux_pane=lambda _session: "%19",
    )

    delivered = DictationCaptureMixin._try_tmux_agent_reply(
        rig, "answer now", SimpleNamespace(tmux_pane="%19", session_id="s19")
    )

    assert delivered is True
    assert sent == [
        {"pane": "%19", "text": "answer now", "session_key": "s19", "agent": ""}
    ]
    assert rig.runtime_status["last_kernel_operation_id"] == "op_19"


def _process_request(**arguments: Any) -> OperationRequest:
    return OperationRequest(
        request_schema=1,
        request_id=str(uuid.uuid4()),
        idempotency_key="dictation-boundary-test",
        name="process.input",
        version=1,
        target_ref="process:terminal_19",
        placement="node:local",
        arguments={
            "text": "receipt must not contain these words",
            "submit": True,
            "expected_generation": "gen_4",
            "command_id": str(uuid.uuid4()),
            "session_key": "session_4",
            "agent": "coder",
            "expected_sequence": 1,
            "expires_in_seconds": 30,
            **arguments,
        },
    )


def test_process_input_receipt_material_is_hashed_and_content_free() -> None:
    admission = ProcessInputCodec(SimpleNamespace()).validate(_process_request())

    assert admission.payload_hash.startswith("sha256:")
    assert len(admission.payload_hash) == len("sha256:") + 64
    assert admission.head == "terminal text 36 bytes submit=True"
    assert "receipt must not contain" not in admission.head
    assert len(admission.head) <= 120

    try:
        ProcessInputCodec(SimpleNamespace()).validate(
            _process_request(audio_frames=[b"never journal audio"])
        )
    except KernelRefused as exc:
        assert exc.reason == "journal_content_forbidden"
    else:
        raise AssertionError("audio frames reached process.input admission")


def test_effect_ledger_records_the_typing_family_migration() -> None:
    ledger = json.loads(_LEDGER.read_text())
    ids = {site["id"] for site in ledger["sites"]}
    debt = [
        site
        for site in ledger["sites"]
        if site["status"] not in {"covered", "read", "exempt_computation"}
    ]

    assert len(debt) == ledger["expected"]["not_covered"] == 18
    assert not {"T03", "T04", "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08"} & ids
    desktop = next(site for site in ledger["sites"] if site["id"] == "D09")
    assert desktop["status"] == "covered"
    assert desktop["selector"]["scope"] == "type_text_from_owner_gesture"


def test_effect_ledger_debt_excludes_all_triaged_non_debt() -> None:
    ledger = json.loads(_LEDGER.read_bytes())
    debt = [
        site
        for site in ledger["sites"]
        if site["status"] not in {"covered", "read", "exempt_computation"}
    ]
    reads = [site for site in ledger["sites"] if site["status"] == "read"]
    exempt = [
        site for site in ledger["sites"]
        if site["status"] == "exempt_computation"
    ]

    assert len(debt) == ledger["expected"]["not_covered"]
    assert len(reads) == ledger["expected"].get("reads", 0)
    assert len(exempt) == ledger["expected"].get("exempt_computation", 0)
