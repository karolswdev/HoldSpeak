# PARKED 2026-11-09 (pipe/test-mass): this test called RecipeService.cancel,
# which no longer exists. The cancel thread died on AttributeError, so the
# fake provider waited out a 60 s guard and the test passed without proof
# (60 s, the slowest test in the suite). The cancel-after-return law is
# still proven for the live runner paths in tests/unit/test_ask_runner_migration.py
# and tests/unit/test_inference_runner_stream.py.
# Moved from tests/unit/test_recipe_runner_migration.py; fixture ``rig`` and
# the imports are there.
from __future__ import annotations


def test_recipe_cancelled_after_provider_return_publishes_and_returns_no_output(
    rig: tuple[Database, object], monkeypatch
) -> None:
    """A direct cancel of the Recipe child lands while the provider is in flight.

    The provider then returns. The receipt records the return; the late output
    is not staged, not published and not returned to the caller.
    """
    from tests._cancel_after_return import (
        SIGNAL_FIRST, assert_provider_return_on_record, cancel_child_in_flight,
        force_cancel_order, invoke_child_operation_id,
    )

    db, broker = rig
    service = RecipeService(db, broker=broker)
    settled = force_cancel_order(monkeypatch, SIGNAL_FIRST)
    seen: list[str] = []

    class CancelledInFlight(Engine):
        def run_prompt(self, **_kwargs: object) -> str:
            seen.append(cancel_child_in_flight(db, settled, lambda iid: service.cancel(OWNER, iid)))
            return "late recipe output"

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: CancelledInFlight()
    try:
        output: object = asyncio.run(service.run(OWNER, "r1", input="first"))
    except Exception as exc:  # noqa: BLE001 - the refusal is the answer here
        output = exc
    assert len(seen) == 1
    assert "late recipe output" not in repr(output)
    assert isinstance(output, Exception), output
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_projection_stages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0
    assert_provider_return_on_record(db, invoke_child_operation_id(db, seen[0]), fenced=True)
