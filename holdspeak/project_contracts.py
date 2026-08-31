"""Command result envelope, typed errors, and ID prefixes for Project Rooms.

This module freezes the NAMES that every later phase (the Room command
contract API-001..003, the MCP family MCP-001..005, the Watch effects)
returns.  It is PURE: no DB, no IO, no side-effects -- constants,
dataclasses, validators, and ID generators only.

SRS traceability
----------------
- Envelope shape: API-003, MCP-004
- Optimistic concurrency: API-001
- Idempotency: API-002, DOM-010
- Capability errors: MCP-005
- ID prefixes: SS4.1
- Result kinds: SS10 (event vocabulary) + SS11.1 (MCP tool table)
"""

from __future__ import annotations

import enum
import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from holdspeak.refs import QualifiedRef, parse as parse_ref


# ------------------------------------------------------------------
# Result kinds -- closed vocabulary (SRS SS10 events + SS11.1 tools)
# ------------------------------------------------------------------

class ResultKind(enum.Enum):
    """Closed vocabulary of command result kinds.

    Each value traces to an SRS operation from SS6/SS10/SS11.1.
    """

    # Project lifecycle (SS11.1 project.create/update/archive/restore,
    # SS10 project.created/updated/archived/restored)
    CREATED = "created"
    UPDATED = "updated"
    ARCHIVED = "archived"
    RESTORED = "restored"

    # Resource relationships (SS11.1 project.link/unlink,
    # SS10 project.resource.linked/unlinked)
    LINKED = "linked"
    UNLINKED = "unlinked"

    # Review and Delta (SS11.1 project.open_review/decide_proposal/
    # accept_review, SS10 project.review.opened/proposal.decided/
    # review.accepted, SS7.2, SS7.3 DEL-005)
    REVIEW_OPENED = "review_opened"
    PROPOSAL_DECIDED = "proposal_decided"
    REVIEW_ACCEPTED = "review_accepted"

    # Update factory (SS11.1 project.draft_update/update_draft/
    # publish_update, SS10 project.update.drafted/published,
    # SS8 UPD-005)
    UPDATE_DRAFTED = "update_drafted"
    UPDATE_SAVED = "update_saved"
    UPDATE_PUBLISHED = "update_published"

    # Steward (SS11.1 project.configure_steward/run_steward/
    # stop_steward, SS10 project.steward.configured/run_started,
    # SS9.2, SS9.4 STW-003, MCP-003)
    STEWARD_CONFIGURED = "steward_configured"
    STEWARD_RUN_REQUESTED = "steward_run_requested"
    STEWARD_STOPPED = "steward_stopped"

    # Idempotent no-op (API-002: repeating a completed command
    # with the same ID and request hash returns the stored result)
    NO_CHANGE = "no_change"


# ------------------------------------------------------------------
# Error codes -- closed enum (API-001, API-002, MCP-005, DOM-006)
# ------------------------------------------------------------------

class ProjectErrorCode(enum.Enum):
    """Closed vocabulary of typed Project error codes.

    Each value traces to an SRS requirement ID.
    """

    # API-001: a stale revision MUST return a typed conflict
    # without partial mutation.
    STALE_REVISION = "stale_revision"

    # API-002: a different request hash on the same command_id
    # MUST return an idempotency conflict.
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"

    # SS6.3 (implied): writes reference existing entities;
    # DOM-001: every Project-owned entity MUST have a stable
    # opaque ID.
    NOT_FOUND = "not_found"

    # DOM-006: YOLO MUST NOT remove input validation;
    # DB-004: JSON fields with closed semantics MUST be validated.
    VALIDATION = "validation"

    # MCP-005: unsupported citizen mutations MUST return a typed
    # capability error, never a simulated success.
    CAPABILITY = "capability"


# ------------------------------------------------------------------
# Envelope -- the command result shape (API-003, MCP-004)
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ProjectWarning:
    """A non-fatal warning attached to a command result."""

    code: str
    message: str
    detail: Any = None


@dataclass(frozen=True, slots=True)
class ProjectError:
    """A typed error attached to a command result."""

    code: ProjectErrorCode
    message: str
    detail: Any = None


@dataclass(frozen=True, slots=True)
class CommandResultEnvelope:
    """The canonical envelope for every Project write result.

    API-003: results MUST include result_kind, project_id,
    project_revision, changed_refs, and typed warnings/errors.

    MCP-004: results MUST be structured JSON-serializable data and
    MUST not require parsing prose to determine success or changed refs.

    ``changed_refs`` are validated through ``holdspeak.refs.parse()``.
    """

    result_kind: ResultKind
    project_id: str
    project_revision: int
    changed_refs: tuple[QualifiedRef, ...] = ()
    warnings: tuple[ProjectWarning, ...] = ()
    errors: tuple[ProjectError, ...] = ()


def validate_envelope(envelope: CommandResultEnvelope) -> list[str]:
    """Validate an envelope's structural integrity.

    Returns a list of violation messages (empty = valid).
    All changed_refs are validated through ``holdspeak.refs.parse()``.
    """
    violations: list[str] = []

    if not isinstance(envelope.result_kind, ResultKind):
        violations.append(
            f"result_kind must be a ResultKind, got {type(envelope.result_kind).__name__}"
        )

    if not envelope.project_id:
        violations.append("project_id must be non-empty")

    if not isinstance(envelope.project_revision, int) or envelope.project_revision < 0:
        violations.append("project_revision must be a non-negative integer")

    for i, ref in enumerate(envelope.changed_refs):
        if not isinstance(ref, QualifiedRef):
            violations.append(
                f"changed_refs[{i}] must be a QualifiedRef, "
                f"got {type(ref).__name__}"
            )
        elif not ref.is_registered:
            violations.append(
                f"changed_refs[{i}] has unregistered type {ref.type!r}"
            )

    for i, w in enumerate(envelope.warnings):
        if not isinstance(w, ProjectWarning):
            violations.append(
                f"warnings[{i}] must be a ProjectWarning, "
                f"got {type(w).__name__}"
            )

    for i, e in enumerate(envelope.errors):
        if not isinstance(e, ProjectError):
            violations.append(
                f"errors[{i}] must be a ProjectError, "
                f"got {type(e).__name__}"
            )
        elif not isinstance(e.code, ProjectErrorCode):
            violations.append(
                f"errors[{i}].code must be a ProjectErrorCode, "
                f"got {type(e.code).__name__}"
            )

    return violations


# ------------------------------------------------------------------
# ID prefixes (SRS SS4.1)
# ------------------------------------------------------------------

# The eleven prefixes from SRS SS4.1, each mapping to its entity name.
ID_PREFIXES: dict[str, str] = {
    "pitem_": "Project item",
    "psrc_": "Source",
    "pobs_": "Observation",
    "pprop_": "Proposal",
    "prev_": "Review",
    "pupd_": "Update",
    "pchg_": "Change",
    "pcmd_": "Command",
    "pstpol_": "Steward policy",
    "pstrun_": "Steward run",
    "pststep_": "Steward step",
}

# Deterministic prefixes: same inputs MUST produce the same ID.
DETERMINISTIC_PREFIXES: frozenset[str] = frozenset({
    "pobs_",    # from adapter, source identity, source version, fact key
    "pprop_",   # from project, review window, proposal kind, target, normalized patch
    "pchg_",    # from project_id, project_revision, ordinal
})

# Regex for validating any project ID: prefix + 32 hex chars (uuid4.hex).
# Deterministic IDs use sha256[:32] but the format is identical.
_ID_RE = re.compile(r"^([a-z_]+)([0-9a-f]{32})$")


def _deterministic_hex(*, parts: Sequence[str]) -> str:
    """Hash ordered parts into 32 hex characters (matching uuid4.hex length)."""
    h = hashlib.sha256()
    for part in parts:
        # Length-prefix each part to avoid collisions like
        # ("ab", "cd") vs ("a", "bcd").
        encoded = part.encode("utf-8")
        h.update(len(encoded).to_bytes(4, "big"))
        h.update(encoded)
    return h.hexdigest()[:32]


# -- Non-deterministic generators (unique per call) ------------------

def generate_pitem_id() -> str:
    """Generate a Project item ID.  SS4.1: stable for the item's lifetime."""
    return "pitem_" + uuid.uuid4().hex


def generate_psrc_id() -> str:
    """Generate a Source ID.  SS4.1: stable for one configured source."""
    return "psrc_" + uuid.uuid4().hex


def generate_prev_id() -> str:
    """Generate a Review ID.  SS4.1: unique accepted/review session identity."""
    return "prev_" + uuid.uuid4().hex


def generate_pupd_id() -> str:
    """Generate an Update ID.  SS4.1: stable draft; revisions do not replace."""
    return "pupd_" + uuid.uuid4().hex


def generate_pcmd_id() -> str:
    """Generate a Command ID.  SS4.1: caller-supplied or generated once."""
    return "pcmd_" + uuid.uuid4().hex


def generate_pstpol_id() -> str:
    """Generate a Steward policy ID.  SS4.1: stable per Project policy."""
    return "pstpol_" + uuid.uuid4().hex


def generate_pstrun_id() -> str:
    """Generate a Steward run ID.  SS4.1: unique execution attempt."""
    return "pstrun_" + uuid.uuid4().hex


def generate_pststep_id() -> str:
    """Generate a Steward step ID.  SS4.1: unique run step/effect attempt."""
    return "pststep_" + uuid.uuid4().hex


# -- Deterministic generators (same inputs -> same ID) ---------------

def generate_pobs_id(
    *,
    adapter: str,
    source_id: str,
    source_version: str,
    fact_key: str,
) -> str:
    """Generate a deterministic Observation ID.

    SS4.1: deterministic from adapter, source identity, source version,
    and observed fact key.
    """
    return "pobs_" + _deterministic_hex(
        parts=[adapter, source_id, source_version, fact_key],
    )


def generate_pprop_id(
    *,
    project_id: str,
    review_window_key: str,
    proposal_kind: str,
    target_ref: str,
    normalized_patch: str,
) -> str:
    """Generate a deterministic Proposal ID.

    SS4.1: deterministic from Project, review window, proposal kind,
    target, and normalized patch.
    """
    return "pprop_" + _deterministic_hex(
        parts=[project_id, review_window_key, proposal_kind,
               target_ref, normalized_patch],
    )


def generate_pchg_id(
    *,
    project_id: str,
    project_revision: int,
    ordinal: int,
) -> str:
    """Generate a deterministic Change ID.

    SS4.1: bound to aggregate revision and deterministic ordinal.
    """
    return "pchg_" + _deterministic_hex(
        parts=[project_id, str(project_revision), str(ordinal)],
    )


# -- Validators ------------------------------------------------------

def validate_id(id_str: str, prefix: str) -> bool:
    """Validate that *id_str* has the given *prefix* + 32 hex characters.

    Returns True if valid, False otherwise.
    """
    if prefix not in ID_PREFIXES:
        raise ValueError(f"Unknown prefix {prefix!r}")
    if not isinstance(id_str, str):
        return False
    m = _ID_RE.match(id_str)
    if m is None:
        return False
    return m.group(1) == prefix


def validate_pitem_id(id_str: str) -> bool:
    """Validate a Project item ID."""
    return validate_id(id_str, "pitem_")


def validate_psrc_id(id_str: str) -> bool:
    """Validate a Source ID."""
    return validate_id(id_str, "psrc_")


def validate_pobs_id(id_str: str) -> bool:
    """Validate an Observation ID."""
    return validate_id(id_str, "pobs_")


def validate_pprop_id(id_str: str) -> bool:
    """Validate a Proposal ID."""
    return validate_id(id_str, "pprop_")


def validate_prev_id(id_str: str) -> bool:
    """Validate a Review ID."""
    return validate_id(id_str, "prev_")


def validate_pupd_id(id_str: str) -> bool:
    """Validate an Update ID."""
    return validate_id(id_str, "pupd_")


def validate_pchg_id(id_str: str) -> bool:
    """Validate a Change ID."""
    return validate_id(id_str, "pchg_")


def validate_pcmd_id(id_str: str) -> bool:
    """Validate a Command ID."""
    return validate_id(id_str, "pcmd_")


def validate_pstpol_id(id_str: str) -> bool:
    """Validate a Steward policy ID."""
    return validate_id(id_str, "pstpol_")


def validate_pstrun_id(id_str: str) -> bool:
    """Validate a Steward run ID."""
    return validate_id(id_str, "pstrun_")


def validate_pststep_id(id_str: str) -> bool:
    """Validate a Steward step ID."""
    return validate_id(id_str, "pststep_")
