"""One parser/composer for the Room's stored claim text and its edit fields."""
from __future__ import annotations

import re
from typing import Any
from .errors import ConflictError, ValidationError
from .project_definitions import ITEM_LIFECYCLES, SEVERITY_RANK
from .room_edit_fields import choice, validate_edit_fields

_KINDS = "|".join(re.escape(kind.capitalize()) for kind in ITEM_LIFECYCLES)
_ITEM = re.compile(rf"^(?P<kind>{_KINDS})(?: \[(?P<severity>[a-z_]+)\])?: (?P<subject>.+) -- (?P<state>[a-z_]+)(?P<tail>, due .+)?$", re.DOTALL)


def claim_editor(claim: dict[str, Any]) -> dict[str, Any]:
    text = str(claim.get("text") or "")
    match = _ITEM.fullmatch(text)
    values: dict[str, Any] = {"subject": text}
    fields = [{"key": "subject", "label": "Subject", "kind": "text"}]
    if match:
        kind = match["kind"].lower()
        values = {"subject": match["subject"], "kind": kind, "state": match["state"]}
        fields += [choice("kind", ITEM_LIFECYCLES), {**choice("state", ITEM_LIFECYCLES[kind]), "values_by_kind": {key:list(states) for key,states in ITEM_LIFECYCLES.items()}}]
        if match["severity"]:
            values["severity"] = match["severity"]
            fields.append(choice("severity", SEVERITY_RANK))
    return {"span_id": claim["span_id"], "section": str(claim.get("section") or ""), "text": text, "values": values, "fields": fields}


def _claim_range(body: str, section: str, headings: dict[str, str]) -> tuple[int, int] | None:
    marker = f"## {headings.get(section, '')}\n"
    start = body.find(marker)
    if start < 0:
        return None if any(f"## {heading}\n" in body for heading in headings.values()) else (0, len(body))
    start += len(marker)
    end = body.find("\n## ", start)
    return start, end if end >= 0 else len(body)


def claim_editors(body: str, claims: list[dict[str, Any]], headings: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for claim in claims:
        bounds = _claim_range(body, str(claim.get("section") or ""), headings)
        text = str(claim.get("text") or "")
        if bounds and text and body[bounds[0]:bounds[1]].count(text) == 1:
            out.append(claim_editor(claim))
    return out


def edit_claim_body(body: str, claims: list[dict[str, Any]], edits: list[dict[str, Any]], headings: dict[str, str]) -> str:
    by_id = {claim["span_id"]: claim for claim in claims}
    for edit in edits:
        claim = by_id.get(edit.get("span_id"))
        old = str(claim.get("text") or "") if claim else ""
        if not claim or old != edit.get("text") or old not in body:
            raise ConflictError("The claim changed. Read it again.", code="claim_edit_stale")
        schema = claim_editor(claim)
        values = edit.get("values")
        if not isinstance(values, dict) or set(values) != set(schema["values"]):
            raise ValidationError("Read the claim fields again.", code="claim_edit_invalid")
        # A kind change uses that kind's lifecycle vocabulary on the same
        # contract; the face does not infer a second set of states.
        fields = schema["fields"]
        if isinstance(values.get("kind"), str) and values["kind"] in ITEM_LIFECYCLES:
            fields = [choice("state", ITEM_LIFECYCLES[values["kind"]]) if field["key"] == "state" else field for field in fields]
        validate_edit_fields(fields, values)
        subject = str(values["subject"] or "").strip()
        if "\n" in subject or "\r" in subject:
            raise ValidationError("Enter one claim subject on one line.", code="claim_subject_invalid")
        if not subject:
            raise ValidationError("Enter the claim subject.", code="claim_subject_required")
        match = _ITEM.fullmatch(old)
        new = subject
        if match:
            severity = f" [{values['severity']}]" if "severity" in values else ""
            new = f"{values['kind'].capitalize()}{severity}: {subject} -- {values['state']}{match['tail'] or ''}"
        # The same source fact can occur in Progress and Risks. Bind its
        # occurrence to the claim's section, not the first matching sentence.
        bounds = _claim_range(body, str(claim.get("section") or ""), headings)
        if bounds is None:
            raise ConflictError("The claim changed. Read it again.", code="claim_edit_stale")
        start, end = bounds
        section = body[start:end]
        if section.count(old) != 1:
            raise ConflictError("The claim changed. Read it again.", code="claim_edit_stale")
        body = body[:start] + section.replace(old, new, 1) + body[end:]
    return body
