"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/unit/test_agent_capabilities.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
def test_route_serves_the_table_and_the_contract_validates_it() -> None:
    from jsonschema import Draft202012Validator

    from holdspeak.web.routes.system.agent_capabilities import (
        build_agent_capabilities_router,
    )

    app = FastAPI()
    app.include_router(build_agent_capabilities_router())
    body = TestClient(app).get("/api/agents/capabilities").json()

    validator = Draft202012Validator(_schema())
    assert list(validator.iter_errors(body)) == []
    assert body == capabilities_payload()
    assert {row["adapter"] for row in body["adapters"]} == set(ADAPTERS)
