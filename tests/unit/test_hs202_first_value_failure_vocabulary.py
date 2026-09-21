"""HS-202-02 — the hub knows every failure name the face can send.

`FirstWords` posts its `DictationFailure` string as `failure_category` on
the first-value receipt (`web/src/desk/firstValue.ts:130-139`), and
`onboarding.finish_attempt` refuses a name it does not hold
(`holdspeak/db/onboarding.py:227-228`), which answers 400 and leaves the
attempt open.

Story 02 added `no_microphone` to the face. The shot walk caught the
consequence immediately — `400 POST /api/setup/first-value/<id>/finish`
on both widths — so the name is added here too, and this fence keeps the
two vocabularies from drifting again.
"""
from __future__ import annotations

import re
from pathlib import Path

from holdspeak.db.onboarding import FIRST_VALUE_FAILURES

_REPO = Path(__file__).resolve().parents[2]
_RECOVERY = _REPO / "web" / "src" / "lib" / "dictationRecovery.ts"

# The three HS-132-05 streaming refusals the hub has never accepted. They
# are a REAL gap with the same shape (a face that names one of them cannot
# close its first-value receipt), found while fixing `no_microphone` and
# reported rather than silently widened into this story.
KNOWN_GAP = {"mic_interval_closed", "provider_failure", "audio_floor_held"}


def _client_failures() -> set[str]:
    """The `DictationFailure` union, read from the client's own source."""
    text = _RECOVERY.read_text()
    union = text[text.index("export type DictationFailure ="):]
    union = union[: union.index(";")]
    # Comments inside the union quote words too; only the members count.
    union = re.sub(r"/\*.*?\*/", "", union, flags=re.S)
    union = re.sub(r"//[^\n]*", "", union)
    return set(re.findall(r'"([a-z_]+)"', union))


def test_the_face_and_the_hub_agree_on_no_microphone() -> None:
    assert "no_microphone" in _client_failures()
    assert "no_microphone" in FIRST_VALUE_FAILURES


def test_no_failure_name_drifts_except_the_reported_gap() -> None:
    missing = _client_failures() - FIRST_VALUE_FAILURES
    assert missing == KNOWN_GAP, (
        "a failure name the face can send that the hub refuses; "
        f"unexpected: {sorted(missing - KNOWN_GAP)}"
    )


def test_the_hub_invents_no_name_the_face_cannot_send() -> None:
    assert FIRST_VALUE_FAILURES <= _client_failures()
