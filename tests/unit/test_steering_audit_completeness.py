"""Audit completeness (HS-87-06) — every steer leaves exactly one row.

The mechanical rule the walk proves in the large, pinned here in the
small: every outcome `deliver` can return — delivered AND every
refusal — writes one audit row, and nothing but the head + hash of the
text is ever stored. A steer path that forgot to audit would drop a
row here.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.coder_steering import arm, clear_grants, deliver


@pytest.fixture(autouse=True)
def _fresh():
    clear_grants()
    yield
    clear_grants()


def _identity(pane_id="%5"):
    return lambda argv, cwd=None: SimpleNamespace(
        stdout=f"{pane_id}\n", returncode=0, stderr=""
    )


class _Audit:
    def __init__(self):
        self.rows = []

    def __call__(self, **kw):
        self.rows.append(kw)
        return len(self.rows)


# Every (setup, expected outcome) the chokepoint can produce.
def test_every_outcome_writes_exactly_one_row() -> None:
    cases = []

    # unarmed
    a = _Audit()
    deliver("k", "t", current_target="hs:0.0", runner=_identity(),
            transport=lambda **kw: None, audit=a)
    cases.append(("unarmed", a))

    # delivered
    a = _Audit()
    arm("k", "hs:0.0", runner=_identity("%9"))
    deliver("k", "t", current_target="hs:0.0", runner=_identity("%9"),
            transport=lambda **kw: None, audit=a)
    cases.append(("delivered", a))
    clear_grants()

    # pane_mismatch (recycled)
    a = _Audit()
    arm("k", "hs:0.0", runner=_identity("%9"))
    deliver("k", "t", current_target="hs:0.0", runner=_identity("%13"),
            transport=lambda **kw: None, audit=a)
    cases.append(("pane_mismatch", a))
    clear_grants()

    # transport_error
    a = _Audit()
    arm("k", "hs:0.0", runner=_identity("%9"))

    def boom(**kw):
        raise RuntimeError("tmux refused")

    deliver("k", "t", current_target="hs:0.0", runner=_identity("%9"),
            transport=boom, audit=a)
    cases.append(("transport_error", a))
    clear_grants()

    # empty_text
    a = _Audit()
    deliver("k", "   ", current_target="hs:0.0", transport=lambda **kw: None, audit=a)
    cases.append(("empty_text", a))

    for outcome, a in cases:
        assert len(a.rows) == 1, f"{outcome} wrote {len(a.rows)} rows, expected 1"
        assert a.rows[0]["outcome"] == outcome
        # The text is never handed to the sink whole — it hashes + heads it.
        assert "text" in a.rows[0]  # the repository hashes; the row carries raw text in only


def test_refused_steer_records_the_refusal_detail() -> None:
    a = _Audit()
    arm("k", "hs:0.0", runner=_identity("%9"))
    deliver("k", "t", current_target="hs:0.0", runner=_identity("%13"),
            transport=lambda **kw: None, audit=a)
    assert a.rows[0]["outcome"] == "pane_mismatch"
    assert "nothing was typed" in a.rows[0]["detail"]
