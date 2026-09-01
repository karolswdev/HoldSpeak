"""The Update Factory: deterministic + model drafting (UPD-001..004).

HS-162-02: the deterministic drafter ships first.  It DEFINES the section
contract and the claim schema the model drafter (03) will be constrained
to.

Section contract (UPD-001)
--------------------------
Every update MUST cover six sections in this canonical order:

  1. Progress          -- focus items and their lifecycle states
  2. Decisions         -- accepted/dismissed proposals from the review
  3. Risks & Blockers  -- open risks and broken/at-risk dependencies
  4. Dependencies      -- all dependency items and their states
  5. Next Actions      -- items with upcoming due dates or planned state
  6. Source Coverage    -- caveats when any room section is degraded/absent

A section with nothing to say renders the honest minimal line (e.g.
"No decisions in this window."), not filler.

Claim schema (UPD-002)
----------------------
Every factual sentence in body_md carries a claim entry in claims_json.
The schema is the single authority for both the deterministic and model
drafters:

    {
      "span_id":  str,          # stable id within this draft (s_<section>_<ordinal>)
      "text":     str,          # the sentence or phrase
      "refs":     [str, ...],   # >= 1 canonical refs (item:, decision:, pobs:, etc.)
      "section":  str           # one of the six section keys
    }

When ``verified`` is ``False`` the claim is MARKED for owner review
(UPD-002: unsupported model language).  Deterministic claims omit the
field (always verified); only the model drafter may set it ``False``.

ZERO prose without a locator -- the deterministic drafter does not know
how to lie.

Determinism law
---------------
Same room state => byte-identical body_md + claims_json.  NO wall-clock
content inside the body.  Sort everything canonically.
"""
from __future__ import annotations

import json
import re as _re
import time as _time
from dataclasses import dataclass, field
from typing import Any, Optional

from ..db.updates import PublishedUpdateError
from ..logging_config import get_logger
from ..principals import Principal
from ..project_contracts import generate_pupd_id

_log = get_logger("services.project_update_service")

# ── Capability identity (HS-162-03) ──────────────────────────────────
PROJECT_UPDATE_CAPABILITY = "project.update_draft"

# ── Marker for unverified model claims (UPD-002) ────────────────────
UNVERIFIED_MARKER = "**[UNVERIFIED]**"


# ── Claim schema (UPD-002) ────────────────────────────────────────────
#
# This is the SINGLE AUTHORITY for both the deterministic and model
# drafters.  Story 03 and the face import this shape.

@dataclass(frozen=True, slots=True)
class Claim:
    """One factual claim in an update draft.

    span_id:  stable identifier within this draft (s_<section>_<ordinal>).
    text:     the factual sentence or phrase.
    refs:     list of >= 1 canonical refs (item:<id>, decision:<id>, etc.).
    section:  one of the six UPD-001 section keys.
    verified: True (default) for deterministic / cited model claims.
              False for MARKED unverified model claims (UPD-002).
              Omitted from to_dict() when True so deterministic output
              stays byte-identical.
    """
    span_id: str
    text: str
    refs: list[str]
    section: str
    verified: bool = True

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "refs": list(self.refs),
            "section": self.section,
            "span_id": self.span_id,
            "text": self.text,
        }
        if not self.verified:
            d["verified"] = False
        return d


# The six UPD-001 section keys, in canonical order.
SECTION_KEYS: tuple[str, ...] = (
    "progress",
    "decisions",
    "risks_blockers",
    "dependencies",
    "next_actions",
    "source_coverage",
)

# Human-readable section headings for the Markdown body.
_SECTION_HEADINGS: dict[str, str] = {
    "progress": "Progress",
    "decisions": "Decisions",
    "risks_blockers": "Risks & Blockers",
    "dependencies": "Dependencies",
    "next_actions": "Next Actions",
    "source_coverage": "Source Coverage",
}

# Honest minimal lines per section (nothing to say).
_HONEST_MINIMAL: dict[str, str] = {
    "progress": "No focus items in this window.",
    "decisions": "No decisions in this window.",
    "risks_blockers": "No risks or blockers in this window.",
    "dependencies": "No dependencies tracked.",
    "next_actions": "No upcoming actions.",
    "source_coverage": "All sources consulted successfully.",
}


# ── Section builders (deterministic) ──────────────────────────────────

def _build_progress(
    items_section: dict[str, Any],
    claims: list[Claim],
) -> str:
    """Progress section from room items (focus block)."""
    focus = items_section.get("focus", [])
    if not focus:
        return _HONEST_MINIMAL["progress"]

    lines: list[str] = []
    for i, item in enumerate(focus):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        lifecycle = item.get("lifecycle", "unknown")
        item_type = item.get("item_type", "item")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"{item_type.capitalize()}{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_{i}"
        claims.append(Claim(
            span_id=f"s_progress_{i}",
            text=text,
            refs=[ref],
            section="progress",
        ))
        lines.append(f"- {text}")

    total = items_section.get("total", len(focus))
    cap = len(focus)
    if total > cap:
        lines.append(f"\n_{total - cap} more items not shown._")

    return "\n".join(lines)


def _build_decisions(
    review_section: dict[str, Any],
    proposals: list[dict[str, Any]],
    claims: list[Claim],
) -> str:
    """Decisions section from the open review's proposals."""
    if not proposals:
        return _HONEST_MINIMAL["decisions"]

    lines: list[str] = []
    ordinal = 0
    for prop in proposals:
        prop_id = prop.get("id", "")
        title = prop.get("title", "Untitled proposal")
        lifecycle = prop.get("lifecycle", "open")
        kind = prop.get("proposal_kind", "")

        text = f"{title} ({kind}) -- {lifecycle}"
        ref = f"decision:{prop_id}" if prop_id else f"decision:unknown_{ordinal}"
        claims.append(Claim(
            span_id=f"s_decisions_{ordinal}",
            text=text,
            refs=[ref],
            section="decisions",
        ))
        lines.append(f"- {text}")
        ordinal += 1

    return "\n".join(lines)


def _build_risks_blockers(
    items_section: dict[str, Any],
    claims: list[Claim],
) -> str:
    """Risks & Blockers from room items filtered to risk/dependency types."""
    focus = items_section.get("focus", [])
    risk_items = [
        item for item in focus
        if item.get("item_type") in ("risk", "dependency")
        and item.get("lifecycle") in ("open", "at_risk", "broken")
    ]
    if not risk_items:
        return _HONEST_MINIMAL["risks_blockers"]

    lines: list[str] = []
    for i, item in enumerate(risk_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        item_type = item.get("item_type", "item")
        lifecycle = item.get("lifecycle", "unknown")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"{item_type.capitalize()}{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_rb_{i}"
        claims.append(Claim(
            span_id=f"s_risks_blockers_{i}",
            text=text,
            refs=[ref],
            section="risks_blockers",
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_dependencies(
    items_section: dict[str, Any],
    claims: list[Claim],
) -> str:
    """Dependencies from room items filtered to dependency type."""
    focus = items_section.get("focus", [])
    dep_items = [
        item for item in focus
        if item.get("item_type") == "dependency"
    ]
    if not dep_items:
        return _HONEST_MINIMAL["dependencies"]

    lines: list[str] = []
    for i, item in enumerate(dep_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        lifecycle = item.get("lifecycle", "unknown")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"Dependency{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_dep_{i}"
        claims.append(Claim(
            span_id=f"s_dependencies_{i}",
            text=text,
            refs=[ref],
            section="dependencies",
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_next_actions(
    items_section: dict[str, Any],
    claims: list[Claim],
) -> str:
    """Next actions: items with planned/active states or upcoming due dates."""
    focus = items_section.get("focus", [])
    action_items = [
        item for item in focus
        if item.get("lifecycle") in ("planned", "active")
        or item.get("due_at") is not None
    ]
    if not action_items:
        return _HONEST_MINIMAL["next_actions"]

    lines: list[str] = []
    for i, item in enumerate(action_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        item_type = item.get("item_type", "item")
        lifecycle = item.get("lifecycle", "unknown")
        due_at = item.get("due_at")

        due_str = f", due {due_at}" if due_at else ""
        text = f"{item_type.capitalize()}: {title} -- {lifecycle}{due_str}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_na_{i}"
        claims.append(Claim(
            span_id=f"s_next_actions_{i}",
            text=text,
            refs=[ref],
            section="next_actions",
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_source_coverage(
    room: dict[str, Any],
    caveats: list[dict[str, str]],
    claims: list[Claim],
) -> str:
    """Source coverage section: appears only when caveats exist."""
    if not caveats:
        return _HONEST_MINIMAL["source_coverage"]

    lines: list[str] = []
    for i, caveat in enumerate(caveats):
        section_name = caveat.get("section", "unknown")
        state = caveat.get("state", "unknown")
        reason = caveat.get("reason", "")

        reason_str = f": {reason}" if reason else ""
        text = f"Section '{section_name}' {state}{reason_str}"
        ref = f"project:{room.get('project_id', 'unknown')}"
        claims.append(Claim(
            span_id=f"s_source_coverage_{i}",
            text=text,
            refs=[ref],
            section="source_coverage",
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


# ── Source manifest builder ───────────────────────────────────────────

def _build_source_manifest(
    room: dict[str, Any],
    review_id: str | None,
    observation_ids: list[str],
    caveats: list[dict[str, str]],
) -> dict[str, Any]:
    """Build the source_manifest_json recording exactly what the draft saw."""
    manifest: dict[str, Any] = {
        "project_revision": room.get("revision", 0),
    }
    if review_id:
        manifest["review_id"] = review_id
    manifest["observation_ids"] = sorted(observation_ids)
    manifest["caveats"] = sorted(caveats, key=lambda c: c.get("section", ""))
    return manifest


# ── Room section caveat scanner ───────────────────────────────────────

_CAVEAT_SECTIONS = ("items", "meetings", "resources", "changes", "review")


def _scan_caveats(room: dict[str, Any]) -> list[dict[str, str]]:
    """Scan room sections for degraded/absent state (the 158 vocabulary)."""
    caveats: list[dict[str, str]] = []
    for section_key in _CAVEAT_SECTIONS:
        section = room.get(section_key, {})
        state = section.get("state", "absent")
        if state in ("degraded", "absent"):
            caveat: dict[str, str] = {"section": section_key, "state": state}
            error_code = section.get("error_code")
            reason = section.get("reason")
            if error_code:
                caveat["reason"] = error_code
            elif reason:
                caveat["reason"] = reason
            caveats.append(caveat)
    return sorted(caveats, key=lambda c: c["section"])


# ── Deterministic Markdown assembler ──────────────────────────────────

def _assemble_body(sections: dict[str, str]) -> str:
    """Assemble the six sections into the final Markdown body.

    Deterministic: sections are emitted in SECTION_KEYS order.
    """
    parts: list[str] = []
    for key in SECTION_KEYS:
        heading = _SECTION_HEADINGS[key]
        content = sections.get(key, _HONEST_MINIMAL[key])
        parts.append(f"## {heading}\n\n{content}")
    return "\n\n".join(parts) + "\n"


# ── Model drafter helpers (HS-162-03) ────────────────────────────────

_THINK_RE = _re.compile(r"<think>.*?</think>", _re.DOTALL)
_FENCE_RE = _re.compile(r"```(?:json)?\s*(.*?)\s*```", _re.DOTALL)


def _extract_structured_json(raw: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from an LLM response.

    Strips ``<think>...</think>`` blocks, tries markdown-fenced JSON
    first, then scans for the first balanced ``{...}`` substring.
    Returns ``None`` when no valid JSON dict is found.
    """
    if not raw:
        return None
    cleaned = _THINK_RE.sub("", raw).strip()
    fence = _FENCE_RE.search(cleaned)
    if fence:
        try:
            obj = json.loads(fence.group(1))
            if isinstance(obj, dict):
                return obj
        except (ValueError, TypeError):
            pass
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(cleaned[start : i + 1])
                    if isinstance(obj, dict):
                        return obj
                except (ValueError, TypeError):
                    pass
                start = -1
    return None


# Model output JSON schema for response_format (structured output).
_MODEL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "sentences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "cited_refs": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["text", "cited_refs"],
                        },
                    },
                },
                "required": ["key", "sentences"],
            },
        },
    },
    "required": ["sections"],
}


def _build_model_prompt(inventory_claims: list[Claim]) -> dict[str, Any]:
    """Build a prompt payload from the deterministic evidence inventory.

    The model is given every deterministic claim (with its refs) and asked
    to rewrite the sections with better prose, citing the exact refs.
    """
    by_section: dict[str, list[Claim]] = {}
    for claim in inventory_claims:
        by_section.setdefault(claim.section, []).append(claim)

    inventory_lines: list[str] = []
    for section_key in SECTION_KEYS:
        claims = by_section.get(section_key, [])
        inventory_lines.append(f"\n[section: {section_key}]")
        if claims:
            for c in claims:
                refs_str = ", ".join(c.refs)
                inventory_lines.append(
                    f"- {c.span_id}: {c.text!r} | refs: {refs_str}"
                )
        else:
            honest = _HONEST_MINIMAL.get(section_key, "")
            inventory_lines.append(f"- (empty section -- use: {honest!r})")

    system_prompt = (
        "You are a technical project update writer. Given the evidence "
        "inventory below, rewrite each section with clear, professional "
        "prose. Every sentence MUST cite its source references.\n\n"
        "RULES:\n"
        "1. Every sentence must cite at least one ref from the inventory "
        "using the EXACT ref strings provided.\n"
        "2. If you add a sentence with no evidence backing, set "
        "cited_refs to an empty list.\n"
        "3. Use ONLY refs from the inventory -- never invent refs.\n"
        "4. Cover all six sections in order: progress, decisions, "
        "risks_blockers, dependencies, next_actions, source_coverage.\n"
        "5. For empty sections, write the honest minimal line.\n"
        "6. Keep prose concise and factual.\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"sections": [{"key": "<section_key>", "sentences": '
        '[{"text": "<sentence>", "cited_refs": ["<ref1>", ...]}]}]}'
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": "EVIDENCE INVENTORY:\n" + "\n".join(inventory_lines),
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "project_update",
                "schema": _MODEL_OUTPUT_SCHEMA,
            },
        },
    }


def _parse_model_output(
    raw: str,
    inventory_refs: frozenset[str],
) -> tuple[dict[str, str], list[Claim]] | None:
    """Parse model JSON output into sections + claims.

    Returns ``(sections_dict, claims_list)`` on success, ``None`` if the
    output is unparseable.  Each claim is either verified (all cited_refs
    exist in the inventory) or MARKED (``verified=False``).
    """
    parsed = _extract_structured_json(raw)
    if parsed is None or "sections" not in parsed:
        return None

    sections: dict[str, str] = {}
    claims: list[Claim] = []

    for section_data in parsed.get("sections", []):
        key = section_data.get("key", "")
        if key not in SECTION_KEYS:
            continue

        sentences = section_data.get("sentences", [])
        lines: list[str] = []

        for i, sentence in enumerate(sentences):
            text = str(sentence.get("text", "")).strip()
            if not text:
                continue
            cited = sentence.get("cited_refs", [])
            if not isinstance(cited, list):
                cited = []

            # Validate: keep only refs that appear in the inventory.
            valid_refs = [r for r in cited if isinstance(r, str) and r in inventory_refs]

            if valid_refs:
                claims.append(Claim(
                    span_id=f"s_{key}_{i}",
                    text=text,
                    refs=valid_refs,
                    section=key,
                    verified=True,
                ))
                lines.append(f"- {text}")
            else:
                # MARKED: unverified claim -- no valid evidence refs.
                claims.append(Claim(
                    span_id=f"s_{key}_{i}",
                    text=text,
                    refs=[],
                    section=key,
                    verified=False,
                ))
                lines.append(f"- {UNVERIFIED_MARKER} {text}")

        if lines:
            sections[key] = "\n".join(lines)
        else:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    # Fill missing sections with honest minimums.
    for key in SECTION_KEYS:
        if key not in sections:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    return sections, claims


def _resolve_for_capability(
    db: Any,
    capability_id: str,
) -> tuple[str, str]:
    """Resolve the deployment revision and assignment ID for a capability.

    Returns ``(deployment_revision_id, assignment_id)``.
    Raises ``RuntimeError`` if no assignment exists.
    """
    key = f"capability:{capability_id}"
    with db._connection() as conn:
        head = conn.execute(
            "SELECT assignment_id, revision FROM inference_assignment_heads "
            "WHERE assignment_key=? AND cleared=0",
            (key,),
        ).fetchone()
        if head is None:
            raise RuntimeError(f"No assignment for {capability_id}")
        assignment_id = str(head["assignment_id"])
        entry = conn.execute(
            "SELECT profile_id FROM inference_assignments "
            "WHERE assignment_id=? AND assignment_revision=? "
            "ORDER BY ordinal LIMIT 1",
            (assignment_id, head["revision"]),
        ).fetchone()
        if entry is None:
            raise RuntimeError(
                f"No entries in assignment for {capability_id}"
            )
        profile_id = entry["profile_id"]
        rev = conn.execute(
            "SELECT id FROM deployment_revisions WHERE model=? LIMIT 1",
            (profile_id,),
        ).fetchone()
        if rev is None:
            raise RuntimeError(
                f"No deployment revision for profile {profile_id}"
            )
        return str(rev["id"]), assignment_id


# ── The service ───────────────────────────────────────────────────────

class ProjectUpdateService:
    """The Update Factory service (SRS SS8).

    draft_update reads the Project room truth over ONE pinned revision,
    emits editable Markdown with the UPD-001 sections, and persists via
    UpdatesRepository.  Regenerate = supersede unaccepted draft (UPD-004).
    """

    def __init__(
        self,
        db: Any,
        *,
        project_service: Any,
        delta_service: Any | None = None,
        broker: Any | None = None,
    ) -> None:
        self._db = db
        self._project_service = project_service
        self._delta_service = delta_service
        self._broker = broker

    # ── Model drafter (HS-162-03) ────────────────────────────────────

    def _draft_with_model(
        self,
        principal: Principal,
        det_claims: list[Claim],
        det_sections: dict[str, str],
        det_body_md: str,
    ) -> tuple[str, str, str]:
        """Attempt model drafting over the deterministic evidence inventory.

        Returns ``(body_md, claims_json, generator)`` on success.
        Raises ``_ModelDraftFailed`` on any failure (router unavailable,
        model error, timeout, unparseable output).
        """
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal

        broker = self._broker
        if broker is None:
            raise _ModelDraftFailed("no_broker")

        runner = broker.inference_runner

        # Resolve deployment revision for the update-draft capability.
        try:
            deployment_rev_id, assignment_id = _resolve_for_capability(
                broker.database, PROJECT_UPDATE_CAPABILITY,
            )
        except RuntimeError as exc:
            raise _ModelDraftFailed(f"no_assignment: {exc}") from exc

        # Build the evidence inventory from deterministic claims.
        inventory_refs: frozenset[str] = frozenset(
            ref for claim in det_claims for ref in claim.refs
        )

        payload = _build_model_prompt(det_claims)

        request = InvocationRequest(
            deployment_revision=deployment_rev_id,
            definition_origin=ServiceContract.for_payload(
                "project.update.draft", "1", payload,
            ),
            deadline_at=_time.time() + 120,
            payload=payload,
        )

        captured: list[Any] = []

        def _capture(value: Any) -> str:
            captured.append(value)
            return f"update-draft:{assignment_id}"

        try:
            with _as_principal(principal):
                outcome = runner.invoke(
                    request, CanonicalPromptAdapter(), publish=_capture,
                )
        except Exception as exc:
            raise _ModelDraftFailed(f"runner_error: {exc}") from exc

        # Extract raw output -- try direct result first, then captured.
        raw: str | None = None
        result = getattr(outcome, "result", None)
        if isinstance(result, dict) and "output" in result:
            raw = str(result["output"])
        elif captured:
            adapter_result = captured[0]
            if isinstance(adapter_result, dict) and "output" in adapter_result:
                raw = str(adapter_result["output"])

        if raw is None:
            raise _ModelDraftFailed("no_output")

        # Parse and constrain to the claim schema.
        parsed = _parse_model_output(raw, inventory_refs)
        if parsed is None:
            raise _ModelDraftFailed("unparseable_output")

        model_sections, model_claims = parsed
        body_md = _assemble_body(model_sections)
        claims_json = json.dumps(
            [c.to_dict() for c in model_claims],
            sort_keys=True,
            separators=(",", ":"),
        )
        generator = f"model:{assignment_id}"
        return body_md, claims_json, generator

    def draft_update(
        self,
        principal: Principal,
        project_id: str,
        *,
        generator: str = "deterministic",
    ) -> dict[str, Any]:
        """Draft a project update.

        Reads the room truth at the current revision, builds the six
        UPD-001 sections with claim entries, and persists the draft.

        If an unaccepted draft exists for this project, supersede it
        (draft_revision+1).  NEVER touches a published row.

        Args:
            principal: the acting principal.
            project_id: the project to draft for.
            generator: ``"deterministic"`` (default) or ``"model"``
                       (HS-162-03).

        Returns:
            The persisted draft as a dict (from the updates repo).
        """
        want_model = generator == "model"

        # 1. Read the room at ONE pinned revision
        room = self._project_service.room(principal, project_id)
        revision = room.get("revision", 0)

        # 2. Scan for caveats (degraded/absent sections)
        caveats = _scan_caveats(room)

        # 3. Read the open review's proposals (if any)
        review_id: str | None = None
        proposals: list[dict[str, Any]] = []
        review_section = room.get("review", {})
        if review_section.get("state") == "ok":
            review_id = review_section.get("open_review_id")
            if review_id:
                proposals = self._db.project_observations.list_proposals(
                    project_id,
                    review_window_key=review_id,
                )
                # Sort deterministically for stable output
                proposals.sort(key=lambda p: (
                    p.get("proposal_kind", ""),
                    p.get("title", ""),
                    p.get("id", ""),
                ))

        # 4. Read observations with evidence links
        observations = self._db.project_observations.list_observations(
            project_id, limit=500,
        )
        observation_ids = sorted([obs["id"] for obs in observations])

        # 5. Build deterministic sections + claims (always -- this is
        #    the evidence inventory the model drafter is constrained to).
        det_claims: list[Claim] = []
        items_section = room.get("items", {})

        det_sections: dict[str, str] = {
            "progress": _build_progress(items_section, det_claims),
            "decisions": _build_decisions(review_section, proposals, det_claims),
            "risks_blockers": _build_risks_blockers(items_section, det_claims),
            "dependencies": _build_dependencies(items_section, det_claims),
            "next_actions": _build_next_actions(items_section, det_claims),
            "source_coverage": _build_source_coverage(room, caveats, det_claims),
        }

        det_body_md = _assemble_body(det_sections)
        det_claims_json = json.dumps(
            [c.to_dict() for c in det_claims],
            sort_keys=True,
            separators=(",", ":"),
        )

        # 6. Build source manifest (byte-identical regardless of generator).
        manifest = _build_source_manifest(
            room, review_id, observation_ids, caveats,
        )
        manifest_json = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"),
        )

        # 7. Choose body + claims based on generator.
        if want_model:
            try:
                body_md, claims_json, actual_generator = (
                    self._draft_with_model(
                        principal, det_claims, det_sections, det_body_md,
                    )
                )
            except _ModelDraftFailed as exc:
                _log.warning(
                    "Model drafter failed (%s); falling back to deterministic.",
                    exc.reason,
                )
                body_md = det_body_md
                claims_json = det_claims_json
                actual_generator = "deterministic"
        else:
            body_md = det_body_md
            claims_json = det_claims_json
            actual_generator = "deterministic"

        # 8. Persist: check for existing unaccepted draft to supersede
        existing_drafts = self._db.project_updates.list_updates(
            project_id, lifecycle="draft",
        )

        if existing_drafts:
            # Supersede the latest unaccepted draft (UPD-004)
            old_draft = existing_drafts[0]  # list is ordered by draft_revision DESC
            new_id = generate_pupd_id()
            try:
                new_row = self._db.project_updates.supersede_draft(
                    old_draft["id"],
                    new_update_id=new_id,
                    body_md=body_md,
                    claims_json=claims_json,
                    source_manifest_json=manifest_json,
                    generator=actual_generator,
                )
                return new_row
            except PublishedUpdateError:
                # The "draft" was actually published (race).  Fall through
                # to create a fresh draft.
                _log.warning(
                    "Draft %s was published between list and supersede; "
                    "creating a new draft instead.",
                    old_draft["id"],
                )

        # No existing draft (or race recovery): create a new one
        new_id = generate_pupd_id()
        self._db.project_updates.insert_update(
            update_id=new_id,
            project_id=project_id,
            project_revision=revision,
            review_id=review_id,
            draft_revision=1,
            body_md=body_md,
            claims_json=claims_json,
            source_manifest_json=manifest_json,
            generator=actual_generator,
        )
        return self._db.project_updates.get_update(new_id)


class _ModelDraftFailed(Exception):
    """Internal signal: the model drafting path failed; fall back."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
