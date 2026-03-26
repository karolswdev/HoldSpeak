from __future__ import annotations

import pytest

import holdspeak.audio_devices as audio_devices


def test_list_pulse_monitor_sources_parses_pactl_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audio_devices.sys, "platform", "linux")

    def fake_pactl_stdout(args: list[str]):
        assert args == ["list", "short", "sources"]
        return "\n".join(
            [
                "0\talsa_output.pci-0000_00_1f.3.analog-stereo.monitor\tmodule-alsa-card.c\ts16le 2ch 44100Hz\tRUNNING",
                "1\talsa_input.pci-0000_00_1f.3.analog-stereo\tmodule-alsa-card.c\ts16le 2ch 44100Hz\tSUSPENDED",
            ]
        )

    monkeypatch.setattr(audio_devices, "_pactl_stdout", fake_pactl_stdout)
    assert audio_devices.list_pulse_monitor_sources() == [
        "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
    ]


def test_find_pulse_monitor_source_prefers_default_sink(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audio_devices.sys, "platform", "linux")

    def fake_pactl_stdout(args: list[str]):
        if args == ["list", "short", "sources"]:
            return "\n".join(
                [
                    "0\talsa_output.A.monitor\t...\t...\tRUNNING",
                    "1\talsa_output.B.monitor\t...\t...\tRUNNING",
                ]
            )
        if args == ["get-default-sink"]:
            return "alsa_output.B"
        raise AssertionError(f"unexpected pactl args: {args}")

    monkeypatch.setattr(audio_devices, "_pactl_stdout", fake_pactl_stdout)
    assert audio_devices.find_pulse_monitor_source() == "alsa_output.B.monitor"

