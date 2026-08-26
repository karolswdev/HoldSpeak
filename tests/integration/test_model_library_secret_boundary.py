"""HS-143-12 S3 — write-only provider credential boundary integration proof."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_key_service import ProfileKeyService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.model_library import build_model_library_router

OWNER = Principal(PrincipalKind.OWNER, "secret-boundary-owner")
AGENT = Principal(PrincipalKind.AGENT, "secret-boundary-agent")
SENTINEL = "HS143_S3_SENTINEL_7c2e929f9f6e4d238b2546200e6da04a"


def _app(tmp_path: Path) -> tuple[TestClient, ModelLibraryApplicationService]:
    db = Database(tmp_path / "secret-boundary.db")
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home",
    )
    library = ModelLibraryApplicationService(
        db,
        setup_service=setup,
        acquisition_service=acquisition,
        profile_key_service=ProfileKeyService(db, store=ProfileKeyStore(tmp_path / "custody" / "keys.json")),
    )
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = OWNER if request.headers.get("x-owner") == "yes" else AGENT
        return await call_next(request)

    app.include_router(build_model_library_router(WebContext(get_state=lambda: {}, model_library_service=library)))
    return TestClient(app), library


def _draft(request_id: str = "secret-connect-1") -> dict[str, object]:
    return {
        "request_id": request_id,
        "profile_id": "secret-boundary-provider",
        "expected_profile_revision": 0,
        "label": "Secret boundary provider",
        "provider_family": "openai_compatible",
        "model": "safe-model",
        "endpoint": "http://127.0.0.1:9011/v1",
        "requires_key": True,
    }


def test_secret_is_absent_from_json_exceptions_logs_receipts_and_assignment_heads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    # One external-wire fake: the existing OpenAI-compatible probe's HTTP result.
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": True, "models": ["safe-model"]})
    client, service = _app(tmp_path)
    caplog.set_level(logging.DEBUG)
    before = json.dumps(service.assignment_heads(OWNER), sort_keys=True, separators=(",", ":"))

    body = {"draft": _draft(), "secret": {"value": SENTINEL}}
    response = client.post("/api/inference/model-library/define-endpoint", headers={"x-owner": "yes"}, json=body)
    assert response.status_code == 200
    receipt = response.json()
    projection = client.get("/api/inference/model-library", headers={"x-owner": "yes"}).json()
    after = json.dumps(service.assignment_heads(OWNER), sort_keys=True, separators=(",", ":"))

    # A known invalid secret produces a content-free exception; validation never
    # interpolates typed secret material into its message/context.
    with pytest.raises(ServiceError) as invalid:
        service.define_endpoint(OWNER, _draft("secret-invalid-1"), {"value": SENTINEL + "\x00"})
    assert SENTINEL not in str(invalid.value)
    assert SENTINEL not in repr(invalid.value.context)

    serialized = "\n".join((
        response.text,
        json.dumps(receipt, sort_keys=True),
        json.dumps(projection, sort_keys=True),
        before,
        after,
        str(invalid.value),
        repr(invalid.value.context),
        "\n".join(record.getMessage() for record in caplog.records),
    ))
    assert SENTINEL not in serialized
    assert receipt["provider"]["secret"] == {"required": True, "present": True}
    assert receipt["receipt"]["assignments_unchanged"] is True
    assert before == after


def test_provider_unexpected_error_is_secret_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    def custody_crash(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError(f"custody adapter crashed with {SENTINEL}")

    monkeypatch.setattr(ProfileKeyService, "set", custody_crash)
    client, _service = _app(tmp_path)
    caplog.set_level(logging.DEBUG)

    response = client.post(
        "/api/inference/model-library/define-endpoint",
        headers={"x-owner": "yes"},
        json={"draft": _draft("secret-error-500"), "secret": {"value": SENTINEL}},
    )

    assert response.status_code == 500
    assert response.json() == {"error": "Provider request could not be completed."}
    serialized = "\n".join((response.text, "\n".join(record.getMessage() for record in caplog.records)))
    assert SENTINEL not in serialized


def test_owner_refusal_precedes_provider_secret_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda *_args, **_kwargs: {"ok": True, "models": []})
    client, service = _app(tmp_path)
    caplog.set_level(logging.DEBUG)
    before = service.assignment_heads(OWNER)
    response = client.post(
        "/api/inference/model-library/define-endpoint",
        json={"draft": _draft("unauthorized-1"), "secret": {"value": SENTINEL}},
    )
    assert response.status_code == 403
    assert SENTINEL not in response.text
    assert SENTINEL not in "\n".join(record.getMessage() for record in caplog.records)
    assert service.assignment_heads(OWNER) == before
