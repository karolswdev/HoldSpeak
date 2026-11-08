"""PARKED 20261108 (subtraction day, Lane R): the HTTP half of the capability parity test (GET /api/inference/capabilities* parked).

Moved from ``tests/unit/test_inference_capability_registry.py``. Not collected.
"""
def test_owner_http_and_mcp_share_the_same_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    service = InferenceCapabilityApplicationService(_registry())
    app = FastAPI()
    current_principal = {"value": OWNER}

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = current_principal["value"]
        return await call_next(request)

    app.include_router(
        build_setup_router(
            WebContext(
                get_state=lambda: {},
                setup_service=SimpleNamespace(),
                inference_setup_service=SimpleNamespace(),
                inference_capability_service=service,
            )
        )
    )
    http = TestClient(app).get("/api/inference/capabilities")
    assert http.status_code == 200
    expected = service.get_capabilities(OWNER)
    assert http.json() == {"capabilities": expected}
    current_principal["value"] = AGENT
    assert TestClient(app).get("/api/inference/capabilities").status_code == 403
    current_principal["value"] = MODEL_TURN
    assert TestClient(app).get("/api/inference/capabilities").status_code == 403

    fake_broker = SimpleNamespace(inference_capability_service=service)
    monkeypatch.setattr(resources, "get_database", lambda: object())
    import holdspeak.kernel.runtime as runtime

    monkeypatch.setattr(runtime, "_configure", lambda _db: fake_broker)
    mcp = resources.read_resource("holdspeak://inference/capabilities", OWNER)
    assert json.loads(mcp["contents"][0]["text"]) == {"capabilities": expected}
    current_principal["value"] = OWNER
    detail_http = TestClient(app).get("/api/inference/capabilities/agent.tool_turn")
    assert detail_http.status_code == 200
    monkeypatch.setattr(resources, "process_inference_capability_registry", lambda: service.registry)
    detail_mcp = resources.read_resource("holdspeak://inference/capabilities/agent.tool_turn", OWNER)
    assert json.loads(detail_mcp["contents"][0]["text"]) == detail_http.json()
    assert all(row["uri"] != "holdspeak://inference/capabilities" for row in resources.list_resources(AGENT)["resources"])
    assert all("inference/capabilities" not in row["uriTemplate"] for row in resources.list_resources(AGENT)["resourceTemplates"])


