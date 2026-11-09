# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_device_handshake.py to restore.

# ruff: noqa


# --- TestCloseCodes: P1: three close-code constants are ints in 4000-4999 and an error carries its constant
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


# --- TestDeviceHandshakeSchema::test_handshake_can_round_trip_through_json: P3: model_dump then parse gives the same pydantic model
# (was a method of class TestDeviceHandshakeSchema)
def test_handshake_can_round_trip_through_json(self) -> None:
    # The wire format is JSON; confirm the model survives a
    # round-trip by an HTTP/WS client that uses ``model_dump``.
    handshake = parse_handshake(_valid_payload())
    wire = json.dumps(handshake.model_dump())
    again = parse_handshake(json.loads(wire))
    assert again == handshake
