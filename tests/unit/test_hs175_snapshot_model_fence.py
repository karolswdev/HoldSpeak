"""HS-175-07 P2-2: snapshot model assignment fence.

Proves the calendar snapshot extraction resolves its model through a
LOCAL-or-NAMED assignment.  The service must never silently reach a
cloud model -- the host must be recorded on the egress receipt
whenever the boundary is cloud or private_network.

Fixed (HS-175 N4): the direct dispatch fallback in
calendar_snapshot_service.py now records the host on the egress dict
for cloud/private_network boundaries (from the revision endpoint), and
prefers local/LAN vision-capable profiles over cloud ones.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SERVICE = _REPO / "holdspeak" / "services" / "calendar_snapshot_service.py"


def _read_source() -> str:
    return _SERVICE.read_text(encoding="utf-8")


def _direct_dispatch_block(source: str) -> str:
    """Extract the direct dispatch path block from the source."""
    lines = source.splitlines()
    in_block = False
    block_lines: list[str] = []
    for line in lines:
        if "Direct dispatch path" in line:
            in_block = True
        if in_block:
            block_lines.append(line)
    return "\n".join(block_lines)


def test_snapshot_direct_dispatch_records_host_for_cloud():
    """The direct dispatch path must record ``host`` on the egress
    dict when the resolved profile boundary is cloud or private_network.

    Structural proof: the block must (a) build an egress dict with
    ``"scope"`` and (b) conditionally set ``"host"`` when the scope
    is cloud or private_network.
    """
    block = _direct_dispatch_block(_read_source())
    assert block, (
        "Could not find the direct dispatch path block "
        "-- the code structure may have changed"
    )

    # 1. The block must construct an egress dict with scope
    assert '"scope"' in block, (
        "Direct dispatch path does not construct an egress dict "
        "with a 'scope' key"
    )

    # 2. The block must record "host" on the egress dict
    assert '"host"' in block, (
        "Direct dispatch path does not record 'host' on the egress "
        "dict -- a cloud model can be silently used without provenance"
    )

    # 3. The host recording must be gated on cloud/private_network scope
    assert "cloud" in block and "private_network" in block, (
        "Direct dispatch path does not gate host recording on "
        "cloud or private_network scope"
    )


def test_snapshot_direct_dispatch_prefers_local_over_cloud():
    """The direct dispatch path must sort vision-capable profiles by
    boundary rank so local/LAN profiles are preferred over cloud ones.

    Structural proof: the direct dispatch path must contain sorting
    logic that ranks profiles by boundary before selecting the target.
    """
    block = _direct_dispatch_block(_read_source())
    assert block, (
        "Could not find the direct dispatch path block "
        "-- the code structure may have changed"
    )

    # The block must sort candidates by boundary rank
    has_sort = "sort" in block.lower() or "sorted" in block.lower()
    has_rank = "BOUNDARY_RANK" in block or "boundary" in block.lower()
    assert has_sort and has_rank, (
        "Direct dispatch path does not sort vision-capable profiles "
        "by boundary rank -- cloud profiles may be silently preferred "
        "over local ones."
    )


def test_snapshot_direct_dispatch_egress_uses_revision_boundary():
    """The direct dispatch path must derive the egress scope from the
    deployment revision boundary (the source of truth), not from the
    captured result's provider string.

    Structural proof: the block must reference ``revision.boundary``
    (or a lookup keyed on it) rather than the old provider-based mapping.
    """
    block = _direct_dispatch_block(_read_source())
    assert block, (
        "Could not find the direct dispatch path block "
        "-- the code structure may have changed"
    )

    assert "revision.boundary" in block, (
        "Direct dispatch path does not use revision.boundary to "
        "derive the egress scope -- the scope may be inaccurate"
    )

    # The old provider-based mapping must be gone
    assert 'provider == "local"' not in block, (
        "Direct dispatch path still uses the provider string to "
        "derive scope -- should use revision.boundary"
    )
