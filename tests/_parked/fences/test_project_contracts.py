# PARKED 2026-11-09 (fences diet, pipe/fences-diet): three length pins (16 result kinds, 5 error codes, 11 id prefixes); each must be edited when a value is added.
# Replaced by the value-pinning tests that stay live in tests/unit/test_project_contracts.py (a renamed or removed value still fails).
from holdspeak.project_contracts import ID_PREFIXES, ProjectErrorCode, ResultKind


def test_result_kind_count_pinned() -> None:
    """The result_kind vocabulary is closed at 16 values."""
    assert len(ResultKind) == 16


def test_error_code_count_pinned() -> None:
    """The error-code vocabulary is closed at 5 values."""
    assert len(ProjectErrorCode) == 5


def test_id_prefix_count_pinned() -> None:
    assert len(ID_PREFIXES) == 11
