"""HS-143-12 S1 — narrow Model Library HTTP transport proofs."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.model_library import build_model_library_router

OWNER = Principal(PrincipalKind.OWNER, "library-http-owner")
AGENT = Principal(PrincipalKind.AGENT, "library-http-agent")


def _client(tmp_path: Path) -> TestClient:
    db = Database(tmp_path / "library-http.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home")
    library = ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition)
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER if request.headers.get("x-owner") == "yes" else AGENT
        return await call_next(request)

    app.include_router(build_model_library_router(WebContext(get_state=lambda: {}, model_library_service=library)))
    return TestClient(app)


def test_library_http_is_owner_before_body_and_closed(tmp_path: Path) -> None:
    client = _client(tmp_path)
    # Invalid JSON remains unparsed for non-owners: owner auth wins.
    denied = client.post("/api/inference/model-library/download", content=b"not-json")
    assert denied.status_code == 403
    assert denied.json()["code"] == "model_library_owner_required"

    projection = client.get("/api/inference/model-library", headers={"x-owner": "yes"})
    assert projection.status_code == 200
    assert set(projection.json()) == {"schema", "catalog_revision", "artifact_detection", "summary", "rows"}
    invalid = client.post(
        "/api/inference/model-library/download", headers={"x-owner": "yes"},
        json={"request_id": "one", "catalog_id": "x", "catalog_revision": 1, "expected_route_revision": "forbidden"},
    )
    assert invalid.status_code == 400
    assert "expected_route_revision" not in invalid.json()["message"]


def test_file_upload_is_one_multipart_command_with_no_path_field(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.post(
        "/api/inference/model-library/use-model-file", headers={"x-owner": "yes"},
        data={"request_id": "file-one"}, files={"file": ("owner.gguf", b"GGUFhttp-fixture", "application/octet-stream")},
    )
    assert response.status_code == 202, response.text
    receipt = response.json()["receipt"]
    assert receipt["assignments_unchanged"] is True
    assert receipt["message"] == "Added to the Model Library. Assignments are unchanged."
    invalid = client.post(
        "/api/inference/model-library/use-model-file", headers={"x-owner": "yes"},
        data={"request_id": "file-two", "path": "/not-allowed"}, files={"file": ("owner.gguf", b"GGUFhttp-fixture", "application/octet-stream")},
    )
    assert invalid.status_code == 400


def test_library_http_never_returns_legacy_assignment_copy(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.get("/api/inference/model-library", headers={"x-owner": "yes"})
    assert response.status_code == 200
    rendered = response.text
    for forbidden in ("Use model", "In use", "Download & use", "Connect & use", "Test", "secret_slot"):
        assert forbidden not in rendered
