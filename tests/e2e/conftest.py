"""e2e conftest — the 163 stale-bundle law for EVERY rig.

`glass_infra._ensure_build` rebuilds the web bundle when any web source
is newer than the oldest built chunk. 19 of 33 glass rigs imported it;
the other 14 (HS-144, HS-152, HS-153, …) booted their own hub and tested
whatever bundle happened to be on disk — seen 2026-09-05: a rig asserting
against a bundle from before the species sweep. This autouse session
fixture applies the law to every test under tests/e2e/, once per
process (xdist workers serialize under the file lock; the mtime check
makes every later call a no-op).
"""
from __future__ import annotations

import pytest

from .glass_infra import _ensure_build


@pytest.fixture(scope="session", autouse=True)
def _web_bundle_is_fresh() -> None:
    _ensure_build()
