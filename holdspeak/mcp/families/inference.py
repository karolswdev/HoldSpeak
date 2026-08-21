"""Owner inference setup/acquisition tools (HS-142-02)."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object", "properties": properties,
            "required": required, "additionalProperties": False,
        },
    }


TOOLS = [
    _tool(
        "inference.download_and_use",
        "Download, verify, install, and use one signed local model preset for Thoughts.",
        {
            "request_id": {"type": "string"},
            "preset_id": {"type": "string"},
            "catalog_revision": {"type": "integer", "minimum": 1},
            "context_choice": {"type": "integer", "enum": [8192, 16384, 32768]},
            "expected_route_revision": {"type": "string"},
        },
        ["request_id", "preset_id", "catalog_revision", "context_choice", "expected_route_revision"],
    ),
    _tool(
        "inference.cancel_model_acquisition",
        "Cancel a model download before verification begins.",
        {
            "request_id": {"type": "string"},
            "job_id": {"type": "string"},
            "expected_revision": {"type": "integer", "minimum": 1},
        },
        ["request_id", "job_id", "expected_revision"],
    ),
    _tool(
        "inference.use_existing_model",
        "Verify and use one local GGUF projected by inference setup.",
        {
            "request_id": {"type": "string"},
            "detected_artifact_id": {"type": "string"},
            "context_choice": {"type": "integer", "enum": [8192]},
            "expected_route_revision": {"type": "string"},
        },
        [
            "request_id", "detected_artifact_id", "context_choice",
            "expected_route_revision",
        ],
    ),
]


def _service() -> InferenceAcquisitionApplicationService:
    db = get_database()
    setup = InferenceSetupApplicationService(db)
    return InferenceAcquisitionApplicationService(
        db, setup_service=setup, auto_recover=False,
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    if name == "inference.download_and_use":
        return _service().download_and_use(principal, dict(arguments))
    if name == "inference.cancel_model_acquisition":
        body = {
            "request_id": arguments["request_id"],
            "expected_revision": arguments["expected_revision"],
        }
        return _service().cancel(principal, str(arguments["job_id"]), body)
    if name == "inference.use_existing_model":
        return _service().use_existing(principal, dict(arguments))
    raise LookupError(name)
