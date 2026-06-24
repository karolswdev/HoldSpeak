"""Dogfood plumbing tier — opt-in, no LLM, no microphone.

Mechanically exercises the deterministic half of the dogfood harness so the
fixtures can't silently rot: every scenario YAML is well-formed, every mock
repo's KB + .hs context loads through the real loaders, and every committed
transcript parses into honest cues through the real parser. The LLM-shaped
half (real say -> Whisper -> .43 intel) stays manual in dogfood/PROTOCOL.md.

Run:
    HOLDSPEAK_DOGFOOD=1 uv run pytest -q tests/e2e/test_dogfood_plumbing_e2e.py
Skipped by default.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from holdspeak.agent_context.hs_context import load_hs_project_context
from holdspeak.plugins.dictation.project_kb import read_project_kb
from holdspeak.transcript_parse import parse_transcript

pytestmark = pytest.mark.skipif(
    os.environ.get("HOLDSPEAK_DOGFOOD") != "1",
    reason="set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e",
)

DOGFOOD = Path(__file__).resolve().parents[2] / "dogfood"
REPOS = DOGFOOD / "repos"
SCENARIOS = DOGFOOD / "scenarios"
TRANSCRIPTS = DOGFOOD / "transcripts"

REPO_NAMES = ["ledgerline", "questline", "pylon-infra"]
HS_FILES = ["context.md", "memory.md", "terms.md", "instructions.md", "workflows.md", "issues.md"]
VALID_PROFILES = {"balanced", "architect", "delivery", "product", "incident"}


def _scenario_files() -> list[Path]:
    return sorted(SCENARIOS.glob("*.yaml"))


def test_harness_layout_present():
    assert REPOS.is_dir(), f"missing {REPOS}"
    assert _scenario_files(), "no scenarios found"
    assert TRANSCRIPTS.is_dir(), f"missing {TRANSCRIPTS}"
    for name in REPO_NAMES:
        assert (REPOS / name).is_dir(), f"missing mock repo {name}"


@pytest.mark.parametrize("name", REPO_NAMES)
def test_repo_kb_and_context_load(name):
    root = REPOS / name
    kb = read_project_kb(root)
    assert kb, f"{name}: project.yaml kb did not load"
    assert all(isinstance(v, str) for v in kb.values()), f"{name}: non-string KB value"
    for fname in HS_FILES:
        assert (root / ".hs" / fname).is_file(), f"{name}: missing .hs/{fname}"
    ctx = load_hs_project_context(root)
    assert ctx.get("exists"), f"{name}: .hs context did not load"
    # context.md must reference real files (the repo should be self-consistent)
    assert (root / "README.md").is_file(), f"{name}: missing README"


@pytest.mark.parametrize("path", _scenario_files(), ids=lambda p: p.stem)
def test_scenario_well_formed(path):
    sc = yaml.safe_load(path.read_text())
    assert sc["id"] == path.stem, f"{path.name}: id must match filename stem"
    assert sc["kind"] in {"meeting", "dictation"}, f"{path.name}: bad kind"
    assert sc.get("repo") in REPO_NAMES, f"{path.name}: repo must be a known mock repo"
    assert sc.get("description"), f"{path.name}: missing description"
    if sc["kind"] == "meeting":
        assert sc.get("profile") in VALID_PROFILES, f"{path.name}: bad profile"
        lines = sc.get("lines") or []
        assert len(lines) >= 3, f"{path.name}: meeting needs >=3 lines"
        for ln in lines:
            assert ln.get("speaker") and ln.get("voice") and ln.get("text"), f"{path.name}: bad line"
    else:
        utts = sc.get("utterances") or []
        assert utts, f"{path.name}: dictation needs utterances"
        assert all(isinstance(u, str) and u.strip() for u in utts), f"{path.name}: bad utterance"


def test_every_profile_is_covered():
    profiles = {
        yaml.safe_load(p.read_text()).get("profile")
        for p in _scenario_files()
        if yaml.safe_load(p.read_text()).get("kind") == "meeting"
    }
    missing = VALID_PROFILES - profiles
    assert not missing, f"meeting scenarios miss profiles: {sorted(missing)}"


@pytest.mark.parametrize(
    "fixture", ["pylon-incident.vtt", "ledgerline-sync.srt", "questline-notes.txt"]
)
def test_committed_transcript_parses(fixture):
    path = TRANSCRIPTS / fixture
    parsed = parse_transcript(path.read_text(), path.name)
    assert parsed.cues, f"{fixture}: produced no cues"
    assert all(c.text.strip() for c in parsed.cues), f"{fixture}: empty cue text"
    # each fixture names multiple distinct speakers
    assert len(parsed.speakers_found) >= 2, f"{fixture}: expected multiple speakers"
