# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_doctor_plain_words.py to restore.

# ruff: noqa


# --- test_every_row_name_is_plain_words: P8: regex over doctor.py source text; the printed-list tests check the words he reads
def test_every_row_name_is_plain_words() -> None:
    source = (REPO / "holdspeak" / "commands" / "doctor.py").read_text(encoding="utf-8")
    names = set(re.findall(r'name="([^"]+)"', source))
    labels = set(hub_doctor.ROW_LABELS.values())
    assert names and labels
    bad = sorted(n for n in names | labels if JARGON.search(n))
    # `Tool-call gate` and `ffmpeg` / `pactl` name the real tool and command.
    assert [n for n in bad if n != "Tool-call gate"] == []


# --- test_the_hub_database_row_says_notes_not_primitives: P8: regex over doctor.py source text; the printed-list tests check the words he reads
def test_the_hub_database_row_says_notes_not_primitives() -> None:
    source = (REPO / "holdspeak" / "doctor.py").read_text(encoding="utf-8")
    assert '"database", "notes readable"' in source
