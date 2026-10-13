"""The quiet concierge: keep the Runs on window off the real hardware scan.

Lifted from the parked tests/e2e/_parked/test_hs201_one_thing_glass.py.
Not a test file.
"""
from __future__ import annotations

from typing import Any

import pytest


def _quiet_concierge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the Runs on window (the Models window) off the real hardware
    scan (speed, not truth)."""
    import holdspeak.services.concierge_service as cs

    detection = {
        "engines": [],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                    "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [],
        "checkedAt": "2026-09-19T09:41:00Z",
    }
    def detect(**kwargs: Any) -> dict[str, Any]:
        # PHILO-16 (C): Runs on draws the engines the library holds, so the
        # quiet scan still lists the owner's own endpoints (no hardware,
        # runtime, file or network scan): an engine added from the face
        # joins the column the way the real detection lists it.
        db = kwargs.get("db")
        engines: list[dict[str, Any]] = []
        for profile in (db.profiles.list() if db is not None else []):
            base = str(getattr(profile, "base_url", "") or "")
            if getattr(profile, "deleted", False) or not base:
                continue
            local = "127.0.0.1" in base or "localhost" in base
            engines.append({
                "id": f"{'local' if local else 'lan'}:{profile.id}",
                "kind": "local" if local else "lan",
                "name": str(getattr(profile, "model", "") or profile.name or profile.id),
                "host": "THIS DEVICE" if local else cs._host_for_base_url(base),
                "state": "READY",
                "baseUrl": base,
                **cs._detected_profile_fields(db, str(profile.id)),
            })
        return {**detection, "engines": engines}

    monkeypatch.setattr(cs, "detect", detect)
    monkeypatch.setattr(cs, "propose", lambda **_: {"rows": [], "receipt": {"groups": 0, "engines": 0, "waiting": 0}})
