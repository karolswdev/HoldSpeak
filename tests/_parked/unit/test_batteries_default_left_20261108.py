"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_batteries_default.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def test_state_route_and_use_it_press(tmp_path: Path, engines) -> None:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    from holdspeak.web.routes.inference_assignments import build_inference_assignments_router

    llama = engines(["Qwen3.5-27B-Instruct"])
    desk = _desk(tmp_path, scan=_scan_of((llama, "llama.cpp")))
    desk.defaults.ensure(reason="boot")
    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_inference_assignments_router(SimpleNamespace(
        inference_assignment_service=desk.assignments, inference_default_service=desk.defaults,
    )))
    client = TestClient(app)
    body = client.get("/api/inference/defaults").json()
    assert body["default"]["made_by"] == "holdspeak"
    assert _by_id(body)["chat.turn"]["state"] == "inherited_from_default"
    missing = client.post("/api/inference/defaults/use-proposal", json={"proposal_id": "nope"})
    assert missing.status_code == 404
    bad = client.post("/api/inference/defaults/use-proposal", json={"proposal_id": "x", "more": 1})
    assert bad.status_code == 400
