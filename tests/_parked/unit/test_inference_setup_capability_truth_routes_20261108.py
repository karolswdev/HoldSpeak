"""PARKED 20261108 (subtraction day, Lane R): GET /api/inference/setup is parked.

Moved from ``tests/unit/test_inference_setup_capability_truth.py``: test_http_agent_is_denied_and_projection_performs_no_runner_or_revision_write, and the HTTP read that opened test_http_setup_has_no_legacy_mcp_resource_alias. Not collected.
"""
def test_http_setup_has_no_legacy_mcp_resource_alias(tmp_path: Path, monkeypatch):
    db, service = _service(tmp_path)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {}, setup_service=SetupService(db), inference_setup_service=service,
    )))
    assert TestClient(app).get("/api/inference/setup").status_code == 200


def test_http_agent_is_denied_and_projection_performs_no_runner_or_revision_write(tmp_path: Path, monkeypatch):
    db, service = _service(tmp_path)
    monkeypatch.setattr(
        "holdspeak.deployment_revisions.capture_deployment_revision",
        lambda *_args, **_kwargs: pytest.fail("projection attempted a deployment upsert"),
    )
    app = FastAPI()

    @app.middleware("http")
    async def agent(request: Request, call_next):
        request.state.principal = AGENT
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {}, setup_service=SetupService(db), inference_setup_service=service,
    )))

    response = TestClient(app).get("/api/inference/setup")

    assert response.status_code == 403
    assert response.json()["error"] == "Owner access is required."


