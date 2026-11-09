# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_one_path_spine.py to restore.

# ruff: noqa


# --- test_the_two_admission_shapes_both_appear_across_every_surface: P2: sanity checks on the test's own driver table and SurfaceRun records, not the product
def test_the_two_admission_shapes_both_appear_across_every_surface() -> None:
    """Sanity on the trace mechanism itself: the fence would be worthless if
    every surface happened to use the same admission shape — prove both a
    root (Broker.submit) and a parent-scoped child (Broker.submit_trusted_child)
    admission are exercised somewhere in the matrix above."""
    import inspect

    assert ROOT_SHAPED_SURFACES | CHILD_SHAPED_SURFACES == set(SURFACE_DRIVERS)
    assert not (ROOT_SHAPED_SURFACES & CHILD_SHAPED_SURFACES)
    assert ROOT_SHAPED_SURFACES and CHILD_SHAPED_SURFACES
    for name in SURFACE_DRIVERS:
        assert inspect.isfunction(SURFACE_DRIVERS[name])


# --- test_each_driver_reports_the_run_it_actually_performed: P2: sanity checks on the test's own driver table and SurfaceRun records, not the product
def test_each_driver_reports_the_run_it_actually_performed(tmp_path, monkeypatch) -> None:
    """The declared admission shape must match what the driver hands back.

    ``SurfaceRun.parent_operation_id`` is the handle the provenance suite reads
    its rows through, so a driver that stopped running under its parent — or
    started running under one — has to be caught HERE rather than quietly
    changing which cohort the fence inspects. Exercised on one surface of each
    shape; the provenance suite re-checks every one against the stored rows.
    """
    for surface in ("Ask", "voice"):
        run = SURFACE_DRIVERS[surface](tmp_path / surface.replace(" ", "-"), monkeypatch)
        assert isinstance(run, SurfaceRun), f"{surface}: driver returned {run!r}"
        assert run.destination_id, f"{surface}: driver named no destination"
        assert run.expected_children >= 1
        if surface in ROOT_SHAPED_SURFACES:
            assert run.parent_operation_id is None and run.parent_kind is None
        else:
            assert run.parent_operation_id and run.parent_kind


# --- test_every_sanitizing_adapter_reraises_control_signals_first: P8/P5: AST scan of except-clause order; the runtime test beside it proves the signal passes through
@pytest.mark.parametrize(("path", "scope"), SANITIZING_ADAPTERS)
def test_every_sanitizing_adapter_reraises_control_signals_first(path: str, scope: str) -> None:
    """Structurally: the CONTROL_SIGNALS clause precedes the BaseException clause.

    Ordering is the whole property. ``except BaseException`` first would catch a
    dialect signal no matter what the later clauses say, which is exactly the bug
    this pins: one physical attempt, one dead receipt, and an endpoint that would
    have answered reported as failed.
    """
    import ast

    body = _dispatch_body(path, scope)
    handlers = [
        handler for node in ast.walk(body)
        if isinstance(node, ast.Try) for handler in node.handlers
    ]
    names = [ast.unparse(handler.type) if handler.type else "bare" for handler in handlers]
    assert "CONTROL_SIGNALS" in names, f"{path}:{scope} does not name CONTROL_SIGNALS"
    catch_all = [
        index for index, name in enumerate(names)
        if name in {"BaseException", "Exception", "bare"}
    ]
    assert catch_all, f"{path}:{scope} no longer sanitizes; re-review this entry"
    assert names.index("CONTROL_SIGNALS") < min(catch_all), (
        f"{path}:{scope} sanitizes BEFORE it re-raises control signals"
    )
