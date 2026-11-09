# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_lamp_words_guard.py to restore.

# ruff: noqa


# --- test_to_upper_case_only_shrinks: P8: a hand-kept per-file count ledger of toUpperCase() calls (a ratchet, the fence kind #2108 parked)
def test_to_upper_case_only_shrinks():
    now = _upper_lines()
    grew = {k: v for k, v in now.items() if v > UPPER_DEBT.get(k, 0)}
    assert not grew, (
        "a source uppercases a word for the face (say the word in sentence case, "
        "or send it through stateWords):\n" + "\n".join(f"{k}: {v}" for k, v in sorted(grew.items()))
    )
