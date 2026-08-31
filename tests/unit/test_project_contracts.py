"""HS-157-02 -- Command result envelope, typed errors, and ID prefixes.

Tests the ``holdspeak.project_contracts`` module that freezes Project
Room command result names, error codes, and ID prefix contracts.

Frozen-name pinning
-------------------
Every test that checks a name or value is a deliberate pin: renaming a
``ResultKind``, ``ProjectErrorCode``, or ID prefix MUST fail a test so
the change is a conscious suite amendment, not an accidental drift.

SRS traceability
----------------
- Envelope: API-003, MCP-004
- Result kinds: SS10 (events) + SS11.1 (MCP tools) + SS8 UPD-005
- Error codes: API-001, API-002, MCP-005, DOM-006, DB-004
- ID prefixes: SS4.1
"""

from __future__ import annotations

import pytest

from holdspeak.project_contracts import (
    DETERMINISTIC_PREFIXES,
    ID_PREFIXES,
    CommandResultEnvelope,
    ProjectError,
    ProjectErrorCode,
    ProjectWarning,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
    generate_pitem_id,
    generate_pobs_id,
    generate_pprop_id,
    generate_prev_id,
    generate_psrc_id,
    generate_pstpol_id,
    generate_pstrun_id,
    generate_pststep_id,
    generate_pupd_id,
    validate_envelope,
    validate_id,
    validate_pchg_id,
    validate_pcmd_id,
    validate_pitem_id,
    validate_pobs_id,
    validate_pprop_id,
    validate_prev_id,
    validate_psrc_id,
    validate_pstpol_id,
    validate_pstrun_id,
    validate_pststep_id,
    validate_pupd_id,
)
from holdspeak.refs import QualifiedRef, parse as parse_ref


# =====================================================================
# Frozen-name pinning: ResultKind
# =====================================================================

# The exact set of result_kind values. Adding or removing a value
# is a deliberate suite amendment.
EXPECTED_RESULT_KINDS = frozenset({
    "created",
    "updated",
    "archived",
    "restored",
    "linked",
    "unlinked",
    "review_opened",
    "proposal_decided",
    "review_accepted",
    "update_drafted",
    "update_saved",
    "update_published",
    "steward_configured",
    "steward_run_requested",
    "steward_stopped",
    "no_change",
})


def test_result_kind_values_pinned() -> None:
    """A rename or removal of any result_kind value MUST fail this test."""
    actual = frozenset(rk.value for rk in ResultKind)
    assert actual == EXPECTED_RESULT_KINDS


def test_result_kind_count_pinned() -> None:
    """The result_kind vocabulary is closed at 16 values."""
    assert len(ResultKind) == 16


@pytest.mark.parametrize("name,value", [
    ("CREATED", "created"),
    ("UPDATED", "updated"),
    ("ARCHIVED", "archived"),
    ("RESTORED", "restored"),
    ("LINKED", "linked"),
    ("UNLINKED", "unlinked"),
    ("REVIEW_OPENED", "review_opened"),
    ("PROPOSAL_DECIDED", "proposal_decided"),
    ("REVIEW_ACCEPTED", "review_accepted"),
    ("UPDATE_DRAFTED", "update_drafted"),
    ("UPDATE_SAVED", "update_saved"),
    ("UPDATE_PUBLISHED", "update_published"),
    ("STEWARD_CONFIGURED", "steward_configured"),
    ("STEWARD_RUN_REQUESTED", "steward_run_requested"),
    ("STEWARD_STOPPED", "steward_stopped"),
    ("NO_CHANGE", "no_change"),
])
def test_result_kind_member_pinned(name: str, value: str) -> None:
    """Each member's Python name and string value are pinned."""
    member = ResultKind[name]
    assert member.value == value


# =====================================================================
# Frozen-name pinning: ProjectErrorCode
# =====================================================================

EXPECTED_ERROR_CODES = frozenset({
    "stale_revision",
    "idempotency_conflict",
    "not_found",
    "validation",
    "capability",
})


def test_error_code_values_pinned() -> None:
    """A rename or removal of any error code MUST fail this test."""
    actual = frozenset(ec.value for ec in ProjectErrorCode)
    assert actual == EXPECTED_ERROR_CODES


def test_error_code_count_pinned() -> None:
    """The error-code vocabulary is closed at 5 values."""
    assert len(ProjectErrorCode) == 5


@pytest.mark.parametrize("name,value", [
    ("STALE_REVISION", "stale_revision"),
    ("IDEMPOTENCY_CONFLICT", "idempotency_conflict"),
    ("NOT_FOUND", "not_found"),
    ("VALIDATION", "validation"),
    ("CAPABILITY", "capability"),
])
def test_error_code_member_pinned(name: str, value: str) -> None:
    member = ProjectErrorCode[name]
    assert member.value == value


# =====================================================================
# Envelope: valid shapes
# =====================================================================


def _make_ref(type_name: str, id_str: str) -> QualifiedRef:
    return parse_ref(f"{type_name}:{id_str}")


def test_envelope_minimal_valid() -> None:
    """A minimal envelope with no refs/warnings/errors validates."""
    env = CommandResultEnvelope(
        result_kind=ResultKind.CREATED,
        project_id="proj-123",
        project_revision=1,
    )
    assert validate_envelope(env) == []


def test_envelope_full_valid() -> None:
    """A fully populated envelope validates."""
    env = CommandResultEnvelope(
        result_kind=ResultKind.UPDATED,
        project_id="proj-456",
        project_revision=3,
        changed_refs=(
            _make_ref("meeting", "mtg-1"),
            _make_ref("decision", "dec-2"),
        ),
        warnings=(ProjectWarning(code="coverage_partial", message="ok"),),
        errors=(),
    )
    assert validate_envelope(env) == []


def test_envelope_changed_refs_validated_through_refs_module() -> None:
    """changed_refs are QualifiedRef instances (from holdspeak.refs)."""
    ref = _make_ref("meeting", "mtg-1")
    assert isinstance(ref, QualifiedRef)
    assert ref.is_registered is True
    env = CommandResultEnvelope(
        result_kind=ResultKind.LINKED,
        project_id="proj-1",
        project_revision=2,
        changed_refs=(ref,),
    )
    assert validate_envelope(env) == []


# =====================================================================
# Envelope: bad shapes
# =====================================================================


def test_envelope_empty_project_id() -> None:
    env = CommandResultEnvelope(
        result_kind=ResultKind.CREATED,
        project_id="",
        project_revision=0,
    )
    violations = validate_envelope(env)
    assert any("project_id" in v for v in violations)


def test_envelope_negative_revision() -> None:
    env = CommandResultEnvelope(
        result_kind=ResultKind.CREATED,
        project_id="proj-1",
        project_revision=-1,
    )
    violations = validate_envelope(env)
    assert any("project_revision" in v for v in violations)


def test_envelope_unregistered_ref_type() -> None:
    """An unregistered type in changed_refs is a violation."""
    ref = parse_ref("unicorn:rainbow-42")
    assert ref.is_registered is False
    env = CommandResultEnvelope(
        result_kind=ResultKind.UPDATED,
        project_id="proj-1",
        project_revision=1,
        changed_refs=(ref,),
    )
    violations = validate_envelope(env)
    assert any("unregistered" in v for v in violations)


def test_envelope_error_with_valid_code() -> None:
    """An error with a valid ProjectErrorCode validates."""
    env = CommandResultEnvelope(
        result_kind=ResultKind.NO_CHANGE,
        project_id="proj-1",
        project_revision=1,
        errors=(
            ProjectError(
                code=ProjectErrorCode.STALE_REVISION,
                message="revision 2 is stale; current is 3",
            ),
        ),
    )
    assert validate_envelope(env) == []


def test_envelope_frozen() -> None:
    """The envelope is immutable (frozen dataclass)."""
    env = CommandResultEnvelope(
        result_kind=ResultKind.CREATED,
        project_id="proj-1",
        project_revision=1,
    )
    with pytest.raises(AttributeError):
        env.project_id = "changed"  # type: ignore[misc]


# =====================================================================
# ID prefixes: pinned set (SS4.1)
# =====================================================================

EXPECTED_PREFIXES = frozenset({
    "pitem_", "psrc_", "pobs_", "pprop_", "prev_",
    "pupd_", "pchg_", "pcmd_", "pstpol_", "pstrun_", "pststep_",
})


def test_id_prefixes_pinned() -> None:
    """All eleven SS4.1 prefixes are present and no extras."""
    assert frozenset(ID_PREFIXES.keys()) == EXPECTED_PREFIXES


def test_id_prefix_count_pinned() -> None:
    assert len(ID_PREFIXES) == 11


def test_deterministic_prefixes_pinned() -> None:
    """Only pobs_, pprop_, pchg_ are deterministic."""
    assert DETERMINISTIC_PREFIXES == frozenset({"pobs_", "pprop_", "pchg_"})


# =====================================================================
# ID generators: non-deterministic produce valid IDs
# =====================================================================

_NON_DETERMINISTIC_GENERATORS = [
    ("pitem_", generate_pitem_id),
    ("psrc_", generate_psrc_id),
    ("prev_", generate_prev_id),
    ("pupd_", generate_pupd_id),
    ("pcmd_", generate_pcmd_id),
    ("pstpol_", generate_pstpol_id),
    ("pstrun_", generate_pstrun_id),
    ("pststep_", generate_pststep_id),
]


@pytest.mark.parametrize("prefix,generator", _NON_DETERMINISTIC_GENERATORS,
                         ids=[p for p, _ in _NON_DETERMINISTIC_GENERATORS])
def test_non_deterministic_generator_produces_valid_id(
    prefix: str, generator
) -> None:
    id_str = generator()
    assert id_str.startswith(prefix)
    assert validate_id(id_str, prefix) is True


@pytest.mark.parametrize("prefix,generator", _NON_DETERMINISTIC_GENERATORS,
                         ids=[p for p, _ in _NON_DETERMINISTIC_GENERATORS])
def test_non_deterministic_generator_uniqueness(
    prefix: str, generator
) -> None:
    """Two calls produce different IDs."""
    a = generator()
    b = generator()
    assert a != b


# =====================================================================
# ID generators: deterministic produce valid and repeatable IDs
# =====================================================================


def test_pobs_generator_valid() -> None:
    id_str = generate_pobs_id(
        adapter="github_pr",
        source_id="psrc_abc123",
        source_version="v42",
        fact_key="pr:123:status",
    )
    assert validate_pobs_id(id_str) is True


def test_pobs_generator_deterministic() -> None:
    """Same inputs produce the same ID."""
    kwargs = dict(
        adapter="github_pr",
        source_id="psrc_abc123",
        source_version="v42",
        fact_key="pr:123:status",
    )
    a = generate_pobs_id(**kwargs)
    b = generate_pobs_id(**kwargs)
    assert a == b


def test_pobs_generator_different_inputs() -> None:
    """Different inputs produce different IDs."""
    a = generate_pobs_id(
        adapter="github_pr",
        source_id="psrc_abc",
        source_version="v1",
        fact_key="pr:1:status",
    )
    b = generate_pobs_id(
        adapter="github_pr",
        source_id="psrc_abc",
        source_version="v2",
        fact_key="pr:1:status",
    )
    assert a != b


def test_pprop_generator_valid() -> None:
    id_str = generate_pprop_id(
        project_id="proj-123",
        review_window_key="rev-window-42",
        proposal_kind="add_item",
        target_ref="meeting:mtg-1",
        normalized_patch='{"field":"value"}',
    )
    assert validate_pprop_id(id_str) is True


def test_pprop_generator_deterministic() -> None:
    kwargs = dict(
        project_id="proj-123",
        review_window_key="rev-window-42",
        proposal_kind="add_item",
        target_ref="meeting:mtg-1",
        normalized_patch='{"field":"value"}',
    )
    a = generate_pprop_id(**kwargs)
    b = generate_pprop_id(**kwargs)
    assert a == b


def test_pprop_generator_different_inputs() -> None:
    base = dict(
        project_id="proj-123",
        review_window_key="rev-window-42",
        proposal_kind="add_item",
        target_ref="meeting:mtg-1",
        normalized_patch='{"field":"value"}',
    )
    a = generate_pprop_id(**base)
    changed = {**base, "normalized_patch": '{"field":"other"}'}
    b = generate_pprop_id(**changed)
    assert a != b


def test_pchg_generator_valid() -> None:
    id_str = generate_pchg_id(
        project_id="proj-123",
        project_revision=5,
        ordinal=0,
    )
    assert validate_pchg_id(id_str) is True


def test_pchg_generator_deterministic() -> None:
    kwargs = dict(project_id="proj-123", project_revision=5, ordinal=0)
    a = generate_pchg_id(**kwargs)
    b = generate_pchg_id(**kwargs)
    assert a == b


def test_pchg_generator_different_ordinal() -> None:
    a = generate_pchg_id(project_id="proj-1", project_revision=5, ordinal=0)
    b = generate_pchg_id(project_id="proj-1", project_revision=5, ordinal=1)
    assert a != b


def test_pchg_generator_different_revision() -> None:
    a = generate_pchg_id(project_id="proj-1", project_revision=5, ordinal=0)
    b = generate_pchg_id(project_id="proj-1", project_revision=6, ordinal=0)
    assert a != b


# =====================================================================
# ID validators: each prefix validates its own and rejects others
# =====================================================================

_VALIDATORS = [
    ("pitem_", validate_pitem_id),
    ("psrc_", validate_psrc_id),
    ("pobs_", validate_pobs_id),
    ("pprop_", validate_pprop_id),
    ("prev_", validate_prev_id),
    ("pupd_", validate_pupd_id),
    ("pchg_", validate_pchg_id),
    ("pcmd_", validate_pcmd_id),
    ("pstpol_", validate_pstpol_id),
    ("pstrun_", validate_pstrun_id),
    ("pststep_", validate_pststep_id),
]


@pytest.mark.parametrize("prefix,validator", _VALIDATORS,
                         ids=[p for p, _ in _VALIDATORS])
def test_validator_accepts_own_prefix(prefix: str, validator) -> None:
    # Use a known-good 32-hex-char suffix.
    id_str = prefix + "a" * 32
    assert validator(id_str) is True


@pytest.mark.parametrize("prefix,validator", _VALIDATORS,
                         ids=[p for p, _ in _VALIDATORS])
def test_validator_rejects_wrong_prefix(prefix: str, validator) -> None:
    # Pick a different prefix.
    other = next(p for p in EXPECTED_PREFIXES if p != prefix)
    id_str = other + "b" * 32
    assert validator(id_str) is False


@pytest.mark.parametrize("prefix,validator", _VALIDATORS,
                         ids=[p for p, _ in _VALIDATORS])
def test_validator_rejects_short_hex(prefix: str, validator) -> None:
    id_str = prefix + "a" * 31  # 31 chars, not 32
    assert validator(id_str) is False


@pytest.mark.parametrize("prefix,validator", _VALIDATORS,
                         ids=[p for p, _ in _VALIDATORS])
def test_validator_rejects_no_prefix(prefix: str, validator) -> None:
    id_str = "a" * 32
    assert validator(id_str) is False


def test_validate_id_rejects_unknown_prefix() -> None:
    with pytest.raises(ValueError, match="Unknown prefix"):
        validate_id("xyzzy_" + "a" * 32, "xyzzy_")


# =====================================================================
# Error-code table closed
# =====================================================================


def test_error_code_table_closed() -> None:
    """The error codes are a closed enum -- no subclassing or mutation."""
    # Enum members cannot be added at runtime in Python.
    # This test verifies the exact set matches our expectation.
    actual = frozenset(ec.value for ec in ProjectErrorCode)
    assert actual == EXPECTED_ERROR_CODES
    # Also verify no accidental duplicates.
    assert len(ProjectErrorCode) == len(actual)


# =====================================================================
# Deterministic collision resistance
# =====================================================================


def test_deterministic_no_prefix_collision() -> None:
    """The length-prefixing prevents ('ab','cd') == ('a','bcd')."""
    a = generate_pobs_id(
        adapter="ab", source_id="cd", source_version="", fact_key="",
    )
    b = generate_pobs_id(
        adapter="a", source_id="bcd", source_version="", fact_key="",
    )
    assert a != b
