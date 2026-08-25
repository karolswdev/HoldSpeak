"""One-shot provider-neutral native-tool model adapter contract (HS-143-09 A5).

This is deliberately below the ToolTurn controller and above a selected provider
wire implementation.  It does not choose a route, retry, admit a child, or
execute a tool.  For every physical ``InferenceRunner`` child it renders one
frozen request with its already-projected palette, sends one provider request,
and parses one response into one closed candidate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from threading import Lock
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from .tool_capability_service import ToolCallCandidate, ToolCapabilityError, canonical_json


class ToolModelAdapterError(ValueError):
    """The one-shot native dialect contract was violated."""


def _json_object(value: Any, *, field: str) -> dict[str, Any]:
    try:
        normalized = json.loads(canonical_json(value))
    except (ToolCapabilityError, TypeError, ValueError) as exc:
        raise ToolModelAdapterError(f"{field} must be canonical JSON") from exc
    if not isinstance(normalized, dict):
        raise ToolModelAdapterError(f"{field} must be an object")
    return normalized


@dataclass(frozen=True)
class ToolModelAnswerCandidate:
    """The sole closed non-tool outcome from one provider response."""

    answer: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "answer", _json_object(self.answer, field="answer"))

    def to_dict(self) -> dict[str, Any]:
        return {"schema": "ToolModelAnswerCandidate@1", "kind": "answer", "answer": dict(self.answer)}

    def provider_result(self) -> dict[str, Any]:
        """Return the frozen operation's ordinary typed result unchanged."""
        return dict(self.answer)


@dataclass(frozen=True)
class ToolModelToolCallCandidate:
    """The sole closed tool outcome from one provider response."""

    tool_call: ToolCallCandidate

    def __post_init__(self) -> None:
        if not isinstance(self.tool_call, ToolCallCandidate):
            raise ToolModelAdapterError("tool_call must be a ToolCallCandidate")

    def to_dict(self) -> dict[str, Any]:
        return {"schema": "ToolModelToolCallCandidate@1", "kind": "tool_call", "tool_call": self.tool_call.to_dict()}

    def provider_result(self) -> dict[str, Any]:
        """Encode one call in the existing frozen ``validated_tool_turn`` result.

        The adapter still yields exactly one candidate.  This carrier only lets
        the existing typed-result/receipt path persist the model child before the
        controller separately admits that one candidate through its real Broker
        boundary.
        """
        return {
            "summary": "native tool call",
            "tool_calls": [{
                "name": self.tool_call.capability_id,
                "arguments_json": canonical_json(dict(self.tool_call.arguments)),
            }],
        }


ToolModelCandidate = ToolModelAnswerCandidate | ToolModelToolCallCandidate


@runtime_checkable
class ToolModelAdapter(Protocol):
    """A provider-native one-request/one-response dialect adapter.

    ``render`` receives only a frozen model request and provider-safe projected
    tools.  ``parse`` accepts one provider response and returns one closed answer
    or tool-call candidate.  Route selection, retries, child admission and tool
    execution belong to the existing controller and never to this interface.
    """

    def render(
        self,
        frozen_request: Mapping[str, Any],
        provider_tools: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]: ...

    def parse(self, response: Mapping[str, Any]) -> ToolModelCandidate: ...


@runtime_checkable
class ToolModelProviderTransport(Protocol):
    """Selected engine wire boundary used by :class:`ToolModelProviderAdapter`."""

    def dispatch(self, engine: Any, request: Mapping[str, Any], cancellation: Any) -> Mapping[str, Any]: ...

    def cancel(self) -> str: ...


class ToolModelProviderAdapter:
    """The real ``InferenceRunner`` adapter bridge for one ToolModelAdapter call.

    It deliberately has no loop.  One ``dispatch`` invokes render once, transport
    once, and parse once.  The produced candidate is retained only so the
    controller can admit its single tool call after the model child is durably
    receipted.
    """

    def __init__(
        self,
        model_adapter: ToolModelAdapter,
        transport: ToolModelProviderTransport,
        provider_tools: Sequence[Mapping[str, Any]],
    ) -> None:
        if not isinstance(model_adapter, ToolModelAdapter):
            raise ToolModelAdapterError("ToolModelAdapter is required")
        if not isinstance(transport, ToolModelProviderTransport):
            raise ToolModelAdapterError("ToolModelProviderTransport is required")
        self._model_adapter = model_adapter
        self._transport = transport
        self._provider_tools = tuple(_json_object(tool, field="provider_tool") for tool in provider_tools)
        self._lock = Lock()
        self._candidates: list[ToolModelCandidate] = []

    def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> dict[str, Any]:
        frozen_request = _json_object(payload, field="frozen_request")
        try:
            provider_request = self._model_adapter.render(frozen_request, self._provider_tools)
            request = _json_object(provider_request, field="provider_request")
            response = self._transport.dispatch(engine, request, cancellation)
            candidate = self._model_adapter.parse(_json_object(response, field="provider_response"))
        except ToolModelAdapterError:
            raise
        except (ToolCapabilityError, TypeError, ValueError) as exc:
            raise ToolModelAdapterError("provider tool dialect rejected its one response") from exc
        if not isinstance(candidate, (ToolModelAnswerCandidate, ToolModelToolCallCandidate)):
            raise ToolModelAdapterError("provider response did not yield one closed candidate")
        with self._lock:
            self._candidates.append(candidate)
        return candidate.provider_result()

    def cancel(self) -> str:
        return self._transport.cancel()

    def terminal_candidate(self) -> ToolModelCandidate:
        """Return the one candidate from a one-attempt terminal model step.

        A retry/fallback has more than one physical child and must settle under
        the existing route controller before a later routing slice chooses which
        candidate is actionable.  Treating the last completion as a winner here
        would violate that receipt authority.
        """
        with self._lock:
            if len(self._candidates) != 1:
                raise ToolModelAdapterError("model step does not have exactly one parsed candidate")
            return self._candidates[0]

    def candidate_for_result(self, result: Mapping[str, Any]) -> ToolModelCandidate:
        """Recover the settled winner's closed candidate from its typed result.

        The existing route controller elects the winning immutable child.  This
        bridge only matches that elected typed result; it never elects a result by
        completion timing.  Identical repeated candidates are semantically the
        same closed candidate, while distinct candidates with one result shape are
        an integrity error.
        """
        result_json = canonical_json(_json_object(result, field="result"))
        with self._lock:
            matches = [candidate for candidate in self._candidates if canonical_json(candidate.provider_result()) == result_json]
        if not matches:
            raise ToolModelAdapterError("settled model result has no parsed candidate")
        identities = {canonical_json(candidate.to_dict()) for candidate in matches}
        if len(identities) != 1:
            raise ToolModelAdapterError("settled model result maps to multiple candidates")
        return matches[-1]


class DeterministicToolModelAdapter:
    """Internal reference dialect for production-path tests, not a provider fake.

    The only fake is the small request/response wire envelope.  Its caller still
    goes through ``InferenceRunner``, route reservation, kernel child admission,
    durable receipt settlement, and (for a call) ToolTurn Broker admission.
    """

    REQUEST_SCHEMA = "DeterministicToolModelRequest@1"
    RESPONSE_SCHEMA = "DeterministicToolModelResponse@1"

    def render(
        self,
        frozen_request: Mapping[str, Any],
        provider_tools: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        return {
            "schema": self.REQUEST_SCHEMA,
            "request": _json_object(frozen_request, field="frozen_request"),
            "tools": [_json_object(tool, field="provider_tool") for tool in provider_tools],
        }

    def parse(self, response: Mapping[str, Any]) -> ToolModelCandidate:
        raw = _json_object(response, field="provider_response")
        if set(raw) != {"schema", "candidate"} or raw["schema"] != self.RESPONSE_SCHEMA:
            raise ToolModelAdapterError("deterministic provider response shape is invalid")
        candidate = _json_object(raw["candidate"], field="provider_candidate")
        kind = candidate.get("kind")
        if kind == "answer" and set(candidate) == {"kind", "answer"}:
            return ToolModelAnswerCandidate(_json_object(candidate["answer"], field="answer"))
        if kind == "tool_call" and set(candidate) == {
            "kind", "provider_tool_call_id", "provider_call_ordinal", "capability_id", "arguments"
        }:
            try:
                return ToolModelToolCallCandidate(ToolCallCandidate(
                    provider_tool_call_id=candidate["provider_tool_call_id"],
                    capability_id=candidate["capability_id"],
                    arguments=_json_object(candidate["arguments"], field="arguments"),
                    provider_call_ordinal=candidate["provider_call_ordinal"],
                ))
            except ToolCapabilityError as exc:
                raise ToolModelAdapterError("deterministic tool candidate is invalid") from exc
        raise ToolModelAdapterError("deterministic provider response has no closed candidate")


class DeterministicToolModelTransport:
    """One-response reference transport used only with the reference dialect."""

    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = _json_object(response, field="response")
        self.requests: list[dict[str, Any]] = []
        self.dispatch_count = 0

    def dispatch(self, _engine: Any, request: Mapping[str, Any], _cancellation: Any) -> Mapping[str, Any]:
        self.dispatch_count += 1
        self.requests.append(_json_object(request, field="request"))
        return dict(self.response)

    def cancel(self) -> str:
        return "cancelled"


__all__ = [
    "DeterministicToolModelAdapter",
    "DeterministicToolModelTransport",
    "ToolModelAdapter",
    "ToolModelAdapterError",
    "ToolModelAnswerCandidate",
    "ToolModelCandidate",
    "ToolModelProviderAdapter",
    "ToolModelProviderTransport",
    "ToolModelToolCallCandidate",
]
