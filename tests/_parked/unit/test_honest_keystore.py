"""HS-149-01 — the honest keystore seam (L3 + L2 + F4).

Tests the file-backed key store, the composition point, the doctor
check, and the L2 people-store-state projection.  Every test that
touches the People store uses an isolated HOME and the
``HOLDSPEAK_PEOPLE_KEYSTORE_FILE`` env var so ZERO keyring/keychain
calls occur end-to-end.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.people.keys import FileKeyStore, MemoryKeyStore, NativeKeyStore, PeopleKeyError, new_key, new_key_id
from holdspeak.people.store import (
    DEFAULT_PEOPLE_DB_PATH,
    EncryptedPeopleStore,
    PeopleReadiness,
    _dev_sidecar_path,
    production_people_store,
)
from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore


# -- FileKeyStore unit tests -------------------------------------------------

class TestFileKeyStore:
    def test_round_trip(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "keys.json"
        store = FileKeyStore(keyfile)
        key = new_key()
        kid = new_key_id()
        store.put(kid, key)
        assert store.get(kid) == key
        # File should exist with 0600 perms.
        assert keyfile.exists()
        assert stat.S_IMODE(keyfile.stat().st_mode) == 0o600

    def test_delete(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "keys.json"
        store = FileKeyStore(keyfile)
        kid = new_key_id()
        store.put(kid, new_key())
        store.delete(kid)
        with pytest.raises(PeopleKeyError, match="missing"):
            store.get(kid)

    def test_missing_key_raises(self, tmp_path: Path) -> None:
        store = FileKeyStore(tmp_path / "keys.json")
        with pytest.raises(PeopleKeyError, match="missing"):
            store.get("nonexistent")

    def test_invalid_key_length_refuses_put(self, tmp_path: Path) -> None:
        store = FileKeyStore(tmp_path / "keys.json")
        with pytest.raises(PeopleKeyError, match="invalid"):
            store.put("test", b"short")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "deep" / "nested" / "keys.json"
        store = FileKeyStore(keyfile)
        store.put(new_key_id(), new_key())
        assert keyfile.exists()

    def test_multiple_keys(self, tmp_path: Path) -> None:
        store = FileKeyStore(tmp_path / "keys.json")
        k1, k2 = new_key(), new_key()
        id1, id2 = new_key_id(), new_key_id()
        store.put(id1, k1)
        store.put(id2, k2)
        assert store.get(id1) == k1
        assert store.get(id2) == k2


# -- Composition point tests ------------------------------------------------

class TestCompositionPoint:
    def test_env_set_selects_file_keystore(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "test-keys.json"
        with patch.dict(os.environ, {"HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(keyfile)}):
            store = production_people_store()
        assert isinstance(store.key_store, FileKeyStore)
        # The sidecar path must be derived from keyfile, NOT production.
        assert store.path == _dev_sidecar_path(keyfile)
        assert store.path != DEFAULT_PEOPLE_DB_PATH

    def test_env_unset_selects_native_keystore(self, tmp_path: Path) -> None:
        """Without the env, the composition is byte-identical to production."""
        env = {k: v for k, v in os.environ.items() if k != "HOLDSPEAK_PEOPLE_KEYSTORE_FILE"}
        with patch.dict(os.environ, env, clear=True):
            # NativeKeyStore init may raise if no native backend is available
            # in the test environment. We catch that and verify it was attempted.
            try:
                store = production_people_store()
                assert isinstance(store.key_store, NativeKeyStore)
                assert store.path == DEFAULT_PEOPLE_DB_PATH
            except PeopleKeyError as exc:
                # Expected in CI/headless: native backend unavailable.
                assert "not_native" in str(exc) or "unavailable" in str(exc)


# -- F4 sidecar isolation tests ---------------------------------------------

class TestF4SidecarIsolation:
    def test_dev_sidecar_path_derived_from_keyfile(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "my-keys.json"
        sidecar = _dev_sidecar_path(keyfile)
        assert sidecar.parent == tmp_path
        assert sidecar.name == "my-keys.sidecar.sqlite3"
        assert sidecar != DEFAULT_PEOPLE_DB_PATH

    def test_dev_store_never_opens_production_sidecar(self, tmp_path: Path) -> None:
        """F4: even if production sidecar exists, the dev store ignores it."""
        keyfile = tmp_path / "dev-keys.json"
        dev_sidecar = _dev_sidecar_path(keyfile)
        # Create a fake production sidecar.
        prod_path = tmp_path / "fake-prod.sqlite3"
        prod_path.write_text("fake production sidecar")
        with patch.dict(os.environ, {"HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(keyfile)}):
            with patch("holdspeak.people.store.DEFAULT_PEOPLE_DB_PATH", prod_path):
                store = production_people_store()
        # The store uses the dev sidecar, never the production one.
        assert store.path == dev_sidecar
        assert store.path != prod_path


# -- Headless seam proof (the acceptance criterion) --------------------------

class TestHeadlessSeamProof:
    """The first-ever headless People setup + CRUD with ZERO keyring calls."""

    def test_full_lifecycle_with_zero_keyring_calls(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "headless-keys.json"
        file_store = FileKeyStore(keyfile)
        sidecar = _dev_sidecar_path(keyfile)
        people_store = EncryptedPeopleStore(sidecar, file_store)

        # SPY: patch the keyring module to detect any call.
        keyring_spy = MagicMock()
        with patch.dict("sys.modules", {"keyring": keyring_spy}):
            # Setup
            assert people_store.readiness() == PeopleReadiness.UNCONFIGURED
            assert people_store.initialize() == PeopleReadiness.READY
            assert people_store.readiness() == PeopleReadiness.READY

            # CRUD
            relationship = people_store.create("relationship", {
                "display_name": "Test Person",
                "relationship_kind": "peer",
                "state": "active",
                "lifecycle": "active",
            })
            assert relationship["display_name"] == "Test Person"

            # Read back
            fetched = people_store.get(relationship["id"], "relationship")
            assert fetched is not None
            assert fetched["display_name"] == "Test Person"

            # List
            items = people_store.list(kind="relationship")
            assert len(items) == 1
            assert items[0]["id"] == relationship["id"]

        # PROOF: zero keyring calls.
        assert keyring_spy.get_keyring.call_count == 0
        assert keyring_spy.get_password.call_count == 0
        assert keyring_spy.set_password.call_count == 0
        assert keyring_spy.delete_password.call_count == 0

    def test_service_level_lifecycle(self, tmp_path: Path) -> None:
        """Full People service lifecycle through the file keystore seam."""
        keyfile = tmp_path / "service-keys.json"
        file_store = FileKeyStore(keyfile)
        sidecar = _dev_sidecar_path(keyfile)
        people_store = EncryptedPeopleStore(sidecar, file_store)

        # Bypass the kernel broker by providing a direct setup_runner.
        def _direct_setup(*, initialize, principal):
            return initialize()

        service = PeopleService(people_store, setup_runner=_direct_setup)

        # A mock owner principal.
        from holdspeak.principals import PrincipalKind
        principal = MagicMock()
        principal.kind = PrincipalKind.OWNER

        # Setup
        readiness = service.setup(principal)
        assert readiness["readiness"] == "ready"

        # Create a relationship
        rel = service.create_relationship(principal, {
            "display_name": "Headless Person",
            "relationship_kind": "direct_report",
        })
        assert rel["display_name"] == "Headless Person"

        # List relationships
        rels = service.list_relationships(principal)
        assert len(rels) == 1


# -- Doctor check tests ------------------------------------------------------

class TestDoctorCheck:
    def test_people_keystore_native_when_env_unset(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "HOLDSPEAK_PEOPLE_KEYSTORE_FILE"}
        with patch.dict(os.environ, env, clear=True):
            from holdspeak.commands.doctor import _check_people_keystore
            check = _check_people_keystore()
        assert check.status == "PASS"
        assert check.name == "People keystore"
        assert "native" in check.detail.lower()

    def test_people_keystore_warns_when_env_set(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "doctor-keys.json"
        with patch.dict(os.environ, {"HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(keyfile)}):
            from holdspeak.commands.doctor import _check_people_keystore
            check = _check_people_keystore()
        assert check.status == "WARN"
        assert "DEV FILE" in check.detail
        assert "not for real use" in check.detail

    def test_both_worlds_warning(self, tmp_path: Path) -> None:
        keyfile = tmp_path / "both-keys.json"
        dev_sidecar = _dev_sidecar_path(keyfile)
        dev_sidecar.parent.mkdir(parents=True, exist_ok=True)
        dev_sidecar.write_text("dev sidecar")
        # Create a fake production sidecar.
        fake_prod = tmp_path / "prod-people.sqlite3"
        fake_prod.write_text("production sidecar")
        with patch.dict(os.environ, {"HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(keyfile)}):
            with patch("holdspeak.people.store.DEFAULT_PEOPLE_DB_PATH", fake_prod):
                from holdspeak.commands.doctor import _check_people_keystore
                check = _check_people_keystore()
        assert check.status == "WARN"
        assert "BOTH WORLDS EXIST" in check.detail


# -- L2: People store state on the Door projection --------------------------

class TestL2PeopleStoreState:
    def _make_follow_through_service(self, people_service: Any) -> Any:
        from holdspeak.services.follow_through_service import FollowThroughService
        db = MagicMock()
        return FollowThroughService(db, people_projection=people_service)

    def test_people_store_state_returns_readiness(self) -> None:
        """When people projection is wired and ready, state is 'ready'."""
        projection = MagicMock()
        projection.readiness.return_value = {"readiness": "ready", "state": "ready"}
        principal = MagicMock()
        ft = self._make_follow_through_service(projection)
        assert ft.people_store_state(principal) == "ready"

    def test_people_store_state_returns_locked(self) -> None:
        projection = MagicMock()
        projection.readiness.return_value = {"readiness": "locked", "state": "locked"}
        principal = MagicMock()
        ft = self._make_follow_through_service(projection)
        assert ft.people_store_state(principal) == "locked"

    def test_people_store_state_returns_unavailable_on_exception(self) -> None:
        projection = MagicMock()
        projection.readiness.side_effect = RuntimeError("boom")
        principal = MagicMock()
        ft = self._make_follow_through_service(projection)
        assert ft.people_store_state(principal) == "unavailable"

    def test_people_store_state_none_without_projection(self) -> None:
        from holdspeak.services.follow_through_service import FollowThroughService
        db = MagicMock()
        ft = FollowThroughService(db, people_projection=None)
        assert ft.people_store_state(MagicMock()) is None

    def test_people_store_state_unconfigured(self) -> None:
        projection = MagicMock()
        projection.readiness.return_value = {"readiness": "unconfigured", "state": "unconfigured"}
        principal = MagicMock()
        ft = self._make_follow_through_service(projection)
        assert ft.people_store_state(principal) == "unconfigured"

    def test_door_service_includes_people_store_state(self) -> None:
        """The door payload carries people_store_state when projection is wired."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughBoard, FollowThroughService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = FollowThroughBoard(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = "locked"

        thought_service = MagicMock()
        thought_service.list_unfinished.return_value = {"items": [], "next_cursor": None}
        scheduled = MagicMock()
        scheduled.list_all.return_value = []
        calendar = MagicMock()
        calendar.upcoming.return_value = []

        door = DoorService(ft, thought_service, scheduled, calendar)
        principal = MagicMock()
        result = door.get(principal)
        assert result["people_store_state"] == "locked"

    def test_door_service_omits_people_store_state_when_none(self) -> None:
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughBoard, FollowThroughService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = FollowThroughBoard(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = None

        thought_service = MagicMock()
        thought_service.list_unfinished.return_value = {"items": [], "next_cursor": None}
        scheduled = MagicMock()
        scheduled.list_all.return_value = []
        calendar = MagicMock()
        calendar.upcoming.return_value = []

        door = DoorService(ft, thought_service, scheduled, calendar)
        principal = MagicMock()
        result = door.get(principal)
        assert "people_store_state" not in result
