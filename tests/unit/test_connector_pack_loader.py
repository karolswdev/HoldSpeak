"""HS-13-04 — connector-pack loader tests.

Discovery walks a user-pack directory, imports each `.py`
file as a module, validates the manifest, and merges the
results into the runtime registry alongside first-party packs.
The loader must:

  - never crash on a malformed pack — surface a structured
    `DiscoveryError` instead,
  - reject ids that collide with first-party packs (first-party
    wins),
  - reject duplicates inside the user dir (first one wins),
  - tag every registered pack with its `source`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak import activity_connectors
from holdspeak.connector_pack_loader import (
    SOURCE_FIRST_PARTY,
    SOURCE_USER,
    build_registry,
    discover_user_packs,
)


# ──────────────────────────── Fixtures ────────────────────────────


_VALID_USER_PACK = """from holdspeak.connector_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "user_demo",
    "label": "Demo user pack",
    "version": "0.1.0",
    "kind": "candidate_inference",
    "capabilities": ["candidates"],
    "permissions": ["read:activity_records"],
    "settings_schema": [
        {"key": "limit", "type": "int", "default": 10},
    ],
})
"""

_NO_MANIFEST_PACK = """# This pack file forgot to export MANIFEST.
DEFAULT_TIMEOUT = 5.0
"""

_BAD_MANIFEST_PACK = """from holdspeak.connector_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "bad_user_pack",
    "label": "Bad user pack",
    "version": "0.1.0",
    "kind": "cli_enrichment",
    # cli_enrichment requires requires_cli — the validator
    # rejects this manifest.
    "capabilities": ["annotations"],
    "permissions": ["shell:exec", "network:outbound"],
})
"""

_IMPORT_RAISES_PACK = """raise RuntimeError("intentional failure for the loader test")
"""

_COLLIDING_PACK = """from holdspeak.connector_sdk import validate_manifest

# `gh` is the first-party github_cli pack id; the loader must
# reject this user pack and keep the first-party one.
MANIFEST = validate_manifest({
    "id": "gh",
    "label": "Sneaky shadow pack",
    "version": "0.1.0",
    "kind": "candidate_inference",
    "capabilities": ["candidates"],
    "permissions": ["read:activity_records"],
})
"""


@pytest.fixture
def user_pack_dir(tmp_path: Path) -> Path:
    return tmp_path / "user_packs"


@pytest.fixture(autouse=True)
def _reset_registry_after():
    """Each test gets the default (no-user-packs) registry back
    so cross-test ordering doesn't leak."""
    yield
    activity_connectors.reload_registry()


# ──────────────────────────── Discovery ───────────────────────────


def test_missing_directory_is_silent(user_pack_dir: Path) -> None:
    packs, errors = discover_user_packs(user_pack_dir)
    assert packs == ()
    assert errors == ()


def test_valid_user_pack_loads_with_user_source(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert errors == ()
    assert len(packs) == 1
    assert packs[0].source == SOURCE_USER
    assert packs[0].manifest.id == "user_demo"
    assert packs[0].file_path == user_pack_dir / "demo.py"


def test_pack_without_manifest_is_rejected(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "nope.py").write_text(_NO_MANIFEST_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert packs == ()
    assert len(errors) == 1
    assert errors[0].code == "no_manifest"
    assert errors[0].file_path == user_pack_dir / "nope.py"


def test_invalid_manifest_is_rejected_with_structured_error(
    user_pack_dir: Path,
) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "bad.py").write_text(_BAD_MANIFEST_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    # The pack import itself raises ConnectorManifestError because
    # `validate_manifest` runs at module import. The loader catches
    # the exception, surfaces it as `import_failed` instead of
    # crashing.
    assert packs == ()
    assert len(errors) == 1
    assert errors[0].code == "import_failed"
    assert "requires_cli" in errors[0].message


def test_pack_that_raises_at_import_does_not_crash(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "explosive.py").write_text(_IMPORT_RAISES_PACK)
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    # The valid pack still loads even though one neighbour blew up.
    assert {p.manifest.id for p in packs} == {"user_demo"}
    assert any(e.code == "import_failed" for e in errors)


def test_id_collision_with_first_party_rejects_user_pack(
    user_pack_dir: Path,
) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "shadow_gh.py").write_text(_COLLIDING_PACK)

    packs, errors = discover_user_packs(
        user_pack_dir, forbidden_ids=frozenset({"gh"})
    )

    assert packs == ()
    assert len(errors) == 1
    assert errors[0].code == "id_collision_first_party"
    assert errors[0].pack_id == "gh"


def test_underscored_files_are_skipped(user_pack_dir: Path) -> None:
    """Convention: `_helpers.py` and `__init__.py` are not packs."""
    user_pack_dir.mkdir()
    (user_pack_dir / "__init__.py").write_text("")
    (user_pack_dir / "_helpers.py").write_text("VALUE = 1")
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert {p.manifest.id for p in packs} == {"user_demo"}
    assert errors == ()


# ─────────────────────── Registry integration ─────────────────────


def test_build_registry_merges_first_party_and_user(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    result = build_registry(user_packs_dir=user_pack_dir)

    by_id = result.by_id()
    assert {"firefox_ext", "gh", "jira", "calendar_activity"} <= set(by_id)
    assert "user_demo" in by_id
    assert by_id["user_demo"].source == SOURCE_USER
    assert by_id["gh"].source == SOURCE_FIRST_PARTY
    assert result.errors == ()


def test_reload_registry_picks_up_user_packs(user_pack_dir: Path) -> None:
    """`activity_connectors.reload_registry(user_packs_dir=...)`
    swaps the module-level registry. After reload the API consumers
    (`enrichment_descriptors`, `get_descriptor`) see the user pack."""
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    activity_connectors.reload_registry(user_packs_dir=user_pack_dir)

    descriptor = activity_connectors.get_descriptor("user_demo")
    assert descriptor is not None
    assert descriptor.source == SOURCE_USER
    # The user pack is `candidate_inference` so it shows up on the
    # enrichment surface alongside calendar_activity.
    enrichment_ids = {d.id for d in activity_connectors.enrichment_descriptors()}
    assert "user_demo" in enrichment_ids
    assert "gh" in enrichment_ids


def test_first_party_descriptors_are_labeled_first_party() -> None:
    activity_connectors.reload_registry()
    by_id = {c.id: c for c in activity_connectors.KNOWN_CONNECTORS}
    for first_party in ("firefox_ext", "gh", "jira", "calendar_activity"):
        assert by_id[first_party].source == SOURCE_FIRST_PARTY
