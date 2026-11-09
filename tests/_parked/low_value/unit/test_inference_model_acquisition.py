# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_inference_model_acquisition.py to restore.

# ruff: noqa


# --- test_retired_acquisition_aliases_disappear_without_replacement_receipt: P8: two retired routes answer 405; a phase-era removal fence
def test_retired_acquisition_aliases_disappear_without_replacement_receipt(tmp_path: Path):
    db, service, _config, preset = _fixture(tmp_path)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(
        get_state=lambda: {},
        setup_service=SetupService(db),
        inference_setup_service=service._setup,
        inference_acquisition_service=service,
    )))
    body = {
        "request_id": "transport-parity",
        "preset_id": preset["id"],
        "catalog_revision": 7,
        "context_choice": 8192,
        "expected_route_revision": service.route_revision(_config),
    }
    client = TestClient(app)
    assert client.post("/api/inference/acquisitions/download-and-use", json=body).status_code == 405
    assert client.post("/api/inference/acquisitions/use-existing", json=body).status_code == 405
    assert {
        "inference.download_and_use", "inference.use_existing_model",
    }.isdisjoint({tool["name"] for tool in inference_mcp.TOOLS})
    for name in ("inference.download_and_use", "inference.use_existing_model"):
        with pytest.raises(LookupError):
            inference_mcp.dispatch(name, body, OWNER)
