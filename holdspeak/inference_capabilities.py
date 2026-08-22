"""Phase 143's canonical, composition-owned inference capability registry.

This module deliberately knows *what a typed intelligence job requires*, not
which model will execute it.  Profiles, bindings, assignments, route plans and
physical inference remain later-story concerns.  Keeping this registry pure
means a bad definition is rejected while the process composes, before a
profile, deployment, credential, or :class:`InferenceRunner` can be reached.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


CAPABILITY_SCHEMA = "InferenceCapabilityDefinition@1"
RETRY_POLICY_SCHEMA = "InferenceRetryPolicyDefinition@1"
REGISTRY_PROJECTION_SCHEMA = "InferenceCapabilityRegistryProjection@1"
_SLUG = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_PLUGIN_REVISION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
# This is the existing Phase-130 provider/placement egress vocabulary.  A
# paired device is topology; its actual egress boundary remains one of these.
_BOUNDARIES = frozenset({"local", "private_network", "mesh", "cloud"})
_CONTEXT_SUPPORT = frozenset({"exact", "bounded", "unavailable"})
_VISIBILITY = frozenset({"owner", "internal", "future"})
_DEFINITION_ORIGINS = frozenset({"admitted_service", "saved_definition", "plugin_definition"})
_DISPOSITIONS = frozenset(
    {
        "preflight_unavailable",
        "known_no_generation_transient",
        "dispatch_outcome_unknown",
        "provider_permanent",
        "invalid_typed_output",
        "invalid_tool_call",
        "context_overflow",
        "local_capacity_unavailable",
        "tool_unavailable_or_stale",
        "permission_denied",
        "policy_refused",
        "owner_cancelled",
        "deadline_exhausted",
        "physical_outcome_unknown",
        "effect_indeterminate",
        "owner_terminal",
    }
)


class InferenceCapabilityRegistryError(ValueError):
    """Base error for a composition-invalid registry."""

    code = "inference_capability_registry_invalid"


class UnknownInferenceCapability(InferenceCapabilityRegistryError):
    code = "unknown_inference_capability"


class DuplicateInferenceCapability(InferenceCapabilityRegistryError):
    code = "duplicate_inference_capability"


class ConfusableInferenceCapability(InferenceCapabilityRegistryError):
    code = "confusable_inference_capability"


class SchemaDriftInferenceCapability(InferenceCapabilityRegistryError):
    code = "inference_capability_schema_drift"


class RetryPolicyReferenceError(InferenceCapabilityRegistryError):
    code = "inference_retry_policy_reference_invalid"


class PluginCapabilityError(InferenceCapabilityRegistryError):
    code = "inference_plugin_capability_invalid"


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            _json_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InferenceCapabilityRegistryError("registry value is not canonically encodable") from exc


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _json_plain(value: Any) -> Any:
    """Convert recursively frozen registry material back to canonical JSON data."""
    if isinstance(value, Mapping):
        return {str(key): _json_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_plain(item) for item in value]
    if isinstance(value, list):
        return [_json_plain(item) for item in value]
    return value


def _freeze_json(value: Any, *, field_name: str) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise InferenceCapabilityRegistryError(f"{field_name} keys must be strings")
            frozen[key] = _freeze_json(item, field_name=field_name)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, field_name=field_name) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise InferenceCapabilityRegistryError(f"{field_name} must contain JSON values only")


def _closed_object_schema(
    *,
    properties: Mapping[str, Mapping[str, Any]],
    required: Sequence[str],
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {str(name): dict(value) for name, value in properties.items()},
        "required": list(required),
    }


def _validate_closed_result_schema(schema: Any) -> Mapping[str, Any]:
    """Accept only the intentionally small, closed JSON-schema subset we freeze."""
    _validate_schema_node(schema, field_name="output_schema", root=True)
    return schema


def _validate_schema_node(schema: Any, *, field_name: str, root: bool = False) -> None:
    """Validate every nested node; object-valued rows can never be open blobs."""
    if not isinstance(schema, Mapping):
        raise InferenceCapabilityRegistryError(f"{field_name} must be an object")
    kind = str(schema.get("type") or "")
    if kind not in {"string", "number", "integer", "boolean", "array", "object"}:
        raise InferenceCapabilityRegistryError(f"{field_name} has unsupported type")
    if kind == "object":
        _validate_closed_object_node(schema, field_name=field_name)
        return
    if root:
        raise InferenceCapabilityRegistryError("output_schema root must be a closed object schema")
    allowed = {"type", "enum", "const", "nullable"}
    if kind == "array":
        allowed.add("items")
    if not set(schema).issubset(allowed):
        raise InferenceCapabilityRegistryError(f"{field_name} has unsupported keywords")
    if kind == "array":
        items = schema.get("items")
        if not isinstance(items, Mapping):
            raise InferenceCapabilityRegistryError(f"{field_name} array needs an item schema")
        _validate_schema_node(items, field_name=f"{field_name}.items")
    if "enum" in schema:
        enum = schema["enum"]
        if not isinstance(enum, (list, tuple)) or not enum or len(enum) != len(set(enum)):
            raise InferenceCapabilityRegistryError(f"{field_name} enum must be a non-empty unique list")
    if "const" in schema and "enum" in schema:
        raise InferenceCapabilityRegistryError(f"{field_name} cannot combine const and enum")
    if "nullable" in schema and not isinstance(schema["nullable"], bool):
        raise InferenceCapabilityRegistryError(f"{field_name} nullable must be boolean")


def _validate_closed_object_node(schema: Mapping[str, Any], *, field_name: str) -> None:
    if set(schema) != {"type", "additionalProperties", "properties", "required"}:
        raise InferenceCapabilityRegistryError(f"{field_name} must be a closed object schema")
    if schema.get("additionalProperties") is not False:
        raise InferenceCapabilityRegistryError(f"{field_name} must forbid additional properties")
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, Mapping) or not properties:
        raise InferenceCapabilityRegistryError(f"{field_name} properties must be a non-empty object")
    if not isinstance(required, (list, tuple)) or not required:
        raise InferenceCapabilityRegistryError(f"{field_name} required must be a non-empty list")
    property_names = {str(name) for name in properties}
    if len(property_names) != len(properties) or any(not _SLUG.fullmatch(name) for name in property_names):
        raise InferenceCapabilityRegistryError(f"{field_name} properties must be stable slugs")
    required_names = [str(name) for name in required]
    if len(required_names) != len(set(required_names)) or not set(required_names).issubset(property_names):
        raise InferenceCapabilityRegistryError(f"{field_name} required names must name known properties")
    for name, definition in properties.items():
        _validate_schema_node(definition, field_name=f"{field_name}.properties.{name}")


def _slug(value: str, *, field_name: str) -> str:
    clean = str(value or "").strip()
    if not _SLUG.fullmatch(clean):
        raise InferenceCapabilityRegistryError(f"{field_name} must be a stable lowercase ASCII slug")
    return clean


def _label(value: str, *, field_name: str, maximum: int = 160) -> str:
    clean = str(value or "").strip()
    if not clean or len(clean) > maximum or any(ord(char) < 32 for char in clean):
        raise InferenceCapabilityRegistryError(f"{field_name} must be a bounded public label")
    return clean


def _positive_int(value: int, *, field_name: str, maximum: int = 2**31 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximum:
        raise InferenceCapabilityRegistryError(f"{field_name} must be a positive bounded integer")
    return value


def _ordered_slugs(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted(_slug(value, field_name=field_name) for value in values))
    if len(normalized) != len(set(normalized)):
        raise InferenceCapabilityRegistryError(f"{field_name} contains duplicates")
    return normalized


def _ordered_values(
    values: Iterable[str], *, field_name: str, allowed: frozenset[str], allow_empty: bool = False
) -> tuple[str, ...]:
    normalized = tuple(sorted(str(value or "").strip() for value in values))
    if (not allow_empty and not normalized) or any(value not in allowed for value in normalized):
        raise InferenceCapabilityRegistryError(f"{field_name} contains an unsupported value")
    if len(normalized) != len(set(normalized)):
        raise InferenceCapabilityRegistryError(f"{field_name} contains duplicates")
    return normalized


def _optional_budget(value: int | None, *, field_name: str) -> int | None:
    if value is None:
        return None
    return _positive_int(value, field_name=field_name)


def _confusable_key(value: str) -> str:
    """Reject punctuation/case lookalikes before they become two routes."""
    return re.sub(r"[._-]", "", value).casefold()


@dataclass(frozen=True)
class CapabilityRequirements:
    """Closed, durable compatibility facts—not volatile model readiness."""

    structured_output: bool = False
    structured_tools: bool = False
    vision: bool = False
    audio: bool = False
    minimum_context_tokens: int = 1
    capability_classes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("structured_output", "structured_tools", "vision", "audio"):
            if not isinstance(getattr(self, field_name), bool):
                raise InferenceCapabilityRegistryError(f"requires.{field_name} must be boolean")
        object.__setattr__(
            self,
            "minimum_context_tokens",
            _positive_int(self.minimum_context_tokens, field_name="requires.minimum_context_tokens", maximum=4_000_000),
        )
        object.__setattr__(
            self,
            "capability_classes",
            _ordered_slugs(self.capability_classes, field_name="requires.capability_classes"),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "structured_output": self.structured_output,
            "structured_tools": self.structured_tools,
            "vision": self.vision,
            "audio": self.audio,
            "minimum_context_tokens": self.minimum_context_tokens,
            "capability_classes": list(self.capability_classes),
        }


@dataclass(frozen=True)
class OperationContract:
    """The sealed operation/result contract a capability names."""

    name: str
    version: int
    definition_origin: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _slug(self.name, field_name="operation_contract.name"))
        object.__setattr__(self, "version", _positive_int(self.version, field_name="operation_contract.version"))
        origin = str(self.definition_origin or "").strip()
        if origin not in _DEFINITION_ORIGINS:
            raise InferenceCapabilityRegistryError("operation_contract.definition_origin is unsupported")
        object.__setattr__(self, "definition_origin", origin)

    def canonical_dict(self) -> dict[str, Any]:
        return {"name": self.name, "version": self.version, "definition_origin": self.definition_origin}


@dataclass(frozen=True)
class InferenceRetryPolicyDefinition:
    """Immutable retry/fallback law for a bounded set of capabilities."""

    id: str
    revision: int
    permitted_capability_ids: tuple[str, ...]
    per_entry_attempts: int
    total_physical_attempts: int
    deadline_ms: int
    retryable_dispositions: tuple[str, ...]
    fallback_dispositions: tuple[str, ...]
    token_budget: int | None = None
    cost_budget: int | None = None
    tool_call_budget: int | None = None
    sha256: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _slug(self.id, field_name="retry policy id"))
        object.__setattr__(self, "revision", _positive_int(self.revision, field_name="retry policy revision"))
        object.__setattr__(
            self, "permitted_capability_ids", _ordered_slugs(
                self.permitted_capability_ids, field_name="retry policy permitted_capability_ids"
            )
        )
        per_entry = _positive_int(self.per_entry_attempts, field_name="retry policy per_entry_attempts", maximum=32)
        total = _positive_int(self.total_physical_attempts, field_name="retry policy total_physical_attempts", maximum=128)
        if total < per_entry:
            raise InferenceCapabilityRegistryError("retry policy total_physical_attempts is below per_entry_attempts")
        object.__setattr__(self, "per_entry_attempts", per_entry)
        object.__setattr__(self, "total_physical_attempts", total)
        object.__setattr__(self, "deadline_ms", _positive_int(self.deadline_ms, field_name="retry policy deadline_ms", maximum=86_400_000))
        object.__setattr__(
            self, "retryable_dispositions", _ordered_values(
                self.retryable_dispositions, field_name="retry policy retryable_dispositions", allowed=_DISPOSITIONS, allow_empty=True
            )
        )
        object.__setattr__(
            self, "fallback_dispositions", _ordered_values(
                self.fallback_dispositions, field_name="retry policy fallback_dispositions", allowed=_DISPOSITIONS, allow_empty=True
            )
        )
        object.__setattr__(self, "token_budget", _optional_budget(self.token_budget, field_name="retry policy token_budget"))
        object.__setattr__(self, "cost_budget", _optional_budget(self.cost_budget, field_name="retry policy cost_budget"))
        object.__setattr__(self, "tool_call_budget", _optional_budget(self.tool_call_budget, field_name="retry policy tool_call_budget"))
        expected = _sha256(self._canonical_material())
        supplied = str(self.sha256 or "").strip()
        if supplied and supplied != expected:
            raise SchemaDriftInferenceCapability(f"retry policy {self.id!r} sha256 drifted")
        object.__setattr__(self, "sha256", expected)

    def _canonical_material(self) -> dict[str, Any]:
        return {
            "schema": RETRY_POLICY_SCHEMA,
            "id": self.id,
            "revision": self.revision,
            "permitted_capability_ids": list(self.permitted_capability_ids),
            "per_entry_attempts": self.per_entry_attempts,
            "total_physical_attempts": self.total_physical_attempts,
            "deadline_ms": self.deadline_ms,
            "token_budget": self.token_budget,
            "cost_budget": self.cost_budget,
            "tool_call_budget": self.tool_call_budget,
            "retryable_dispositions": list(self.retryable_dispositions),
            "fallback_dispositions": list(self.fallback_dispositions),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._canonical_material(), "sha256": self.sha256}


@dataclass(frozen=True)
class InferenceCapabilityDefinition:
    """One durable, exact capability definition revision."""

    id: str
    revision: int
    label: str
    group_id: str
    group_label: str
    description: str
    operation_contract: OperationContract
    input_modalities: tuple[str, ...]
    output_kind: str
    output_schema: Mapping[str, Any]
    output_schema_sha256: str
    context_support: str
    requires: CapabilityRequirements
    allowed_boundaries: tuple[str, ...]
    permitted_retry_policy_ids: tuple[str, ...]
    default_retry_policy_id: str
    fallback_dispositions: tuple[str, ...]
    owner_visibility: str
    source_module: str
    plugin_id: str | None = None
    plugin_definition_revision: str | None = None
    schema_sha256: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _slug(self.id, field_name="capability id"))
        object.__setattr__(self, "revision", _positive_int(self.revision, field_name="capability revision"))
        object.__setattr__(self, "label", _label(self.label, field_name="capability label"))
        object.__setattr__(self, "group_id", _slug(self.group_id, field_name="capability group_id"))
        object.__setattr__(self, "group_label", _label(self.group_label, field_name="capability group_label"))
        object.__setattr__(self, "description", _label(self.description, field_name="capability description", maximum=400))
        if not isinstance(self.operation_contract, OperationContract):
            raise InferenceCapabilityRegistryError("operation_contract must be an OperationContract")
        if not isinstance(self.requires, CapabilityRequirements):
            raise InferenceCapabilityRegistryError("requires must be CapabilityRequirements")
        object.__setattr__(self, "input_modalities", _ordered_slugs(self.input_modalities, field_name="input_modalities"))
        if not self.input_modalities:
            raise InferenceCapabilityRegistryError("input_modalities cannot be empty")
        object.__setattr__(self, "output_kind", _slug(self.output_kind, field_name="output_kind"))
        _validate_closed_result_schema(self.output_schema)
        frozen_output_schema = _freeze_json(self.output_schema, field_name="output_schema")
        object.__setattr__(self, "output_schema", frozen_output_schema)
        expected_output_hash = _sha256(_json_plain(frozen_output_schema))
        output_hash = str(self.output_schema_sha256 or "").strip()
        if output_hash and output_hash != expected_output_hash:
            raise SchemaDriftInferenceCapability(f"capability {self.id!r} output schema drifted")
        object.__setattr__(self, "output_schema_sha256", expected_output_hash)
        context = str(self.context_support or "").strip()
        if context not in _CONTEXT_SUPPORT:
            raise InferenceCapabilityRegistryError("context_support is unsupported")
        object.__setattr__(self, "context_support", context)
        boundaries = _ordered_values(self.allowed_boundaries, field_name="allowed_boundaries", allowed=_BOUNDARIES)
        object.__setattr__(self, "allowed_boundaries", boundaries)
        policies = _ordered_slugs(self.permitted_retry_policy_ids, field_name="permitted_retry_policy_ids")
        if not policies:
            raise InferenceCapabilityRegistryError("permitted_retry_policy_ids cannot be empty")
        object.__setattr__(self, "permitted_retry_policy_ids", policies)
        default_policy = _slug(self.default_retry_policy_id, field_name="default_retry_policy_id")
        if default_policy not in policies:
            raise RetryPolicyReferenceError("default_retry_policy_id must be permitted by its capability")
        object.__setattr__(self, "default_retry_policy_id", default_policy)
        object.__setattr__(
            self, "fallback_dispositions", _ordered_values(
                self.fallback_dispositions, field_name="fallback_dispositions", allowed=_DISPOSITIONS, allow_empty=True
            )
        )
        visibility = str(self.owner_visibility or "").strip()
        if visibility not in _VISIBILITY:
            raise InferenceCapabilityRegistryError("owner_visibility is unsupported")
        object.__setattr__(self, "owner_visibility", visibility)
        module = str(self.source_module or "").strip()
        if not module or "/" in module or "\\" in module or not re.fullmatch(r"[a-zA-Z0-9_.]+", module):
            raise InferenceCapabilityRegistryError("source_module must be a module identifier")
        object.__setattr__(self, "source_module", module)
        plugin_id = None if self.plugin_id is None else _slug(self.plugin_id, field_name="plugin_id")
        plugin_revision = None if self.plugin_definition_revision is None else str(self.plugin_definition_revision).strip()
        if plugin_id is None and plugin_revision is not None:
            raise PluginCapabilityError("plugin_definition_revision requires plugin_id")
        if plugin_id is not None:
            if self.operation_contract.definition_origin != "plugin_definition":
                raise PluginCapabilityError("plugin capabilities require plugin_definition origin")
            if not plugin_revision or not _PLUGIN_REVISION.fullmatch(plugin_revision):
                raise PluginCapabilityError("plugin_definition_revision must be a bounded exact revision")
            if self.id != f"meeting.plugin.{plugin_id}":
                raise PluginCapabilityError("plugin capability id must be exactly meeting.plugin.<plugin_id>")
        elif self.operation_contract.definition_origin == "plugin_definition":
            raise PluginCapabilityError("plugin_definition origin requires plugin_id and plugin_definition_revision")
        object.__setattr__(self, "plugin_id", plugin_id)
        object.__setattr__(self, "plugin_definition_revision", plugin_revision)
        expected = _sha256(self._canonical_material())
        supplied = str(self.schema_sha256 or "").strip()
        if supplied and supplied != expected:
            raise SchemaDriftInferenceCapability(f"capability {self.id!r} schema_sha256 drifted")
        object.__setattr__(self, "schema_sha256", expected)

    def _canonical_material(self) -> dict[str, Any]:
        return {
            "schema": CAPABILITY_SCHEMA,
            "id": self.id,
            "revision": self.revision,
            "label": self.label,
            "group_id": self.group_id,
            "group_label": self.group_label,
            "description": self.description,
            "operation_contract": self.operation_contract.canonical_dict(),
            "input_modalities": list(self.input_modalities),
            "output_kind": self.output_kind,
            "output_schema": _json_plain(self.output_schema),
            "output_schema_sha256": self.output_schema_sha256,
            "context_support": self.context_support,
            "requires": self.requires.canonical_dict(),
            "allowed_boundaries": list(self.allowed_boundaries),
            "permitted_retry_policy_ids": list(self.permitted_retry_policy_ids),
            "default_retry_policy_id": self.default_retry_policy_id,
            "fallback_dispositions": list(self.fallback_dispositions),
            "owner_visibility": self.owner_visibility,
            "source_module": self.source_module,
            "plugin_id": self.plugin_id,
            "plugin_definition_revision": self.plugin_definition_revision,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._canonical_material(), "schema_sha256": self.schema_sha256}

    def owner_projection(self, policies: Mapping[str, InferenceRetryPolicyDefinition]) -> dict[str, Any]:
        """A closed projection with compatibility facts but no execution locators."""
        policy = policies[self.default_retry_policy_id]
        return {
            "schema": "InferenceCapabilityOwnerProjection@1",
            "id": self.id,
            "revision": self.revision,
            "schema_sha256": self.schema_sha256,
            "label": self.label,
            "group": {"id": self.group_id, "label": self.group_label},
            "description": self.description,
            "operation_contract": {
                "name": self.operation_contract.name,
                "version": self.operation_contract.version,
                "definition_origin": self.operation_contract.definition_origin,
            },
            "input_modalities": list(self.input_modalities),
            "output_kind": self.output_kind,
            "output_schema_sha256": self.output_schema_sha256,
            "context_support": self.context_support,
            "requirements": self.requires.canonical_dict(),
            "allowed_boundaries": list(self.allowed_boundaries),
            "retry": {
                "permitted_policy_ids": list(self.permitted_retry_policy_ids),
                "default_policy": {
                    "id": policy.id,
                    "revision": policy.revision,
                    "sha256": policy.sha256,
                    "per_entry_attempts": policy.per_entry_attempts,
                    "total_physical_attempts": policy.total_physical_attempts,
                    "deadline_ms": policy.deadline_ms,
                    "token_budget": policy.token_budget,
                    "cost_budget": policy.cost_budget,
                    "tool_call_budget": policy.tool_call_budget,
                    "retryable_dispositions": list(policy.retryable_dispositions),
                    "fallback_dispositions": list(policy.fallback_dispositions),
                },
            },
            "fallback_dispositions": list(self.fallback_dispositions),
            "owner_visibility": self.owner_visibility,
            "plugin": (
                {"id": self.plugin_id, "definition_revision": self.plugin_definition_revision}
                if self.plugin_id is not None
                else None
            ),
        }

    def validate_result(self, value: Any) -> None:
        """Reject a staged/domain result that drifts from this frozen revision."""
        _validate_result_value(value, self.output_schema, field_name=f"result for {self.id}")


@dataclass(frozen=True)
class InferenceCapabilityRegistry:
    """Sealed lookup used by feature modules before route/profile resolution."""

    _capabilities: Mapping[str, InferenceCapabilityDefinition]
    _retry_policies: Mapping[str, InferenceRetryPolicyDefinition]
    registry_sha256: str

    @classmethod
    def compose(
        cls,
        *,
        capabilities: Iterable[InferenceCapabilityDefinition],
        retry_policies: Iterable[InferenceRetryPolicyDefinition],
    ) -> "InferenceCapabilityRegistry":
        capability_map: dict[str, InferenceCapabilityDefinition] = {}
        policy_map: dict[str, InferenceRetryPolicyDefinition] = {}
        capability_confusables: dict[str, str] = {}
        policy_confusables: dict[str, str] = {}
        for definition in capabilities:
            if not isinstance(definition, InferenceCapabilityDefinition):
                raise InferenceCapabilityRegistryError("registry received a non-capability definition")
            if definition.schema_sha256 != _sha256(definition._canonical_material()):
                raise SchemaDriftInferenceCapability(f"capability {definition.id!r} schema_sha256 drifted")
            cls._register_exact(
                capability_map, capability_confusables, definition.id, definition, kind="capability"
            )
        for definition in retry_policies:
            if not isinstance(definition, InferenceRetryPolicyDefinition):
                raise InferenceCapabilityRegistryError("registry received a non-retry-policy definition")
            if definition.sha256 != _sha256(definition._canonical_material()):
                raise SchemaDriftInferenceCapability(f"retry policy {definition.id!r} sha256 drifted")
            cls._register_exact(policy_map, policy_confusables, definition.id, definition, kind="retry policy")
        if not capability_map or not policy_map:
            raise InferenceCapabilityRegistryError("registry requires capability and retry-policy definitions")
        cls._validate_references(capability_map, policy_map)
        frozen_caps = MappingProxyType(dict(sorted(capability_map.items())))
        frozen_policies = MappingProxyType(dict(sorted(policy_map.items())))
        material = {
            "schema": "InferenceCapabilityRegistry@1",
            "capabilities": [definition.canonical_dict() for definition in frozen_caps.values()],
            "retry_policies": [definition.canonical_dict() for definition in frozen_policies.values()],
        }
        return cls(frozen_caps, frozen_policies, _sha256(material))

    @staticmethod
    def _register_exact(
        target: dict[str, Any], confusables: dict[str, str], identifier: str, definition: Any, *, kind: str) -> None:
        if identifier in target:
            raise DuplicateInferenceCapability(f"duplicate {kind} id {identifier!r}")
        skeleton = _confusable_key(identifier)
        prior = confusables.get(skeleton)
        if prior is not None:
            raise ConfusableInferenceCapability(f"confusable {kind} ids {prior!r} and {identifier!r}")
        target[identifier] = definition
        confusables[skeleton] = identifier

    @staticmethod
    def _validate_references(
        capabilities: Mapping[str, InferenceCapabilityDefinition],
        policies: Mapping[str, InferenceRetryPolicyDefinition],
    ) -> None:
        group_labels: dict[str, str] = {}
        group_ids_by_label: dict[str, str] = {}
        group_confusables: dict[str, str] = {}
        for capability in capabilities.values():
            prior_label = group_labels.get(capability.group_id)
            if prior_label is not None and prior_label != capability.group_label:
                raise InferenceCapabilityRegistryError(
                    f"group {capability.group_id!r} has conflicting labels "
                    f"{prior_label!r} and {capability.group_label!r}"
                )
            group_labels[capability.group_id] = capability.group_label
            label_key = " ".join(capability.group_label.casefold().split())
            prior_group = group_ids_by_label.get(label_key)
            if prior_group is not None and prior_group != capability.group_id:
                raise ConfusableInferenceCapability(
                    f"group labels {prior_group!r} and {capability.group_id!r} are confusable"
                )
            group_ids_by_label[label_key] = capability.group_id
            skeleton = _confusable_key(capability.group_id)
            prior_group = group_confusables.get(skeleton)
            if prior_group is not None and prior_group != capability.group_id:
                raise ConfusableInferenceCapability(
                    f"confusable capability group ids {prior_group!r} and {capability.group_id!r}"
                )
            group_confusables[skeleton] = capability.group_id
        for capability in capabilities.values():
            for policy_id in capability.permitted_retry_policy_ids:
                policy = policies.get(policy_id)
                if policy is None:
                    raise RetryPolicyReferenceError(
                        f"capability {capability.id!r} references unknown retry policy {policy_id!r}"
                    )
                if capability.id not in policy.permitted_capability_ids:
                    raise RetryPolicyReferenceError(
                        f"retry policy {policy_id!r} does not permit capability {capability.id!r}"
                    )
                if not set(capability.fallback_dispositions).issubset(policy.fallback_dispositions):
                    raise RetryPolicyReferenceError(
                        f"capability {capability.id!r} broadens retry policy {policy_id!r} fallback law"
                    )
            if capability.default_retry_policy_id not in policies:
                raise RetryPolicyReferenceError(
                    f"capability {capability.id!r} has an unknown default retry policy"
                )
        for policy in policies.values():
            for capability_id in policy.permitted_capability_ids:
                capability = capabilities.get(capability_id)
                if capability is None:
                    raise RetryPolicyReferenceError(
                        f"retry policy {policy.id!r} references unknown capability {capability_id!r}"
                    )
                if policy.id not in capability.permitted_retry_policy_ids:
                    raise RetryPolicyReferenceError(
                        f"capability {capability_id!r} does not permit retry policy {policy.id!r}"
                    )

    @property
    def capability_ids(self) -> tuple[str, ...]:
        return tuple(self._capabilities)

    @property
    def retry_policy_ids(self) -> tuple[str, ...]:
        return tuple(self._retry_policies)

    def require(self, capability_id: str) -> InferenceCapabilityDefinition:
        """Refuse before any profile resolver or runner is consulted."""
        clean = str(capability_id or "").strip()
        definition = self._capabilities.get(clean)
        if definition is None:
            raise UnknownInferenceCapability(f"unknown inference capability {clean!r}")
        return definition

    def retry_policy(self, policy_id: str) -> InferenceRetryPolicyDefinition:
        clean = str(policy_id or "").strip()
        policy = self._retry_policies.get(clean)
        if policy is None:
            raise RetryPolicyReferenceError(f"unknown retry policy {clean!r}")
        return policy

    def require_before_profile_resolution(
        self, capability_id: str, profile_resolver: Any, *args: Any, **kwargs: Any
    ) -> tuple[InferenceCapabilityDefinition, Any]:
        """A narrow adapter for adopters: lookup is intentionally first."""
        definition = self.require(capability_id)
        return definition, profile_resolver(*args, **kwargs)

    def capability_projection(self, capability_id: str) -> dict[str, Any]:
        return self.require(capability_id).owner_projection(self._retry_policies)

    def owner_projection(self, *, include_future: bool = False) -> dict[str, Any]:
        rows = [
            definition.owner_projection(self._retry_policies)
            for definition in self._capabilities.values()
            if definition.owner_visibility == "owner" or (include_future and definition.owner_visibility == "future")
        ]
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for row in rows:
            group = row["group"]
            groups.setdefault((str(group["id"]), str(group["label"])), []).append(row)
        return {
            "schema": REGISTRY_PROJECTION_SCHEMA,
            "registry_sha256": self.registry_sha256,
            "groups": [
                {
                    "id": group_id,
                    "label": label,
                    "capabilities": sorted(capabilities, key=lambda row: str(row["id"])),
                }
                for (group_id, label), capabilities in sorted(groups.items())
            ],
        }


def _validate_result_value(value: Any, schema: Mapping[str, Any], *, field_name: str) -> None:
    """Validate a JSON value against the same closed subset used for registry schemas."""
    kind = str(schema["type"])
    if value is None:
        if schema.get("nullable") is True:
            return
        raise InferenceCapabilityRegistryError(f"{field_name} cannot be null")
    expected = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": (list, tuple),
        "object": Mapping,
    }
    if kind == "number" and isinstance(value, bool):
        raise InferenceCapabilityRegistryError(f"{field_name} must be a number")
    if kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
        raise InferenceCapabilityRegistryError(f"{field_name} must be an integer")
    if kind not in {"number", "integer"} and not isinstance(value, expected[kind]):
        raise InferenceCapabilityRegistryError(f"{field_name} must be a {kind}")
    if "const" in schema and value != schema["const"]:
        raise InferenceCapabilityRegistryError(f"{field_name} does not match its frozen constant")
    if "enum" in schema and value not in schema["enum"]:
        raise InferenceCapabilityRegistryError(f"{field_name} is outside its frozen enum")
    if kind == "array":
        for index, item in enumerate(value):
            _validate_result_value(item, schema["items"], field_name=f"{field_name}[{index}]")
    elif kind == "object":
        properties = schema["properties"]
        unknown = set(value) - set(properties)
        if unknown:
            raise InferenceCapabilityRegistryError(f"{field_name} has unregistered fields: {sorted(unknown)!r}")
        missing = set(schema["required"]) - set(value)
        if missing:
            raise InferenceCapabilityRegistryError(f"{field_name} is missing required fields: {sorted(missing)!r}")
        for name, nested in properties.items():
            if name in value:
                _validate_result_value(value[name], nested, field_name=f"{field_name}.{name}")


def _result_schema(operation: str, kind: str, contract: str) -> dict[str, Any]:
    """Return the actual closed result schema named by a capability revision."""
    scalar = {"type": "string"}
    action_item = _closed_object_schema(
        properties={
            "task": scalar,
            "owner": {"type": "string", "nullable": True},
            "due": {"type": "string", "nullable": True},
        },
        required=("task", "owner", "due"),
    )
    plan_step = _closed_object_schema(
        properties={"title": scalar, "detail": scalar}, required=("title", "detail")
    )
    validated_tool_call = _closed_object_schema(
        properties={"name": scalar, "arguments_json": scalar},
        required=("name", "arguments_json"),
    )
    string_list = {"type": "array", "items": scalar}
    target_readiness = _closed_object_schema(
        properties={"state": scalar, "available": {"type": "boolean"}, "reason": scalar},
        required=("state", "available", "reason"),
    )
    target_secret = _closed_object_schema(
        properties={"required": {"type": "boolean"}, "present": {"type": "boolean"}},
        required=("required", "present"),
    )
    target_data_scope = _closed_object_schema(
        properties={"sent": string_list, "returned": string_list}, required=("sent", "returned")
    )
    inference_target = _closed_object_schema(
        properties={
            "version": {"type": "integer"}, "id": scalar, "profile_id": {"type": "string", "nullable": True},
            "name": scalar, "kind": scalar, "boundary": scalar, "owner": scalar, "transport": scalar,
            "data_scope": target_data_scope, "engine": scalar, "model": scalar, "context_limit": {"type": "integer"},
            "readiness": target_readiness, "secret": target_secret, "endpoint": scalar, "node": scalar,
        },
        required=("version", "id", "profile_id", "name", "kind", "boundary", "owner", "transport", "data_scope", "engine", "model", "context_limit", "readiness", "secret", "endpoint", "node"),
    )
    actual_placement = _closed_object_schema(
        properties={
            "target_id": scalar, "target_name": scalar, "target_kind": scalar, "boundary": scalar,
            "owner": scalar, "transport": scalar, "data_classes": string_list, "engine": scalar,
            "model": scalar, "fallback_reason": {"type": "string", "nullable": True},
        },
        required=("target_id", "target_name", "target_kind", "boundary", "owner", "transport", "data_classes", "engine", "model", "fallback_reason"),
    )
    egress = _closed_object_schema(
        properties={"scope": scalar, "host": scalar}, required=("scope",)
    )
    claim = _closed_object_schema(
        properties={"text": scalar, "score": {"type": "number"}, "label": scalar, "flagged": {"type": "boolean"}},
        required=("text", "score", "label", "flagged"),
    )
    rails_ref = _closed_object_schema(
        properties={
            "repo": scalar,
            "project": scalar,
            "kind": {"type": "string", "enum": ["phase", "story", "evidence", "roadmap"]},
            "id": scalar,
        },
        required=("repo", "project", "kind", "id"),
    )
    grounding = _closed_object_schema(
        properties={
            "meeting_ids": string_list, "artifact_ids": string_list, "expand": scalar,
            "titles": string_list, "source_refs": string_list, "selection": scalar,
            "matched_count": {"type": "integer"}, "overflow_count": {"type": "integer"},
            "refs": string_list,
            "rails": {"type": "array", "items": rails_ref},
        },
        required=("meeting_ids", "artifact_ids", "expand", "titles", "source_refs", "selection", "matched_count", "overflow_count"),
    )
    placement = _closed_object_schema(
        properties={"effective_target_id": scalar, "source": scalar},
        required=("effective_target_id", "source"),
    )
    plugin_base = {
        "summary": scalar,
        "confidence_hint": {"type": "number"},
        "active_intents": string_list,
    }
    plugin_items: dict[str, tuple[str, Mapping[str, Mapping[str, Any]]]] = {
        "requirements_extractor": ("requirements", {"text": scalar, "type": scalar}),
        "action_owner_enforcer": ("action_items", {"task": scalar, "owner": {"type": "string", "nullable": True}, "due": {"type": "string", "nullable": True}, "gap": {"type": "boolean"}}),
        "adr_drafter": ("adrs", {"title": scalar, "status": scalar, "context": scalar, "decision": scalar, "consequences": scalar}),
        "milestone_planner": ("milestones", {"name": scalar, "target": {"type": "string", "nullable": True}, "deliverables": string_list, "dependencies": string_list}),
        "dependency_mapper": ("dependencies", {"from": scalar, "to": scalar, "note": {"type": "string", "nullable": True}}),
        "scope_guard": ("findings", {"item": scalar, "verdict": scalar, "rationale": {"type": "string", "nullable": True}}),
        "customer_signal_extractor": ("signals", {"signal": scalar, "type": scalar, "quote": {"type": "string", "nullable": True}}),
        "incident_timeline": ("events", {"time": {"type": "string", "nullable": True}, "event": scalar}),
        "risk_heatmap": ("risks", {"risk": scalar, "impact": scalar, "likelihood": scalar, "mitigation": {"type": "string", "nullable": True}, "owner": {"type": "string", "nullable": True}}),
        "runbook_delta": ("changes", {"change": scalar, "type": scalar, "detail": {"type": "string", "nullable": True}}),
        "decision_announcement_drafter": ("announcements", {"title": scalar, "audience": {"type": "string", "nullable": True}, "message": scalar}),
    }
    if operation.startswith("meeting.plugin."):
        plugin_id = operation.removeprefix("meeting.plugin.")
        if plugin_id == "project_detector":
            match = _closed_object_schema(
                properties={"project_id": scalar, "project_name": scalar, "score": {"type": "number"}, "keyword_hits": string_list, "member_hits": string_list, "detection_threshold": {"type": "number"}},
                required=("project_id", "project_name", "score", "keyword_hits", "member_hits", "detection_threshold"),
            )
            return _closed_object_schema(
                properties={**plugin_base, "plugin_id": scalar, "kind": scalar, "matched_projects": {"type": "array", "items": match}, "token_count": {"type": "integer"}},
                required=("plugin_id", "kind", "summary", "matched_projects", "token_count", "active_intents", "confidence_hint"),
            )
        if plugin_id == "mermaid_architecture":
            return _closed_object_schema(
                properties={**plugin_base, "mermaid": scalar, "diagram_kind": scalar},
                required=("summary", "confidence_hint", "active_intents"),
            )
        if plugin_id == "stakeholder_update_drafter":
            update = _closed_object_schema(
                properties={"headline": {"type": "string", "nullable": True}, "highlights": string_list, "risks": string_list, "next_steps": string_list},
                required=("headline", "highlights", "risks", "next_steps"),
            )
            return _closed_object_schema(
                properties={**plugin_base, "update": update},
                required=("summary", "confidence_hint", "active_intents"),
            )
        if plugin_id == "decision_capture":
            decision = _closed_object_schema(
                properties={"decision": scalar, "rationale": {"type": "string", "nullable": True}, "source_timestamp": {"type": "number"}},
                required=("decision", "rationale"),
            )
            drop = _closed_object_schema(
                properties={"decision": scalar, "field": scalar, "rejected_value": {"type": "number"}, "reason": scalar},
                required=("decision", "field", "rejected_value", "reason"),
            )
            return _closed_object_schema(
                properties={**plugin_base, "decisions": {"type": "array", "items": decision}, "open_questions": string_list, "provenance_drops": {"type": "array", "items": drop}},
                required=("summary", "confidence_hint", "active_intents"),
            )
        named = plugin_items.get(plugin_id)
        if named is not None:
            field, item_properties = named
            item = _closed_object_schema(properties=item_properties, required=tuple(item_properties))
            return _closed_object_schema(
                properties={**plugin_base, field: {"type": "array", "items": item}},
                required=("summary", "confidence_hint", "active_intents"),
            )
        raise PluginCapabilityError(f"installed meeting plugin {plugin_id!r} has no closed result schema")
    schemas: dict[str, dict[str, Any]] = {
        "ask_answer": _closed_object_schema(
            properties={
                "output": scalar, "lens": scalar, "provider": scalar,
                "profile_id": {"type": "string", "nullable": True}, "inference_target": inference_target,
                "actual_placement": actual_placement, "egress": egress, "model": scalar,
                "context_ids": string_list, "context_titles": string_list,
                "grounding_claims": {"type": "array", "items": claim},
                "grounding": grounding, "placement": placement,
            },
            required=("output", "lens", "provider", "profile_id", "inference_target", "actual_placement", "egress", "model", "context_ids", "context_titles"),
        ),
        "question_or_synthesis": _closed_object_schema(
            properties={
                "branch": {"type": "string", "enum": ["next_question", "synthesis"]},
                "question": {"type": "string", "nullable": True},
                "synthesis": {"type": "string", "nullable": True},
            },
            required=("branch", "question", "synthesis"),
        ),
        "dictation_intent": _closed_object_schema(
            properties={"intent": scalar, "confidence": {"type": "number"}}, required=("intent", "confidence")
        ),
        "dictation_target": _closed_object_schema(
            properties={"target": scalar, "confidence": {"type": "number"}}, required=("target", "confidence")
        ),
        "meeting_analysis": _closed_object_schema(
            properties={
                "topics": {"type": "array", "items": scalar},
                "summary": scalar,
                "action_items": {"type": "array", "items": action_item},
            },
            required=("topics", "summary", "action_items"),
        ),
        "agent_plan": _closed_object_schema(
            properties={"summary": scalar, "steps": {"type": "array", "items": plan_step}},
            required=("summary", "steps"),
        ),
        "validated_tool_turn": _closed_object_schema(
            properties={
                "summary": scalar,
                "tool_calls": {"type": "array", "items": validated_tool_call},
            },
            required=("summary", "tool_calls"),
        ),
        "reference_resolution": _closed_object_schema(
            properties={"reference": scalar, "confidence": {"type": "number"}}, required=("reference", "confidence")
        ),
        "transcript": _closed_object_schema(
            properties={"text": scalar, "language": {"type": "string", "nullable": True}}, required=("text", "language")
        ),
        "lifecycle": _closed_object_schema(
            properties={"state": scalar}, required=("state",)
        ),
    }
    schema = schemas.get(kind)
    if schema is not None:
        return schema
    # Every remaining text-shaped capability receives this exact result from
    # the admitted ``CanonicalPromptAdapter`` before its domain materializer
    # persists or decorates it. Do not invent an operation/contract/value
    # wrapper here: no runtime emits one. A later stage-specific capability
    # revision may replace this with its durable projection schema.
    return _closed_object_schema(
        properties={
            "output": scalar,
            "provider": scalar,
            "model": scalar,
        },
        required=("output", "provider", "model"),
    )


def _capability(
    identifier: str,
    label: str,
    group_id: str,
    group_label: str,
    description: str,
    *,
    operation: str,
    origin: str = "admitted_service",
    input_modalities: Sequence[str] = ("text",),
    output_kind: str = "text",
    result_contract: str | None = None,
    context_support: str = "bounded",
    structured_output: bool = False,
    structured_tools: bool = False,
    vision: bool = False,
    audio: bool = False,
    minimum_context_tokens: int = 2048,
    capability_classes: Sequence[str] = (),
    boundaries: Sequence[str] = ("cloud", "local", "mesh", "private_network"),
    policy: str = "retry.text.standard",
    fallback_dispositions: Sequence[str] = ("known_no_generation_transient", "provider_permanent"),
    visibility: str = "owner",
    source_module: str,
) -> InferenceCapabilityDefinition:
    return InferenceCapabilityDefinition(
        id=identifier,
        revision=1,
        label=label,
        group_id=group_id,
        group_label=group_label,
        description=description,
        operation_contract=OperationContract(operation, 1, origin),
        input_modalities=tuple(input_modalities),
        output_kind=output_kind,
        output_schema=_result_schema(
            operation, output_kind, result_contract or f"holdspeak.{operation}.result@1"
        ),
        output_schema_sha256="",
        context_support=context_support,
        requires=CapabilityRequirements(
            structured_output=structured_output,
            structured_tools=structured_tools,
            vision=vision,
            audio=audio,
            minimum_context_tokens=minimum_context_tokens,
            capability_classes=tuple(capability_classes),
        ),
        allowed_boundaries=tuple(boundaries),
        permitted_retry_policy_ids=(policy,),
        default_retry_policy_id=policy,
        fallback_dispositions=tuple(fallback_dispositions),
        owner_visibility=visibility,
        source_module=source_module,
    )


def builtin_capability_definitions() -> tuple[InferenceCapabilityDefinition, ...]:
    """The complete Story-01 semantic census plus chartered near-term jobs.

    ``internal.*`` names are present only to retain truthful provenance for
    adapter/lifecycle work.  They are never projected as assignable owner rows.
    Apple definitions are marked ``future`` until those legacy bypasses adopt
    the server route/controller law.
    """
    thought = ("thoughts_notes", "Thoughts & notes")
    writing = ("writing_dictation", "Writing & dictation")
    speech = ("speech_recognition", "Speech recognition")
    meetings = ("meetings", "Meetings")
    agents = ("agents_tools", "Agents & tools")
    background = ("background", "Background")
    internal = ("internal", "Internal")
    future = ("future", "Future integrations")
    text_fallback = ("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "context_overflow", "local_capacity_unavailable")
    structured_fallback = ("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "context_overflow", "local_capacity_unavailable")
    return (
        _capability("thought.interview", "Thought development", *thought, "Develop a Thought through its question-or-synthesis result contract.", operation="thought.interview", output_kind="question_or_synthesis", result_contract="holdspeak.refinement.question_or_synthesis@1", structured_output=True, minimum_context_tokens=8192, fallback_dispositions=structured_fallback, source_module="holdspeak.services.refinement_coordinator"),
        _capability("ask.answer", "Ask answer", *thought, "Answer a direct desk question with its admitted context.", operation="ask.answer", output_kind="ask_answer", minimum_context_tokens=4096, fallback_dispositions=text_fallback, source_module="holdspeak.services.ask_service"),
        _capability("speech.intent_classify", "Dictation intent", *writing, "Classify a dictated utterance before the writing pipeline continues.", operation="speech.intent.classify", input_modalities=("text",), output_kind="dictation_intent", structured_output=True, minimum_context_tokens=1024, policy="retry.structured.standard", fallback_dispositions=("known_no_generation_transient", "provider_permanent", "invalid_typed_output"), source_module="holdspeak.speech_session"),
        _capability("speech.rewrite", "Dictation rewrite", *writing, "Rewrite dictated words under the selected writing policy.", operation="speech.rewrite", output_kind="rewritten_text", minimum_context_tokens=2048, fallback_dispositions=text_fallback, source_module="holdspeak.speech_session"),
        _capability("speech.punctuate", "Dictation punctuation", *writing, "Restore punctuation for a dictated text result.", operation="speech.punctuate", output_kind="punctuated_text", minimum_context_tokens=1024, fallback_dispositions=text_fallback, source_module="holdspeak.speech_session"),
        _capability("speech.target_classify", "Dictation target", *writing, "Classify a bounded target profile for the active writing request.", operation="speech.target.classify", output_kind="dictation_target", structured_output=True, minimum_context_tokens=1024, policy="retry.structured.standard", fallback_dispositions=("known_no_generation_transient", "provider_permanent", "invalid_typed_output"), source_module="holdspeak.target_profile"),
        _capability("speech.transcribe", "Speech transcription", *speech, "Transcribe admitted audio into text.", operation="speech.transcribe", input_modalities=("audio",), output_kind="transcript", audio=True, minimum_context_tokens=1, policy="retry.audio.transcription", boundaries=("local", "mesh", "private_network"), fallback_dispositions=("known_no_generation_transient", "provider_permanent", "local_capacity_unavailable"), source_module="holdspeak.speech_session.transcription"),
        _capability("speech.preload", "Speech preload", *internal, "Warm a fixed speech artifact before an admitted transcription child.", operation="speech.preload", input_modalities=("audio",), output_kind="lifecycle", audio=True, minimum_context_tokens=1, policy="retry.internal.lifecycle", boundaries=("local", "mesh", "private_network"), fallback_dispositions=("known_no_generation_transient",), visibility="internal", source_module="holdspeak.speech_session.transcription"),
        _capability("meeting.live_analysis", "Live meeting analysis", *meetings, "Analyze one admitted live meeting window.", operation="meeting.live.analysis", output_kind="meeting_analysis", structured_output=True, minimum_context_tokens=8192, policy="retry.structured.standard", fallback_dispositions=structured_fallback, source_module="holdspeak.meeting_session"),
        _capability("meeting.bookmark_label", "Meeting bookmark label", *meetings, "Label one meeting bookmark from its admitted context.", operation="meeting.bookmark.label", output_kind="bookmark_label", minimum_context_tokens=2048, fallback_dispositions=text_fallback, source_module="holdspeak.meeting_session"),
        _capability("meeting.auto_title", "Meeting title", *meetings, "Generate a bounded meeting title.", operation="meeting.auto.title", output_kind="meeting_title", minimum_context_tokens=2048, fallback_dispositions=text_fallback, source_module="holdspeak.meeting_session"),
        _capability("meeting.deferred_analysis", "Deferred meeting analysis", *meetings, "Analyze a queued meeting window under its admitted job.", operation="meeting.deferred.analysis", output_kind="meeting_analysis", structured_output=True, minimum_context_tokens=8192, policy="retry.structured.standard", fallback_dispositions=structured_fallback, source_module="holdspeak.meeting_session.deferred_admission"),
        _capability("agent.plan", "Agent plan", *agents, "Plan a bounded agent task without authorizing effects.", operation="agent.plan", output_kind="agent_plan", structured_output=True, minimum_context_tokens=8192, policy="retry.structured.standard", fallback_dispositions=structured_fallback, source_module="holdspeak.plugins.intelligence"),
        _capability("agent.tool_turn", "Agent tool turn", *agents, "Produce one validated tool-turn proposal under a private lease.", operation="agent.tool.turn", output_kind="validated_tool_turn", structured_output=True, structured_tools=True, minimum_context_tokens=8192, capability_classes=("tool_turn",), policy="retry.tool.turn", fallback_dispositions=("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "invalid_tool_call", "context_overflow", "local_capacity_unavailable", "tool_unavailable_or_stale"), source_module="holdspeak.plugins.intelligence"),
        _capability("agent.code", "Agent code", *agents, "Produce a bounded code-oriented agent result without effect authority.", operation="agent.code", output_kind="code_proposal", minimum_context_tokens=8192, fallback_dispositions=text_fallback, source_module="holdspeak.plugins.intelligence"),
        _capability("workbench.item", "Workbench item", *agents, "Run one admitted Workbench item.", operation="workbench.item", output_kind="workbench_item_output", minimum_context_tokens=8192, fallback_dispositions=text_fallback, source_module="holdspeak.services.workbench_runner"),
        _capability("recipe.run", "Recipe run", *agents, "Run one saved recipe with rendered input.", operation="recipe.run", origin="saved_definition", output_kind="recipe_output", minimum_context_tokens=4096, fallback_dispositions=text_fallback, source_module="holdspeak.services.recipe_service"),
        _capability("recipe.chat", "Recipe chat", *agents, "Continue one recipe conversation with admitted grounding.", operation="recipe.chat", origin="saved_definition", output_kind="recipe_chat_answer", minimum_context_tokens=8192, fallback_dispositions=text_fallback, source_module="holdspeak.services.recipe_service"),
        _capability("voice.reference_resolve", "Voice reference resolution", *agents, "Resolve a spoken reference against bounded Workbench context.", operation="voice.reference.resolve", output_kind="reference_resolution", minimum_context_tokens=2048, fallback_dispositions=text_fallback, source_module="holdspeak.services.workbench_service"),
        _capability("sequence.step", "Sequence step", *agents, "Run one typed Sequence step using its saved recipe definition.", operation="sequence.step", origin="saved_definition", output_kind="sequence_step_output", minimum_context_tokens=4096, fallback_dispositions=text_fallback, source_module="holdspeak.services.sequence_workflow_service"),
        _capability("workflow.node", "Workflow node", *agents, "Run one typed Workflow model node.", operation="workflow.node", output_kind="workflow_node_output", minimum_context_tokens=4096, fallback_dispositions=text_fallback, source_module="holdspeak.services.sequence_workflow_service"),
        _capability("project_doc.suggest_update", "Project document suggestion", *agents, "Suggest a bounded project-document update.", operation="project.doc.suggest.update", output_kind="project_document_update", minimum_context_tokens=4096, fallback_dispositions=text_fallback, source_module="holdspeak.project_doc_suggestions"),
        _capability("background.rails_summary", "Rails summary", *background, "Summarize an admitted software-delivery event batch.", operation="background.rails.summary", output_kind="rails_summary", minimum_context_tokens=4096, policy="retry.background.standard", fallback_dispositions=text_fallback, source_module="holdspeak.rails_observer"),
        _capability("background.cadence_draft", "Cadence draft", *background, "Draft one bounded cadence action.", operation="background.cadence.draft", output_kind="cadence_draft", minimum_context_tokens=4096, policy="retry.background.standard", fallback_dispositions=text_fallback, source_module="holdspeak.services.cadence_service"),
        _capability("decision.promotion_draft", "Decision promotion draft", *background, "Draft a decision-record promotion.", operation="decision.promotion.draft", output_kind="decision_promotion_draft", minimum_context_tokens=4096, policy="retry.background.standard", fallback_dispositions=text_fallback, source_module="holdspeak.services.decision_lifecycle_service"),
        _capability("delivery.pr_review_draft", "Pull request review draft", *background, "Draft an admitted pull-request review.", operation="delivery.pr.review.draft", output_kind="pull_request_review_draft", minimum_context_tokens=8192, policy="retry.background.standard", fallback_dispositions=text_fallback, source_module="holdspeak.web.routes.delivery_prs"),
        _capability("internal.inference.dispatch", "Inference dispatch", *internal, "Context-gated provider adapter work supplied by a typed parent capability.", operation="internal.inference.dispatch", minimum_context_tokens=1, policy="retry.internal.lifecycle", fallback_dispositions=("known_no_generation_transient",), visibility="internal", source_module="holdspeak.kernel.inference_runner"),
        _capability("internal.speech.runtime_assembly", "Speech runtime assembly", *internal, "Context-gated speech runtime assembly supplied by a typed parent capability.", operation="internal.speech.runtime.assembly", minimum_context_tokens=1, policy="retry.internal.lifecycle", fallback_dispositions=("known_no_generation_transient",), visibility="internal", source_module="holdspeak.speech_session"),
        _capability("internal.semantic_dispatch", "Semantic dispatch", *internal, "Shared Ask, Recipe, and workflow helper dispatch supplied by its semantic caller.", operation="internal.semantic.dispatch", minimum_context_tokens=1, policy="retry.internal.lifecycle", fallback_dispositions=("known_no_generation_transient",), visibility="internal", source_module="holdspeak.services"),
        _capability("apple.local_completion", "Apple local completion", *future, "Legacy Apple local completion awaiting canonical route adoption.", operation="apple.local.completion", minimum_context_tokens=2048, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.inference_llama"),
        _capability("apple.endpoint_completion", "Apple endpoint completion", *future, "Legacy Apple endpoint completion awaiting canonical route adoption.", operation="apple.endpoint.completion", minimum_context_tokens=2048, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.providers.inference"),
        _capability("apple.structured_output", "Apple structured output", *future, "Legacy Apple structured-output call awaiting canonical route adoption.", operation="apple.structured.output", structured_output=True, minimum_context_tokens=2048, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.providers.inference"),
        _capability("apple.mesh_serve", "Apple mesh serve", *future, "Legacy Apple mesh completion awaiting canonical route adoption.", operation="apple.mesh.serve", minimum_context_tokens=2048, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.providers.desktop"),
        _capability("apple.coder_answer", "Apple coder answer", *future, "Legacy Apple coder completion awaiting canonical route adoption.", operation="apple.coder.answer", minimum_context_tokens=8192, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.runtimecore.companion"),
        _capability("apple.workbench.blueprint", "Apple Workbench blueprint", *future, "Legacy Apple Workbench blueprint awaiting controller alignment.", operation="apple.workbench.blueprint", minimum_context_tokens=4096, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.runtimecore.workbench"),
        _capability("apple.workbench.workflow", "Apple Workbench workflow", *future, "Legacy Apple Workbench workflow awaiting controller alignment.", operation="apple.workbench.workflow", minimum_context_tokens=4096, policy="retry.future.legacy", fallback_dispositions=("known_no_generation_transient",), visibility="future", source_module="apple.runtimecore.workbench"),
    )


def installed_meeting_plugin_capability_definitions() -> tuple[InferenceCapabilityDefinition, ...]:
    """Bind every plugin the actual meeting host registers to one exact revision.

    ``MeetingIntelPlan`` presently derives `meeting.plugin.<id>` from the
    built-in host plus its project detector.  This function mirrors that host's
    installed membership without building a host, reading a database, or
    executing plugin code.  User/pack plugins are not in that runtime host yet;
    they must enter through :func:`compose_inference_capability_registry` with
    their validated manifest revision instead of a runtime-string wildcard.
    """
    from .plugins.builtin import DeterministicPlugin, _BUILTIN_PLUGIN_DEFS, _REAL_PLUGINS
    from .plugins.project_detector import ProjectDetectorPlugin

    plugins: list[tuple[str, str, str]] = []
    for plugin_id, kind in _BUILTIN_PLUGIN_DEFS:
        plugin_type = _REAL_PLUGINS.get(plugin_id)
        plugin = plugin_type() if plugin_type is not None else DeterministicPlugin(plugin_id, kind)
        revision = str(getattr(plugin, "version", "") or "").strip()
        if not revision:
            raise PluginCapabilityError(f"installed meeting plugin {plugin_id!r} has no bounded revision")
        plugins.append((str(plugin_id), revision, "holdspeak.plugins.builtin"))
    detector = ProjectDetectorPlugin()
    plugins.append((str(detector.id), str(detector.version), "holdspeak.plugins.project_detector"))
    definitions: list[InferenceCapabilityDefinition] = []
    for plugin_id, revision, source_module in sorted(plugins):
        operation = f"meeting.plugin.{plugin_id}"
        output_kind = "meeting_plugin_output"
        schema = _result_schema(operation, output_kind, f"holdspeak.{operation}.result@1")
        definitions.append(
            InferenceCapabilityDefinition(
                id=operation,
                revision=1,
                label=f"Meeting plugin: {plugin_id.replace('_', ' ')}",
                group_id="meetings",
                group_label="Meetings",
                description="Run one installed meeting plugin under its exact registered revision.",
                operation_contract=OperationContract(operation, 1, "plugin_definition"),
                input_modalities=("text",),
                output_kind=output_kind,
                output_schema=schema,
                output_schema_sha256="",
                context_support="bounded",
                requires=CapabilityRequirements(
                    structured_output=True,
                    minimum_context_tokens=4096,
                    capability_classes=("meeting_plugin",),
                ),
                allowed_boundaries=("cloud", "local", "mesh", "private_network"),
                permitted_retry_policy_ids=("retry.structured.standard",),
                default_retry_policy_id="retry.structured.standard",
                fallback_dispositions=(
                    "known_no_generation_transient",
                    "provider_permanent",
                    "invalid_typed_output",
                    "context_overflow",
                    "local_capacity_unavailable",
                ),
                owner_visibility="owner",
                source_module=source_module,
                plugin_id=plugin_id,
                plugin_definition_revision=revision,
            )
        )
    return tuple(definitions)


def builtin_retry_policy_definitions(
    capabilities: Iterable[InferenceCapabilityDefinition] | None = None,
) -> tuple[InferenceRetryPolicyDefinition, ...]:
    definitions = tuple(capabilities or builtin_capability_definitions())
    by_policy: dict[str, list[str]] = {}
    for definition in definitions:
        for policy_id in definition.permitted_retry_policy_ids:
            by_policy.setdefault(policy_id, []).append(definition.id)
    rows = {
        "retry.text.standard": dict(per_entry_attempts=2, total_physical_attempts=4, deadline_ms=60_000, token_budget=32_768, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient", "invalid_typed_output"), fallback=("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "context_overflow", "local_capacity_unavailable")),
        "retry.structured.standard": dict(per_entry_attempts=2, total_physical_attempts=4, deadline_ms=75_000, token_budget=32_768, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient", "invalid_typed_output"), fallback=("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "context_overflow", "local_capacity_unavailable")),
        "retry.audio.transcription": dict(per_entry_attempts=1, total_physical_attempts=2, deadline_ms=120_000, token_budget=None, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient",), fallback=("known_no_generation_transient", "provider_permanent", "local_capacity_unavailable")),
        "retry.tool.turn": dict(per_entry_attempts=2, total_physical_attempts=4, deadline_ms=75_000, token_budget=32_768, cost_budget=None, tool_call_budget=8, retryable=("known_no_generation_transient", "invalid_typed_output", "invalid_tool_call"), fallback=("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "invalid_tool_call", "context_overflow", "local_capacity_unavailable", "tool_unavailable_or_stale")),
        "retry.background.standard": dict(per_entry_attempts=2, total_physical_attempts=3, deadline_ms=60_000, token_budget=16_384, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient", "invalid_typed_output"), fallback=("known_no_generation_transient", "provider_permanent", "invalid_typed_output", "context_overflow", "local_capacity_unavailable")),
        "retry.internal.lifecycle": dict(per_entry_attempts=1, total_physical_attempts=1, deadline_ms=30_000, token_budget=None, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient",), fallback=("known_no_generation_transient",)),
        "retry.future.legacy": dict(per_entry_attempts=1, total_physical_attempts=1, deadline_ms=60_000, token_budget=None, cost_budget=None, tool_call_budget=None, retryable=("known_no_generation_transient",), fallback=("known_no_generation_transient",)),
    }
    return tuple(
        InferenceRetryPolicyDefinition(
            id=identifier,
            revision=1,
            permitted_capability_ids=tuple(sorted(by_policy.get(identifier, ()))),
            per_entry_attempts=values["per_entry_attempts"],
            total_physical_attempts=values["total_physical_attempts"],
            deadline_ms=values["deadline_ms"],
            token_budget=values["token_budget"],
            cost_budget=values["cost_budget"],
            tool_call_budget=values["tool_call_budget"],
            retryable_dispositions=values["retryable"],
            fallback_dispositions=values["fallback"],
        )
        for identifier, values in sorted(rows.items())
    )


def compose_inference_capability_registry(
    *, plugin_capabilities: Iterable[InferenceCapabilityDefinition] = (),
) -> InferenceCapabilityRegistry:
    """Compose the sealed process registry, including bounded plugin revisions."""
    builtin = builtin_capability_definitions()
    installed_plugins = installed_meeting_plugin_capability_definitions()
    plugins = tuple(plugin_capabilities)
    for definition in plugins:
        if not isinstance(definition, InferenceCapabilityDefinition) or definition.plugin_id is None:
            raise PluginCapabilityError("plugin registration requires a bounded plugin capability definition")
    definitions = builtin + installed_plugins + plugins
    policies = builtin_retry_policy_definitions(definitions)
    return InferenceCapabilityRegistry.compose(capabilities=definitions, retry_policies=policies)


_process_registry: InferenceCapabilityRegistry | None = None


def process_inference_capability_registry() -> InferenceCapabilityRegistry:
    """Return the one eagerly composed immutable registry for this process."""
    global _process_registry
    if _process_registry is None:
        _process_registry = compose_inference_capability_registry()
    return _process_registry


__all__ = [
    "CAPABILITY_SCHEMA",
    "RETRY_POLICY_SCHEMA",
    "CapabilityRequirements",
    "ConfusableInferenceCapability",
    "DuplicateInferenceCapability",
    "InferenceCapabilityDefinition",
    "InferenceCapabilityRegistry",
    "InferenceCapabilityRegistryError",
    "InferenceRetryPolicyDefinition",
    "OperationContract",
    "PluginCapabilityError",
    "RetryPolicyReferenceError",
    "SchemaDriftInferenceCapability",
    "UnknownInferenceCapability",
    "builtin_capability_definitions",
    "builtin_retry_policy_definitions",
    "compose_inference_capability_registry",
    "installed_meeting_plugin_capability_definitions",
    "process_inference_capability_registry",
]
