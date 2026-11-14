"""Editable Room fields: the read contract and write validator share the choices."""
from __future__ import annotations

from typing import Any
from .errors import ValidationError
from .project_definitions import ITEM_LIFECYCLES, SEVERITY_RANK

# A record-only review flag is open until its subject is closed. These
# words do not change the proposal's separate Accept/Defer/Dismiss lifecycle.
REVIEW_STATES = ("open", "closed")


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


def validate_edit_fields(fields: list[dict[str, Any]], values: dict[str, Any]) -> None:
    for field in fields:
        key = field["key"]
        if key not in values:
            continue
        value = values[key]
        if field["kind"] == "choice" and not any(type(value) is type(allowed) and value == allowed for allowed in field["values"]):
            label = field["label"].lower()
            article = "an" if label.startswith(tuple("aeiou")) else "a"
            message = f"Choose True or False for {label}." if all(isinstance(allowed, bool) for allowed in field["values"]) else f"Choose {article} {label} from the list."
            raise ValidationError(message, code="field_choice_invalid")
        if field["kind"] == "number" and (not isinstance(value, (float, int)) or isinstance(value, bool)):
            raise ValidationError(f"Enter a number for {field['label'].lower()}.", code="field_number_invalid")
        if field["kind"] == "text" and value is not None and not isinstance(value, str):
            raise ValidationError(f"Enter text for {field['label'].lower()}.", code="field_text_invalid")
