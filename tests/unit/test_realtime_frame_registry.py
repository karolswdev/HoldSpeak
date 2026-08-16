"""HS-132-03 — the orphan guard over the one realtime frame vocabulary.

A frame type that is broadcast to nobody is a lie the hub tells itself; a
subscription with no emitter is a surface waiting forever. This test
re-derives both sides from source and fails on either.
"""

from __future__ import annotations

import pytest

from holdspeak.realtime_frames import (
    CONSUMED_WITHOUT_EMITTER,
    EMITTED_WITHOUT_CONSUMER,
    RUNTIME_FRAME_TYPES,
    read_web_mirror,
    repo_root,
    scan_consumers,
    scan_emitters,
)


@pytest.fixture(scope="module")
def emitters() -> dict[str, list[str]]:
    return scan_emitters(repo_root())


@pytest.fixture(scope="module")
def consumers() -> dict[str, list[str]]:
    return scan_consumers(repo_root())


def _fmt(sites: dict[str, list[str]], names: set[str]) -> str:
    return "\n".join(f"  {n}: {', '.join(sites.get(n, [])[:4])}" for n in sorted(names))


def test_vocabulary_is_a_set() -> None:
    """One name, one entry."""
    assert len(set(RUNTIME_FRAME_TYPES)) == len(RUNTIME_FRAME_TYPES)


def test_web_mirror_matches_the_registry() -> None:
    """The web copy is a mirror, not a second opinion."""
    assert read_web_mirror(repo_root()) == RUNTIME_FRAME_TYPES


def test_the_scanners_actually_see_the_trees(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    """A guard that scans nothing passes everything."""
    assert len(emitters) >= 20, f"emitter scan found only {sorted(emitters)}"
    assert len(consumers) >= 15, f"consumer scan found only {sorted(consumers)}"


def test_every_emitted_frame_is_registered(emitters: dict[str, list[str]]) -> None:
    unknown = set(emitters) - set(RUNTIME_FRAME_TYPES)
    assert not unknown, (
        "These frame types are broadcast but absent from RUNTIME_FRAME_TYPES "
        f"(holdspeak/realtime_frames.py):\n{_fmt(emitters, unknown)}"
    )


def test_every_consumed_frame_is_registered(consumers: dict[str, list[str]]) -> None:
    unknown = set(consumers) - set(RUNTIME_FRAME_TYPES)
    assert not unknown, (
        "These frame types are consumed by the web but absent from "
        f"RUNTIME_FRAME_TYPES:\n{_fmt(consumers, unknown)}"
    )


def test_no_frame_is_emitted_with_no_consumer(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    orphans = set(emitters) - set(consumers) - set(EMITTED_WITHOUT_CONSUMER)
    assert not orphans, (
        "These frames are broadcast to nobody. Give each an honest consumer, "
        "or register it in EMITTED_WITHOUT_CONSUMER with a reason:\n"
        f"{_fmt(emitters, orphans)}"
    )


def test_no_frame_is_consumed_with_no_emitter(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    phantoms = set(consumers) - set(emitters) - set(CONSUMED_WITHOUT_EMITTER)
    assert not phantoms, (
        "These subscriptions wait for a frame nothing sends. Emit it, or "
        "retire the subscription:\n"
        f"{_fmt(consumers, phantoms)}"
    )


def test_registered_frames_are_all_live(
    emitters: dict[str, list[str]], consumers: dict[str, list[str]]
) -> None:
    """No registry entry may name a frame that neither side speaks."""
    dead = set(RUNTIME_FRAME_TYPES) - set(emitters) - set(consumers)
    assert not dead, f"Registered but wired nowhere: {sorted(dead)}"


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


def test_intel_token_is_never_journaled() -> None:
    """Article XI.5: the token stream is display material only."""
    root = repo_root()
    for rel in ("holdspeak/meeting_session/intel_admission.py",):
        text = (root / rel).read_text(encoding="utf-8")
        assert "Token broadcasts stay ephemeral and are never journaled." in text
    live = (root / "web/src/pages/cores/LiveCore.tsx").read_text(encoding="utf-8")
    # The stream lands in component state and dies with the surface. If a
    # token ever reaches an apiFetch, this file is the place it would happen.
    assert "intel_token" in live
