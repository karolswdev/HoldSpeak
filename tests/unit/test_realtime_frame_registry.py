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


