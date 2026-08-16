"""HS-134-07 -- Sync understands inherit.

Proves three properties:
1. A pushed null placement means "inherit" and lands as null on the receiving
   side; an explicit value survives the round-trip.  No path materializes a
   default (this_machine or otherwise) into the stored placement field.
2. A field *absent* from the push payload preserves the receiving side's
   existing value (distinct from explicit null).
3. Bounded-delegation revocation fires correctly on null->value and
   value->null placement transitions during sync push.
"""
from __future__ import annotations

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.sync_service import SyncService

OWNER = Principal(PrincipalKind.OWNER, "sync-inherit-owner")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workbench(db: Database, *, workbench_id: str = "wb-1",
                    name: str = "Test WB",
                    recipe_id: str | None = None,
                    profile_id: str | None = None,
                    resolver_profile_id: str | None = None,
                    schedule: str | None = None,
                    schedule_enabled: bool = False):
    """Directly insert a workbench for sync-layer testing."""
    return db.workbenches.upsert(
        workbench_id=workbench_id, name=name, recipe_id=recipe_id,
        profile_id=profile_id, resolver_profile_id=resolver_profile_id,
        schedule=schedule, schedule_enabled=schedule_enabled,
    )


def _push_workbench_record(db: Database, *, workbench_id: str, value: dict,
                           last_modified: str = "2099-01-01T00:00:00Z",
                           deleted: bool = False):
    """Push a single synthetic workbench record through the sync service."""
    payload = {
        "workbenches": [{
            "meta": {
                "id": workbench_id,
                "kind": "workbench",
                "last_modified": last_modified,
                "deleted": deleted,
            },
            "value": None if deleted else value,
        }],
    }
    return SyncService(db).push(OWNER, payload)


# ---------------------------------------------------------------------------
# 1. Round-trip: null inherits, explicit value survives
# ---------------------------------------------------------------------------

class TestNullInheritRoundTrip:
    """A workbench with profile_id=null round-trips as null (inherit);
    a workbench with an explicit profile_id round-trips with the value."""

    def test_null_profile_id_survives_round_trip(self, tmp_path) -> None:
        """null pushed, pulled, pushed again: still null on destination."""
        source = Database(tmp_path / "source.db")
        dest = Database(tmp_path / "dest.db")

        _make_workbench(source, workbench_id="wb-null", profile_id=None,
                        resolver_profile_id=None)
        pulled = SyncService(source).pull(OWNER)
        SyncService(dest).push(OWNER, pulled)

        wb = dest.workbenches.get("wb-null")
        assert wb is not None
        assert wb.profile_id is None, (
            f"null (inherit) was materialised as {wb.profile_id!r}")
        assert wb.resolver_profile_id is None

    def test_explicit_profile_id_survives_round_trip(self, tmp_path) -> None:
        source = Database(tmp_path / "source.db")
        dest = Database(tmp_path / "dest.db")

        source.profiles.upsert(profile_id="prof-1", name="P",
                               kind="openAICompatible",
                               base_url="http://x", model="m")
        _make_workbench(source, workbench_id="wb-explicit",
                        profile_id="prof-1",
                        resolver_profile_id="prof-1")
        pulled = SyncService(source).pull(OWNER)
        SyncService(dest).push(OWNER, pulled)

        wb = dest.workbenches.get("wb-explicit")
        assert wb is not None
        assert wb.profile_id == "prof-1"
        assert wb.resolver_profile_id == "prof-1"

    def test_both_inherit_identically_on_two_dbs(self, tmp_path) -> None:
        """Two isolated DBs see the same null after the same push."""
        source = Database(tmp_path / "source.db")
        dest_a = Database(tmp_path / "dest_a.db")
        dest_b = Database(tmp_path / "dest_b.db")

        _make_workbench(source, workbench_id="wb-twin", profile_id=None)
        pulled = SyncService(source).pull(OWNER)
        SyncService(dest_a).push(OWNER, pulled)
        SyncService(dest_b).push(OWNER, pulled)

        for label, db in [("dest_a", dest_a), ("dest_b", dest_b)]:
            wb = db.workbenches.get("wb-twin")
            assert wb is not None, f"{label}: workbench not found"
            assert wb.profile_id is None, (
                f"{label}: profile_id should be null (inherit), "
                f"got {wb.profile_id!r}")


# ---------------------------------------------------------------------------
# 2. No path materialises this_machine into a stored placement field
# ---------------------------------------------------------------------------

class TestNoDefaultMaterialisation:
    """The pull serialiser and the push merger must never insert a default
    (this_machine or any other) into the stored profile_id."""

    def test_pull_serialises_null_profile_id_as_null(self, tmp_path) -> None:
        db = Database(tmp_path / "pull.db")
        _make_workbench(db, workbench_id="wb-pull", profile_id=None)
        pulled = SyncService(db).pull(OWNER)

        wb_records = pulled["workbenches"]
        match = [r for r in wb_records if r["meta"]["id"] == "wb-pull"]
        assert len(match) == 1
        value = match[0]["value"]
        assert value["profile_id"] is None, (
            f"pull should emit null, got {value['profile_id']!r}")
        assert "this_machine" not in str(value)

    def test_push_does_not_materialise_default_on_new_workbench(self, tmp_path) -> None:
        db = Database(tmp_path / "push.db")
        _push_workbench_record(db, workbench_id="wb-new", value={
            "id": "wb-new", "name": "New",
            "profile_id": None, "resolver_profile_id": None,
            "recipe_id": None, "schedule": None,
            "schedule_enabled": False, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })
        wb = db.workbenches.get("wb-new")
        assert wb is not None
        assert wb.profile_id is None
        assert wb.resolver_profile_id is None


# ---------------------------------------------------------------------------
# 3. Absent-from-payload preserves existing value
# ---------------------------------------------------------------------------

class TestAbsentFieldPreservesExisting:
    """A push payload missing profile_id must NOT clobber the existing
    value to null.  This is the key semantic: absent != null."""

    def test_absent_profile_id_preserves_existing(self, tmp_path) -> None:
        db = Database(tmp_path / "absent.db")
        # Seed an existing workbench with an explicit profile_id
        _make_workbench(db, workbench_id="wb-partial",
                        profile_id="keep-me",
                        resolver_profile_id="also-keep")

        # Push a record that omits profile_id and resolver_profile_id
        _push_workbench_record(db, workbench_id="wb-partial", value={
            "id": "wb-partial", "name": "Updated Name",
            # profile_id and resolver_profile_id deliberately absent
            "recipe_id": None, "schedule": None,
            "schedule_enabled": False, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        wb = db.workbenches.get("wb-partial")
        assert wb is not None
        assert wb.name == "Updated Name", "name should be updated"
        assert wb.profile_id == "keep-me", (
            f"absent profile_id should preserve existing, got {wb.profile_id!r}")
        assert wb.resolver_profile_id == "also-keep", (
            f"absent resolver_profile_id should preserve existing, "
            f"got {wb.resolver_profile_id!r}")

    def test_explicit_null_overwrites_existing(self, tmp_path) -> None:
        """Explicit null in payload means 'inherit' -- it SHOULD clobber."""
        db = Database(tmp_path / "explicit.db")
        _make_workbench(db, workbench_id="wb-clobber",
                        profile_id="will-be-cleared",
                        resolver_profile_id="also-cleared")

        _push_workbench_record(db, workbench_id="wb-clobber", value={
            "id": "wb-clobber", "name": "Cleared",
            "profile_id": None,
            "resolver_profile_id": None,
            "recipe_id": None, "schedule": None,
            "schedule_enabled": False, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        wb = db.workbenches.get("wb-clobber")
        assert wb is not None
        assert wb.profile_id is None, (
            f"explicit null should clear profile_id, got {wb.profile_id!r}")
        assert wb.resolver_profile_id is None


# ---------------------------------------------------------------------------
# 4. Bounded-delegation revocation fires on placement transitions
# ---------------------------------------------------------------------------

class TestRevocationOnPlacementTransitions:
    """Bounded-delegation revocation must fire when profile_id changes
    during sync -- including null->value and value->null transitions."""

    def _rig(self, tmp_path, *, profile_id="prof-dest", db_name="revocation.db"):
        """Create a workbench with a LIVE delegation.

        Uses a real openAICompatible profile so resolve_placement
        succeeds and delegation can be minted.
        """
        import time
        db = Database(tmp_path / db_name)
        db.profiles.upsert(
            profile_id="prof-dest", name="P",
            kind="openAICompatible", base_url="http://x", model="m")
        db.recipes.upsert(
            recipe_id="r", name="R", system_prompt="S")
        from holdspeak.services.workbench_service import WorkbenchService
        service = WorkbenchService(db)
        wb = service.create_workbench(
            OWNER, name="Delegated",
            recipe_id="r", profile_id=profile_id,
            schedule="* * * * *")
        wid = wb["id"]
        service.update_workbench(OWNER, wid, schedule_enabled=True)
        # For the null-start case: after delegation is minted with the real
        # profile, set profile_id to null directly so we can test null->value.
        return db, wid

    def _rig_null_start(self, tmp_path):
        """Create a workbench that STARTS with profile_id=null and a LIVE delegation.

        We mint the delegation with a real profile, then surgically update
        the workbench's profile_id to null (keeping the delegation LIVE)
        so the sync push sees a null->value transition.
        """
        db, wid = self._rig(tmp_path, profile_id="prof-dest",
                            db_name="revocation-null.db")
        # Set profile_id to null, simulating an inherit state
        with db._connection() as conn:
            conn.execute(
                "UPDATE workbenches SET profile_id = NULL WHERE id = ?",
                (wid,),
            )
        wb = db.workbenches.get(wid)
        assert wb.profile_id is None, "pre-condition: profile_id should be null"
        return db, wid

    def test_value_to_null_fires_revocation(self, tmp_path) -> None:
        """Changing profile_id from a value to null (inherit) revokes."""
        db, wid = self._rig(tmp_path, profile_id="prof-dest")

        from holdspeak.services.schedule_delegation import ScheduleDelegationService
        delegation = ScheduleDelegationService(db).live(wid)
        assert delegation is not None, "delegation must exist before the test"

        # Push a sync record that sets profile_id to null
        _push_workbench_record(db, workbench_id=wid, value={
            "id": wid, "name": "Delegated",
            "profile_id": None,  # value -> null
            "resolver_profile_id": None,
            "recipe_id": "r", "schedule": "* * * * *",
            "schedule_enabled": True, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        with db._connection() as conn:
            row = conn.execute(
                "SELECT state, revocation_reason FROM kernel_schedule_delegations "
                "WHERE workbench_id = ? ORDER BY updated_at DESC LIMIT 1",
                (wid,),
            ).fetchone()
        assert row is not None
        assert row["state"] == "REVOKED"
        assert row["revocation_reason"] == "synced_bound_terms_changed"

    def test_null_to_value_fires_revocation(self, tmp_path) -> None:
        """Changing profile_id from null (inherit) to a value revokes."""
        db, wid = self._rig_null_start(tmp_path)

        from holdspeak.services.schedule_delegation import ScheduleDelegationService
        delegation = ScheduleDelegationService(db).live(wid)
        assert delegation is not None

        # Push a sync record that sets profile_id to a value
        _push_workbench_record(db, workbench_id=wid, value={
            "id": wid, "name": "Delegated",
            "profile_id": "prof-dest",  # null -> value
            "resolver_profile_id": None,
            "recipe_id": "r", "schedule": "* * * * *",
            "schedule_enabled": True, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        with db._connection() as conn:
            row = conn.execute(
                "SELECT state, revocation_reason FROM kernel_schedule_delegations "
                "WHERE workbench_id = ? ORDER BY updated_at DESC LIMIT 1",
                (wid,),
            ).fetchone()
        assert row is not None
        assert row["state"] == "REVOKED"
        assert row["revocation_reason"] == "synced_bound_terms_changed"

    def test_unchanged_placement_does_not_revoke(self, tmp_path) -> None:
        """Pushing the same profile_id should NOT revoke the delegation."""
        db, wid = self._rig(tmp_path, profile_id="prof-dest")

        from holdspeak.services.schedule_delegation import ScheduleDelegationService
        delegation_before = ScheduleDelegationService(db).live(wid)
        assert delegation_before is not None

        # Push with the same profile_id
        _push_workbench_record(db, workbench_id=wid, value={
            "id": wid, "name": "Delegated",
            "profile_id": "prof-dest",  # same value
            "resolver_profile_id": None,
            "recipe_id": "r", "schedule": "* * * * *",
            "schedule_enabled": True, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        delegation_after = ScheduleDelegationService(db).live(wid)
        assert delegation_after is not None
        assert delegation_after["state"] == "LIVE"

    def test_absent_profile_id_does_not_revoke(self, tmp_path) -> None:
        """A push omitting profile_id should preserve existing and NOT revoke."""
        db, wid = self._rig(tmp_path, profile_id="prof-dest")

        from holdspeak.services.schedule_delegation import ScheduleDelegationService
        delegation_before = ScheduleDelegationService(db).live(wid)
        assert delegation_before is not None

        # Push a record WITHOUT profile_id in the value
        _push_workbench_record(db, workbench_id=wid, value={
            "id": wid, "name": "Delegated",
            # profile_id absent -- no opinion
            "recipe_id": "r", "schedule": "* * * * *",
            "schedule_enabled": True, "item_order": [],
            "created_at": "2026-01-01T00:00:00Z",
            "last_modified": "2099-01-01T00:00:00Z",
            "deleted": False,
        })

        delegation_after = ScheduleDelegationService(db).live(wid)
        assert delegation_after is not None, "delegation should still be live"
        assert delegation_after["state"] == "LIVE"

        wb = db.workbenches.get(wid)
        assert wb.profile_id == "prof-dest", (
            "absent profile_id should preserve existing value")
