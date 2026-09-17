"""HS-200-46 — a stale document fails CI instead of misleading the next agent.

Planned suite: ``phase200_doc_claims``.

The registry (``tests/unit/doc_claims/registry.py``) holds one row per
load-bearing sentence, each with a predicate over the REAL module, file, or
generated surface.  This module turns those rows into a fence that fails in
both directions:

* a ``holds`` sentence whose code stops satisfying it fails;
* a ``known_false`` sentence whose code STARTS satisfying it fails, so the
  fix cannot land without correcting the prose in the same commit;
* the anchor of every row must still be findable, so a moved or deleted
  sentence fails rather than silently stopping being checked;
* the ``known_false`` count is a dated, down-only ratchet.
"""
from __future__ import annotations

import pytest

from tests.unit.doc_claims.registry import (
    CLAIMS,
    KNOWN_FALSE_RATCHET,
    KNOWN_FALSE_RATCHET_DATE,
    KNOWN_FALSE_RATCHET_REASON,
    Claim,
    known_false_claims,
)

_IDS = [claim.label for claim in CLAIMS]


def _where(claim: Claim) -> str:
    line = claim.anchor_line()
    return f"{claim.doc}:{line}" if line else claim.doc


def _owner(claim: Claim) -> str:
    return f"owned by {claim.story}" if claim.story else "no story owns the repair"


@pytest.mark.parametrize("claim", CLAIMS, ids=_IDS)
def test_registered_claim_anchor_is_still_in_its_document(claim: Claim) -> None:
    """The sentence must still be where the registry says it is."""
    path = claim.path()
    assert path.exists(), f"{claim.doc} is gone; the claim row must go with it"
    assert claim.anchor in path.read_text(encoding="utf-8"), (
        f"a registered documentation claim has MOVED or been DELETED: {claim.doc}\n"
        f"  anchor not found: {claim.anchor!r}\n"
        f"  the claim: {claim.sentence}\n"
        "  Either restore the sentence, or update/remove its row in "
        "tests/unit/doc_claims/registry.py in the same commit."
    )


@pytest.mark.parametrize("claim", CLAIMS, ids=_IDS)
def test_registered_claim_matches_its_state(claim: Claim) -> None:
    """A ``holds`` claim must stay true; a ``known_false`` claim must stay false."""
    assert claim.state in {"holds", "known_false"}, claim.state
    satisfied = bool(claim.predicate())

    if claim.state == "holds":
        assert satisfied, (
            f"a documentation claim that used to HOLD is now FALSE: {_where(claim)}\n"
            f"  the sentence: {claim.sentence}\n"
            f"  what is true: {claim.truth}\n"
            "  Fix the code, or correct the sentence AND its registry row "
            "(tests/unit/doc_claims/registry.py) in this same commit."
        )
        return

    assert not satisfied, (
        f"a KNOWN-FALSE documentation claim is now SATISFIED by the code: "
        f"{_where(claim)}\n"
        f"  the sentence: {claim.sentence}\n"
        f"  what the registry recorded as true: {claim.truth}\n"
        f"  {_owner(claim)}\n"
        "  This is good news and still a failure: fix the sentence in the same "
        "commit and move this claim to holds (state=\"holds\", with truth "
        "rewritten to what the code now does, and lower KNOWN_FALSE_RATCHET)."
    )


def test_known_false_count_is_a_down_only_ratchet() -> None:
    """The recorded debt may shrink; it may not grow without a named reason."""
    live = known_false_claims()
    assert len(live) <= KNOWN_FALSE_RATCHET, (
        "the HS-200-46 documentation-claim ratchet has GROWN: "
        f"{len(live)} known_false claims against a ceiling of {KNOWN_FALSE_RATCHET} "
        f"set {KNOWN_FALSE_RATCHET_DATE}.\n"
        "  the recorded reason for the current ceiling: "
        f"{KNOWN_FALSE_RATCHET_REASON}\n"
        "  the known_false rows now in the registry:\n    "
        + "\n    ".join(f"{_where(claim)} ({_owner(claim)})" for claim in live)
        + "\n  A new false sentence is not admitted by raising this number alone: "
        "change KNOWN_FALSE_RATCHET_REASON in the same commit to name the new "
        "debt and why it is being admitted."
    )


def test_ratchet_ceiling_is_not_left_slack() -> None:
    """A healed claim must lower the ceiling, or the permission slip outlives it."""
    live = known_false_claims()
    assert len(live) == KNOWN_FALSE_RATCHET, (
        f"{KNOWN_FALSE_RATCHET - len(live)} documentation claim(s) have been "
        "repaired since the ratchet was set: lower KNOWN_FALSE_RATCHET to "
        f"{len(live)} (and refresh KNOWN_FALSE_RATCHET_DATE / "
        "KNOWN_FALSE_RATCHET_REASON) so the slack cannot absorb a NEW lie."
    )


def test_registry_rows_are_distinct_and_named() -> None:
    """Two rows must not share an identity, or one failure would hide the other."""
    keys = [(claim.doc, claim.anchor) for claim in CLAIMS]
    assert len(keys) == len(set(keys)), "duplicate (doc, anchor) rows in the registry"
    assert len(_IDS) == len(set(_IDS)), f"ambiguous claim ids: {_IDS}"
    for claim in CLAIMS:
        assert claim.sentence.strip(), f"{claim.doc}: a claim needs the author's words"
        assert claim.truth.strip(), f"{claim.doc}: a claim needs its measured truth"
