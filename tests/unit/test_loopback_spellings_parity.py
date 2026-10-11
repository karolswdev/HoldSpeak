"""PHILO-17 U16 (Astra r2 M3): the face and the transport classify a host the same way.

``tests/fixtures/loopback_spellings.json`` is the one table. The web side
(``web/src/desk/surface/__tests__/egress.test.ts``) reads it for
``isLoopbackHost`` and ``hostPlace``; this file reads it for the backend's
own rules, so a change on either side fails a fence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.intel.providers import egress_boundary
from holdspeak.loopback_http import is_loopback_engine_host

TABLE = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "loopback_spellings.json").read_text())


@pytest.mark.parametrize("row", TABLE["loopback"], ids=lambda r: r["host"])
def test_loopback_spelling_matches_transport(row: dict) -> None:
    assert is_loopback_engine_host(row["host"]) is row["loopback"]


@pytest.mark.parametrize("row", TABLE["boundary"], ids=lambda r: r["url"])
def test_egress_boundary_matches_table(row: dict) -> None:
    # Includes the trailing-dot rule: `127.0.0.1.` is the private network.
    assert egress_boundary(base_url=row["url"]) == row["boundary"]
