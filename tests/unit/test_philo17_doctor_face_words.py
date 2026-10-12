"""PHILO-17 REFIT: a doctor check's face words.

`face_words(check)` is the short plain sentence the Setup face and the Guide
show; `/api/setup/status` sends it as a section's `detail` and the check's
own technical detail as `raw`. The check's name, status and detail (what the
CLI prints) do not change.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import holdspeak.config as config_module
import holdspeak.setup_status as setup_status
from holdspeak.commands.doctor import DoctorCheck, collect_doctor_checks, face_words
from holdspeak.config import Config


@pytest.mark.parametrize(
    ("check", "words"),
    [
        (DoctorCheck("Dictation AI model", "PASS", "the model file q.gguf is on this device (llama_cpp; auto: fallback to llama_cpp)"),
         "with llama.cpp"),
        (DoctorCheck("Dictation AI model", "PASS", "off (dictation clean-up is disabled; it is optional)"),
         "Off. Dictation clean-up is optional."),
        (DoctorCheck("Speech model", "FAIL", "Speech is not set up: Whisper base (mlx) is not on this device"),
         "No speech model yet"),
        (DoctorCheck("Transcription backend", "PASS", "`auto` resolves to `mlx`"), "Speech to text uses MLX"),
        (DoctorCheck("Where AI runs", "WARN", "This device · not set up yet"), "No AI engine is set up yet"),
        (DoctorCheck("Where AI runs", "WARN", "This device · not set up yet; lan: private endpoint · ready"),
         "1 ready. Some places for AI are not set up or not available"),
        (DoctorCheck("Coding agents", "PASS", "Claude Code hooks installed; Codex does not trust the HoldSpeak hooks yet (it does not run them)"),
         "Some agent hooks are not installed"),
        (DoctorCheck("Some new check", "WARN", "x=1; y_z (raw)"), "Needs a check"),
        (DoctorCheck("Some new check", "PASS", "All good."), "All good"),
    ],
)
def test_face_words_are_plain(check: DoctorCheck, words: str) -> None:
    assert words in face_words(check)


def test_every_real_check_has_short_plain_words(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    for check in collect_doctor_checks(skip_network=True):
        words = face_words(check)
        assert words and len(words) <= 80, (check.name, words)
        assert not any(mark in words for mark in (";", "=", "`", "_cpp")), (check.name, words)


def test_the_setup_section_carries_words_and_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks",
        lambda **_: [DoctorCheck(name="ffmpeg", status="WARN", detail="Not found in PATH", fix="brew install ffmpeg")],
    )
    section = setup_status.build_setup_status(config=Config())["sections"][0]
    assert section["label"] == "ffmpeg" and section["status"] == "warn"
    assert section["detail"] == "ffmpeg is not installed"
    assert section["raw"] == "Not found in PATH"
