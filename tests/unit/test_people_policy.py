from __future__ import annotations

import pytest

from holdspeak.people.policy import PeopleOperation, PeoplePolicy, PeopleUse, Visibility


@pytest.mark.parametrize("visibility", list(Visibility))
@pytest.mark.parametrize("operation", list(PeopleOperation))
def test_pr1_allows_only_local_owner_read_and_write(visibility: Visibility, operation: PeopleOperation) -> None:
    expected = operation in {PeopleOperation.READ, PeopleOperation.WRITE}
    assert PeoplePolicy.allows(visibility, operation) is expected
    assert PeoplePolicy.refusal(visibility, operation) == (None if expected else "people_operation_unsupported")


def test_unknown_visibility_is_refused() -> None:
    assert PeoplePolicy.allows("private", PeopleOperation.READ) is False  # type: ignore[arg-type]


@pytest.mark.parametrize("use", [use for use in PeopleUse if use is not PeopleUse.SOURCE_CITED_DRAFT])
def test_employment_scoring_surveillance_and_decisions_are_hard_refused(use: PeopleUse) -> None:
    assert PeoplePolicy.refusal_for_use(use) == "people_employment_use_prohibited"


def test_even_source_cited_drafting_is_unavailable_in_manual_pr1() -> None:
    assert PeoplePolicy.refusal_for_use(PeopleUse.SOURCE_CITED_DRAFT) == "people_inference_unsupported"
