"""W1-TRUTH (atlas 2026-10-27): a 1:1 title never makes a fake person.

"1:1 Priya / Karol" is Priya and the owner, not "Priya Karol".
"""
from __future__ import annotations

from holdspeak.services.people_suggestions import name_from_one_on_one_title, names_from_one_on_one_title


def _me(name: str) -> bool:
    return name.casefold() in {"karol", "me"}


def _nobody(name: str) -> bool:
    return False


def test_the_owner_name_drops_out_of_a_slash_title() -> None:
    assert name_from_one_on_one_title("1:1 Priya / Karol", _me) == "Priya"
    assert name_from_one_on_one_title("Mira <> Karol 1:1", _me) == "Mira"
    assert name_from_one_on_one_title("1:1 Theo & Karol", _me) == "Theo"


def test_two_names_are_never_joined_into_one_person() -> None:
    assert names_from_one_on_one_title("1:1 Priya / Karol", _nobody) == ["Priya", "Karol"]
    # With no owner name the face does not guess which one he meets.
    assert name_from_one_on_one_title("1:1 Priya / Karol", _nobody) == ""


def test_the_plain_titles_still_name_their_person() -> None:
    assert name_from_one_on_one_title("1:1 with Mira", _me) == "Mira"
    assert name_from_one_on_one_title("Weekly 1:1 with Mira Okafor", _me) == "Mira Okafor"
    assert name_from_one_on_one_title("1:1", _me) == ""
