"""The stored item sentence has one codec, including punctuation in its subject."""
from pathlib import Path

import pytest

from holdspeak.services import room_claim_editor as sentence
from holdspeak.services.project_definitions import ITEM_LIFECYCLES, SEVERITY_RANK


@pytest.mark.parametrize("kind,state", [(kind, state) for kind, states in ITEM_LIFECYCLES.items() for state in states])
@pytest.mark.parametrize("severity", [None, *SEVERITY_RANK])
@pytest.mark.parametrize("subject", ["Read [the plan]", "[", "]", "A: B -- open", "First\nSecond\n", "[x]: --\nRisk [critical]: nested -- closed", *[f"X{char}- Risk [critical]: injected" for char in ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029", "\x00", "\t", "\x7f", "\u200b")]])
def test_declared_item_sentences_round_trip(kind, severity, subject, state):
    fields = dict(kind=kind, severity=severity, subject=subject, state=state)
    assert sentence.parse(sentence.compose(**fields)) == fields


def test_due_date_is_kept_out_of_the_subject_and_state():
    fields = dict(kind="milestone", severity=None, subject="Keep [x]: --\nthe due plan", state="planned", due="2026-11-20")
    assert sentence.parse(sentence.compose(**fields)) == fields


def test_item_sentence_pattern_is_owned_by_its_codec():
    root = Path(__file__).resolve().parents[2]
    owner = root / "holdspeak/services/room_claim_editor.py"
    # Literal grep for the stored-format regex and the former hand-built
    # templates. Presentation-only words do not own a second storage codec.
    patterns = ("(?P<severity>", "{sev_str}: ", "{severity}: {subject} -- ")
    for folder in (root / "holdspeak", root / "web/src"):
        for path in folder.rglob("*"):
            if path == owner or not path.is_file() or path.suffix not in (".py", ".ts", ".tsx") or any(part in path.parts for part in ("_parked", "__tests__")):
                continue
            text = path.read_text()
            assert not any(pattern in text for pattern in patterns), str(path.relative_to(root))
