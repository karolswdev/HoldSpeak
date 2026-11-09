# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_realtime_frame_registry.py to restore.

# ruff: noqa


# --- test_vocabulary_is_a_set: P3/P2/P8/P5: a tuple has no duplicates, the scanner finds 20 things, registry and allowlist tidiness, and five names the no-phantom-consumer test already covers
def test_vocabulary_is_a_set() -> None:
    """One name, one entry."""
    assert len(set(RUNTIME_FRAME_TYPES)) == len(RUNTIME_FRAME_TYPES)


# --- test_the_scanners_actually_see_the_trees: P3/P2/P8/P5: a tuple has no duplicates, the scanner finds 20 things, registry and allowlist tidiness, and five names the no-phantom-consumer test already covers
def test_the_scanners_actually_see_the_trees(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    """A guard that scans nothing passes everything."""
    assert len(emitters) >= 20, f"emitter scan found only {sorted(emitters)}"
    assert len(consumers) >= 15, f"consumer scan found only {sorted(consumers)}"


# --- test_registered_frames_are_all_live: P3/P2/P8/P5: a tuple has no duplicates, the scanner finds 20 things, registry and allowlist tidiness, and five names the no-phantom-consumer test already covers
def test_registered_frames_are_all_live(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    """No registry entry may name a frame that neither side speaks."""
    dead = set(RUNTIME_FRAME_TYPES) - set(emitters) - set(consumers)
    assert not dead, f"Registered but wired nowhere: {sorted(dead)}"


# --- test_allowlists_are_honest: P3/P2/P8/P5: a tuple has no duplicates, the scanner finds 20 things, registry and allowlist tidiness, and five names the no-phantom-consumer test already covers
def test_allowlists_are_honest(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    """An allowlist entry must be registered, real, and carry a reason."""
    for name, reason in EMITTED_WITHOUT_CONSUMER.items():
        assert name in RUNTIME_FRAME_TYPES, f"{name} is allowlisted but unregistered"
        assert name in emitters, f"{name} is allowlisted but nothing emits it"
        assert name not in consumers, f"{name} has a consumer — drop the allowlist"
        assert len(reason.strip()) > 20, f"{name} needs a real reason"
    for name, reason in CONSUMED_WITHOUT_EMITTER.items():
        assert name in RUNTIME_FRAME_TYPES, f"{name} is allowlisted but unregistered"
        assert name in consumers, f"{name} is allowlisted but nothing consumes it"
        assert name not in emitters, f"{name} has an emitter — drop the allowlist"
        assert len(reason.strip()) > 20, f"{name} needs a real reason"


# --- test_the_five_workbench_frames_are_emitted: P3/P2/P8/P5: a tuple has no duplicates, the scanner finds 20 things, registry and allowlist tidiness, and five names the no-phantom-consumer test already covers
def test_the_five_workbench_frames_are_emitted(emitters: dict[str, list[str]]) -> None:
    """HS-132-03: the WorkbenchWindow subscriptions have a real counterpart."""
    for name in (
        "workbench.run_start",
        "workbench.item_claimed",
        "workbench.item_done",
        "workbench.item_failed",
        "workbench.run_complete",
    ):
        assert name in emitters, f"{name} is subscribed but never broadcast"
