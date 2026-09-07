"""Critical journey: P200-A03 — a cold install reaches a kept sentence.

"Cold install reaches an edited, copied or kept sentence without an LLM" is the
first useful result the product promises. This journey proves it on a machine
with **no model file** (`no_local_model` forces the readiness predicate false
for the whole run), no microphone and no network: the speech engine is the one
external adapter substituted, and everything after it — the journal, the
routes, the correction store — is the real product.

The correction leg matters as much as the capture: a sentence you cannot fix
is not a kept sentence, and a correction that silently loses the original is a
critical defect.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.critical

HEARD = "the postgress migration lands on friday"
SAID = "the postgres migration lands on friday"


def _capture(db, *, transcript: str, final_text: str | None = None):
    """One utterance, as the recorder would deliver it.

    The speech engine is the substituted adapter: everything downstream of the
    delivered text — the journal row, its retention, its receipt — is the real
    product path.
    """
    return db.dictation_journal.record(
        source="dictation",
        transcript=transcript,
        final_text=final_text if final_text is not None else transcript,
        total_ms=120.0,
    )


def test_a_cold_install_keeps_a_dictated_sentence_and_reads_it_back(
    db, client
) -> None:
    entry = _capture(db, transcript=HEARD)
    assert entry.id

    listed = client.get("/api/dictation/journal").json()
    items = listed.get("items") or []
    texts = [str(row.get("final_text") or row.get("transcript") or "") for row in items]
    assert HEARD in texts, listed
    assert listed.get("count") == 1, listed


def test_correcting_a_kept_sentence_keeps_the_correction_and_the_original(
    db, client
) -> None:
    entry = _capture(db, transcript=HEARD)

    response = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "text", "heard": HEARD, "said": SAID},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload.get("success") is not False, payload
    assert not payload.get("reason"), payload

    # The correction is kept ...
    corrected = db.dictation_journal.get(entry.id)
    assert corrected is not None
    assert corrected.corrected is True

    # ... and the original heard text is still recoverable. A correction that
    # overwrote history would make the journal unable to explain itself.
    assert HEARD in (corrected.transcript or "")


def test_the_journey_needed_no_model_and_no_inference_target(db) -> None:
    """The cold condition, asserted rather than assumed.

    If a future change routes the first sentence through inference, this fails
    here instead of failing on every machine that has no `~/Models` tree.
    """
    from holdspeak.inference_targets import this_machine_target

    _capture(db, transcript=HEARD)

    target = this_machine_target()
    assert not target.ready, (
        "this journey must run with no local model; a ready target means the "
        "cold condition was not actually enforced"
    )
    assert db.dictation_journal.count() >= 1, "the sentence was kept anyway"
