"""Private MODEL_TURN capability projection and tool-qualification authority.

This module deliberately does not import the MCP catalogue.  Composition supplies
canonical application-operation descriptors, then this adapter produces the much
narrower provider-facing dialect used by a frozen turn lease.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SAFE_TEXT = re.compile(r"^[^\x00-\x1f]{1,240}$")
_TOOL_CLASSES = frozenset({"evidence_read", "candidate_builder", "effect_proposal"})
_EFFECT_MODES = frozenset({"read", "candidate", "proposal", "execute_if_policy_admits"})
_TOOL_DIALECTS = frozenset({"none", "gemma4", "qwen", "openai", "granite", "other-closed"})
_TOOL_QUALIFICATIONS = frozenset({"unavailable", "candidate", "qualified"})
_PALETTES = frozenset({0, 1, 4, 8, 12})


class ToolCapabilityError(ValueError):
    """A closed tool-capability or manifest contract was violated."""

    code = "tool_capability_invalid"


def _plain_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(_plain_json(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ToolCapabilityError("tool capability material is not canonical JSON") from exc


def sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_id(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _ID.fullmatch(clean):
        raise ToolCapabilityError(f"{field} must be a stable capability identifier")
    return clean


def _require_hash(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _SHA256.fullmatch(clean):
        raise ToolCapabilityError(f"{field} must be a sha256 digest")
    return clean


def _require_text(value: Any, *, field: str, maximum: int = 240) -> str:
    clean = str(value or "").strip()
    if len(clean) > maximum or not _SAFE_TEXT.fullmatch(clean):
        raise ToolCapabilityError(f"{field} must be bounded safe text")
    return clean


def _require_positive(value: Any, *, field: str, maximum: int = 2**31 - 1, allow_zero: bool = False) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1) or value > maximum:
        raise ToolCapabilityError(f"{field} must be a bounded integer")
    return value


def _json_plain(value: Any) -> Any:
    """Round-trip JSON data and reject Python objects before it reaches a lease."""
    try:
        return json.loads(canonical_json(value))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:  # pragma: no cover - canonical_json owns normal path
        raise ToolCapabilityError("tool capability value must be JSON") from exc


def validate_closed_schema(schema: Any, *, root: bool = True, field: str = "schema") -> dict[str, Any]:
    """Validate the small recursively closed JSON-schema dialect models may see."""
    if not isinstance(schema, Mapping):
        raise ToolCapabilityError(f"{field} must be an object")
    keys = set(schema)
    if keys == {"oneOf"}:
        branches = schema["oneOf"]
        if not isinstance(branches, list) or len(branches) < 2:
            raise ToolCapabilityError(f"{field}.oneOf must contain at least two branches")
        return {"oneOf": [validate_closed_schema(item, root=True, field=f"{field}.oneOf") for item in branches]}
    kind = schema.get("type")
    if kind not in {"string", "number", "integer", "boolean", "array", "object"}:
        raise ToolCapabilityError(f"{field}.type is unsupported")
    if kind == "object":
        expected = {"type", "additionalProperties", "properties", "required"}
        if keys != expected or schema.get("additionalProperties") is not False:
            raise ToolCapabilityError(f"{field} must be a closed object schema")
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, Mapping) or not properties or not isinstance(required, list):
            raise ToolCapabilityError(f"{field} must have non-empty properties and required")
        property_names = list(properties)
        if any(not isinstance(name, str) or not _ID.fullmatch(name) for name in property_names):
            raise ToolCapabilityError(f"{field} property names must be stable identifiers")
        if len(property_names) != len(set(property_names)) or len(required) != len(set(required)) or set(required) - set(property_names):
            raise ToolCapabilityError(f"{field}.required is invalid")
        if not required:
            raise ToolCapabilityError(f"{field}.required cannot be empty")
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: validate_closed_schema(value, root=False, field=f"{field}.properties.{name}")
                for name, value in sorted(properties.items())
            },
            "required": sorted(required),
        }
    if root:
        raise ToolCapabilityError(f"{field} root must be a closed object")
    allowed = {"type", "enum", "const", "nullable"}
    if kind == "array":
        allowed.add("items")
    if not keys <= allowed:
        raise ToolCapabilityError(f"{field} has unsupported schema keywords")
    result: dict[str, Any] = {"type": kind}
    if "enum" in schema:
        values = schema["enum"]
        if not isinstance(values, list) or not values or len(canonical_json(values)) > 4096:
            raise ToolCapabilityError(f"{field}.enum is invalid")
        normalized = _json_plain(values)
        if len({canonical_json(item) for item in normalized}) != len(normalized):
            raise ToolCapabilityError(f"{field}.enum has duplicates")
        result["enum"] = normalized
    if "const" in schema:
        if "enum" in schema:
            raise ToolCapabilityError(f"{field} cannot combine enum and const")
        result["const"] = _json_plain(schema["const"])
    if "nullable" in schema:
        if type(schema["nullable"]) is not bool:
            raise ToolCapabilityError(f"{field}.nullable must be boolean")
        result["nullable"] = schema["nullable"]
    if kind == "array":
        if not isinstance(schema.get("items"), Mapping):
            raise ToolCapabilityError(f"{field}.items is required")
        result["items"] = validate_closed_schema(schema["items"], root=False, field=f"{field}.items")
    return result


def validate_closed_arguments(schema: Mapping[str, Any], arguments: Any, *, field: str = "arguments") -> dict[str, Any]:
    """Validate native-call data against the same recursively closed dialect.

    The schema is normalized first, so callers cannot use a syntactically
    equivalent but differently shaped schema to smuggle an open argument into a
    frozen capability.  The returned JSON value is canonical-ready and contains
    no Python objects.
    """
    closed = validate_closed_schema(schema)

    def walk(node: Mapping[str, Any], value: Any, path: str) -> Any:
        if "oneOf" in node:
            matches: list[Any] = []
            for branch in node["oneOf"]:
                try:
                    matches.append(walk(branch, value, path))
                except ToolCapabilityError:
                    pass
            if len(matches) != 1:
                raise ToolCapabilityError(f"{path} does not match one closed schema branch")
            return matches[0]
        if value is None and node.get("nullable") is True:
            return None
        kind = node["type"]
        if kind == "object":
            if (
                not isinstance(value, Mapping)
                or set(value) - set(node["properties"])
                or set(node["required"]) - set(value)
            ):
                raise ToolCapabilityError(f"{path} must satisfy the closed properties")
            return {
                name: walk(node["properties"][name], value[name], f"{path}.{name}")
                for name in sorted(value)
            }
        if kind == "array":
            if not isinstance(value, list):
                raise ToolCapabilityError(f"{path} must be an array")
            return [walk(node["items"], item, f"{path}[]") for item in value]
        type_matches = {
            "string": isinstance(value, str),
            "number": type(value) in {int, float} and not isinstance(value, bool),
            "integer": type(value) is int,
            "boolean": type(value) is bool,
        }
        if not type_matches[kind]:
            raise ToolCapabilityError(f"{path} has the wrong JSON type")
        plain = _json_plain(value)
        if "const" in node and plain != node["const"]:
            raise ToolCapabilityError(f"{path} does not match the closed constant")
        if "enum" in node and plain not in node["enum"]:
            raise ToolCapabilityError(f"{path} is outside the closed enum")
        return plain

    result = walk(closed, arguments, field)
    if not isinstance(result, dict):  # The projection contract always has an object root.
        raise ToolCapabilityError(f"{field} must be an object")
    return result


@dataclass(frozen=True)
class CanonicalApplicationOperationDescriptor:
    """Canonical operation semantics, stripped of all owner transport fields.

    This is intentionally a composition input, not a registry generated from
    ``mcp.tools.TOOLS``.  It represents the shared application operation a later
    Broker admission will call, while keeping MCP tokens, owner arguments and
    generic discovery structurally impossible in the model projection.
    """

    capability_id: str
    revision: int
    label: str
    description: str
    argument_schema: Mapping[str, Any]
    service_operation: str
    capability_class: str
    effect_mode: str
    allowed_data_classes: tuple[str, ...]
    allowed_placements: tuple[str, ...]
    allowed_egress: tuple[str, ...]
    max_calls: int
    max_result_bytes: int
    max_result_tokens: int
    commutative_read: bool = False
    descriptor_sha256: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", _require_id(self.capability_id, field="capability_id"))
        object.__setattr__(self, "revision", _require_positive(self.revision, field="revision", maximum=1_000_000))
        object.__setattr__(self, "label", _require_text(self.label, field="label", maximum=120))
        object.__setattr__(self, "description", _require_text(self.description, field="description", maximum=400))
        object.__setattr__(self, "service_operation", _require_id(self.service_operation, field="service_operation"))
        if self.capability_class not in _TOOL_CLASSES:
            raise ToolCapabilityError("capability_class is unsupported")
        if self.effect_mode not in _EFFECT_MODES:
            raise ToolCapabilityError("effect_mode is unsupported")
        if self.capability_class == "evidence_read" and self.effect_mode != "read":
            raise ToolCapabilityError("evidence reads must use read effect mode")
        if self.effect_mode == "execute_if_policy_admits" and self.capability_class != "effect_proposal":
            raise ToolCapabilityError("execute_if_policy_admits requires an effect proposal")
        object.__setattr__(self, "argument_schema", MappingProxyType(validate_closed_schema(self.argument_schema)))
        for field_name in ("allowed_data_classes", "allowed_placements", "allowed_egress"):
            values = tuple(sorted({_require_id(value, field=field_name) for value in getattr(self, field_name)}))
            if not values:
                raise ToolCapabilityError(f"{field_name} cannot be empty")
            object.__setattr__(self, field_name, values)
        object.__setattr__(self, "max_calls", _require_positive(self.max_calls, field="max_calls", maximum=6))
        object.__setattr__(self, "max_result_bytes", _require_positive(self.max_result_bytes, field="max_result_bytes", maximum=32 * 1024))
        object.__setattr__(self, "max_result_tokens", _require_positive(self.max_result_tokens, field="max_result_tokens", maximum=8 * 1024))
        if type(self.commutative_read) is not bool or self.commutative_read and self.effect_mode != "read":
            raise ToolCapabilityError("commutative_read is valid only for reads")
        expected = sha256(self._material())
        supplied = str(self.descriptor_sha256 or "").strip()
        if supplied and supplied != expected:
            raise ToolCapabilityError("canonical descriptor hash drifted")
        object.__setattr__(self, "descriptor_sha256", expected)

    @property
    def schema_sha256(self) -> str:
        return sha256(dict(self.argument_schema))

    def _material(self) -> dict[str, Any]:
        return {
            "schema": "CanonicalApplicationOperationDescriptor@1",
            "capability_id": self.capability_id,
            "revision": self.revision,
            "label": self.label,
            "description": self.description,
            "argument_schema": dict(self.argument_schema),
            "service_operation": self.service_operation,
            "capability_class": self.capability_class,
            "effect_mode": self.effect_mode,
            "allowed_data_classes": list(self.allowed_data_classes),
            "allowed_placements": list(self.allowed_placements),
            "allowed_egress": list(self.allowed_egress),
            "max_calls": self.max_calls,
            "max_result_bytes": self.max_result_bytes,
            "max_result_tokens": self.max_result_tokens,
            "commutative_read": self.commutative_read,
        }

    def provider_candidate(self) -> dict[str, Any]:
        """Return the provider-safe dialect; no lease, owner or transport facts."""
        return {
            "schema": "ModelTurnProviderTool@1",
            "name": self.capability_id,
            "description": self.description,
            "parameters": _json_plain(dict(self.argument_schema)),
        }


class ModelTurnCapabilityProjection:
    """Closed deterministic projection over composition-owned descriptors."""

    def __init__(self, descriptors: Iterable[CanonicalApplicationOperationDescriptor]) -> None:
        values = sorted(tuple(descriptors), key=lambda item: item.capability_id)
        if not values:
            raise ToolCapabilityError("MODEL_TURN projection needs at least one descriptor")
        duplicates = [item.capability_id for item in values]
        if len(duplicates) != len(set(duplicates)):
            raise ToolCapabilityError("MODEL_TURN projection has duplicate capabilities")
        confusables: set[str] = set()
        for item in values:
            key = re.sub(r"[._-]", "", item.capability_id).casefold()
            if key in confusables:
                raise ToolCapabilityError("MODEL_TURN projection has confusable capabilities")
            confusables.add(key)
        self._descriptors = MappingProxyType({item.capability_id: item for item in values})
        self.sha256 = sha256({"schema": "ModelTurnCapabilityProjection@1", "descriptors": [item._material() | {"descriptor_sha256": item.descriptor_sha256} for item in values]})

    @property
    def capability_ids(self) -> tuple[str, ...]:
        return tuple(self._descriptors)

    def require(self, capability_id: str) -> CanonicalApplicationOperationDescriptor:
        try:
            return self._descriptors[_require_id(capability_id, field="capability_id")]
        except KeyError as exc:
            raise ToolCapabilityError("capability is not eligible for MODEL_TURN") from exc

    def provider_tools(self, capability_ids: Sequence[str]) -> list[dict[str, Any]]:
        selected = tuple(sorted({_require_id(value, field="capability_id") for value in capability_ids}))
        if not selected or len(selected) > 12:
            raise ToolCapabilityError("MODEL_TURN palette is invalid")
        return [self.require(item).provider_candidate() for item in selected]


@dataclass(frozen=True)
class ToolQualification:
    """Closed evidence that an exact deployment has native-tool qualification."""

    structured_tool_use: str
    qualified_palette: int
    tool_eval_revision: str | None
    native_tool_dialect: str
    sha256: str = ""

    def __post_init__(self) -> None:
        if self.structured_tool_use not in _TOOL_QUALIFICATIONS:
            raise ToolCapabilityError("structured_tool_use is invalid")
        if type(self.qualified_palette) is not int or self.qualified_palette not in _PALETTES:
            raise ToolCapabilityError("qualified_palette is invalid")
        if self.structured_tool_use == "qualified":
            if self.qualified_palette == 0 or not self.tool_eval_revision or self.native_tool_dialect == "none":
                raise ToolCapabilityError("qualified tool evidence is incomplete")
        elif self.qualified_palette != 0 or self.tool_eval_revision is not None or self.native_tool_dialect != "none":
            raise ToolCapabilityError("unqualified tool evidence must have zero palette")
        if self.tool_eval_revision is not None:
            object.__setattr__(self, "tool_eval_revision", _require_text(self.tool_eval_revision, field="tool_eval_revision", maximum=120))
        if self.native_tool_dialect not in _TOOL_DIALECTS:
            raise ToolCapabilityError("native_tool_dialect is invalid")
        expected = sha256(self.material())
        supplied = str(self.sha256 or "").strip()
        if supplied and supplied != expected:
            raise ToolCapabilityError("tool qualification hash drifted")
        object.__setattr__(self, "sha256", expected)

    def material(self) -> dict[str, Any]:
        return {
            "structured_tool_use": self.structured_tool_use,
            "qualified_palette": self.qualified_palette,
            "tool_eval_revision": self.tool_eval_revision,
            "native_tool_dialect": self.native_tool_dialect,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.material(), "sha256": self.sha256}

    @classmethod
    def unavailable(cls) -> "ToolQualification":
        return cls("unavailable", 0, None, "none")


def parse_capability_manifest(value: Any) -> tuple[dict[str, Any], ToolQualification]:
    """Validate legacy and v2 bodies without ever upgrading legacy evidence.

    A legacy `{revision, claims, sha256}` body remains stored as-is and receives
    only an in-memory unavailable projection.  Its old digest is deliberately
    not rewritten, so a historic deployment cannot become tool-qualified merely
    by loading this code.
    """
    if not isinstance(value, Mapping):
        raise ToolCapabilityError("capability_manifest must be an object")
    keys = set(value)
    legacy = {"revision", "claims", "sha256"}
    current = legacy | {"tool_qualification"}
    if keys not in (legacy, current):
        raise ToolCapabilityError("capability_manifest has an invalid shape")
    revision = value.get("revision")
    if not isinstance(revision, (str, int)) or isinstance(revision, bool):
        raise ToolCapabilityError("capability_manifest.revision is invalid")
    claims = value.get("claims")
    if not isinstance(claims, list) or len(claims) > 128:
        raise ToolCapabilityError("capability_manifest.claims is invalid")
    normalized_claims = [_require_text(item, field="capability_manifest.claims", maximum=120) for item in claims]
    if len(normalized_claims) != len(set(normalized_claims)):
        raise ToolCapabilityError("capability_manifest.claims contains duplicates")
    if not _SHA256.fullmatch(str(value.get("sha256") or "")):
        raise ToolCapabilityError("capability_manifest.sha256 is invalid")
    material: dict[str, Any] = {"revision": revision, "claims": normalized_claims}
    qualification = ToolQualification.unavailable()
    if keys == current:
        raw_qualification = value.get("tool_qualification")
        if not isinstance(raw_qualification, Mapping) or set(raw_qualification) != {
            "structured_tool_use", "qualified_palette", "tool_eval_revision", "native_tool_dialect", "sha256"
        }:
            raise ToolCapabilityError("tool_qualification has an invalid shape")
        qualification = ToolQualification(
            structured_tool_use=raw_qualification["structured_tool_use"],
            qualified_palette=raw_qualification["qualified_palette"],
            tool_eval_revision=raw_qualification["tool_eval_revision"],
            native_tool_dialect=raw_qualification["native_tool_dialect"],
            sha256=raw_qualification["sha256"],
        )
        material["tool_qualification"] = qualification.to_dict()
    if str(value["sha256"]) != sha256(material):
        raise ToolCapabilityError("capability_manifest hash does not match its evidence")
    normalized = {**material, "sha256": str(value["sha256"])}
    return normalized, qualification


class ToolCapabilityFoundation:
    """Server-side composition registration required for tool route eligibility."""

    def __init__(self, projection: ModelTurnCapabilityProjection, controller: Any) -> None:
        if not isinstance(projection, ModelTurnCapabilityProjection):
            raise ToolCapabilityError("foundation projection is invalid")
        if not bool(getattr(controller, "is_tool_turn_controller", False)):
            raise ToolCapabilityError("foundation controller is invalid")
        self.projection = projection
        self.controller = controller

    def ready_for(self, *, palette: int, dialect: str) -> bool:
        return palette > 0 and dialect in _TOOL_DIALECTS - {"none"}


@dataclass(frozen=True)
class ToolCallCandidate:
    """One provider-native call translated into a closed provider-neutral shape."""

    provider_tool_call_id: str
    capability_id: str
    arguments: Mapping[str, Any]
    provider_call_ordinal: int = 1
    canonical_args_sha256: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_tool_call_id", _require_id(self.provider_tool_call_id, field="provider_tool_call_id"))
        object.__setattr__(self, "capability_id", _require_id(self.capability_id, field="capability_id"))
        object.__setattr__(self, "provider_call_ordinal", _require_positive(
            self.provider_call_ordinal, field="provider_call_ordinal", maximum=6
        ))
        arguments = _json_plain(self.arguments)
        if not isinstance(arguments, dict):
            raise ToolCapabilityError("tool call arguments must be an object")
        object.__setattr__(self, "arguments", MappingProxyType(arguments))
        expected = sha256(arguments)
        supplied = str(self.canonical_args_sha256 or "").strip()
        if supplied and supplied != expected:
            raise ToolCapabilityError("tool call argument hash drifted")
        object.__setattr__(self, "canonical_args_sha256", expected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ToolCallCandidate@1",
            "provider_tool_call_id": self.provider_tool_call_id,
            "provider_call_ordinal": self.provider_call_ordinal,
            "capability_id": self.capability_id,
            "arguments": _json_plain(self.arguments),
            "canonical_args_sha256": self.canonical_args_sha256,
        }


@dataclass(frozen=True)
class ToolResultEnvelope:
    """Closed, provider-untrusted result continuation evidence for later slices."""

    status: str
    result_sha256: str | None
    result_bytes: int
    result_tokens: int
    final_answer_may_name_limitation: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"available", "unavailable", "denied", "oversize", "indeterminate"}:
            raise ToolCapabilityError("tool result status is invalid")
        if self.result_sha256 is not None:
            object.__setattr__(self, "result_sha256", _require_hash(self.result_sha256, field="result_sha256"))
        object.__setattr__(self, "result_bytes", _require_positive(self.result_bytes, field="result_bytes", allow_zero=True, maximum=32 * 1024))
        object.__setattr__(self, "result_tokens", _require_positive(self.result_tokens, field="result_tokens", allow_zero=True, maximum=8 * 1024))
        if type(self.final_answer_may_name_limitation) is not bool:
            raise ToolCapabilityError("final_answer_may_name_limitation must be boolean")
        if self.status == "available":
            if self.result_sha256 is None:
                raise ToolCapabilityError("available tool result requires a digest")
        elif self.result_sha256 is not None or self.result_bytes != 0 or self.result_tokens != 0:
            raise ToolCapabilityError("non-available tool result cannot carry result material")

    @classmethod
    def available(cls, result: Any, *, final_answer_may_name_limitation: bool = False) -> "ToolResultEnvelope":
        """Construct the sole continuation envelope for capped untrusted data."""
        encoded = canonical_json(result).encode("utf-8")
        return cls(
            "available", sha256(result), len(encoded), len(encoded),
            final_answer_may_name_limitation,
        )

    @classmethod
    def limitation(cls, status: str, *, final_answer_may_name_limitation: bool = False) -> "ToolResultEnvelope":
        return cls(status, None, 0, 0, final_answer_may_name_limitation)


__all__ = [
    "CanonicalApplicationOperationDescriptor",
    "ModelTurnCapabilityProjection",
    "ToolCapabilityError",
    "ToolCapabilityFoundation",
    "ToolCallCandidate",
    "ToolQualification",
    "ToolResultEnvelope",
    "canonical_json",
    "parse_capability_manifest",
    "sha256",
    "validate_closed_arguments",
    "validate_closed_schema",
]
