"""HS-143-11 S2 — declarative reciprocal HTTP/MCP owner-transport goldens.

Each table row runs fresh, real HTTP and MCP compositions.  The normalizer keeps
transport envelope facts separate, while replacing only generated IDs, hashes,
and timestamps by their structural role.  It never records a transcript.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.mcp import server
from holdspeak.mcp.families import inference_assignments, model_library
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_service import ProfileService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.inference_assignments import build_inference_assignments_router
from holdspeak.web.routes.model_library import build_model_library_router
from tests.unit.test_phase143_inference_assignments import _profile

OWNER = Principal(PrincipalKind.OWNER, "transport-parity-owner")
AGENT = Principal(PrincipalKind.AGENT, "transport-parity-agent")
MODEL_TURN = Principal(PrincipalKind.SERVICE, "transport-parity-turn")


@dataclass
class Side:
    db: Database
    library: ModelLibraryApplicationService
    assignments: InferenceAssignmentService
    client: TestClient | None
    home: Path


@dataclass(frozen=True)
class Vector:
    name: str
    mcp_name: str
    http_method: str
    http_path: str
    family: str
    seed: Callable[[Side], None]
    command: Callable[[Side], dict[str, Any]]
    invalid: Callable[[Side], dict[str, Any]] | None
    replay: bool = False
    cas: bool = False


def _side(tmp_path: Path, *, http: bool) -> Side:
    db = Database(tmp_path / ("http.db" if http else "mcp.db"))
    home = tmp_path / "home"
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: home,
    )
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: home,
    )
    # A parity vector compares command admission/receipt, not a network transfer.
    # The production acquisition service remains in use; only its asynchronous
    # executor handoff is held so a catalogue URL can never outlive this test.
    acquisition._submit = lambda _job_id: None
    library = ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition)
    assignments = InferenceAssignmentService(db)
    if not http:
        return Side(db, library, assignments, None, home)
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        kind = request.headers.get("x-principal")
        request.state.principal = {
            "owner": OWNER, "agent": AGENT, "model-turn": MODEL_TURN, "none": None,
        }.get(kind, AGENT)
        return await call_next(request)

    app.include_router(build_model_library_router(WebContext(get_state=lambda: {}, model_library_service=library)))
    app.include_router(build_inference_assignments_router(WebContext(get_state=lambda: {}, inference_assignment_service=assignments)))
    return Side(db, library, assignments, TestClient(app), home)


def _none(_side: Side) -> None:
    return None


def _detected(side: Side) -> None:
    path = side.home / "Models" / "gguf" / "transport-parity.gguf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"GGUFtransport-parity")


def _paired(side: Side) -> None:
    ProfileService(side.db).create_profile(OWNER, {
        "id": "transport-paired", "name": "Parity device", "kind": "meshNode",
        "node": "offline-node", "model": "Parity remote",
    })


def _profile_seed(side: Side) -> None:
    _profile(side.db, "transport-primary")


def _clear_seed(side: Side) -> None:
    _profile_seed(side)
    side.assignments.set_assignment(OWNER, {
        "command_id": "transport-clear-seed", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "transport-primary", "profile_revision": 1}],
        "retry_policy_id": None,
    })


def _catalog_command(side: Side) -> dict[str, Any]:
    projection = side.library.get_library(OWNER)
    catalog = next(row for row in projection["rows"] if row["source"] == "catalog")
    return {
        "request_id": "transport-download", "catalog_id": catalog["id"].removeprefix("catalog:"),
        "catalog_revision": projection["catalog_revision"],
    }


def _detected_command(side: Side) -> dict[str, Any]:
    projection = side.library.get_library(OWNER)
    detected = next(row for row in projection["rows"] if row["source"] == "detected")
    return {"request_id": "transport-detected", "detected_artifact_id": detected["id"].removeprefix("detected:")}


def _hosted_command(_side: Side) -> dict[str, Any]:
    return {
        "draft": {
            "request_id": "transport-hosted", "profile_id": "transport-hosted", "expected_profile_revision": 0,
            "label": "Transport hosted", "provider_family": "anthropic", "model": "safe-model", "requires_key": True,
        },
        "secret": {"value": "transport-secret-sentinel"},
    }


def _endpoint_command(_side: Side) -> dict[str, Any]:
    return {
        "draft": {
            "request_id": "transport-endpoint", "profile_id": "transport-endpoint", "expected_profile_revision": 0,
            "label": "Transport endpoint", "provider_family": "future_backend", "model": "safe-model",
            "endpoint": "http://127.0.0.1:9999/v1", "requires_key": False,
        },
        "secret": None,
    }


def _paired_command(_side: Side) -> dict[str, Any]:
    return {"draft": {
        "request_id": "transport-paired", "profile_id": "transport-paired", "expected_profile_revision": 0,
        "label": "Parity device", "provider_family": "paired_device", "model": "Parity remote",
        "paired_target_id": "transport-paired",
    }}


def _upload_command(_side: Side) -> dict[str, Any]:
    return {
        "request_id": "transport-upload", "filename": "transport.gguf",
        "bytes_base64": base64.b64encode(b"GGUFtransport-upload").decode(),
    }


def _editor_command(_side: Side) -> dict[str, Any]:
    return {"scope": {"kind": "global"}, "capability_id": "ask.answer"}


def _set_command(_side: Side) -> dict[str, Any]:
    return {
        "command_id": "transport-set", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "transport-primary", "profile_revision": 1}], "retry_policy_id": None,
    }


def _clear_command(side: Side) -> dict[str, Any]:
    preview = side.assignments.preview_use_default(OWNER, scope={"kind": "global"}, capability_id="ask.answer")
    return {
        "command_id": "transport-clear", "expected_revision": preview["expected_revision"],
        "scope": {"kind": "global"}, "capability_id": "ask.answer",
    }


def _unknown(command: Callable[[Side], dict[str, Any]]) -> Callable[[Side], dict[str, Any]]:
    return lambda side: {**command(side), "unknown_nested_or_route_field": {"private_locator": "/never"}}


# This is the golden declaration. Each mutating row declares replay and, for
# assignments, the narrow stale-CAS variant. Projections have no request body,
# so their invalid-payload column is explicitly N/A rather than inventing HTTP
# glass that the shipped owner API does not parse.
VECTORS = (
    Vector("model_library.get", "model_library.get", "GET", "/api/inference/model-library", "library", _none, lambda _s: {}, None),
    Vector("model_library.download", "model_library.download", "POST", "/api/inference/model-library/download", "library", _none, _catalog_command, _unknown(_catalog_command), replay=True),
    Vector("model_library.add_to_library", "model_library.add_to_library", "POST", "/api/inference/model-library/add-to-library", "library", _detected, _detected_command, _unknown(_detected_command), replay=True),
    Vector("model_library.use_model_file", "model_library.use_model_file", "POST", "/api/inference/model-library/use-model-file", "library", _none, _upload_command, _unknown(_upload_command), replay=True),
    Vector("model_library.connect_hosted_model", "model_library.connect_hosted_model", "POST", "/api/inference/model-library/connect-hosted-model", "library", _none, _hosted_command, _unknown(_hosted_command), replay=True),
    Vector("model_library.define_endpoint", "model_library.define_endpoint", "POST", "/api/inference/model-library/define-endpoint", "library", _none, _endpoint_command, _unknown(_endpoint_command), replay=True),
    Vector("model_library.connect_paired_device", "model_library.connect_paired_device", "POST", "/api/inference/model-library/connect-paired-device", "library", _paired, _paired_command, _unknown(_paired_command), replay=True),
    Vector("inference_assignment.summary", "inference_assignment.summary", "GET", "/api/inference/assignments", "assignment", _none, lambda _s: {}, None),
    Vector("inference_assignment.editor", "inference_assignment.editor", "POST", "/api/inference/assignments/editor", "assignment", _none, _editor_command, _unknown(_editor_command)),
    Vector("inference_assignment.set", "inference_assignment.set", "POST", "/api/inference/assignments/set", "assignment", _profile_seed, _set_command, _unknown(_set_command), replay=True, cas=True),
    Vector("inference_assignment.preview_use_default", "inference_assignment.preview_use_default", "POST", "/api/inference/assignments/preview-use-default", "assignment", _none, _editor_command, _unknown(_editor_command)),
    Vector("inference_assignment.clear", "inference_assignment.clear", "POST", "/api/inference/assignments/clear", "assignment", _clear_seed, _clear_command, _unknown(_clear_command), replay=True, cas=True),
)


def _http_call(vector: Vector, side: Side, body: dict[str, Any], principal: str) -> tuple[bool, dict[str, Any], int]:
    assert side.client is not None
    headers = {"x-principal": principal}
    if vector.name == "model_library.use_model_file":
        data = {"request_id": body.get("request_id", "")}
        if "unknown_nested_or_route_field" in body:
            data["unknown_nested_or_route_field"] = "refuse"
        response = side.client.post(
            vector.http_path, headers=headers, data=data,
            files={"file": (str(body.get("filename", "")), base64.b64decode(str(body.get("bytes_base64", ""))))},
        )
    elif vector.http_method == "GET":
        response = side.client.get(vector.http_path, headers=headers)
    else:
        # The shipped paired-device HTTP seam deliberately uses the same
        # provider envelope and requires the explicit null secret marker; its
        # MCP twin omits that transport-only marker because it has no secret.
        payload = {**body, "secret": None} if vector.name == "model_library.connect_paired_device" else body
        response = side.client.request(vector.http_method, vector.http_path, headers=headers, json=payload)
    return response.status_code < 400, response.json(), response.status_code


def _mcp_call(vector: Vector, body: dict[str, Any], principal: Principal) -> tuple[bool, dict[str, Any]]:
    response = server.handle_message({
        "jsonrpc": "2.0", "id": vector.name, "method": "tools/call",
        "params": {"name": vector.mcp_name, "arguments": body},
    })
    assert response is not None
    result = response["result"]
    return not result["isError"], json.loads(result["content"][0]["text"])


def _assignment_head_bytes(side: Side) -> bytes:
    return json.dumps(
        side.library.assignment_heads(OWNER), sort_keys=True, separators=(",", ":")
    ).encode()


def _normalize(value: Any, *, key: str = "") -> Any:
    if isinstance(value, list):
        return [_normalize(item, key=key) for item in value]
    if not isinstance(value, dict):
        if key.endswith("_at") and isinstance(value, str):
            return "<timestamp>"
        if key in {"id", "assignment_id", "binding_id", "observation_id", "job_id"} and isinstance(value, str):
            return "<generated-id>"
        if key in {"sha256", "request_sha256", "response_sha256"} and isinstance(value, str):
            return "<sha256>"
        return value
    # The HTTP error transport intentionally omits safe service context whereas
    # MCP's standard envelope preserves it. The shared logical error is code.
    if "code" in value and "error" in value:
        return {"code": value["code"]}
    if "code" in value and "message" in value and len(value) <= 2:
        return {"code": value["code"]}
    return {key_: _normalize(item, key=key_) for key_, item in value.items()}


def _assert_equal(http: tuple[bool, dict[str, Any], int], mcp: tuple[bool, dict[str, Any]]) -> None:
    http_ok, http_body, status = http
    mcp_ok, mcp_body = mcp
    assert http_ok is mcp_ok
    # Envelope facts remain assertions, rather than being silently normalized.
    assert status < 400 if http_ok else status in {400, 403, 404, 409, 413, 503}
    assert mcp_ok is http_ok
    assert _normalize(http_body) == _normalize(mcp_body)


@pytest.mark.parametrize("vector", VECTORS, ids=lambda vector: vector.name)
def test_transport_parity_vectors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, vector: Vector,
) -> None:
    http_side = _side(tmp_path / "http", http=True)
    mcp_side = _side(tmp_path / "mcp", http=False)
    vector.seed(http_side)
    vector.seed(mcp_side)
    monkeypatch.setattr(model_library, "_service", lambda: mcp_side.library)
    monkeypatch.setattr(inference_assignments, "_service", lambda: mcp_side.assignments)
    current = SimpleNamespace(principal=OWNER)
    monkeypatch.setattr(server, "resolve_auth", lambda: current)

    http_body, mcp_body = vector.command(http_side), vector.command(mcp_side)
    http_heads = _assignment_head_bytes(http_side) if vector.family == "library" else None
    mcp_heads = _assignment_head_bytes(mcp_side) if vector.family == "library" else None
    first_http = _http_call(vector, http_side, http_body, "owner")
    first_mcp = _mcp_call(vector, mcp_body, OWNER)
    _assert_equal(first_http, first_mcp)
    # The availability library can never choose a capability model. Check the
    # exact canonical bytes around every one of its seven HTTP/MCP twins.
    if vector.family == "library":
        assert _assignment_head_bytes(http_side) == http_heads
        assert _assignment_head_bytes(mcp_side) == mcp_heads

    # All tools reject non-owner calls before a malformed body becomes a command
    # input. The HTTP parser therefore sees a 403 and MCP exposes the same code.
    current.principal = AGENT
    denied_http = _http_call(vector, http_side, {"private_locator": "/owner-only"}, "agent")
    denied_mcp = _mcp_call(vector, {"private_locator": "/owner-only"}, AGENT)
    _assert_equal(denied_http, denied_mcp)
    assert _normalize(denied_http[1]) == {"code": "model_library_owner_required" if vector.family == "library" else "inference_assignment_owner_required"}
    current.principal = OWNER

    if vector.invalid is not None:
        invalid_http = _http_call(vector, http_side, vector.invalid(http_side), "owner")
        invalid_mcp = _mcp_call(vector, vector.invalid(mcp_side), OWNER)
        _assert_equal(invalid_http, invalid_mcp)
    if vector.replay:
        replay_http = _http_call(vector, http_side, http_body, "owner")
        replay_mcp = _mcp_call(vector, mcp_body, OWNER)
        _assert_equal(replay_http, replay_mcp)
        assert _normalize(replay_http[1]) == _normalize(first_http[1])
        assert _normalize(replay_mcp[1]) == _normalize(first_mcp[1])
    if vector.cas:
        stale_revision = 0 if vector.name == "inference_assignment.set" else http_body["expected_revision"]
        stale_http = _http_call(vector, http_side, {**http_body, "command_id": "transport-stale", "expected_revision": stale_revision}, "owner")
        stale_mcp = _mcp_call(vector, {**mcp_body, "command_id": "transport-stale", "expected_revision": stale_revision}, OWNER)
        _assert_equal(stale_http, stale_mcp)
        assert _normalize(stale_http[1]) == {"code": "inference_assignment_revision_conflict"}


def test_assignment_set_committed_effect_replay_is_identical_but_not_a_projection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """ORCH-CALL 4: receipt chain/hash replay, with no private material."""
    http_side = _side(tmp_path / "http", http=True)
    mcp_side = _side(tmp_path / "mcp", http=False)
    _profile_seed(http_side)
    _profile_seed(mcp_side)
    monkeypatch.setattr(model_library, "_service", lambda: mcp_side.library)
    monkeypatch.setattr(inference_assignments, "_service", lambda: mcp_side.assignments)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    vector = next(item for item in VECTORS if item.name == "inference_assignment.set")
    http_body, mcp_body = _set_command(http_side), _set_command(mcp_side)
    first_http, first_mcp = _http_call(vector, http_side, http_body, "owner"), _mcp_call(vector, mcp_body, OWNER)
    replay_http, replay_mcp = _http_call(vector, http_side, http_body, "owner"), _mcp_call(vector, mcp_body, OWNER)
    for first, replay in ((first_http[1], replay_http[1]), (first_mcp[1], replay_mcp[1])):
        assert replay["committed_effect"] == first["committed_effect"]
        assert replay["committed_effect"]["sha256"] != ""
        assert replay["committed_effect"] != {"schema": "InferenceAssignmentSummary@1"}
        rendered = json.dumps(replay["committed_effect"], sort_keys=True)
        for forbidden in ("local_locator", "secret_slot", "endpoint", "binding_id", "/private/"):
            assert forbidden not in rendered
