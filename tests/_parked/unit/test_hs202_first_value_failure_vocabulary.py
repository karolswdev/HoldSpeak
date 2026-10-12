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

# Astra's counsel finding 7 on PR #595 ruled the debt gets a concrete
# home or is paid here. It is PAID here: the three HS-132-05 streaming
# refusals the face has been able to send since that story now round-trip
# too, so no failure name the owner can see leaves its receipt open.
KNOWN_GAP: set[str] = set()


def _client_failures() -> set[str]:
    """The `DictationFailure` union, read from the client's own source."""
    text = _RECOVERY.read_text()
    # Strip comments FIRST: they quote words and carry semicolons, either
    # of which corrupts the union's boundary or its member list.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    union = text[text.index("export type DictationFailure ="):]
    union = union[: union.index(";")]
    return set(re.findall(r'"([a-z_]+)"', union))


def test_the_face_and_the_hub_agree_on_the_microphone_names() -> None:
    for name in ("no_microphone", "microphone_unavailable"):
        assert name in _client_failures(), name
        assert name in FIRST_VALUE_FAILURES, name


def test_every_failure_the_face_can_send_closes_its_receipt() -> None:
    missing = _client_failures() - FIRST_VALUE_FAILURES
    assert missing == KNOWN_GAP, (
        "a failure name the face can send that the hub refuses, so the "
        f"first-value receipt answers 400: {sorted(missing)}"
    )


def test_the_hub_invents_no_name_the_face_cannot_send() -> None:
    assert FIRST_VALUE_FAILURES <= _client_failures()
