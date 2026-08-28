"""Closed semantic result adapters for routed Story-143 adopters.

These adapters sit inside the Runner attempt.  They return only the capability
result bytes that the registry validates; provider, model, boundary, and route
metadata remain controller/DeploymentRevision receipt truth.  Consequently an
invalid provider result raises before Runner can elect or stage a successful
candidate.

The module deliberately does not install itself into any legacy entrance.
Story 143-08 adopter composition owns that later cutover.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from ..inference_capabilities import (
    InferenceCapabilityRegistry,
    InferenceCapabilityRegistryError,
    process_inference_capability_registry,
    _validate_result_value,
)
from ..kernel.model import KernelRefused
from ..kernel.provider_signals import InferenceInvalidTypedOutput


SemanticCall = Callable[[Any, Mapping[str, Any], Any], Any]


@dataclass(frozen=True)
class SemanticAdapterContract:
    capability_id: str
    capability_revision: int
    schema_sha256: str
    result_schema: Mapping[str, Any] | None = None
    allow_historical: bool = False

    @classmethod
    def current(
        cls,
        capability_id: str,
        *,
        registry: InferenceCapabilityRegistry | None = None,
    ) -> "SemanticAdapterContract":
        definition = (registry or process_inference_capability_registry()).require(
            capability_id
        )
        return cls(
            definition.id,
            definition.revision,
            definition.schema_sha256,
            definition.output_schema,
            False,
        )

    @classmethod
    def frozen(cls, definition: Mapping[str, Any]) -> "SemanticAdapterContract":
        required = {"id", "revision", "schema_sha256", "output_schema"}
        if not required <= set(definition):
            raise ValueError("frozen capability definition is incomplete")
        return cls(
            str(definition["id"]),
            int(definition["revision"]),
            str(definition["schema_sha256"]),
            dict(definition["output_schema"]),
            True,
        )


class ClosedSemanticAdapter:
    """Runner adapter that refuses before returning any untyped output."""

    connector_id = "inference-provider"

    def __init__(
        self,
        contract: SemanticAdapterContract,
        call: SemanticCall,
        normalize: Callable[[Any], Mapping[str, Any]],
        *,
        registry: InferenceCapabilityRegistry | None = None,
    ) -> None:
        self._registry = registry or process_inference_capability_registry()
        self._contract = contract
        self._call = call
        self._normalize = normalize

    def _validate(self, result: Mapping[str, Any]) -> None:
        definition = self._registry.require(self._contract.capability_id)
        if (
            definition.revision == self._contract.capability_revision
            and definition.schema_sha256 == self._contract.schema_sha256
        ):
            definition.validate_result(result)
            return
        if not self._contract.allow_historical or self._contract.result_schema is None:
            raise InferenceInvalidTypedOutput()
        _validate_result_value(
            result,
            self._contract.result_schema,
            field_name=f"{self._contract.capability_id}.result",
        )

    def dispatch(
        self, engine: Any, payload: Mapping[str, Any], cancellation: Any
    ) -> dict[str, Any]:
        raw = self._call(engine, payload, cancellation)
        try:
            result = dict(self._normalize(raw))
            self._validate(result)
        except KernelRefused:
            raise
        except (
            InferenceCapabilityRegistryError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            raise InferenceInvalidTypedOutput() from None
        return result

    def cancel(self) -> str:
        return "not_supported"


def _exact_mapping(raw: Any, fields: frozenset[str]) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != fields:
        raise ValueError("result shape")
    return raw


def _nullable_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("nullable text")
    return value


def normalize_meeting_analysis(raw: Any) -> Mapping[str, Any]:
    if isinstance(raw, Mapping):
        source = _exact_mapping(raw, frozenset({"summary", "topics", "action_items"}))
        summary, topics, action_items = (
            source["summary"],
            source["topics"],
            source["action_items"],
        )
    else:
        if str(getattr(raw, "error", "") or ""):
            raise ValueError("provider result error")
        summary = getattr(raw, "summary")
        topics = getattr(raw, "topics")
        action_items = getattr(raw, "action_items")
    if not isinstance(summary, str) or not isinstance(topics, list) or not isinstance(action_items, list):
        raise ValueError("meeting analysis fields")
    normalized_items: list[dict[str, Any]] = []
    for item in action_items:
        if isinstance(item, Mapping):
            value = _exact_mapping(item, frozenset({"task", "owner", "due"}))
            task, owner, due = value["task"], value["owner"], value["due"]
        else:
            task, owner, due = (
                getattr(item, "task"),
                getattr(item, "owner", None),
                getattr(item, "due", None),
            )
        if not isinstance(task, str):
            raise ValueError("action task")
        normalized_items.append(
            {"task": task, "owner": _nullable_text(owner), "due": _nullable_text(due)}
        )
    if any(not isinstance(topic, str) for topic in topics):
        raise ValueError("topic")
    return {"summary": summary, "topics": list(topics), "action_items": normalized_items}


def normalize_bookmark_label(raw: Any) -> Mapping[str, Any]:
    if not isinstance(raw, str):
        raise ValueError("bookmark label")
    return {"label": raw}


def normalize_meeting_title(raw: Any) -> Mapping[str, Any]:
    if not isinstance(raw, str):
        raise ValueError("meeting title")
    return {"title": raw}


def normalize_transcript(raw: Any) -> Mapping[str, Any]:
    if isinstance(raw, str):
        return {"text": raw, "language": None}
    value = _exact_mapping(raw, frozenset({"text", "language"}))
    if not isinstance(value["text"], str):
        raise ValueError("transcript text")
    return {"text": value["text"], "language": _nullable_text(value["language"])}


def normalize_lifecycle(raw: Any) -> Mapping[str, Any]:
    value = _exact_mapping(raw, frozenset({"state"}))
    if not isinstance(value["state"], str) or not value["state"]:
        raise ValueError("lifecycle state")
    return {"state": value["state"]}


def normalize_plugin_result(raw: Any) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("plugin result")
    return dict(raw)


def normalize_named_text(field: str) -> Callable[[Any], Mapping[str, Any]]:
    def normalize(raw: Any) -> Mapping[str, Any]:
        if isinstance(raw, str):
            return {field: raw}
        # The canonical prompt adapter's closed v1 carrier is admissible only
        # as this exact one-field source; provider/model evidence remains in its
        # kernel receipt and is not a semantic result field.
        if isinstance(raw, Mapping) and set(raw) == {"output", "provider", "model"} and isinstance(raw["output"], str):
            return {field: raw["output"]}
        raise ValueError(field)

    return normalize


def adapter_for(
    capability_id: str,
    call: SemanticCall,
    *,
    registry: InferenceCapabilityRegistry | None = None,
) -> ClosedSemanticAdapter:
    selected = registry or process_inference_capability_registry()
    if capability_id in {"meeting.live_analysis", "meeting.deferred_analysis"}:
        normalize = normalize_meeting_analysis
    elif capability_id == "meeting.bookmark_label":
        normalize = normalize_bookmark_label
    elif capability_id == "meeting.auto_title":
        normalize = normalize_meeting_title
    elif capability_id == "speech.transcribe":
        normalize = normalize_transcript
    elif capability_id == "speech.preload":
        normalize = normalize_lifecycle
    elif capability_id.startswith("meeting.plugin."):
        normalize = normalize_plugin_result
    elif capability_id == "background.rails_summary":
        normalize = normalize_named_text("summary")
    elif capability_id in {
        "background.cadence_draft",
        "decision.promotion_draft",
        "delivery.pr_review_draft",
    }:
        normalize = normalize_named_text("draft")
    elif capability_id == "calendar.snapshot_extract":
        normalize = normalize_named_text("output")
    else:
        raise ValueError("capability has no Story-143 semantic adapter")
    return ClosedSemanticAdapter(
        SemanticAdapterContract.current(capability_id, registry=selected),
        call,
        normalize,
        registry=selected,
    )


def adapter_for_frozen_definition(
    definition: Mapping[str, Any],
    call: SemanticCall,
    *,
    registry: InferenceCapabilityRegistry | None = None,
) -> ClosedSemanticAdapter:
    """Build the adapter named by immutable route authority evidence.

    Corrected v2 text contracts use semantic-only results.  Historical v1
    text routes retain their exact closed `{output,provider,model}` shape via a
    named read/execution adapter; they are never reinterpreted as v2.
    """
    contract = SemanticAdapterContract.frozen(definition)
    selected = registry or process_inference_capability_registry()
    current = selected.require(contract.capability_id)
    if (
        contract.capability_revision == current.revision
        and contract.schema_sha256 == current.schema_sha256
    ):
        return adapter_for(contract.capability_id, call, registry=selected)
    if contract.capability_id not in {
        "meeting.bookmark_label",
        "meeting.auto_title",
        "background.rails_summary",
        "background.cadence_draft",
        "decision.promotion_draft",
        "delivery.pr_review_draft",
    } or contract.capability_revision != 1:
        raise ValueError("no historical semantic adapter is registered")

    def historical_call(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
        raw = call(engine, payload, cancellation)
        if not isinstance(raw, str):
            raise InferenceInvalidTypedOutput()
        return {
            "output": raw,
            "provider": str(getattr(engine, "active_provider", "") or ""),
            "model": str(getattr(engine, "active_model", "") or ""),
        }

    return ClosedSemanticAdapter(
        contract,
        historical_call,
        normalize_plugin_result,
        registry=selected,
    )


__all__ = [
    "ClosedSemanticAdapter",
    "SemanticAdapterContract",
    "adapter_for",
    "adapter_for_frozen_definition",
    "normalize_bookmark_label",
    "normalize_lifecycle",
    "normalize_meeting_analysis",
    "normalize_meeting_title",
    "normalize_plugin_result",
    "normalize_transcript",
]
