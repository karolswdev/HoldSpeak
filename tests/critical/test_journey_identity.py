"""Critical journey: P200-A01 — the installation can say what it is.

The Phase 200 baseline found two hubs running against one database with
neither reporting the other, and a running product that was not the checkout.
An installation that cannot name its own backend, bundle and database cannot
carry release evidence, so this journey is a G0 gate.

The behaviour itself is HS-200-02's; this file is the cold, runner-safe
journey over it. `tests/integration/test_phase200_runtime_identity.py` holds
the field-by-field unit proof.
"""

from __future__ import annotations

import json
import os

import pytest

from holdspeak import runtime_identity as ri
from holdspeak.db.schema import SCHEMA_VERSION

pytestmark = pytest.mark.critical

_C1_FIELDS = (
    "backend_version",
    "backend_revision",
    "process_start",
    "pid",
    "frontend_build",
    "database_id",
    "schema_version_expected",
    "schema_version_loaded",
    "config_revision",
)


def _stamp_bundle(cold_install, build_id: str):
    bundle = cold_install.home / "_built"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / ri.BUILD_STAMP_NAME).write_text(
        json.dumps({"build_id": build_id}), encoding="utf-8"
    )
    return bundle


def test_a_cold_installation_names_what_it_loaded(
    cold_install, db, client, monkeypatch
) -> None:
    """Every C1 identity field is served, on a machine with no model and no history."""
    bundle = _stamp_bundle(cold_install, "cold-build")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    ri.capture_runtime_identity(db_path=cold_install.db_path, force=True)

    body = client.get("/api/system/identity").json()
    identity = body["identity"]

    missing = [field for field in _C1_FIELDS if identity.get(field) is None]
    assert not missing, f"identity is silent about: {missing}"
    assert identity["pid"] == os.getpid()
    assert identity["frontend_build"] == "cold-build"
    assert identity["schema_version_loaded"] == SCHEMA_VERSION
    assert identity["schema_version_expected"] == SCHEMA_VERSION
    assert "diagnoses" in body


def test_a_stale_bundle_is_a_named_diagnosis_not_a_silence(
    cold_install, db, client, monkeypatch
) -> None:
    """The serving process must SAY the bundle moved under it."""
    bundle = _stamp_bundle(cold_install, "the-build-that-was-loaded")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    ri.capture_runtime_identity(db_path=cold_install.db_path, force=True)

    # The tree moves on; the running process must keep reporting what it loaded
    # and must name the divergence rather than quietly serving the new bundle.
    (bundle / ri.BUILD_STAMP_NAME).write_text(
        json.dumps({"build_id": "a-newer-build"}), encoding="utf-8"
    )

    body = client.get("/api/system/identity").json()
    assert body["identity"]["frontend_build"] == "the-build-that-was-loaded"
    tokens = {str(item.get("token") or item) for item in body["diagnoses"]}
    assert any("STALE" in token.upper() for token in tokens), tokens


def test_the_cold_desk_surface_carries_the_tokens_without_the_path(
    cold_install, db, client, monkeypatch
) -> None:
    """The ordinary surface names the condition; only diagnostics names the path."""
    bundle = _stamp_bundle(cold_install, "cold-build")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    ri.capture_runtime_identity(db_path=cold_install.db_path, force=True)

    status = client.get("/api/setup/status").json()
    block = json.dumps(status)
    assert "runtime" in block.lower()
    assert str(cold_install.db_path) not in block, (
        "the ordinary surface must not publish the database path"
    )
