"""Editable Room fields: the read contract and write validator share the choices."""
from __future__ import annotations

import json
import math
from typing import Any
from .errors import ValidationError
from .project_definitions import ITEM_LIFECYCLES, SEVERITY_RANK

# A record-only review flag is open until its subject is closed. These
# words do not change the proposal's separate Accept/Defer/Dismiss lifecycle.
REVIEW_STATES = ("open", "closed")
MAX_REVIEW_TEXT_BYTES = 4096
MAX_REVIEW_PATCH_BYTES = 16384


def choice(key: str, values: Any, label: str | None = None) -> dict[str, Any]:
    return {"key": key, "label": label or key.replace("_", " ").capitalize(),
            "kind": "choice", "values": list(values)}


def review_edit_fields(patch: dict[str, Any], proposal_kind: str) -> list[dict[str, Any]]:
    choices = {
        "state": ("failed", "stale") if proposal_kind == "coverage_degraded" else REVIEW_STATES,
        "item_type": tuple(ITEM_LIFECYCLES),
        "severity": tuple(SEVERITY_RANK),
        "lifecycle": ITEM_LIFECYCLES.get(str(patch.get("item_type") or "risk"), ()),
        "review_status": ("draft", "accepted"),
    }
    fields = []
    for key, value in patch.items():
        if key.startswith("_") or key.endswith(("_id", "_ref")) or isinstance(value, (dict, list)):
            continue
        if key in choices:
            field = choice(key, choices[key])
            if key == "lifecycle":
                field["values_by_item_type"] = {kind: list(states) for kind, states in ITEM_LIFECYCLES.items()}
            fields.append(field)
        elif isinstance(value, bool):
            fields.append(choice(key, (False, True)))
        else:
            fields.append({"key": key, "label": key.replace("_", " ").capitalize(),
                           "kind": "number" if isinstance(value, (float, int)) else "text"})
    return fields


def validate_edit_fields(fields: list[dict[str, Any]], values: dict[str, Any], *, resulting: dict[str, Any] | None = None) -> None:
    for field in fields:
        key = field["key"]
        if key not in values:
            continue
        value = values[key]
        if isinstance(value, (dict, list)):
            raise ValidationError("Enter one value for each review field.", code="field_type_invalid")
        allowed_values = field.get("values", [])
        if resulting is not None and "values_by_item_type" in field:
            item_type = resulting.get("item_type", "risk")
            allowed_values = field["values_by_item_type"].get(item_type, ()) if isinstance(item_type, str) else ()
        if field["kind"] == "choice" and not any(type(value) is type(allowed) and value == allowed for allowed in allowed_values):
            label = field["label"].lower()
            article = "an" if label.startswith(tuple("aeiou")) else "a"
            message = f"Choose True or False for {label}." if all(isinstance(allowed, bool) for allowed in allowed_values) else f"Choose {article} {label} from the list."
            raise ValidationError(message, code="field_choice_invalid")
        if field["kind"] == "number" and (type(value) not in (float, int) or (type(value) is float and not math.isfinite(value))):
            raise ValidationError(f"Enter a number for {field['label'].lower()}.", code="field_number_invalid")
        if field["kind"] == "text" and type(value) is not str:
            raise ValidationError(f"Enter text for {field['label'].lower()}.", code="field_text_invalid")


def read_review_patch(patch: dict[str, Any], proposal_kind: str) -> dict[str, Any]:
    """The public proposal fields, shared by every reader (including legacy rows).

    Private/internal keys are removed at every depth. Public producer facts
    and recurrence links stay readable without becoming editable.
    """
    def public(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: public(item) for key, item in value.items() if not key.startswith("_")}
        if isinstance(value, list):
            return [public(item) for item in value]
        return value
    return public(patch) if isinstance(patch, dict) else {}


def merge_review_edits(saved: dict[str, Any], proposal_kind: str, edits: Any) -> dict[str, Any]:
    """Saved declarations decide admission; caller values never declare fields."""
    fields = review_edit_fields(saved, proposal_kind)
    allowed = {field["key"] for field in fields}
    if not isinstance(edits, dict) or set(edits) - allowed:
        raise ValidationError("Change only the review fields shown in the last read.", code="review_field_unknown")
    result = {key: saved[key] for key in allowed}
    result.update(edits)
    checked = dict(edits)
    if "item_type" in edits and "lifecycle" in allowed:
        checked["lifecycle"] = result["lifecycle"]
    validate_edit_fields(fields, checked, resulting=result)
    for value in result.values():
        if isinstance(value, str):
            try:
                size = len(value.encode("utf-8"))
            except UnicodeEncodeError:
                raise ValidationError("Enter valid text for each review field.", code="field_text_invalid") from None
            if size > MAX_REVIEW_TEXT_BYTES:
                raise ValidationError("Keep each review text field within 4,096 bytes.", code="review_text_too_long")
    if len(json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")) > MAX_REVIEW_PATCH_BYTES:
        raise ValidationError("Keep the review patch within 16,384 bytes.", code="review_patch_too_large")
    return result
