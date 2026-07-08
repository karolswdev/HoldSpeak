"""Rails objects as grounding kinds (HS-88-01).

A fake `dw context` runner + a temp repo tree — the resolver's duties
pinned: each kind resolves through the CLI-NAMED trace path, unknown
and unreachable refs refuse by name, the cap+cut, and the receipt rule
(no rail STATE parsed from markdown — the file is opaque text).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from holdspeak import grounding_rails
from holdspeak.grounding import GROUNDING_TRANSCRIPT_CAP
from holdspeak.grounding_rails import hydrate_rails_refs


def _context_doc() -> dict:
    return {
        "kind": "delivery-workbench-roadmap-context",
        "projects": [
            {
                "slug": "holdspeak",
                "readme": "pm/roadmap/holdspeak/README.md",
                "phases": [
                    {
                        "number": 88,
                        "slug": "rails-aware-desk",
                        "status_file": "pm/roadmap/holdspeak/phase-88/current-phase-status.md",
                        "stories": [
                            {
                                "story_id": "HS-88-01",
                                "title": "Rails grounding",
                                "trace": {
                                    "story": "pm/roadmap/holdspeak/phase-88/story-01.md",
                                    "evidence": "pm/roadmap/holdspeak/phase-88/evidence-story-01.md",
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _repo(tmp_path, files: dict[str, str]):
    """Build a repo tree + a runner that returns the context doc and a
    project map pointing at it. Returns (project_map, runner)."""
    repo = tmp_path / "repo"
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    doc = json.dumps(_context_doc())

    def runner(argv, cwd=None):
        assert "context" in argv  # the resolver reads context, nothing else
        return SimpleNamespace(stdout=doc, returncode=0, stderr="")

    project_map = {"projects": {"holdspeak": str(repo)}, "default": str(repo)}
    return project_map, runner


def test_story_ref_hydrates_the_cli_named_file(tmp_path) -> None:
    pm, runner = _repo(
        tmp_path, {"pm/roadmap/holdspeak/phase-88/story-01.md": "# The story body"}
    )
    blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"}],
        project_map=pm,
        runner=runner,
    )
    assert unknown == []
    assert len(blocks) == 1
    b = blocks[0]
    assert b.kind == "rails:story"
    assert b.text == "# The story body"
    assert b.subtitle == "holdspeak/holdspeak"
    assert "HS-88-01" in b.title


def test_phase_evidence_roadmap_each_resolve_their_trace(tmp_path) -> None:
    pm, runner = _repo(
        tmp_path,
        {
            "pm/roadmap/holdspeak/phase-88/current-phase-status.md": "PHASE",
            "pm/roadmap/holdspeak/phase-88/evidence-story-01.md": "EVIDENCE",
            "pm/roadmap/holdspeak/README.md": "ROADMAP",
        },
    )
    refs = [
        {"repo": "holdspeak", "project": "holdspeak", "kind": "phase", "id": "88"},
        {"repo": "holdspeak", "project": "holdspeak", "kind": "evidence", "id": "HS-88-01"},
        {"repo": "holdspeak", "project": "holdspeak", "kind": "roadmap", "id": "holdspeak"},
    ]
    blocks, unknown = hydrate_rails_refs(refs, project_map=pm, runner=runner)
    assert unknown == []
    assert [b.text for b in blocks] == ["PHASE", "EVIDENCE", "ROADMAP"]
    assert [b.kind for b in blocks] == ["rails:phase", "rails:evidence", "rails:roadmap"]


def test_unknown_id_refuses_by_name(tmp_path) -> None:
    pm, runner = _repo(tmp_path, {"pm/roadmap/holdspeak/phase-88/story-01.md": "x"})
    blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-99-99"}],
        project_map=pm,
        runner=runner,
    )
    assert blocks == []
    assert unknown == ["story:HS-99-99"]


def test_repo_not_in_the_map_refuses(tmp_path) -> None:
    pm, runner = _repo(tmp_path, {})
    _blocks, unknown = hydrate_rails_refs(
        [{"repo": "ghost", "project": "holdspeak", "kind": "story", "id": "HS-88-01"}],
        project_map=pm,
        runner=runner,
    )
    assert unknown == ["story:HS-88-01"]


def test_bad_kind_refuses(tmp_path) -> None:
    pm, runner = _repo(tmp_path, {})
    _blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "secret", "id": "x"}],
        project_map=pm,
        runner=runner,
    )
    assert unknown == ["secret:x"]


def test_dw_unavailable_refuses(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    pm = {"projects": {"holdspeak": str(repo)}, "default": str(repo)}

    def runner(argv, cwd=None):
        return SimpleNamespace(stdout="", returncode=1, stderr="dw boom")

    _blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"}],
        project_map=pm,
        runner=runner,
    )
    assert unknown == ["story:HS-88-01"]


def test_a_named_path_the_repo_does_not_hold_refuses(tmp_path) -> None:
    # dw names the trace path, but the file is absent — a receipt that
    # cannot be read is not a best-effort block.
    pm, runner = _repo(tmp_path, {})  # no files written
    _blocks, unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"}],
        project_map=pm,
        runner=runner,
    )
    assert unknown == ["story:HS-88-01"]


def test_over_cap_rail_content_is_cut_and_marked(tmp_path) -> None:
    big = "z" * (GROUNDING_TRANSCRIPT_CAP + 500)
    pm, runner = _repo(tmp_path, {"pm/roadmap/holdspeak/phase-88/story-01.md": big})
    blocks, _unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"}],
        project_map=pm,
        runner=runner,
    )
    assert "[rail object cut at" in blocks[0].text
    assert len(blocks[0].text) < len(big)


def test_one_context_fetch_per_repo(tmp_path) -> None:
    # Two refs into the same repo → the context is read once (cached).
    pm, runner = _repo(
        tmp_path,
        {
            "pm/roadmap/holdspeak/phase-88/story-01.md": "S",
            "pm/roadmap/holdspeak/phase-88/current-phase-status.md": "P",
        },
    )
    calls = {"n": 0}
    doc = json.dumps(_context_doc())

    def counting_runner(argv, cwd=None):
        calls["n"] += 1
        return SimpleNamespace(stdout=doc, returncode=0, stderr="")

    hydrate_rails_refs(
        [
            {"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-01"},
            {"repo": "holdspeak", "project": "holdspeak", "kind": "phase", "id": "88"},
        ],
        project_map=pm,
        runner=counting_runner,
    )
    assert calls["n"] == 1
