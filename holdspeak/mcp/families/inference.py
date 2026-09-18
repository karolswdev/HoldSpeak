"""Owner inference setup/acquisition tools (HS-142-02)."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

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
        "inference.cancel_model_acquisition",
        "Cancel a model download before verification begins. This does not change model assignments.",
        {
            "request_id": {"type": "string"},
            "job_id": {"type": "string"},
            "expected_revision": {"type": "integer", "minimum": 1},
        },
        ["request_id", "job_id", "expected_revision"],
    ),
]


def _build_service() -> InferenceAcquisitionApplicationService:
    db = db_or(get_database)
    setup = InferenceSetupApplicationService(db)
    return InferenceAcquisitionApplicationService(
        db, setup_service=setup, auto_recover=False,
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    if name == "inference.cancel_model_acquisition":
        body = {
            "request_id": arguments["request_id"],
            "expected_revision": arguments["expected_revision"],
        }
        return _service().cancel(principal, str(arguments["job_id"]), body)
    raise LookupError(name)


# HS-200-45 R1: _service asks the ONE composition root first. Inside the hub that
# returns the instance the HTTP routes use -- composed with auto-recovery against the hub's setup service.
# Outside a hub (a unit test's bare root, or the standalone diagnosis hatch) the
# root holds nothing and the bare builder above runs, producing exactly the
# object the pre-HS-200-45 code produced.
def _service() -> InferenceAcquisitionApplicationService:
    """The hub's live service, else the bare composition above."""
    return runtime_service("inference_acquisition_service", _build_service)
