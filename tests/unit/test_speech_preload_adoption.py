"""HS-143-08 Phase D slice 2: the MLX warm through the engine door.

These tests use the composed Database/broker/door/session and a normally
constructed ``Transcriber``. Only MLX's physical library hooks are bounded; the
door's chain, the warm job, its receipts, and reuse are production code.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.principals import PrincipalKind
from holdspeak.speech_session import (
    SpeechSessionRefused,
    admit_one_shot_session,
    hold_gesture_principal,
    preload_service_admission,
)
from holdspeak.transcribe import Transcriber, TranscriberError, _MlxTranscriber

from tests.unit.test_dictation_session_admission import (
    AUDIO_SENTINEL,
    TEXT_SENTINEL,
    _build_host,
    _install_historical_nonlocal_speech_assignment,
    _operations,
)

pytestmark = [pytest.mark.timeout(60, method="signal"), pytest.mark.usefixtures("whisper_on_device")]


def _speech_outcomes(db: Any) -> list[str]:
    """The receipts of the speech jobs (warm and transcription), in order."""
    with db._connection() as conn:
        return [str(row[0]) for row in conn.execute(
            """SELECT r.outcome FROM kernel_operations o
                 JOIN kernel_receipts r ON r.operation_id=o.operation_id
                WHERE o.name='inference.invoke' AND o.native_id LIKE 'speech\\_%' ESCAPE '\\'
                ORDER BY o.created_at"""
        )]


def _production_mlx(monkeypatch, *, holder: Any, silent: Any = None) -> tuple[Transcriber, list[str]]:
    """Construct the real public Transcriber while bounding MLX library calls."""
    calls: list[str] = []
    real_import = importlib.import_module
    mlx_core = SimpleNamespace(float16="float16")

    class Whisper:
        @staticmethod
        def transcribe(_audio: Any, **_kwargs: Any) -> dict[str, str]:
            calls.append("audio")
            return {"text": TEXT_SENTINEL}

    def imported(name: str, package: str | None = None) -> Any:
        if name == "mlx.core":
            return mlx_core
        if name == "mlx_whisper":
            return Whisper()
        return real_import(name, package)

    monkeypatch.setattr("holdspeak.transcribe._resolve_backend", lambda _backend: "mlx")
    monkeypatch.setattr("holdspeak.transcribe.importlib.import_module", imported)

    def model_holder(self: _MlxTranscriber, candidate: str) -> str:
        calls.append("model-holder:" + candidate)
        return holder(candidate)

    def silent_audio(self: _MlxTranscriber, candidate: str) -> str:
        calls.append("silent-audio:" + candidate)
        if silent is None:
            return "silent-audio"
        return silent(candidate)

    # These two methods are the external MLX physical boundary.  The real
    # _MlxTranscriber lifecycle walker, public Transcriber, and routed adapter
    # remain intact.
    monkeypatch.setattr(_MlxTranscriber, "_model_holder_get", model_holder)
    monkeypatch.setattr(_MlxTranscriber, "_silent_audio_load", silent_audio)
    return Transcriber(model_name="base", backend="mlx", language="auto"), calls



@pytest.mark.parametrize("boundary", ["mesh", "private_network"])
def test_parentless_preload_refuses_nonlocal_speech_before_constructing(tmp_path, monkeypatch, boundary):
    """Coverage 3: a nonlocal speech assignment cannot become a local warm."""
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    _install_historical_nonlocal_speech_assignment(db, boundary)
    constructed: list[str] = []
    monkeypatch.setattr("holdspeak.transcribe.Transcriber", lambda **_kwargs: constructed.append("built"))

    with pytest.raises(SpeechSessionRefused) as raised:
        preload_service_admission(config_snapshot=Config())

    assert raised.value.reason == "inference_route_boundary_unsupported"
    assert constructed == []
    assert _operations(db, name="inference.invoke") == []


@pytest.mark.requires_local_dictation_route
def test_preload_freezes_one_sequence_and_stops_on_indeterminate(tmp_path, monkeypatch):
    """Coverage 5/6: one P=1 operation, frozen stages, unknown never advances."""
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)

    from holdspeak.kernel.provider_signals import ProviderIndeterminate

    transcriber, calls = _production_mlx(
        monkeypatch,
        holder=lambda _candidate: (_ for _ in ()).throw(ProviderIndeterminate()),
        silent=lambda _candidate: (_ for _ in ()).throw(AssertionError("must not advance")),
    )
    admission = preload_service_admission(config_snapshot=Config())
    frozen = admission.frozen_preload_material()
    assert frozen["strategy_sequence"] == ["model-holder", "silent-audio"]
    assert frozen["stop_rules"] == [
        "success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion"
    ]

    with pytest.raises(TranscriberError):
        transcriber.warm(admission)

    assert [call.split(":", 1)[0] for call in calls] == ["model-holder"]
    assert _speech_outcomes(db) == ["indeterminate"]


@pytest.mark.requires_local_dictation_route
def test_revision_mismatch_reloads_but_matching_receipt_reuses(tmp_path, monkeypatch):
    """Coverage 4/7: deployment revision plus durable receipt gates reuse."""
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    transcriber, calls = _production_mlx(monkeypatch, holder=lambda _candidate: "model-holder")
    prewarm = preload_service_admission(config_snapshot=Config())
    transcriber.warm(prewarm)
    first_loads = [call for call in calls if call.startswith("model-holder:")]
    assert len(first_loads) == 1

    # The later production session has the same frozen identity and the durable
    # parentless receipt, so it performs no second physical model load.
    matching = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=Config()
    )
    assert transcriber.transcribe(np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=matching.transcription()) == TEXT_SENTINEL
    assert [call for call in calls if call.startswith("model-holder:")] == first_loads
    matching.close("succeeded")

    # A different frozen deployment revision, even with identical model strings,
    # is not reusable.  This mutates only the runtime provenance carrier; the
    # second session and bounded lifecycle remain production objects.
    transcriber._impl._holdspeak_preload_provenance["deployment_revision_id"] = "dep_other_revision"
    mismatched = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=Config()
    )
    assert transcriber.transcribe(np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=mismatched.transcription()) == TEXT_SENTINEL
    assert len([call for call in calls if call.startswith("model-holder:")]) == 2
    mismatched.close("succeeded")
    # warm, transcription (reused), warm again, transcription
    assert _speech_outcomes(db) == ["succeeded"] * 4


@pytest.mark.requires_local_dictation_route
def test_failed_prewarm_defers_to_first_lawful_transcription(tmp_path, monkeypatch):
    """Coverage 8: a failed accelerator never makes capture unavailable."""
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    failing = {"value": True}

    def holder(_candidate: str) -> str:
        if failing["value"]:
            raise RuntimeError("offline model store")
        return "model-holder"

    def silent(_candidate: str) -> str:
        if failing["value"]:
            raise RuntimeError("offline model store")
        return "silent-audio"

    transcriber, calls = _production_mlx(monkeypatch, holder=holder, silent=silent)
    with pytest.raises(TranscriberError):
        transcriber.warm(preload_service_admission(config_snapshot=Config()))
    assert [call.split(":", 1)[0] for call in calls] == [
        "model-holder", "silent-audio", "model-holder", "silent-audio"
    ]

    failing["value"] = False
    session = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=Config()
    )
    assert transcriber.transcribe(np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()) == TEXT_SENTINEL
    session.close("succeeded")
    assert len([call for call in calls if call.startswith("model-holder:")]) == 3
    assert _speech_outcomes(db) == ["failed", "succeeded", "succeeded"]
