"""Sequence family — MCP tools for the SequenceWorkflowService surface."""
from __future__ import annotations

import asyncio
from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal

TOOLS: list[dict[str, Any]] = [
    {
        "name": "sequence.run",
        "description": "Run a Sequence (chain) through the admitted inference path. MODEL-INVOKING. The result carries the receipt, steps, and artifact reference.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chain_id": {"type": "string", "description": "Sequence identifier."},
                "input": {"type": "string", "description": "Input text for the first step."},
                "variables": {"type": "object", "description": "Template variables for prompt rendering."},
                "inference_target_id": {"type": "string", "description": "Override inference destination."},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "max_tokens": {"type": "integer", "minimum": 1},
                "request_id": {"type": "string", "description": "Idempotency key for replay."},
            },
            "required": ["chain_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sequence.cancel",
        "description": "Cancel an in-flight Sequence run by its parent operation id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_operation_id": {"type": "string"},
            },
            "required": ["parent_operation_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workflow.run",
        "description": "Run a Workflow through the admitted inference path. MODEL-INVOKING. Returns the receipt, node steps, and artifact reference.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "Workflow identifier."},
                "input": {"type": "string", "description": "Input text for the workflow."},
                "variables": {"type": "object", "description": "Template variables for prompt rendering."},
                "inference_target_id": {"type": "string", "description": "Override inference destination."},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "max_tokens": {"type": "integer", "minimum": 1},
                "request_id": {"type": "string", "description": "Idempotency key for replay."},
            },
            "required": ["workflow_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workflow.cancel",
        "description": "Cancel an in-flight Workflow run by its parent operation id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_operation_id": {"type": "string"},
            },
            "required": ["parent_operation_id"],
            "additionalProperties": False,
        },
    },
]


def _run(coro: Any) -> Any:
    """Run an async coroutine synchronously; mirrors tools.py:411-416."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ValueError("async MCP tools cannot execute inside an active event loop")


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name == "sequence.run":
        chain_id = arguments.get("chain_id")
        if not isinstance(chain_id, str) or not chain_id.strip():
            raise ValueError("chain_id is required")
        from holdspeak.kernel.runtime import _configure
        from holdspeak.services.sequence_workflow_service import SequenceWorkflowService
        db = get_database()
        broker = _configure(db)
        svc = SequenceWorkflowService(db, broker)
        body: dict[str, Any] = {}
        if "input" in arguments:
            body["input"] = arguments["input"]
        if "variables" in arguments:
            body["variables"] = arguments["variables"]
        if "inference_target_id" in arguments:
            body["inference_target_id"] = arguments["inference_target_id"]
        if "temperature" in arguments:
            body["temperature"] = arguments["temperature"]
        if "max_tokens" in arguments:
            body["max_tokens"] = arguments["max_tokens"]
        if "request_id" in arguments:
            body["request_id"] = arguments["request_id"]
        return _run(svc.run_sequence(principal, chain_id, body))

    if name == "sequence.cancel":
        parent_operation_id = arguments.get("parent_operation_id")
        if not isinstance(parent_operation_id, str) or not parent_operation_id.strip():
            raise ValueError("parent_operation_id is required")
        from holdspeak.kernel.runtime import _configure
        db = get_database()
        broker = _configure(db)
        disposition = broker.parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)
        return {"parent_operation_id": parent_operation_id, "disposition": disposition}

    if name == "workflow.run":
        workflow_id = arguments.get("workflow_id")
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError("workflow_id is required")
        from holdspeak.kernel.runtime import _configure
        from holdspeak.services.sequence_workflow_service import SequenceWorkflowService
        db = get_database()
        broker = _configure(db)
        svc = SequenceWorkflowService(db, broker)
        body = {}
        if "input" in arguments:
            body["input"] = arguments["input"]
        if "variables" in arguments:
            body["variables"] = arguments["variables"]
        if "inference_target_id" in arguments:
            body["inference_target_id"] = arguments["inference_target_id"]
        if "temperature" in arguments:
            body["temperature"] = arguments["temperature"]
        if "max_tokens" in arguments:
            body["max_tokens"] = arguments["max_tokens"]
        if "request_id" in arguments:
            body["request_id"] = arguments["request_id"]
        return _run(svc.run_workflow(principal, workflow_id, body))

    if name == "workflow.cancel":
        parent_operation_id = arguments.get("parent_operation_id")
        if not isinstance(parent_operation_id, str) or not parent_operation_id.strip():
            raise ValueError("parent_operation_id is required")
        from holdspeak.kernel.runtime import _configure
        db = get_database()
        broker = _configure(db)
        disposition = broker.parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)
        return {"parent_operation_id": parent_operation_id, "disposition": disposition}

    raise LookupError(name)
