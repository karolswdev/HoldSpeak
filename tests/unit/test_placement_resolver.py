"""HS-130-01 — the precedence resolver: one placement authority.

One function turns a stored placement pointer into an effective target AND its
provenance. Precedence: invocation → Workbench → Agent/capability → global.
``None``/unset at every tier inherits DOWN; the global default is the one
terminal, NAMED fallback. These tests pin each tier, each inherit-down path,
the Agent-honored regression (audit-2 claim 3), and the inline-fallback guard.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import (
    GLOBAL_DEFAULT_TARGET_ID,
    PLACEMENT_SOURCES,
    THIS_MACHINE_ID,
    resolve_placement,
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    reset_database()
    database = Database(tmp_path / "placement.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    # A real private-endpoint profile the Agent tier can point at.
    database.profiles.upsert(
        profile_id="lan",
        name="LAN box",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8000/v1",
        model="Qwen",
    )
    database.profiles.upsert(
        profile_id="wbtarget",
        name="Workbench box",
        kind="openAICompatible",
        base_url="http://192.168.1.50:8000/v1",
        model="Qwen",
    )
    yield database
    reset_database()


def test_the_named_global_default_is_the_one_terminal_fallback(db) -> None:
    # Everything unset → the explicit, named global default. NOT reached by an
    # accidental ``pointer or "this_machine"``.
    res = resolve_placement(db, invocation=None, workbench=None, agent=None)
    assert res.source == "global"
    assert res.effective_target_id == GLOBAL_DEFAULT_TARGET_ID == THIS_MACHINE_ID
    assert res.target.id == THIS_MACHINE_ID


def test_workbench_override_wins_over_agent_and_global(db) -> None:
    res = resolve_placement(db, workbench="wbtarget", agent="lan")
    assert res.source == "workbench"
    assert res.effective_target_id == "wbtarget"
    assert res.target.kind == "private_endpoint"


def test_invocation_override_wins_over_everything(db) -> None:
    res = resolve_placement(db, invocation="lan", workbench="wbtarget", agent="wbtarget")
    assert res.source == "invocation"
    assert res.effective_target_id == "lan"


def test_workbench_unset_plus_agent_set_resolves_to_agent(db) -> None:
    # Audit-2 claim 3 regression: this was SILENTLY ignored (old code computed
    # ``wb.profile_id or "this_machine"`` and never consulted the Agent). Old
    # behavior would have resolved to ``this_machine``; the new behavior honors
    # the Agent's private endpoint with source "agent".
    old_behavior = (None) or "this_machine"  # what the deleted line computed
    assert old_behavior == "this_machine"

    res = resolve_placement(db, workbench=None, agent="lan")
    assert res.source == "agent"
    assert res.effective_target_id == "lan"
    assert res.target.id == "lan"
    assert res.target.id != old_behavior


def test_blank_string_tiers_inherit_down_like_none(db) -> None:
    # Empty/whitespace pointers are UNSET, not a request for a blank target.
    res = resolve_placement(db, invocation="", workbench="   ", agent="lan")
    assert res.source == "agent"
    assert res.effective_target_id == "lan"


def test_placement_dict_is_the_wire_shape(db) -> None:
    res = resolve_placement(db, agent="lan")
    assert res.placement_dict() == {"effective_target_id": "lan", "source": "agent"}
    assert set(PLACEMENT_SOURCES) == {"invocation", "workbench", "agent", "global"}


# ── The inline-fallback guard (rides with the invariant it protects) ──────────

# Files this story migrated onto the resolver. Reintroducing an inline
# ``… or "this_machine"`` placement fallback in any of them regrows owner #9.
_GUARDED_FILES = (
    "holdspeak/workbench_conductor.py",
    "holdspeak/services/workbench_service.py",
)
_INLINE_FALLBACK = re.compile(r'or\s+["\']this_machine["\']')


def _repo_root() -> Path:
    # tests/unit/<file> → repo root two parents up.
    return Path(__file__).resolve().parents[2]


def test_no_inline_this_machine_fallback_in_migrated_files() -> None:
    root = _repo_root()
    offenders = []
    for rel in _GUARDED_FILES:
        text = (root / rel).read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _INLINE_FALLBACK.search(line):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Inline `or \"this_machine\"` placement fallback reintroduced outside "
        "the resolver — route it through resolve_placement instead:\n"
        + "\n".join(offenders)
    )


def test_the_guard_actually_fires_on_a_reintroduced_fallback() -> None:
    # Prove the guard is not vacuous: the pattern it forbids really matches.
    assert _INLINE_FALLBACK.search('target = resolve(db, wb.profile_id or "this_machine")')
    assert _INLINE_FALLBACK.search("x = y or 'this_machine'")
    assert not _INLINE_FALLBACK.search("target = resolve_placement(db, workbench=wb.profile_id)")
