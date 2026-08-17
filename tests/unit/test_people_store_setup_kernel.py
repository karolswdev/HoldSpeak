"""Kernel admission for the one People sidecar creation gesture."""
from __future__ import annotations

import pytest

import holdspeak.db.core as db_core
from holdspeak.db import Database
from holdspeak.kernel import runtime
from holdspeak.kernel.people_store_setup import (
    PEOPLE_STORE_SETUP_EXECUTIONS,
    PeopleStoreSetupRefused,
    run_people_store_setup,
)
from holdspeak.principals import Principal, PrincipalKind


OWNER = Principal(PrincipalKind.OWNER, "people-setup-owner")
AGENT = Principal(PrincipalKind.AGENT, "people-setup-agent")


@pytest.fixture
def broker(tmp_path, monkeypatch):
    database = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(db_core, "_db", database)
    PEOPLE_STORE_SETUP_EXECUTIONS._plans.clear()
    PEOPLE_STORE_SETUP_EXECUTIONS._operation_ids.clear()
    PEOPLE_STORE_SETUP_EXECUTIONS._outcomes.clear()
    return database, runtime._configure(database)


def _full(broker, operation_id: str):
    return broker.read([f"operation:{operation_id}"], "full", "committed", OWNER)["objects"][0]


def test_owner_approval_initializes_once_and_receipts_content_free(broker) -> None:
    database, kernel = broker
    sentinel = "SENTINEL-NAME-OR-PATH-NEVER-JOURNALED"
    called: list[str] = []

    assert run_people_store_setup(initialize=lambda: called.append(sentinel) or "ready", principal=OWNER, broker=kernel) == "ready"
    result = next(iter(PEOPLE_STORE_SETUP_EXECUTIONS._outcomes.items()))
    native_id, outcome = result
    full = _full(kernel, PEOPLE_STORE_SETUP_EXECUTIONS._operation_ids[native_id])

    assert called == [sentinel]
    assert outcome == "succeeded"
    assert full["receipt"]["outcome"] == "succeeded"
    assert full["operation"]["target_ref"] == "people-store:local"
    assert full["native_receipts"] == [{"receipt_ref": full["receipt"]["result_ref"], "native_id": native_id, "outcome": "succeeded"}]
    assert sentinel not in str(full)
    assert sentinel.encode() not in database.db_path.read_bytes()


def test_non_owner_is_refused_and_initializer_never_runs(broker) -> None:
    _database, kernel = broker
    called = False

    def initialize():
        nonlocal called
        called = True

    with pytest.raises(PeopleStoreSetupRefused, match="people_store_setup_owner_required"):
        run_people_store_setup(initialize=initialize, principal=AGENT, broker=kernel)
    assert called is False


def test_initializer_failure_terminalizes_indeterminate_without_error_content(broker) -> None:
    database, kernel = broker
    sentinel = "SENTINEL-FAILURE-CONTENT"

    def initialize():
        raise RuntimeError(sentinel)

    with pytest.raises(RuntimeError, match=sentinel):
        run_people_store_setup(initialize=initialize, principal=OWNER, broker=kernel)
    native_id = next(iter(PEOPLE_STORE_SETUP_EXECUTIONS._outcomes))
    full = _full(kernel, PEOPLE_STORE_SETUP_EXECUTIONS._operation_ids[native_id])
    assert full["receipt"]["outcome"] == "indeterminate"
    assert sentinel not in str(full)
    assert sentinel.encode() not in database.db_path.read_bytes()
