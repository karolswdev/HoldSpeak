"""Unit tests for the device handshake protocol + PSK helpers (HS-14-03)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.config import Config, DeviceConfig
from holdspeak.device_audio import (
    DEVICE_HANDSHAKE_VERSION,
    DeviceHandshake,
    InvalidHandshakeError,
    WS_CLOSE_DUPLICATE_LABEL,
    WS_CLOSE_INVALID_HANDSHAKE,
    WS_CLOSE_PSK_MISMATCH,
    ensure_device_psk,
    generate_device_psk,
    parse_handshake,
    rotate_device_psk,
    verify_psk,
)


def _valid_payload(**overrides: object) -> dict:
    payload = {
        "type": "hello",
        "device_id": "aipi-1",
        "label": "Karol",
        "psk": "abc-secret",
        "version": DEVICE_HANDSHAKE_VERSION,
    }
    payload.update(overrides)
    return payload


class TestDeviceHandshakeSchema:
    def test_valid_payload_parses(self) -> None:
        handshake = parse_handshake(_valid_payload())
        assert isinstance(handshake, DeviceHandshake)
        assert handshake.type == "hello"
        assert handshake.device_id == "aipi-1"
        assert handshake.label == "Karol"
        assert handshake.psk == "abc-secret"
        assert handshake.version == DEVICE_HANDSHAKE_VERSION

    def test_missing_field_rejected(self) -> None:
        payload = _valid_payload()
        del payload["device_id"]
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(payload)

    def test_extra_field_rejected_strictly(self) -> None:
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(_valid_payload(rogue="oops"))

    def test_wrong_type_literal_rejected(self) -> None:
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(_valid_payload(type="goodbye"))

    def test_empty_string_field_rejected(self) -> None:
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(_valid_payload(psk=""))
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(_valid_payload(label=""))

    def test_whitespace_only_field_rejected(self) -> None:
        # Pydantic config strips strings, so whitespace becomes ""
        # which the field validator rejects.
        with pytest.raises(InvalidHandshakeError):
            parse_handshake(_valid_payload(device_id="   "))

    def test_non_dict_payload_rejected(self) -> None:
        with pytest.raises(InvalidHandshakeError):
            parse_handshake("not a dict")  # type: ignore[arg-type]
        with pytest.raises(InvalidHandshakeError):
            parse_handshake([("type", "hello")])  # type: ignore[arg-type]

    def test_handshake_can_round_trip_through_json(self) -> None:
        # The wire format is JSON; confirm the model survives a
        # round-trip by an HTTP/WS client that uses ``model_dump``.
        handshake = parse_handshake(_valid_payload())
        wire = json.dumps(handshake.model_dump())
        again = parse_handshake(json.loads(wire))
        assert again == handshake


class TestPskCompare:
    def test_matching_psks_compare_true(self) -> None:
        assert verify_psk("abc-123", "abc-123") is True

    def test_different_psks_compare_false(self) -> None:
        assert verify_psk("abc-123", "xyz-999") is False

    def test_empty_provided_returns_false(self) -> None:
        assert verify_psk("", "expected") is False

    def test_empty_expected_returns_false(self) -> None:
        # A freshly-installed instance with no PSK on disk must not
        # accept an empty PSK from a device.
        assert verify_psk("provided", "") is False

    def test_both_empty_returns_false(self) -> None:
        assert verify_psk("", "") is False

    def test_length_mismatch_does_not_raise(self) -> None:
        # hmac.compare_digest tolerates different-length inputs by
        # returning False; we should pass that through, not raise.
        assert verify_psk("short", "much-longer-string") is False


class TestCloseCodes:
    def test_close_codes_are_distinct_app_range_integers(self) -> None:
        codes = (
            WS_CLOSE_INVALID_HANDSHAKE,
            WS_CLOSE_PSK_MISMATCH,
            WS_CLOSE_DUPLICATE_LABEL,
        )
        for code in codes:
            assert isinstance(code, int)
            assert 4000 <= code < 5000
        assert len(set(codes)) == 3

    def test_invalid_handshake_error_carries_code(self) -> None:
        err = InvalidHandshakeError("boom")
        assert err.code == WS_CLOSE_INVALID_HANDSHAKE


class TestPskLifecycle:
    def test_generate_returns_long_url_safe_string(self) -> None:
        psk = generate_device_psk()
        assert isinstance(psk, str)
        assert len(psk) >= 24
        # token_urlsafe alphabet is base64-url (A-Z a-z 0-9 - _).
        allowed = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789-_"
        )
        assert set(psk) <= allowed

    def test_generate_is_random(self) -> None:
        psks = {generate_device_psk() for _ in range(8)}
        assert len(psks) == 8

    def test_ensure_generates_when_empty_and_persists(
        self, tmp_path: Path
    ) -> None:
        config_path = tmp_path / "config.json"
        config = Config()
        # Force the in-memory config to point at the tmp path on save
        # by passing save_path explicitly.
        assert config.device.psk == ""

        psk = ensure_device_psk(config, save_path=config_path)
        assert psk
        assert config.device.psk == psk

        # File on disk must contain the new PSK.
        on_disk = json.loads(config_path.read_text())
        assert on_disk["device"]["psk"] == psk

    def test_ensure_returns_existing_without_writing(
        self, tmp_path: Path
    ) -> None:
        config_path = tmp_path / "config.json"
        config = Config()
        config.device = DeviceConfig(psk="preset-psk")

        # No file exists yet; ensure must NOT create one.
        psk = ensure_device_psk(config, save_path=config_path)
        assert psk == "preset-psk"
        assert not config_path.exists()

    def test_rotate_replaces_and_persists(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config()
        config.device = DeviceConfig(psk="old-psk")

        new_psk = rotate_device_psk(config, save_path=config_path)
        assert new_psk != "old-psk"
        assert config.device.psk == new_psk

        on_disk = json.loads(config_path.read_text())
        assert on_disk["device"]["psk"] == new_psk

    def test_load_round_trips_device_psk(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config()
        config.device = DeviceConfig(psk="round-trip-psk")
        config.save(config_path)

        reloaded = Config.load(config_path)
        assert reloaded.device.psk == "round-trip-psk"


class TestDevicePskCli:
    def test_show_action_prints_existing_psk(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from holdspeak.commands import device as device_cmd

        config_path = tmp_path / "config.json"
        Config().save(config_path)
        # Pre-set a PSK on disk so ``show`` doesn't have to generate one.
        existing = Config.load(config_path)
        existing.device = DeviceConfig(psk="cli-existing-psk")
        existing.save(config_path)

        # Point ensure_device_psk at the temp config without monkey-
        # patching the global config path: stub Config.load + redirect
        # save.
        original_load = Config.load
        monkeypatch.setattr(
            Config, "load", classmethod(lambda cls, path=None: original_load(config_path))
        )
        original_save = Config.save
        monkeypatch.setattr(
            Config, "save", lambda self, path=None: original_save(self, config_path)
        )

        rc = device_cmd.run_device_psk_command(SimpleNamespace(psk_action="show"))
        captured = capsys.readouterr()

        assert rc == 0
        assert captured.out.strip() == "cli-existing-psk"

    def test_rotate_action_replaces_and_prints(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from holdspeak.commands import device as device_cmd

        config_path = tmp_path / "config.json"
        Config().save(config_path)
        seeded = Config.load(config_path)
        seeded.device = DeviceConfig(psk="cli-old-psk")
        seeded.save(config_path)

        original_load = Config.load
        monkeypatch.setattr(
            Config, "load", classmethod(lambda cls, path=None: original_load(config_path))
        )
        original_save = Config.save
        monkeypatch.setattr(
            Config, "save", lambda self, path=None: original_save(self, config_path)
        )

        rc = device_cmd.run_device_psk_command(SimpleNamespace(psk_action="rotate"))
        captured = capsys.readouterr()
        new_psk = captured.out.strip()

        assert rc == 0
        assert new_psk
        assert new_psk != "cli-old-psk"

        reloaded = Config.load(config_path)
        assert reloaded.device.psk == new_psk

    def test_unknown_action_returns_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from holdspeak.commands import device as device_cmd

        rc = device_cmd.run_device_psk_command(SimpleNamespace(psk_action=None))
        captured = capsys.readouterr()
        assert rc == 2
        assert "Usage" in captured.err
