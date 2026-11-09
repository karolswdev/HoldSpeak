"""PARKED 20261109 (lane door/rest-park-waist) from tests/unit/test_tool_capability_lease.py: the ToolTurn controller is parked (the recipe agent turn runs through the engine door).
Not collected (tests/_parked/conftest.py). Restore with git revert.
"""
from __future__ import annotations
import hashlib
import json
import pytest
from holdspeak.services.tool_capability_service import (
    CanonicalApplicationOperationDescriptor,
    ModelTurnCapabilityProjection,
    ToolCapabilityError,
    ToolQualification,
    ToolResultEnvelope,
    parse_capability_manifest,
)
from holdspeak.services.tool_turn_controller import TurnCapabilityLease


def test_lease_normalizes_hashes_and_refuses_palette_expansion_or_expiry_extension() -> None:
    descriptor = _descriptor()
    terms = _terms(descriptor)
    first = TurnCapabilityLease.parse(terms, now=100.0)
    reordered = _terms(descriptor)
    reordered["capabilities"] = list(reversed(reordered["capabilities"]))
    assert TurnCapabilityLease.parse(reordered, now=100.0).terms_sha256 == first.terms_sha256

    escalated = _terms(descriptor)
    escalated["max_tool_calls"] = 3
    with pytest.raises(Exception, match="exceeds capability limits"):
        TurnCapabilityLease.parse(escalated, now=100.0)
    expired_extension = _terms(descriptor)
    expired_extension["expires_at"] = 131.0
    with pytest.raises(Exception, match="expiry exceeds"):
        TurnCapabilityLease.parse(expired_extension, now=100.0)


