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

ZERO prose without a locator -- the deterministic drafter does not know
how to lie.

Determinism law
---------------
Same room state => byte-identical body_md + claims_json.  NO wall-clock
content inside the body.  Sort everything canonically.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ..db.updates import PublishedUpdateError
from ..logging_config import get_logger
from ..principals import Principal
from ..project_contracts import generate_pupd_id

_log = get_logger("services.project_update_service")


# ── Claim schema (UPD-002) ────────────────────────────────────────────
#
# This is the SINGLE AUTHORITY for both the deterministic and model
# drafters.  Story 03 and the face import this shape.

@dataclass(frozen=True, slots=True)
class Claim:
    """One factual claim in an update draft.

    span_id: stable identifier within this draft (s_<section>_<ordinal>).
    text:    the factual sentence or phrase.
    refs:    list of >= 1 canonical refs (item:<id>, decision:<id>, etc.).
    section: one of the six UPD-001 section keys.
    """
    span_id: str
    text: str
    refs: list[str]
    section: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    ) -> None:
        self._db = db
        self._project_service = project_service
        self._delta_service = delta_service

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
            generator: "deterministic" (default) or "model" (story 03).

        Returns:
            The persisted draft as a dict (from the updates repo).
        """
        if generator != "deterministic":
            raise ValueError(
                f"Generator {generator!r} not yet supported; "
                f"only 'deterministic' is available."
            )

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

        # 5. Build sections + claims
        claims: list[Claim] = []
        items_section = room.get("items", {})

        sections: dict[str, str] = {
            "progress": _build_progress(items_section, claims),
            "decisions": _build_decisions(review_section, proposals, claims),
            "risks_blockers": _build_risks_blockers(items_section, claims),
            "dependencies": _build_dependencies(items_section, claims),
            "next_actions": _build_next_actions(items_section, claims),
            "source_coverage": _build_source_coverage(room, caveats, claims),
        }

        body_md = _assemble_body(sections)
        claims_json = json.dumps(
            [c.to_dict() for c in claims],
            sort_keys=True,
            separators=(",", ":"),
        )

        # 6. Build source manifest
        manifest = _build_source_manifest(
            room, review_id, observation_ids, caveats,
        )
        manifest_json = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"),
        )

        # 7. Persist: check for existing unaccepted draft to supersede
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
                    generator=generator,
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
            generator=generator,
        )
        return self._db.project_updates.get_update(new_id)
