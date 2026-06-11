"""HS-59-02 — the spoken-symbol dictionary.

The contract: an empty dictionary is byte-identical (locked against a
golden set of built-in behaviors); user entries merge over the built-ins
with the user winning on a spoken-phrase conflict; attach semantics land
the documented spacing; longest-first matching holds across merged tables;
the user's symbol is literal text, never a regex template.
"""
from __future__ import annotations

import pytest

from holdspeak.config import (
    DictationConfig,
    DictationConfigError,
    validate_spoken_symbols,
)
from holdspeak.text_processor import TextProcessor

# ── the byte-identical lock ──────────────────────────────────────────────────

GOLDEN_BUILTINS = [
    ("hello period", "hello."),
    ("hello comma world", "hello, world"),
    ("open quote hi close quote", '"hi"'),
    ("self dash aware", "self-aware"),
    ("one new line two", "one\ntwo"),
    ("periodic table", "periodic table"),  # word boundaries hold
]


def test_empty_dictionary_is_byte_identical() -> None:
    bare = TextProcessor()
    empty = TextProcessor(spoken_symbols=[])
    for spoken, expected in GOLDEN_BUILTINS:
        assert bare._process_punctuation(spoken) == expected
        assert empty._process_punctuation(spoken) == expected


# ── attach semantics ─────────────────────────────────────────────────────────


def test_plain_replacement_keeps_spacing() -> None:
    tp = TextProcessor(spoken_symbols=[{"spoken": "arrow", "symbol": "→", "attach": "none"}])
    assert tp._process_punctuation("x arrow y") == "x → y"


def test_attach_left_glues_to_the_previous_word() -> None:
    tp = TextProcessor(spoken_symbols=[{"spoken": "bang", "symbol": "!", "attach": "left"}])
    assert tp._process_punctuation("wow bang") == "wow!"


def test_attach_right_glues_to_the_next_word() -> None:
    tp = TextProcessor(spoken_symbols=[{"spoken": "tilde", "symbol": "~", "attach": "right"}])
    assert tp._process_punctuation("cd tilde slash") == "cd ~slash"


def test_attach_both_glues_both_sides() -> None:
    tp = TextProcessor(spoken_symbols=[{"spoken": "double colon", "symbol": "::", "attach": "both"}])
    assert tp._process_punctuation("std double colon vector") == "std::vector"


def test_symbol_is_literal_never_a_regex_template() -> None:
    tp = TextProcessor(
        spoken_symbols=[{"spoken": "backslash g", "symbol": r"\g<oops>", "attach": "none"}]
    )
    assert tp._process_punctuation("a backslash g b") == r"a \g<oops> b"


# ── the merge rules ──────────────────────────────────────────────────────────


def test_user_overrides_a_builtin() -> None:
    tp = TextProcessor(
        spoken_symbols=[{"spoken": "period", "symbol": "。", "attach": "left"}]
    )
    assert tp._process_punctuation("hello period") == "hello。"
    # The class table is untouched (instances do not mutate the built-ins).
    assert TextProcessor().ATTACH_LEFT["period"] == "."
    assert TextProcessor()._process_punctuation("hello period") == "hello."


def test_user_can_move_a_builtin_to_another_mode() -> None:
    # "dash" is built-in attach-both; the user makes it a plain em-free dash.
    tp = TextProcessor(spoken_symbols=[{"spoken": "dash", "symbol": "-", "attach": "none"}])
    assert tp._process_punctuation("a dash b") == "a - b"


def test_longer_user_phrase_beats_shorter_builtin_prefix() -> None:
    tp = TextProcessor(
        spoken_symbols=[{"spoken": "open square bracket", "symbol": "[", "attach": "right"}]
    )
    # "open square bracket" must be consumed whole, not as "open ..." anything.
    assert tp._process_punctuation("list open square bracket zero") == "list [zero"


def test_multiword_plain_runs_before_attach_passes() -> None:
    # The plain entry contains the word "comma" — it must be consumed before
    # the built-in comma pass can eat its inner word.
    tp = TextProcessor(
        spoken_symbols=[{"spoken": "inverted comma", "symbol": "'", "attach": "none"}]
    )
    assert tp._process_punctuation("an inverted comma here") == "an ' here"


# ── config validation ────────────────────────────────────────────────────────


def test_validate_normalizes_and_defaults() -> None:
    out = validate_spoken_symbols([{"spoken": "  Arrow ", "symbol": "→"}])
    assert out == [{"spoken": "Arrow", "symbol": "→", "attach": "none"}]


@pytest.mark.parametrize(
    "bad, message",
    [
        ([{"symbol": "~"}], "spoken phrase must not be empty"),
        ([{"spoken": "tilde"}], "symbol must not be empty"),
        ([{"spoken": "x", "symbol": "y", "attach": "sideways"}], "attach must be one of"),
        ([{"spoken": "x", "symbol": "1"}, {"spoken": "X", "symbol": "2"}], "duplicate spoken phrase"),
        ("nope", "must be a list"),
    ],
)
def test_validate_refuses_malformed(bad, message) -> None:
    with pytest.raises(DictationConfigError, match=message):
        validate_spoken_symbols(bad)


def test_dictation_config_validates_on_construction() -> None:
    with pytest.raises(DictationConfigError):
        DictationConfig(spoken_symbols=[{"spoken": "", "symbol": "~"}])
    cfg = DictationConfig(spoken_symbols=[{"spoken": "tilde", "symbol": "~"}])
    assert cfg.spoken_symbols[0]["attach"] == "none"
    # The default stays empty (byte-identical config shape).
    assert DictationConfig().spoken_symbols == []
