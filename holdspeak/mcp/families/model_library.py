"""Owner Model Library MCP twins over the HTTP application's service boundary.

The MCP file command accepts bounded encoded bytes, stages them under hub custody,
and never accepts a client filesystem locator. Provider secrets are an explicit
write-only field and are passed only to ``ModelLibraryApplicationService``.
"""
from __future__ import annotations

import base64
import binascii
import tempfile
from pathlib import Path
from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService

# The encoded field is deliberately bounded before decoding.  The command is a
# small-control-plane intake, not a way to stream an arbitrary client file.
MAX_MODEL_FILE_BYTES = 16 * 1024 * 1024
MAX_MODEL_FILE_BASE64_CHARS = ((MAX_MODEL_FILE_BYTES + 2) // 3) * 4


def _schema(
    name: str, properties: dict[str, Any], required: list[str], *, description: str
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "$id": f"holdspeak://mcp/{name}@1",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


_REQUEST_ID = {"type": "string", "minLength": 1, "maxLength": 128}
_PROFILE_ID = {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,95}$"}
_SECRET = {
    "type": ["object", "null"],
    "properties": {"value": {"type": "string", "minLength": 1, "maxLength": 4096}},
    "required": ["value"],
    "additionalProperties": False,
}
_HOSTED_DRAFT = {
    "type": "object",
    "properties": {
        "request_id": _REQUEST_ID,
        "profile_id": _PROFILE_ID,
        "expected_profile_revision": {"type": "integer", "minimum": 0},
        "label": {"type": "string", "minLength": 1, "maxLength": 200},
        "provider_family": {"type": "string", "enum": ["openrouter", "anthropic"]},
        "model": {"type": "string", "minLength": 1, "maxLength": 200},
        "requires_key": {"type": "boolean"},
    },
    "required": [
        "request_id", "profile_id", "expected_profile_revision", "label", "provider_family",
        "model", "requires_key",
    ],
    "additionalProperties": False,
}
_ENDPOINT_DRAFT = {
    "type": "object",
    "properties": {
        "request_id": _REQUEST_ID,
        "profile_id": _PROFILE_ID,
        "expected_profile_revision": {"type": "integer", "minimum": 0},
        "label": {"type": "string", "minLength": 1, "maxLength": 200},
        "provider_family": {
            "type": "string", "enum": ["openai_compatible", "private_endpoint", "future_backend"]
        },
        "model": {"type": "string", "minLength": 1, "maxLength": 200},
        "endpoint": {"type": "string", "minLength": 1, "maxLength": 1024},
        "requires_key": {"type": "boolean"},
    },
    "required": [
        "request_id", "profile_id", "expected_profile_revision", "label", "provider_family",
        "model", "endpoint", "requires_key",
    ],
    "additionalProperties": False,
}
_PAIRED_DRAFT = {
    "type": "object",
    "properties": {
        "request_id": _REQUEST_ID,
        "profile_id": _PROFILE_ID,
        "expected_profile_revision": {"type": "integer", "minimum": 0},
        "label": {"type": "string", "minLength": 1, "maxLength": 200},
        "provider_family": {"type": "string", "enum": ["paired_device"]},
        "model": {"type": "string", "minLength": 1, "maxLength": 200},
        "paired_target_id": {"type": "string", "minLength": 1, "maxLength": 160},
    },
    "required": [
        "request_id", "profile_id", "expected_profile_revision", "label", "provider_family",
        "model", "paired_target_id",
    ],
    "additionalProperties": False,
}
_PROVIDER_INPUT = {"draft": _HOSTED_DRAFT, "secret": _SECRET}


TOOLS: list[dict[str, Any]] = [
    _schema("model_library.get", {}, [], description="Read the owner Model Library projection."),
    _schema(
        "model_library.download",
        {
            "request_id": _REQUEST_ID,
            "catalog_id": {"type": "string", "minLength": 1, "maxLength": 160},
            "catalog_revision": {"type": "integer", "minimum": 1},
        },
        ["request_id", "catalog_id", "catalog_revision"],
        description="Start one catalog-pinned Model Library download. Assignments stay unchanged.",
    ),
    _schema(
        "model_library.add_to_library",
        {"request_id": _REQUEST_ID, "detected_artifact_id": {"type": "string", "minLength": 1, "maxLength": 160}},
        ["request_id", "detected_artifact_id"],
        description="Add one server-detected artifact to the Model Library. Assignments stay unchanged.",
    ),
    _schema(
        "model_library.connect_hosted_model",
        _PROVIDER_INPUT,
        ["draft", "secret"],
        description="Connect a hosted provider. secret is write-only and is never returned, logged, or receipted.",
    ),
    _schema(
        "model_library.define_endpoint",
        {"draft": _ENDPOINT_DRAFT, "secret": _SECRET},
        ["draft", "secret"],
        description="Define a provider endpoint. secret is write-only and is never returned, logged, or receipted.",
    ),
    _schema(
        "model_library.connect_paired_device",
        {"draft": _PAIRED_DRAFT},
        ["draft"],
        description="Connect one already-paired device to the Model Library.",
    ),
    _schema(
        "model_library.use_model_file",
        {
            "request_id": _REQUEST_ID,
            "filename": {"type": "string", "minLength": 1, "maxLength": 180},
            "bytes_base64": {"type": "string", "minLength": 4, "maxLength": MAX_MODEL_FILE_BASE64_CHARS},
        },
        ["request_id", "filename", "bytes_base64"],
        description=(
            "Add one model file from base64 bytes (maximum 16 MiB decoded). The hub stages and "
            "deletes the file; client paths and extra fields are refused."
        ),
    ),
]


def _service() -> ModelLibraryApplicationService:
    """Compose the same owner aggregate and acquisition foundation as web startup."""
    db = get_database()
    setup = InferenceSetupApplicationService(db)
    acquisition = InferenceAcquisitionApplicationService(db, setup_service=setup)
    return ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition,
    )


def _invalid_upload() -> ServiceError:
    return ServiceError(
        "model_library_upload_invalid", "Use model file has an invalid request shape.", context={"status": 400}
    )


def _closed(arguments: dict[str, Any], *allowed: str) -> None:
    if set(arguments) != set(allowed):
        raise ServiceError(
            "model_library_request_invalid", "Model Library request has an invalid request shape.", context={"status": 400}
        )


def _staged_file(arguments: dict[str, Any]) -> tuple[str, str, bytes]:
    if set(arguments) != {"request_id", "filename", "bytes_base64"}:
        raise _invalid_upload()
    filename = arguments.get("filename")
    encoded = arguments.get("bytes_base64")
    if not isinstance(filename, str) or not isinstance(encoded, str):
        raise _invalid_upload()
    # Explicitly reject a path rather than accepting a string then relying on
    # tempfile's directory choice.  The service repeats the basename guard.
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise _invalid_upload()
    if len(encoded) > MAX_MODEL_FILE_BASE64_CHARS:
        raise _invalid_upload()
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise _invalid_upload() from None
    if not payload or len(payload) > MAX_MODEL_FILE_BYTES:
        raise _invalid_upload()
    return str(arguments["request_id"]), filename, payload


def _provider_arguments(arguments: dict[str, Any], expected_draft: set[str], *, secret: bool) -> tuple[dict[str, Any], dict[str, Any] | None]:
    allowed = {"draft", "secret"} if secret else {"draft"}
    if set(arguments) != allowed or not isinstance(arguments.get("draft"), dict):
        raise ServiceError("model_library_provider_invalid", "Provider request is invalid.", context={"status": 400})
    draft = arguments["draft"]
    if set(draft) != expected_draft:
        raise ServiceError("model_library_provider_invalid", "Provider request is invalid.", context={"status": 400})
    value = arguments.get("secret")
    if secret and value is not None and not isinstance(value, dict):
        raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
    return draft, value if secret else None


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch only closed Model Library commands after owner authority.

    The guard deliberately precedes every argument inspection, including base64
    decoding and provider-secret handling, matching the HTTP seam's order.
    """
    service = _service()
    service.require_owner(principal)
    if name == "model_library.get":
        _closed(arguments)
        return service.get_library(principal)
    if name == "model_library.download":
        # The shared command validates its exact request DTO. Calling it directly
        # preserves the HTTP seam's specific stable refusal code.
        return service.download(principal, dict(arguments))
    if name == "model_library.add_to_library":
        return service.add_to_library(principal, dict(arguments))
    if name == "model_library.connect_hosted_model":
        draft, secret = _provider_arguments(
            arguments,
            {"request_id", "profile_id", "expected_profile_revision", "label", "provider_family", "model", "requires_key"},
            secret=True,
        )
        return service.connect_hosted_model(principal, draft, secret)
    if name == "model_library.define_endpoint":
        draft, secret = _provider_arguments(
            arguments,
            {"request_id", "profile_id", "expected_profile_revision", "label", "provider_family", "model", "endpoint", "requires_key"},
            secret=True,
        )
        return service.define_endpoint(principal, draft, secret)
    if name == "model_library.connect_paired_device":
        draft, _ = _provider_arguments(
            arguments,
            {"request_id", "profile_id", "expected_profile_revision", "label", "provider_family", "model", "paired_target_id"},
            secret=False,
        )
        return service.connect_paired_device(principal, draft)
    if name == "model_library.use_model_file":
        request_id, filename, payload = _staged_file(arguments)
        suffix = Path(filename).suffix.lower() or ".upload"
        staging_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="holdspeak-model-library-", suffix=suffix, delete=False
            ) as staged:
                staging_path = Path(staged.name)
                staged.write(payload)
            return service.use_model_file(
                principal, request_id=request_id, filename=filename, staging_path=staging_path,
            )
        finally:
            if staging_path is not None:
                staging_path.unlink(missing_ok=True)
    raise LookupError(name)


__all__ = ["MAX_MODEL_FILE_BYTES", "TOOLS", "dispatch"]
