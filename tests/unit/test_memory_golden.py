"""Historical score portability must not mask retrieval regressions."""
from __future__ import annotations

import math
from copy import deepcopy

import pytest

from tests.memory_bench.bench import assert_keyword_golden


GOLDEN = {"question|": {"hits": [{
    "bm25": -0.125,
    "normalized_score": 0.16449065032704363,
    "graph_score": 0.0,
    "rank": 1,
    "source_ref": "note:cutover",
    "snippet": "The cutover is Friday.",
}]}}


def _steps(value: float, count: int) -> float:
    for _ in range(count):
        value = math.nextafter(value, math.copysign(math.inf, value))
    return value


@pytest.mark.parametrize("field,recorded,actual", [
    ("bm25", -2.3381469153451175, -2.338146915345117),
    ("normalized_score", 0.16449065032704363, 0.164490650327043),
    ("normalized_score", 0.22491941435858806, 0.22491941435858748),
    ("bm25", -0.125, _steps(-0.125, 8)),
    ("normalized_score", 0.16449065032704363, _steps(0.16449065032704363, 32)),
])
def test_only_bounded_score_roundoff_matches_the_golden(field, recorded, actual) -> None:
    assert_keyword_golden({field: actual}, {field: recorded})


@pytest.mark.parametrize("field,value", [
    ("bm25", _steps(-0.125, 9)),
    ("bm25", -0.124),
    ("normalized_score", _steps(0.16449065032704363, 33)),
    ("normalized_score", 0.17),
    ("graph_score", math.ulp(0.0)),
    ("rank", 2),
    ("rank", True),
    ("source_ref", "note:another"),
    ("snippet", "The cutover is Saturday."),
    ("bm25", float("nan")),
    ("normalized_score", float("inf")),
])
def test_retrieval_or_score_changes_fail(field, value) -> None:
    changed = deepcopy(GOLDEN)
    changed["question|"]["hits"][0][field] = value
    with pytest.raises(AssertionError):
        assert_keyword_golden(changed, GOLDEN)


def test_absolute_score_bound_still_applies_inside_the_ulp_bound() -> None:
    with pytest.raises(AssertionError):
        assert_keyword_golden({"bm25": _steps(8.0, 1)}, {"bm25": 8.0})


@pytest.mark.parametrize("change", ["missing_field", "extra_field", "extra_hit", "list_type"])
def test_snapshot_structure_stays_exact(change) -> None:
    changed = deepcopy(GOLDEN)
    hit = changed["question|"]["hits"][0]
    if change == "missing_field":
        hit.pop("rank")
    elif change == "extra_field":
        hit["invented"] = "field"
    elif change == "extra_hit":
        changed["question|"]["hits"].append(deepcopy(hit))
    else:
        changed["question|"]["hits"] = tuple(changed["question|"]["hits"])
    with pytest.raises(AssertionError):
        assert_keyword_golden(changed, GOLDEN)
