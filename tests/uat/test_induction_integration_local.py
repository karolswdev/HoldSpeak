"""The induction engine against a REAL boot — the fully-local recipes.

Proves fresh-desk, seeded-desk (idempotent — applied twice, verified both
times, no duplicate desk), and intel-endpoint-dead (the bad-endpoint deck
degrading honestly through the product's own runtime-test + doctor). No `.43`
needed. Self-skips (with the log tail) if the package can't boot here; the
`.43` recipes live in `test_induction_integration_43.py`.
"""

from __future__ import annotations

import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield mgr
    finally:
        mgr.teardown_all()


def _boot_or_skip(mgr):
    run = mgr.create_run(deck="golden-local")
    if run.status != "up":
        logs = mgr.logs(run.id, 60)
        pytest.skip(
            f"product did not boot: {run.error}\nstderr:\n{logs.get('stderr','')}"
        )
    return run


def test_fresh_desk_probe_green(real_manager):
    run = _boot_or_skip(real_manager)
    result = real_manager.apply_recipe(run.id, "fresh-desk")
    assert result.probe["ok"], result.probe


def test_seeded_desk_is_idempotent(real_manager):
    run = _boot_or_skip(real_manager)

    first = real_manager.apply_recipe(run.id, "seeded-desk")
    assert first.probe["ok"], first.probe
    assert first.already_satisfied is False  # staged this time

    client = real_manager.product_client(run.id)
    notes_after_first = client.get_json("/api/notes")["notes"]
    kbs_after_first = client.get_json("/api/kbs")["kbs"]

    # Apply again: probe-first short-circuits, no new state.
    second = real_manager.apply_recipe(run.id, "seeded-desk")
    assert second.probe["ok"], second.probe
    assert second.already_satisfied is True

    notes_after_second = client.get_json("/api/notes")["notes"]
    kbs_after_second = client.get_json("/api/kbs")["kbs"]
    assert len(notes_after_second) == len(notes_after_first)  # no duplicate desk
    assert len(kbs_after_second) == len(kbs_after_first)
    # The seeded items are all present and indistinguishable from user-made.
    ids = {n["id"] for n in notes_after_second}
    assert {"uat-seed-note-decisions", "uat-seed-note-glossary"} <= ids


def test_intel_endpoint_dead_degrades_honestly(real_manager):
    run = _boot_or_skip(real_manager)
    result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
    assert result.probe["ok"], result.probe
    # The run flipped onto the bad-endpoint deck.
    assert real_manager.get(run.id).deck == "bad-endpoint"
    # The runtime-test assertion refused fast and named the dead endpoint.
    runtime = next(
        r for r in result.probe["results"] if r["kind"] == "runtime_endpoint_unreachable"
    )
    assert runtime["ok"], runtime


def test_recipe_verify_failure_is_loud(real_manager, tmp_path):
    """A recipe whose probe cannot hold raises RecipeVerifyError, not a silent pass."""
    from uat.conductor.induction.recipes import RecipeEngine, RecipeRegistry, RecipeVerifyError

    # A recipe that seeds nothing but demands a note — impossible to satisfy.
    (tmp_path / "impossible.yaml").write_text(
        "title: impossible\ndeck: golden-local\nprobe:\n  - note_exists: never-seeded\n"
    )
    real_manager.recipes = RecipeEngine(RecipeRegistry(tmp_path))
    run = _boot_or_skip(real_manager)
    with pytest.raises(RecipeVerifyError, match="failed to verify"):
        real_manager.apply_recipe(run.id, "impossible")
