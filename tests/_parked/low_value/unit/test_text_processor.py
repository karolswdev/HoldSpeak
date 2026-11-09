# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_text_processor.py to restore.

# ruff: noqa


# --- TestProcessorStateless::test_new_instance_same_behavior: P3/P5: two instances of a class give the same answer; every other test already checks the answer
# (was a method of class TestProcessorStateless)
def test_new_instance_same_behavior(self):
    p1 = TextProcessor()
    p2 = TextProcessor()
    assert p1.process("test period") == p2.process("test period")
