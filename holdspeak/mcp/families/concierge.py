"""Concierge MCP twins (HS-170-03).

Five tools: concierge.detect, concierge.propose, concierge.probe,
concierge.apply, concierge.download.
"""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError


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


TOOLS: list[dict[str, Any]] = [
    _schema(
        "concierge.detect",
        {},
        [],
        description="Detect every engine: LAN endpoints, local files, cloud keys present, presets not yet downloaded.",
    ),
    _schema(
        "concierge.propose",
        {},
        [],
        description="Propose one engine set for the seven capability groups.",
    ),
    _schema(
        "concierge.probe",
        {
            "engineId": {"type": "string", "minLength": 1, "maxLength": 256},
            "generate": {
                "type": "boolean",
                "description": "Pass true for a cloud engine to perform an explicit one-token probe (cost: 1 token).",
            },
        },
        ["engineId"],
        description="Probe one engine. LAN/local always probes; cloud only with generate:true.",
    ),
    _schema(
        "concierge.apply",
        {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "group": {"type": "string"},
                        "engineId": {"type": ["string", "null"]},
                        "state": {"type": "string"},
                    },
                    "required": ["group"],
                },
                "minItems": 1,
            },
        },
        ["rows"],
        description="Apply the engine set. Refuses if any group is WAITING and not OFF.",
    ),
    _schema(
        "concierge.download",
        {
            "presetId": {"type": "string", "minLength": 1, "maxLength": 160},
        },
        ["presetId"],
        description="Start a preset download. Returns the job id and a progress shape.",
    ),
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route concierge MCP tool calls."""
    db = get_database()

    if name == "concierge.detect":
        from holdspeak.services.concierge_service import detect
        return detect(db=db)

    if name == "concierge.propose":
        from holdspeak.services.concierge_service import detect, propose
        detection = detect(db=db)
        return propose(engines=detection["engines"])

    if name == "concierge.probe":
        engine_id = str(arguments.get("engineId", ""))
        generate = bool(arguments.get("generate", False))
        if not engine_id:
            raise ServiceError(
                "concierge_probe_invalid",
                "engineId is required.",
                context={"status": 400},
            )
        from holdspeak.services.concierge_service import detect, probe
        detection = detect(db=db)
        engine = None
        for e in detection["engines"]:
            if e["id"] == engine_id:
                engine = e
                break
        if engine is None:
            raise ServiceError(
                "concierge_engine_not_found",
                f"Engine '{engine_id}' not found.",
                context={"status": 404},
            )
        return probe(engine=engine, generate=generate)

    if name == "concierge.apply":
        rows = arguments.get("rows", [])
        if not isinstance(rows, list) or not rows:
            raise ServiceError(
                "concierge_apply_invalid",
                "rows is required.",
                context={"status": 400},
            )
        from holdspeak.services.concierge_service import apply, detect
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        detection = detect(db=db)
        assignment_svc = InferenceAssignmentService(db)
        return apply(
            rows=rows,
            engines=detection["engines"],
            assignment_service=assignment_svc,
            principal=principal,
            db=db,
        )

    if name == "concierge.download":
        preset_id = str(arguments.get("presetId", ""))
        if not preset_id:
            raise ServiceError(
                "concierge_download_invalid",
                "presetId is required.",
                context={"status": 400},
            )
        from holdspeak.services.concierge_service import download
        from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
        from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
        from holdspeak.services.model_library_service import ModelLibraryApplicationService
        from holdspeak.inference_setup_catalog import (
            packaged_catalog_envelope_json,
            verify_catalog_envelope,
        )
        from datetime import datetime, timezone

        setup = InferenceSetupApplicationService(db)
        acquisition = InferenceAcquisitionApplicationService(db, setup_service=setup)
        model_lib_svc = ModelLibraryApplicationService(
            db, setup_service=setup, acquisition_service=acquisition,
        )

        now = datetime.now(timezone.utc)
        envelope_json = packaged_catalog_envelope_json()
        catalog = verify_catalog_envelope(envelope_json, now=now)
        catalog_revision = catalog["catalog_revision"]

        return download(
            preset_id=preset_id,
            model_library_service=model_lib_svc,
            principal=principal,
            catalog_revision=catalog_revision,
        )

    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
