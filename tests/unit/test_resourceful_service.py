from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.resourceful_service import ResourcefulService, _night_key


OWNER = Principal(PrincipalKind.OWNER, "resourceful-owner")


def _rig(tmp_path):  # noqa: ANN001
    db = Database(tmp_path / "resourceful.db")
    recipe = db.recipes.upsert(recipe_id="recipe-resourceful", name="Optimizer")
    db.workbenches.upsert(
        workbench_id="wb-resourceful",
        name="Resourceful",
        recipe_id=recipe.id,
    )
    directory = db.directories.upsert(directory_id="dir-ideas", name="Loose Ideas")
    return db, directory


def _idea(db, directory, idea_id: str, title: str, revision: str) -> None:  # noqa: ANN001
    db.notes.upsert(
        note_id=idea_id,
        title=title,
        body_markdown=f"Explore {title}",
        last_modified=revision,
    )
    db.directory_memberships.upsert(
        primitive_id=f"note:{idea_id}", directory_id=directory.id,
    )


def test_two_resourceful_items_can_complete_in_one_night_six_hours_apart(tmp_path) -> None:
    db, directory = _rig(tmp_path)
    _idea(db, directory, "idea-1", "Ambient project memory", "2026-01-01T00:00:00+00:00")
    _idea(db, directory, "idea-2", "Causal work maps", "2026-01-02T00:00:00+00:00")
    calls = []

    async def run_one(principal, workbench_id, item_id, event):  # noqa: ANN001
        calls.append((principal, workbench_id, item_id, event))
        with db._connection() as conn:
            conn.execute(
                "UPDATE workbench_items SET status='done',completed_at=datetime('now') WHERE id=?",
                (item_id,),
            )
        return {
            "parent_operation_id": f"op-{len(calls)}",
            "receipt_id": f"receipt-{len(calls)}",
            "terminal_disposition": "succeeded",
        }

    service = ResourcefulService(db, item_runner=run_one)
    policy = service.configure_policy(OWNER, "wb-resourceful", enabled=True)
    assert policy["cooldown_hours"] == 6
    assert policy["nightly_target"] == 2

    start = datetime(2026, 8, 16, 22, 0, tzinfo=timezone.utc)
    assert asyncio.run(service.tick(OWNER, now=start))[0]["status"] == "idle_started"
    first = asyncio.run(service.tick(OWNER, now=start + timedelta(minutes=31)))[0]
    assert first["status"] == "completed"
    assert asyncio.run(service.tick(OWNER, now=start + timedelta(hours=5)))[0]["status"] == "cooldown"

    second = asyncio.run(service.tick(OWNER, now=start + timedelta(hours=6, minutes=31)))[0]
    assert second["status"] == "completed"
    assert len(calls) == 2
    assert service.get_policy(OWNER, "wb-resourceful")["nightly_count"] == 2
    assert len(service.history(OWNER, "wb-resourceful")) == 2
    assert len(db.automations.list_events(event_type="workbench.became_idle")) == 1
    assert len(db.automations.list_events(
        event_type="workbench.resourceful_opportunity_found"
    )) == 2


def test_candidate_revision_is_not_redispatched_and_no_candidate_is_bounded(tmp_path) -> None:
    db, directory = _rig(tmp_path)
    _idea(db, directory, "idea-1", "One idea", "2026-01-01T00:00:00+00:00")

    async def run_one(principal, workbench_id, item_id, event):  # noqa: ANN001
        del principal, workbench_id, event
        with db._connection() as conn:
            conn.execute("UPDATE workbench_items SET status='done' WHERE id=?", (item_id,))
        return {"terminal_disposition": "succeeded"}

    service = ResourcefulService(db, item_runner=run_one)
    service.configure_policy(
        OWNER, "wb-resourceful", enabled=True, cooldown_hours=1, nightly_target=3,
    )
    start = datetime(2026, 8, 16, 22, 0, tzinfo=timezone.utc)
    asyncio.run(service.tick(OWNER, now=start))
    asyncio.run(service.tick(OWNER, now=start + timedelta(minutes=31)))
    empty = asyncio.run(service.tick(OWNER, now=start + timedelta(hours=1, minutes=32)))[0]
    assert empty["status"] == "no_candidate"
    bounded = asyncio.run(service.tick(OWNER, now=start + timedelta(hours=2)))[0]
    assert bounded["status"] == "no_candidate_cooldown"
    assert len(service.history(OWNER, "wb-resourceful")) == 1


def test_ordinary_pending_work_resets_the_idle_epoch(tmp_path) -> None:
    db, _ = _rig(tmp_path)
    service = ResourcefulService(db, item_runner=lambda *args: {})
    service.configure_policy(OWNER, "wb-resourceful", enabled=True)
    start = datetime(2026, 8, 16, 22, 0, tzinfo=timezone.utc)
    asyncio.run(service.tick(OWNER, now=start))
    db.workbench_items.upsert(
        item_id="ordinary", workbench_id="wb-resourceful", title="Owner work",
    )

    result = asyncio.run(service.tick(OWNER, now=start + timedelta(hours=1)))[0]

    assert result["status"] == "busy"
    assert service.get_policy(OWNER, "wb-resourceful")["idle_since"] is None


def test_execution_exception_fails_admitted_item_instead_of_stranding_busy(tmp_path) -> None:
    db, directory = _rig(tmp_path)
    _idea(db, directory, "idea-1", "Fragile idea", "2026-01-01T00:00:00+00:00")

    async def fail_run(*args):  # noqa: ANN002
        del args
        raise RuntimeError("model disappeared")

    service = ResourcefulService(db, item_runner=fail_run)
    service.configure_policy(OWNER, "wb-resourceful", enabled=True)
    start = datetime(2026, 8, 16, 22, 0, tzinfo=timezone.utc)
    asyncio.run(service.tick(OWNER, now=start))

    failed = asyncio.run(service.tick(OWNER, now=start + timedelta(minutes=31)))[0]

    assert failed["status"] == "failed"
    item = db.workbench_items.list_for_workbench("wb-resourceful")[0]
    assert item.status == "failed"
    assert "model disappeared" in str(item.result)
    assert service.history(OWNER, "wb-resourceful")[0]["outcome"] == "failed"
    assert asyncio.run(
        service.tick(OWNER, now=start + timedelta(hours=1))
    )[0]["status"] == "cooldown"


def test_night_key_returns_none_during_day_and_key_during_night() -> None:
    # Default night window: 22:00 - 07:00 (start > end, wraps midnight)
    afternoon = datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc)
    assert _night_key(afternoon, 22, 7) is None

    late_night = datetime(2026, 8, 17, 23, 30, tzinfo=timezone.utc)
    assert _night_key(late_night, 22, 7) == "2026-08-17"

    early_morning = datetime(2026, 8, 17, 3, 0, tzinfo=timezone.utc)
    assert _night_key(early_morning, 22, 7) == "2026-08-16"

    # Non-wrapping window: 01:00 - 05:00
    assert _night_key(datetime(2026, 8, 17, 3, 0, tzinfo=timezone.utc), 1, 5) == "2026-08-17"
    assert _night_key(datetime(2026, 8, 17, 10, 0, tzinfo=timezone.utc), 1, 5) is None


def test_daytime_tick_with_night_only_returns_awaiting_night(tmp_path) -> None:
    db, directory = _rig(tmp_path)
    _idea(db, directory, "idea-1", "Daytime idea", "2026-01-01T00:00:00+00:00")

    service = ResourcefulService(db, item_runner=lambda *a: {})
    service.configure_policy(OWNER, "wb-resourceful", enabled=True, night_only=True)

    # Start the idle epoch at a nighttime hour so it registers
    night_start = datetime(2026, 8, 16, 23, 0, tzinfo=timezone.utc)
    asyncio.run(service.tick(OWNER, now=night_start))

    # Tick at 14:00 (daytime) - should be gated by night_only
    daytime = datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc)
    result = asyncio.run(service.tick(OWNER, now=daytime))[0]
    assert result["status"] == "awaiting_night"
