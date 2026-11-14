"""One parser/composer for the Room's stored claim text and its edit fields."""
from __future__ import annotations

import re
import unicodedata
from typing import Any
from .errors import ConflictError, ValidationError
from .project_definitions import ITEM_LIFECYCLES, SEVERITY_RANK
from .room_edit_fields import choice, validate_edit_fields

_KINDS = "|".join(re.escape(kind.capitalize()) for kind in ITEM_LIFECYCLES)
_ITEM = re.compile(rf"^(?P<kind>{_KINDS})(?: \[(?P<severity>[a-z_]+)\])?: (?P<subject>.+) -- (?P<state>[a-z_]+)(?:, due (?P<due>.+))?$", re.DOTALL)


def compose(kind: str, severity: str | None, subject: str, state: str, *, due: str | None = None) -> str:
    """The stored item sentence. Subject punctuation and line breaks stay exact."""
    level = f" [{severity}]" if severity else ""
    return f"{kind.capitalize()}{level}: {subject} -- {state}" + (f", due {due}" if due else "")


def parse(text: str) -> dict[str, Any] | None:
    """Read a saved item sentence; other claim formats have no item fields."""
    match = _ITEM.fullmatch(text)
    if not match:
        return None
    fields = {**match.groupdict(), "kind": match["kind"].lower()}
    if fields["due"] is None:
        del fields["due"]
    return fields


def claim_editor(claim: dict[str, Any]) -> dict[str, Any]:
    text = str(claim.get("text") or "")
    match = parse(text)
    values: dict[str, Any] = {"subject": text}
    fields = [{"key": "subject", "label": "Subject", "kind": "text"}]
    if match:
        kind = match["kind"]
        values = {"subject": match["subject"], "kind": kind, "state": match["state"]}
        fields += [choice("kind", ITEM_LIFECYCLES), {**choice("state", ITEM_LIFECYCLES[kind]), "values_by_kind": {key:list(states) for key,states in ITEM_LIFECYCLES.items()}}]
        if match["severity"]:
            values["severity"] = match["severity"]
            fields.append(choice("severity", SEVERITY_RANK))
    return {"span_id": claim["span_id"], "section": str(claim.get("section") or ""), "text": text, "values": values, "fields": fields}


def _claim_occurrences(body: str, claim: dict[str, Any], headings: dict[str, str]) -> list[tuple[int, int]]:
    """Locate complete current claim payloads, never a substring in newer words."""
    from .project_update_service import UNVERIFIED_MARKER

    sections = {f"## {title}": key for key, title in headings.items()}
    section = None
    offset = 0
    found = []
    wanted = str(claim.get("text") or "")
    decoded = parse(wanted)
    for line in body.splitlines(keepends=True):
        text = line.rstrip("\r\n")
        if text in sections:
            section = sections[text]
        else:
            start = offset
            for prefix in ("- ", "* ", "+ ", "> "):
                if text != wanted and text.startswith(prefix):
                    start += len(prefix)
                    text = text[len(prefix):]
                    break
            marker = UNVERIFIED_MARKER + " "
            if text != wanted and text.startswith(marker):
                start += len(marker)
                text = text[len(marker):]
            if text != wanted and text.startswith("**") and text.endswith("**"):
                start += 2
                text = text[2:-2]
            if wanted and text == wanted and parse(text) == decoded and (section is None or section == claim.get("section")):
                found.append((start, start + len(text)))
        offset += len(line)
    return found


def claim_editors(body: str, claims: list[dict[str, Any]], headings: dict[str, str]) -> list[dict[str, Any]]:
    return [claim_editor(claim) for claim in claims if len(_claim_occurrences(body, claim, headings)) == 1]


def edit_claim_body(body: str, claims: list[dict[str, Any]], edits: list[dict[str, Any]], headings: dict[str, str]) -> str:
    by_id = {claim["span_id"]: claim for claim in claims}
    for edit in edits:
        claim = by_id.get(edit.get("span_id"))
        old = str(claim.get("text") or "") if claim else ""
        if not claim or old != edit.get("text"):
            raise ConflictError("This item changed or its saved version is missing. Nothing changed. Read again.", code="answer_stale")
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
        subject = values["subject"]
        if len(subject.splitlines()) != 1 or any(unicodedata.category(char) in ("Cc", "Cf", "Cs", "Zl", "Zp") for char in subject):
            raise ValidationError("Enter one claim subject on one line.", code="claim_subject_invalid")
        subject = subject.strip()
        if not subject:
            raise ValidationError("Enter the claim subject.", code="claim_subject_required")
        saved = parse(old)
        new = compose(values["kind"], values.get("severity"), subject, values["state"], due=saved.get("due")) if saved else subject
        occurrences = _claim_occurrences(body, claim, headings)
        if len(occurrences) != 1:
            raise ConflictError("This item changed or its saved version is missing. Nothing changed. Read again.", code="answer_stale")
        start, end = occurrences[0]
        body = body[:start] + new + body[end:]
    return body
