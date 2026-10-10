"""PHILO-17 speech: one speech-readiness truth, read by every face.

A fresh desk without the speech model said READY / PASS / "Listening for
speech" and lost the owner's first meeting. `whisper_models.speech_readiness`
is the one disk-only answer; the doctor's "Speech model" row, the boot warm,
the meeting session and the Set up local AI status all read it. No test here
makes a network request: the files are written to a temporary HOME.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.memory.local_model import PinnedModel
from holdspeak.whisper_models import (
    SPEECH_NOT_SET_UP,
    configured_speech_readiness,
    pinned_whisper_dir,
    speech_readiness,
)

CONFIG = b'{"model_type": "whisper"}'
WEIGHTS = b"whisper-weights-" * 2_000
REPO = "mlx-community/whisper-base-mlx"


def _pin(filename: str, content: bytes) -> PinnedModel:
    return PinnedModel(
        name=filename, label="whisper-base-mlx", repository=REPO, revision="r1", filename=filename,
        sha256=hashlib.sha256(content).hexdigest(), size=len(content), license="MIT",
        architecture="whisper", context_ceiling=0, magic=b"",
    )


PINS = (_pin("config.json", CONFIG), _pin("weights.npz", WEIGHTS))


@pytest.fixture()
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    where = tmp_path / "home"
    where.mkdir()
    for name in ("HF_HUB_CACHE", "HF_HOME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("holdspeak.whisper_models._PINNED", {("mlx", "base"): PINS})
    return where


def _land(home: Path) -> None:
    folder = pinned_whisper_dir(REPO, home)
    folder.mkdir(parents=True)
    (folder / "config.json").write_bytes(CONFIG)
    (folder / "weights.npz").write_bytes(WEIGHTS)


def test_missing_pinned_model_is_not_ready_and_names_its_size(home: Path) -> None:
    speech = speech_readiness("base", "mlx", home=home)
    assert speech == {
        "model": "base", "backend": "mlx", "state": "will_download",
        "ready": False, "bytes": len(CONFIG) + len(WEIGHTS),
    }


def test_landed_pinned_model_is_ready(home: Path) -> None:
    _land(home)
    speech = speech_readiness("base", "mlx", home=home)
    assert speech["state"] == "on_device"
    assert speech["ready"] is True
    assert speech["bytes"] == 0


def test_a_model_setup_cannot_get_is_not_covered(home: Path) -> None:
    speech = speech_readiness("small", "mlx", home=home)
    assert speech["state"] == "not_covered"
    assert speech["ready"] is False


def test_configured_readiness_reads_the_config_model(home: Path) -> None:
    config = SimpleNamespace(model=SimpleNamespace(name="base", backend="mlx"))
    assert configured_speech_readiness(config=config, home=home)["state"] == "will_download"
    _land(home)
    assert configured_speech_readiness(config=config, home=home)["ready"] is True


def test_doctor_speech_row_fails_until_the_model_lands(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.commands.doctor as doctor

    monkeypatch.setenv("HOME", str(home))
    config = SimpleNamespace(model=SimpleNamespace(name="base", backend="mlx"))
    row = doctor._check_speech_model(config)  # type: ignore[arg-type]
    assert row.name == "Speech model"
    assert row.status == "FAIL"
    assert row.detail.startswith("Speech is not set up")
    assert row.fix == "Set up speech"

    _land(home)
    assert doctor._check_speech_model(config).status == "PASS"  # type: ignore[arg-type]


def test_doctor_lists_the_speech_row_after_the_backend_row(monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.commands.doctor as doctor

    names = [check.name for check in doctor.collect_doctor_checks(skip_network=True)]
    assert names.index("Speech model") == names.index("Transcription backend") + 1


def test_boot_warm_reads_the_same_truth(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.runtime.transcriber_state import TranscriberStateMixin

    monkeypatch.setenv("HOME", str(home))
    host = SimpleNamespace(config=SimpleNamespace(model=SimpleNamespace(name="base", backend="mlx")))
    assert TranscriberStateMixin._whisper_model_on_disk(host) is False  # type: ignore[arg-type]
    _land(home)
    assert TranscriberStateMixin._whisper_model_on_disk(host) is True  # type: ignore[arg-type]


def test_meeting_list_row_carries_the_speech_reason() -> None:
    from holdspeak.db.models import MeetingSummary
    from holdspeak.services.meeting_service import MeetingService

    detail = {"family": "speech-recognition-route-assignments", "reason_code": SPEECH_NOT_SET_UP,
              "repair": "set_up_speech"}
    row = MeetingSummary(
        id="m-speech", started_at=datetime(2026, 10, 10, 9, 0), ended_at=datetime(2026, 10, 10, 9, 1),
        title=None, duration_seconds=6.0, segment_count=0, action_item_count=0, tags=[],
        transcription_status="record_only", transcription_status_detail=detail,
    )
    payload = MeetingService._summary_payload(row)
    assert payload["transcription_status"] == "record_only"
    assert payload["transcription_status_detail"]["reason_code"] == "speech_not_set_up"
