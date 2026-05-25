"""Cross-repo schema drift detector.

`holdspeak_proto.Hello` mirrors `holdspeak.device_audio.DeviceHandshake`
by hand. The bridge's strict Pydantic models will catch drift at
runtime — but only after the handshake fails on real traffic. This
test catches it earlier when the sibling HoldSpeak repo is checked
out, and skips cleanly when it's not (so CI in environments without
HoldSpeak still passes).

To exercise locally:

    git clone https://github.com/karolswdev/HoldSpeak ~/dev/HoldSpeak
    pytest tests/test_protocol_sync.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOLDSPEAK_ROOT = Path.home() / "dev" / "HoldSpeak"
HOLDSPEAK_AVAILABLE = (HOLDSPEAK_ROOT / "holdspeak" / "device_audio.py").exists()


@pytest.fixture(scope="module")
def holdspeak_devicehandshake():
    """Import HoldSpeak's `DeviceHandshake` model from the sibling repo.

    Module-scoped so we only manipulate `sys.path` once. Skips the test
    if the sibling repo isn't present.
    """
    if not HOLDSPEAK_AVAILABLE:
        pytest.skip(
            f"HoldSpeak sibling repo not at {HOLDSPEAK_ROOT}; "
            "test is opt-in"
        )
    sys.path.insert(0, str(HOLDSPEAK_ROOT))
    try:
        from holdspeak.device_audio import DeviceHandshake  # type: ignore
    finally:
        # Best-effort cleanup. Keeping sys.path mutation scoped to
        # module fixture so other tests aren't affected by the import
        # ordering.
        try:
            sys.path.remove(str(HOLDSPEAK_ROOT))
        except ValueError:
            pass
    return DeviceHandshake


def test_hello_field_names_match_devicehandshake(holdspeak_devicehandshake):
    """Bridge's `Hello` and HoldSpeak's `DeviceHandshake` must have the
    same field name set. A drift means one side will reject what the
    other sends (extra="forbid")."""
    from holdspeak_proto import Hello

    bridge_fields = set(Hello.model_fields.keys())
    holdspeak_fields = set(holdspeak_devicehandshake.model_fields.keys())

    assert bridge_fields == holdspeak_fields, (
        f"field-set drift: bridge has {bridge_fields - holdspeak_fields} extra, "
        f"HoldSpeak has {holdspeak_fields - bridge_fields} extra"
    )


def test_hello_config_matches_devicehandshake(holdspeak_devicehandshake):
    """Both sides must reject unknown fields and strip whitespace —
    asymmetry would let a frame validate on one side and fail on the
    other."""
    from holdspeak_proto import Hello

    for key in ("extra", "str_strip_whitespace"):
        bridge_val = Hello.model_config.get(key)
        holdspeak_val = holdspeak_devicehandshake.model_config.get(key)
        assert bridge_val == holdspeak_val, (
            f"model_config[{key!r}] drift: bridge={bridge_val!r}, "
            f"holdspeak={holdspeak_val!r}"
        )


def test_hello_non_empty_validator_covers_same_fields(holdspeak_devicehandshake):
    """Both schemas reject empty values for device_id / label / psk. The
    bridge's `Hello._non_empty` and HoldSpeak's `DeviceHandshake._non_empty`
    must agree on which fields are guarded."""
    from pydantic import ValidationError

    from holdspeak_proto import Hello

    for empty_field in ("device_id", "label", "psk"):
        kwargs = {
            "type": "hello",
            "device_id": "x",
            "label": "y",
            "psk": "z",
            "version": 1,
        }
        kwargs[empty_field] = ""

        with pytest.raises(ValidationError):
            Hello.model_validate(kwargs)
        with pytest.raises(ValidationError):
            holdspeak_devicehandshake.model_validate(kwargs)


def test_hello_round_trip_validates_on_holdspeak(holdspeak_devicehandshake):
    """A Hello frame the bridge would actually send must parse cleanly
    on the HoldSpeak side. Catches subtle JSON-encoding drift (whitespace
    stripping, Literal type mismatch, version=int)."""
    from holdspeak_proto import Hello

    sent = Hello(
        device_id="aipi-1",
        label="Test",
        psk="abc123",
        version=1,
    )
    parsed = holdspeak_devicehandshake.model_validate_json(sent.model_dump_json())
    assert parsed.device_id == "aipi-1"
    assert parsed.label == "Test"
    assert parsed.psk == "abc123"
    assert parsed.version == 1
    assert parsed.type == "hello"
